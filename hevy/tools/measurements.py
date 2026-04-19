"""Tools for the Hevy ``/v1/body_measurements*`` endpoints."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from hevy.models.common import OperationStatus
from hevy.models.measurements import (
    BodyMeasurement,
    PaginatedBodyMeasurements,
    PutBodyMeasurement,
)
from hevy.utils.client import hevy_request

_MAX_PAGE_SIZE = 10


def _validate_page_size(page_size: int | None) -> None:
    """Reject ``page_size`` values outside Hevy's documented body-measurements max."""
    if page_size is not None and page_size > _MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be <= {_MAX_PAGE_SIZE} for body_measurements endpoints",
        )


async def list_body_measurements(
    page: Annotated[
        int | None,
        Field(description="Page number (1-indexed). Defaults to 1 server-side when omitted."),
    ] = None,
    page_size: Annotated[
        int | None,
        Field(
            description=(
                "Number of body measurements per page. Hevy max is 10; larger values are "
                "rejected client-side. Defaults to 10 server-side when omitted."
            ),
        ),
    ] = None,
) -> PaginatedBodyMeasurements:
    """List body measurements for the authenticated user, newest first.

    Args:
        page: Page number (1-indexed). Omit to use Hevy's default.
        page_size: Items per page (max 10). Omit to use Hevy's default.

    Returns:
        A ``PaginatedBodyMeasurements`` with ``page``, ``page_count``, and the
        list of ``body_measurements`` on the requested page.
    """
    _validate_page_size(page_size)
    data = await hevy_request(
        "GET",
        "/v1/body_measurements",
        params={"page": page, "pageSize": page_size},
    )
    return PaginatedBodyMeasurements.model_validate(data)


async def get_body_measurement(
    date: Annotated[
        str,
        Field(
            description=(
                "The date of the body measurement in YYYY-MM-DD format (e.g. '2024-08-14')."
            ),
        ),
    ],
) -> BodyMeasurement:
    """Get the body measurement recorded on a specific date.

    Args:
        date: The measurement date in YYYY-MM-DD format.

    Returns:
        The ``BodyMeasurement`` for that date.

    Raises:
        HevyAPIError: With ``status_code=404`` if no measurement exists for the date.
    """
    data = await hevy_request("GET", f"/v1/body_measurements/{date}")
    return BodyMeasurement.model_validate(data)


async def create_body_measurement(
    measurement: Annotated[
        BodyMeasurement,
        Field(
            description=(
                "The body measurement to create. ``date`` is required (YYYY-MM-DD); all "
                "other fields are optional and default to null when omitted."
            ),
        ),
    ],
) -> OperationStatus:
    """Create a body measurement entry for a given date.

    The Hevy API responds with an empty 200 on success, so this tool returns an
    ``OperationStatus`` envelope rather than echoing the created measurement.

    Args:
        measurement: The measurement payload. Must include ``date``.

    Returns:
        An ``OperationStatus`` with ``success=True`` and a confirmation message
        containing the measurement date.

    Raises:
        HevyAPIError: With ``status_code=409`` if a measurement already exists
            for that date (Hevy does not allow two entries on the same day).
        HevyAPIError: With ``status_code=400`` if the request body is invalid.
    """
    body = measurement.model_dump(mode="json", exclude_none=False)
    await hevy_request("POST", "/v1/body_measurements", json_body=body)
    return OperationStatus(
        success=True,
        message=f"Body measurement for {measurement.date} created",
    )


async def update_body_measurement(
    date: Annotated[
        str,
        Field(description="The date of the measurement to update in YYYY-MM-DD format."),
    ],
    measurement: Annotated[
        PutBodyMeasurement,
        Field(
            description=(
                "The fields you want to change. Any field left unset is preserved "
                "from the existing measurement — this tool performs a safe merge, "
                "not a destructive overwrite. Set a field to null explicitly to "
                "clear it."
            ),
        ),
    ],
) -> OperationStatus:
    """Merge-update an existing body measurement for a given date.

    Hevy's native PUT is destructive (any field you omit is nulled out on the
    server). To make this safe for agent use, this tool first reads the existing
    measurement, overlays the fields you set, and only then writes the merged
    result back. Fields you don't mention keep their current values.

    If you genuinely want to clear a field, pass it explicitly as ``None`` — the
    merge preserves caller-provided ``None`` values.

    Args:
        date: The measurement date to update in YYYY-MM-DD format.
        measurement: Partial update. Only fields set by the caller are applied.

    Returns:
        An ``OperationStatus`` with ``success=True`` and a confirmation message.

    Raises:
        HevyAPIError: With ``status_code=404`` if no measurement exists for the date.
        HevyAPIError: With ``status_code=400`` if the request body is invalid.
    """
    existing = await hevy_request("GET", f"/v1/body_measurements/{date}")
    existing_measurement = BodyMeasurement.model_validate(existing)
    base = existing_measurement.model_dump(mode="json", exclude={"date"})
    patch = measurement.model_dump(mode="json", exclude_unset=True)
    merged = {**base, **patch}
    await hevy_request("PUT", f"/v1/body_measurements/{date}", json_body=merged)
    return OperationStatus(
        success=True,
        message=f"Body measurement for {date} updated (merged {len(patch)} field(s))",
    )


TOOLS = [
    list_body_measurements,
    get_body_measurement,
    create_body_measurement,
    update_body_measurement,
]


async def _smoke_reads(session, ctx: dict) -> None:
    """Smoke probe for body measurement reads."""
    from tests.smoke_reads import _call
    print("\n── body_measurements ──")
    page = await _call(session, "list_body_measurements", {"page_size": 1})
    if page and page.get("body_measurements"):
        ctx["measurement_date"] = page["body_measurements"][0]["date"]
        await _call(
            session,
            "get_body_measurement",
            {"date": ctx["measurement_date"]},
        )


async def _smoke_writes(session, created: dict) -> None:
    """Smoke probe for body measurement writes.

    Uses sentinel date 1999-01-01 to avoid colliding with real data.
    If the sentinel already exists (from a prior run), falls through to update.
    """
    from tests.smoke_writes import _call
    print("\n── body_measurements (writes) ──")
    sentinel = "1999-01-01"
    result = await _call(
        session,
        "create_body_measurement",
        {"measurement": {"date": sentinel, "weight_kg": 1.0}},
    )
    # Whether create succeeded or 409'd, try to read + update the sentinel
    await _call(session, "get_body_measurement", {"date": sentinel})
    await _call(
        session,
        "update_body_measurement",
        {"date": sentinel, "measurement": {"weight_kg": 1.1}},
    )
    if result is not None:
        created["body_measurement_date"] = sentinel
    else:
        created["body_measurement_date_preexisting"] = sentinel
