"""Tools for the Hevy ``/v1/workouts*`` endpoints."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from hevy.models.workouts import (
    DeletedWorkout,
    PaginatedWorkoutEvents,
    PaginatedWorkouts,
    PostWorkoutsRequestWorkout,
    Workout,
    WorkoutCount,
)
from hevy.utils.client import hevy_request

_MAX_PAGE_SIZE = 10


def _validate_page_size(page_size: int | None) -> None:
    """Reject ``page_size`` values outside Hevy's documented workouts max."""
    if page_size is not None and page_size > _MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be <= {_MAX_PAGE_SIZE} for workouts endpoints",
        )


async def list_workouts(
    page: Annotated[
        int | None,
        Field(description="Page number (1-indexed). Defaults to 1 server-side when omitted."),
    ] = None,
    page_size: Annotated[
        int | None,
        Field(
            description=(
                "Number of workouts per page. Hevy max is 10; larger values are rejected "
                "client-side. Defaults to 5 server-side when omitted."
            ),
        ),
    ] = None,
) -> PaginatedWorkouts:
    """List the authenticated user's workouts, newest first.

    Args:
        page: Page number (1-indexed). Omit to use Hevy's default.
        page_size: Items per page (max 10). Omit to use Hevy's default.

    Returns:
        A ``PaginatedWorkouts`` with ``page``, ``page_count``, and the ``workouts``
        on the current page.
    """
    _validate_page_size(page_size)
    data = await hevy_request(
        "GET",
        "/v1/workouts",
        params={"page": page, "pageSize": page_size},
    )
    return PaginatedWorkouts.model_validate(data)


async def get_workout_count() -> WorkoutCount:
    """Get the total number of workouts on the authenticated account.

    Returns:
        A ``WorkoutCount`` wrapping the integer ``workout_count``.
    """
    data = await hevy_request("GET", "/v1/workouts/count")
    return WorkoutCount.model_validate(data)


async def get_workout_events(
    page: Annotated[
        int | None,
        Field(description="Page number (1-indexed). Defaults to 1 server-side when omitted."),
    ] = None,
    page_size: Annotated[
        int | None,
        Field(
            description=(
                "Number of events per page. Hevy max is 10; larger values are rejected "
                "client-side. Defaults to 5 server-side when omitted."
            ),
        ),
    ] = None,
    since: Annotated[
        str | None,
        Field(
            description=(
                "ISO 8601 timestamp (e.g. '2024-01-01T00:00:00Z'). Only events newer than "
                "this are returned. Defaults to 1970-01-01T00:00:00Z server-side when "
                "omitted."
            ),
        ),
    ] = None,
) -> PaginatedWorkoutEvents:
    """List workout events (updates or deletions) since a given date.

    Events are ordered newest to oldest. Useful for keeping a local cache of
    workouts up to date without refetching the entire list.

    The raw Hevy response mixes updates and deletions into a single polymorphic
    list. This tool pre-sorts them into two typed lists on the returned model:

    - ``updated``: list of full ``Workout`` objects that were created or updated.
    - ``deleted``: list of ``DeletedWorkout`` references (just id + deleted_at).

    Callers never have to branch on a discriminator.

    Args:
        page: Page number (1-indexed). Omit to use Hevy's default.
        page_size: Items per page (max 10). Omit to use Hevy's default.
        since: ISO 8601 timestamp; only events after this are returned.

    Returns:
        A ``PaginatedWorkoutEvents`` with ``page``, ``page_count``, ``updated``,
        and ``deleted``.
    """
    _validate_page_size(page_size)
    data = await hevy_request(
        "GET",
        "/v1/workouts/events",
        params={"page": page, "pageSize": page_size, "since": since},
    )
    raw = data or {}
    updated: list[Workout] = []
    deleted: list[DeletedWorkout] = []
    for event in raw.get("events", []):
        event_type = event.get("type")
        if event_type == "updated":
            updated.append(Workout.model_validate(event["workout"]))
        elif event_type == "deleted":
            deleted.append(DeletedWorkout.model_validate(event))
    return PaginatedWorkoutEvents(
        page=raw.get("page", 1),
        page_count=raw.get("page_count", 0),
        updated=updated,
        deleted=deleted,
    )


