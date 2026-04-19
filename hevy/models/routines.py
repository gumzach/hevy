"""Models for the ``/v1/routines`` endpoints.

Covers the Routine response (with nested ``RoutineExercise`` / ``RoutineExerciseSet``)
and the POST / PUT request bodies. ``PostRoutines*`` and ``PutRoutines*`` are modeled
separately because the PUT body omits ``folder_id`` on the routine object.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from hevy.models.common import RepRange, SetType

__all__ = [
    "PaginatedRoutines",
    "PostRoutinesRequestExercise",
    "PostRoutinesRequestRoutine",
    "PostRoutinesRequestSet",
    "PutRoutinesRequestExercise",
    "PutRoutinesRequestRoutine",
    "PutRoutinesRequestSet",
    "Routine",
    "RoutineExercise",
    "RoutineExerciseSet",
]


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class RoutineExerciseSet(BaseModel):
    """A single set within a routine exercise (as returned by the Hevy API)."""

    index: int = Field(
        description="Zero-based index indicating the order of the set in the exercise.",
    )
    type: str = Field(
        description=(
            "Set type. One of 'normal', 'warmup', 'dropset', 'failure'. Left as a plain "
            "string (not the SetType enum) to tolerate future API-side additions."
        ),
    )
    weight_kg: float | None = Field(
        default=None,
        description="Weight lifted in kilograms. ``null`` when not applicable.",
    )
    reps: float | None = Field(
        default=None,
        description="Number of reps logged for the set. Spec types this as a number.",
    )
    rep_range: RepRange | None = Field(
        default=None,
        description="Inclusive rep range for the set, if the routine specifies one.",
    )
    distance_meters: float | None = Field(
        default=None,
        description="Distance in meters for cardio-style sets. ``null`` when not applicable.",
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Duration in seconds for timed sets. ``null`` when not applicable.",
    )
    rpe: float | None = Field(
        default=None,
        description=(
            "Relative Perceived Exertion logged for the set (typically in "
            "[6, 7, 7.5, 8, 8.5, 9, 9.5, 10]). ``null`` when not logged."
        ),
    )
    custom_metric: float | None = Field(
        default=None,
        description=(
            "Custom metric logged for the set (currently only used for floors or steps "
            "on stair-machine exercises). ``null`` when not applicable."
        ),
    )


class RoutineExercise(BaseModel):
    """An exercise slot within a routine (as returned by the Hevy API)."""

    index: int = Field(
        description="Zero-based index indicating the order of the exercise in the routine.",
    )
    title: str = Field(
        description="Display title of the exercise (e.g. 'Bench Press (Barbell)').",
    )
    rest_seconds: int | None = Field(
        default=None,
        description=(
            "Rest time in seconds between sets. Hevy's spec types this as a string but the "
            "live API returns an integer; we coerce strings to ``int`` defensively."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Routine-level notes on this exercise. ``null`` when not set.",
    )
    exercise_template_id: str = Field(
        description=(
            "Exercise template ID. Can be passed to ``get_exercise_template`` to fetch "
            "the underlying template definition."
        ),
    )
    supersets_id: int | None = Field(
        default=None,
        description=(
            "ID of the superset this exercise belongs to, or ``null`` if it is not part "
            "of a superset."
        ),
    )
    sets: list[RoutineExerciseSet] = Field(
        default_factory=list,
        description="Ordered list of sets prescribed for this exercise.",
    )

    @field_validator("rest_seconds", mode="before")
    @classmethod
    def _coerce_rest_seconds(cls, value: object) -> object:
        """Accept string rest_seconds (per spec) and coerce to int (per live API)."""
        if value is None or isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return int(stripped)
            except ValueError:
                try:
                    return int(float(stripped))
                except ValueError:
                    return None
        if isinstance(value, float):
            return int(value)
        return value


class Routine(BaseModel):
    """A Hevy routine (workout template)."""

    id: str = Field(description="The routine ID (UUID).")
    title: str = Field(description="The routine title.")
    folder_id: int | None = Field(
        default=None,
        description=(
            "ID of the routine folder this routine lives in, or ``null`` for the "
            "default 'My Routines' folder."
        ),
    )
    updated_at: str = Field(
        description="ISO 8601 timestamp of when the routine was last updated.",
    )
    created_at: str = Field(
        description="ISO 8601 timestamp of when the routine was created.",
    )
    exercises: list[RoutineExercise] = Field(
        default_factory=list,
        description="Ordered list of exercises in the routine.",
    )


class PaginatedRoutines(BaseModel):
    """Paginated response for ``GET /v1/routines``."""

    page: int = Field(description="Current page number (1-based).")
    page_count: int = Field(description="Total number of pages available for this query.")
    routines: list[Routine] = Field(
        default_factory=list,
        description="Routines on the current page.",
    )


# ---------------------------------------------------------------------------
# POST /v1/routines request models
# ---------------------------------------------------------------------------


class PostRoutinesRequestSet(BaseModel):
    """A single set inside a routine being created."""

    type: SetType = Field(
        description="The set type. One of 'warmup', 'normal', 'failure', 'dropset'.",
    )
    weight_kg: float | None = Field(
        default=None,
        description="Weight in kilograms. Pass ``null`` to leave unset.",
    )
    reps: int | None = Field(
        default=None,
        description="Number of repetitions. Pass ``null`` to leave unset.",
    )
    distance_meters: int | None = Field(
        default=None,
        description="Distance in meters (for cardio-style sets). Pass ``null`` to leave unset.",
    )
    duration_seconds: int | None = Field(
        default=None,
        description="Duration in seconds (for timed sets). Pass ``null`` to leave unset.",
    )
    custom_metric: float | None = Field(
        default=None,
        description=(
            "Custom metric (e.g. floors or steps on stair-machine exercises). "
            "Pass ``null`` to leave unset."
        ),
    )
    rep_range: RepRange | None = Field(
        default=None,
        description="Inclusive rep range for the set. Pass ``null`` for a single-rep target.",
    )


class PostRoutinesRequestExercise(BaseModel):
    """A single exercise inside a routine being created."""

    exercise_template_id: str = Field(
        description=(
            "Exercise template ID (e.g. 'D04AC939'). Obtain via ``list_exercise_templates`` "
            "or ``create_custom_exercise_template``."
        ),
    )
    superset_id: int | None = Field(
        default=None,
        description="ID of the superset this exercise belongs to, or ``null`` for none.",
    )
    rest_seconds: int | None = Field(
        default=None,
        description="Rest time in seconds between sets, or ``null`` to leave unset.",
    )
    notes: str | None = Field(
        default=None,
        description="Routine-level notes for this exercise, or ``null`` for none.",
    )
    sets: list[PostRoutinesRequestSet] = Field(
        default_factory=list,
        description="Ordered list of sets prescribed for this exercise.",
    )


class PostRoutinesRequestRoutine(BaseModel):
    """Request body for ``POST /v1/routines`` (the ``routine`` object)."""

    title: str = Field(description="The routine title.")
    folder_id: int | None = Field(
        default=None,
        description=(
            "Target routine folder ID, or ``null`` to insert into the default "
            "'My Routines' folder."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Routine-level notes, or ``null`` for none.",
    )
    exercises: list[PostRoutinesRequestExercise] = Field(
        default_factory=list,
        description="Ordered list of exercises that make up the routine.",
    )


# ---------------------------------------------------------------------------
# PUT /v1/routines/{id} request models
# ---------------------------------------------------------------------------


class PutRoutinesRequestSet(BaseModel):
    """A single set inside a routine being updated.

    Identical in shape to :class:`PostRoutinesRequestSet`, modeled separately to keep
    generated schemas tied to the exact Hevy request schema.
    """

    type: SetType = Field(
        description="The set type. One of 'warmup', 'normal', 'failure', 'dropset'.",
    )
    weight_kg: float | None = Field(
        default=None,
        description="Weight in kilograms. Pass ``null`` to leave unset.",
    )
    reps: int | None = Field(
        default=None,
        description="Number of repetitions. Pass ``null`` to leave unset.",
    )
    distance_meters: int | None = Field(
        default=None,
        description="Distance in meters (for cardio-style sets). Pass ``null`` to leave unset.",
    )
    duration_seconds: int | None = Field(
        default=None,
        description="Duration in seconds (for timed sets). Pass ``null`` to leave unset.",
    )
    custom_metric: float | None = Field(
        default=None,
        description=(
            "Custom metric (e.g. floors or steps on stair-machine exercises). "
            "Pass ``null`` to leave unset."
        ),
    )
    rep_range: RepRange | None = Field(
        default=None,
        description="Inclusive rep range for the set. Pass ``null`` for a single-rep target.",
    )


class PutRoutinesRequestExercise(BaseModel):
    """A single exercise inside a routine being updated."""

    exercise_template_id: str = Field(
        description="Exercise template ID (e.g. 'D04AC939').",
    )
    superset_id: int | None = Field(
        default=None,
        description="ID of the superset this exercise belongs to, or ``null`` for none.",
    )
    rest_seconds: int | None = Field(
        default=None,
        description="Rest time in seconds between sets, or ``null`` to leave unset.",
    )
    notes: str | None = Field(
        default=None,
        description="Routine-level notes for this exercise, or ``null`` for none.",
    )
    sets: list[PutRoutinesRequestSet] = Field(
        default_factory=list,
        description="Ordered list of sets prescribed for this exercise.",
    )


class PutRoutinesRequestRoutine(BaseModel):
    """Request body for ``PUT /v1/routines/{routineId}`` (the ``routine`` object).

    Unlike the POST body, the PUT body does **not** include ``folder_id``; a routine
    cannot be moved between folders via this endpoint.
    """

    title: str = Field(description="The routine title.")
    notes: str | None = Field(
        default=None,
        description="Routine-level notes, or ``null`` for none.",
    )
    exercises: list[PutRoutinesRequestExercise] = Field(
        default_factory=list,
        description="Ordered list of exercises that make up the routine.",
    )
