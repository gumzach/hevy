"""Tools for the ``/v1/routines`` endpoints."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from hevy.models.routines import (
    PaginatedRoutines,
    PostRoutinesRequestRoutine,
    PutRoutinesRequestRoutine,
    Routine,
)
from hevy.utils.client import hevy_request

_MAX_PAGE_SIZE = 10


def _validate_page_size(page_size: int | None) -> None:
    """Reject ``page_size`` values outside Hevy's documented routines max (10)."""
    if page_size is not None and page_size > _MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be <= {_MAX_PAGE_SIZE} for routines endpoints",
        )


async def list_routines(
    page: Annotated[
        int | None,
        Field(description="Page number (1-indexed). Defaults to 1 server-side when omitted."),
    ] = None,
    page_size: Annotated[
        int | None,
        Field(
            description=(
                "Number of routines per page. Hevy max is 10; larger values are rejected "
                "client-side. Defaults to 5 server-side when omitted."
            ),
        ),
    ] = None,
) -> PaginatedRoutines:
    """List the authenticated user's routines.

    Args:
        page: Page number (1-indexed). Omit to use Hevy's default.
        page_size: Items per page (max 10). Omit to use Hevy's default.

    Returns:
        A ``PaginatedRoutines`` with ``page``, ``page_count``, and the ``routines`` list.

    Raises:
        ValueError: If ``page_size`` exceeds 10 (Hevy's documented maximum).
        HevyAPIError: On any non-2xx response from the Hevy API.
    """
    _validate_page_size(page_size)
    data = await hevy_request(
        "GET",
        "/v1/routines",
        params={"page": page, "pageSize": page_size},
    )
    return PaginatedRoutines.model_validate(data or {})


async def get_routine(
    routine_id: Annotated[
        str,
        Field(description="The ID (UUID) of the routine to fetch."),
    ],
) -> Routine:
    """Get a single routine by its ID.

    The Hevy API wraps the response under a ``routine`` key; this tool unwraps it
    and returns the ``Routine`` directly. If the live API ever returns a bare
    Routine payload, we handle that fallback too.

    Args:
        routine_id: UUID of the routine to retrieve.

    Returns:
        The full ``Routine`` including its exercises and sets.

    Raises:
        HevyAPIError: On any non-2xx response (e.g. 404 if the routine does not
            exist or does not belong to the authenticated user).
    """
    data = await hevy_request("GET", f"/v1/routines/{routine_id}")
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected response type for get_routine: {type(data).__name__}")
    payload = data.get("routine", data)
    return Routine.model_validate(payload)


async def create_routine(
    routine: Annotated[
        PostRoutinesRequestRoutine,
        Field(
            description=(
                "The routine to create. Must include a ``title`` and at least one "
                "exercise with one set. ``folder_id`` is optional — pass null to "
                "insert into the default 'My Routines' folder."
            ),
        ),
    ],
) -> Routine:
    """Create a new routine for the authenticated user.

    Args:
        routine: The routine payload (title, optional folder_id, optional notes, exercises).

    Returns:
        The newly-created ``Routine`` as returned by the Hevy API (201).

    Raises:
        HevyAPIError: On any non-2xx response. A ``403`` typically means the
            account's routine limit has been reached.
    """
    body = {"routine": routine.model_dump(exclude_none=True, mode="json")}
    data = await hevy_request("POST", "/v1/routines", json_body=body)
    if isinstance(data, dict) and "routine" in data:
        return Routine.model_validate(data["routine"])
    return Routine.model_validate(data)


async def update_routine(
    routine_id: Annotated[
        str,
        Field(description="The ID (UUID) of the routine to update."),
    ],
    routine: Annotated[
        PutRoutinesRequestRoutine,
        Field(
            description=(
                "Replacement routine state. The PUT body does NOT include "
                "``folder_id`` — a routine cannot be moved between folders via this "
                "endpoint."
            ),
        ),
    ],
) -> Routine:
    """Update an existing routine by replacing its title, notes, and exercises.

    Args:
        routine_id: UUID of the routine to update.
        routine: The full replacement payload (title, optional notes, exercises).

    Returns:
        The updated ``Routine`` as returned by the Hevy API.

    Raises:
        HevyAPIError: On any non-2xx response (e.g. 404 if the routine does not
            exist or does not belong to the authenticated user).
    """
    body = {"routine": routine.model_dump(exclude_none=True, mode="json")}
    data = await hevy_request("PUT", f"/v1/routines/{routine_id}", json_body=body)
    if isinstance(data, dict) and "routine" in data:
        return Routine.model_validate(data["routine"])
    return Routine.model_validate(data)


TOOLS = [list_routines, get_routine, create_routine, update_routine]


# ---------------------------------------------------------------------------
# Smoke probes (invoked from tests/smoke_reads.py and tests/smoke_writes.py)
# ---------------------------------------------------------------------------


async def _smoke_reads(session, ctx: dict) -> None:
    """Smoke probe for routines read tools."""
    from tests.smoke_reads import _call

    print("\n── routines ──")
    page = await _call(session, "list_routines", {"page_size": 1})
    if page and page.get("routines"):
        ctx["routine_id"] = page["routines"][0]["id"]
        await _call(session, "get_routine", {"routine_id": ctx["routine_id"]})


async def _smoke_writes(session, created: dict) -> None:
    """Smoke probe for routine writes."""
    from tests.smoke_writes import SMOKE_TAG, _call

    print("\n── routines (writes) ──")
    # Need an exercise_template_id
    tpl_page = await _call(session, "list_exercise_templates", {"page_size": 1})
    tpl_id = None
    if tpl_page and tpl_page.get("exercise_templates"):
        tpl_id = tpl_page["exercise_templates"][0]["id"]
    if not tpl_id:
        print("  ⚠️  skipping routines write smoke — no exercise template available")
        return
    body = {
        "routine": {
            "title": f"{SMOKE_TAG} test routine",
            "notes": "Created by mcp smoke test",
            "exercises": [
                {
                    "exercise_template_id": tpl_id,
                    "rest_seconds": 60,
                    "sets": [{"type": "normal", "weight_kg": 20.0, "reps": 5}],
                }
            ],
        }
    }
    result = await _call(session, "create_routine", {"routine": body["routine"]})
    if result and result.get("id"):
        created["routine_id"] = result["id"]
        await _call(session, "get_routine", {"routine_id": result["id"]})
        await _call(
            session,
            "update_routine",
            {
                "routine_id": result["id"],
                "routine": {
                    "title": f"{SMOKE_TAG} updated routine",
                    "notes": "Updated",
                    "exercises": body["routine"]["exercises"],
                },
            },
        )
