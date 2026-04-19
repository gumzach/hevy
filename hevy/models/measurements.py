"""Models for the ``/v1/body_measurements`` endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = [
    "BodyMeasurement",
    "PaginatedBodyMeasurements",
    "PutBodyMeasurement",
]


class BodyMeasurement(BaseModel):
    """A single body measurement entry for a specific date.

    ``date`` is the only required field. All measurement values are optional and
    may be ``null`` when the user did not record them.
    """

    date: str = Field(
        description="The date of the measurement in YYYY-MM-DD format (e.g. '2024-08-14').",
    )
    weight_kg: float | None = Field(
        default=None,
        description="Body weight in kilograms. May be null if not recorded.",
    )
    lean_mass_kg: float | None = Field(
        default=None,
        description="Lean body mass in kilograms. May be null if not recorded.",
    )
    fat_percent: float | None = Field(
        default=None,
        description="Body fat percentage (e.g. 18.5 for 18.5%). May be null if not recorded.",
    )
    neck_cm: float | None = Field(
        default=None,
        description="Neck circumference in centimeters. May be null if not recorded.",
    )
    shoulder_cm: float | None = Field(
        default=None,
        description="Shoulder circumference in centimeters. May be null if not recorded.",
    )
    chest_cm: float | None = Field(
        default=None,
        description="Chest circumference in centimeters. May be null if not recorded.",
    )
    left_bicep_cm: float | None = Field(
        default=None,
        description="Left bicep circumference in centimeters. May be null if not recorded.",
    )
    right_bicep_cm: float | None = Field(
        default=None,
        description="Right bicep circumference in centimeters. May be null if not recorded.",
    )
    left_forearm_cm: float | None = Field(
        default=None,
        description="Left forearm circumference in centimeters. May be null if not recorded.",
    )
    right_forearm_cm: float | None = Field(
        default=None,
        description="Right forearm circumference in centimeters. May be null if not recorded.",
    )
    abdomen: float | None = Field(
        default=None,
        description="Abdomen circumference in centimeters. May be null if not recorded.",
    )
    waist: float | None = Field(
        default=None,
        description="Waist circumference in centimeters. May be null if not recorded.",
    )
    hips: float | None = Field(
        default=None,
        description="Hip circumference in centimeters. May be null if not recorded.",
    )
    left_thigh: float | None = Field(
        default=None,
        description="Left thigh circumference in centimeters. May be null if not recorded.",
    )
    right_thigh: float | None = Field(
        default=None,
        description="Right thigh circumference in centimeters. May be null if not recorded.",
    )
    left_calf: float | None = Field(
        default=None,
        description="Left calf circumference in centimeters. May be null if not recorded.",
    )
    right_calf: float | None = Field(
        default=None,
        description="Right calf circumference in centimeters. May be null if not recorded.",
    )


class PutBodyMeasurement(BaseModel):
    """Request body for updating an existing body measurement.

    The ``date`` is passed as a path parameter, not in the body. All fields are
    optional, but note the Hevy API semantics: on PUT, all fields are
    overwritten — any field omitted from the request is set to ``null``.
    """

    weight_kg: float | None = Field(
        default=None,
        description="Body weight in kilograms. Omit or set null to clear the value.",
    )
    lean_mass_kg: float | None = Field(
        default=None,
        description="Lean body mass in kilograms. Omit or set null to clear the value.",
    )
    fat_percent: float | None = Field(
        default=None,
        description="Body fat percentage. Omit or set null to clear the value.",
    )
    neck_cm: float | None = Field(
        default=None,
        description="Neck circumference in centimeters. Omit or set null to clear the value.",
    )
    shoulder_cm: float | None = Field(
        default=None,
        description="Shoulder circumference in centimeters. Omit or set null to clear the value.",
    )
    chest_cm: float | None = Field(
        default=None,
        description="Chest circumference in centimeters. Omit or set null to clear the value.",
    )
    left_bicep_cm: float | None = Field(
        default=None,
        description="Left bicep circumference in centimeters. Omit or set null to clear the value.",
    )
    right_bicep_cm: float | None = Field(
        default=None,
        description=(
            "Right bicep circumference in centimeters. Omit or set null to clear the value."
        ),
    )
    left_forearm_cm: float | None = Field(
        default=None,
        description=(
            "Left forearm circumference in centimeters. Omit or set null to clear the value."
        ),
    )
    right_forearm_cm: float | None = Field(
        default=None,
        description=(
            "Right forearm circumference in centimeters. Omit or set null to clear the value."
        ),
    )
    abdomen: float | None = Field(
        default=None,
        description="Abdomen circumference in centimeters. Omit or set null to clear the value.",
    )
    waist: float | None = Field(
        default=None,
        description="Waist circumference in centimeters. Omit or set null to clear the value.",
    )
    hips: float | None = Field(
        default=None,
        description="Hip circumference in centimeters. Omit or set null to clear the value.",
    )
    left_thigh: float | None = Field(
        default=None,
        description="Left thigh circumference in centimeters. Omit or set null to clear the value.",
    )
    right_thigh: float | None = Field(
        default=None,
        description=(
            "Right thigh circumference in centimeters. Omit or set null to clear the value."
        ),
    )
    left_calf: float | None = Field(
        default=None,
        description="Left calf circumference in centimeters. Omit or set null to clear the value.",
    )
    right_calf: float | None = Field(
        default=None,
        description="Right calf circumference in centimeters. Omit or set null to clear the value.",
    )


class PaginatedBodyMeasurements(BaseModel):
    """A single page of body measurements returned by ``GET /v1/body_measurements``."""

    page: int = Field(description="The current page number (1-indexed).")
    page_count: int = Field(description="The total number of pages available.")
    body_measurements: list[BodyMeasurement] = Field(
        description="The body measurement entries on this page.",
    )