async def get_workout(
    workout_id: Annotated[
        str,
        Field(description="The ID (UUID) of the workout to fetch."),
    ],
) -> Workout:
    """Fetch a single workout's full details by ID.

    Args:
        workout_id: The ID (UUID) of the workout to fetch.

    Returns:
        The ``Workout`` with all exercises and sets.
    """
    data = await hevy_request("GET", f"/v1/workouts/{workout_id}")
    return Workout.model_validate(data)


async def create_workout(
    workout: Annotated[
        PostWorkoutsRequestWorkout,
        Field(
            description=(
                "The workout payload to create. Provide ``title``, ``start_time``, "
                "``end_time``, and ``exercises`` at minimum. ``description`` and "
                "``is_private`` are optional."
            ),
        ),
    ],
) -> Workout:
    """Create a new workout on the authenticated account.

    The API wraps the workout under a top-level ``{"workout": ...}`` key; this
    tool performs that wrapping for you.

    Args:
        workout: The inner workout object to create.

    Returns:
        The created ``Workout`` as stored by Hevy (including server-assigned ID
        and timestamps).
    """
    json_body = {"workout": workout.model_dump(exclude_none=True, mode="json")}
    data = await hevy_request("POST", "/v1/workouts", json_body=json_body)
    return Workout.model_validate(data)


async def update_workout(
    workout_id: Annotated[
        str,
        Field(description="The ID (UUID) of the workout to update."),
    ],
    workout: Annotated[
        PostWorkoutsRequestWorkout,
        Field(
            description=(
                "The replacement workout payload. Same shape as ``create_workout``. "
                "The provided payload overwrites the existing workout."
            ),
        ),
    ],
) -> Workout:
    """Update an existing workout by ID.

    The API wraps the workout under a top-level ``{"workout": ...}`` key; this
    tool performs that wrapping for you.

    Args:
        workout_id: The ID (UUID) of the workout to update.
        workout: The replacement workout payload.

    Returns:
        The updated ``Workout`` as stored by Hevy.
    """
    json_body = {"workout": workout.model_dump(exclude_none=True, mode="json")}
    data = await hevy_request("PUT", f"/v1/workouts/{workout_id}", json_body=json_body)
    return Workout.model_validate(data)


TOOLS = [
    list_workouts,
    get_workout_count,
    get_workout_events,
    get_workout,
    create_workout,
    update_workout,
]


async def _smoke_reads(session, ctx: dict) -> None:
    """Smoke probe for workouts read tools. Used by tests/smoke_reads.py."""
    from tests.smoke_reads import _call  # late import to avoid test-dep at runtime

    print("\n── workouts ──")
    await _call(session, "get_workout_count")
    page = await _call(session, "list_workouts", {"page_size": 1})
    if page and page.get("workouts"):
        ctx["workout_id"] = page["workouts"][0]["id"]
        await _call(session, "get_workout", {"workout_id": ctx["workout_id"]})
    await _call(session, "get_workout_events", {"page_size": 1})


async def _smoke_writes(session, created: dict) -> None:
    """Smoke probe for workout writes. Creates → gets → updates a single workout."""
    from datetime import UTC, datetime, timedelta

    from tests.smoke_writes import SMOKE_TAG, _call

    print("\n── workouts (writes) ──")
    now = datetime.now(UTC)
    start = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    # Needs a real exercise_template_id — pull from list_exercise_templates first
    tpl_page = await _call(session, "list_exercise_templates", {"page_size": 1})
    tpl_id = None
    if tpl_page and tpl_page.get("exercise_templates"):
        tpl_id = tpl_page["exercise_templates"][0]["id"]
    if not tpl_id:
        print("  ⚠️  skipping workouts write smoke — no exercise template available")
        return
    body = {
        "workout": {
            "title": f"{SMOKE_TAG} test workout",
            "description": "Created by mcp smoke test",
            "start_time": start,
            "end_time": end,
            "is_private": True,
            "exercises": [
                {
                    "exercise_template_id": tpl_id,
                    "sets": [{"type": "normal", "weight_kg": 20.0, "reps": 5}],
                }
            ],
        }
    }
    result = await _call(session, "create_workout", {"workout": body["workout"]})
    if result and result.get("id"):
        created["workout_id"] = result["id"]
        await _call(session, "get_workout", {"workout_id": result["id"]})
        await _call(
            session,
            "update_workout",
            {
                "workout_id": result["id"],
                "workout": {**body["workout"], "title": f"{SMOKE_TAG} updated workout"},
            },
        )
