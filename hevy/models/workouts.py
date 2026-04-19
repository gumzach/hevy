"""Models for the Hevy ``/v1/workouts*`` endpoints (reads and writes)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from hevy.models.common import SetType

__all__ = [
    "DeletedWorkout",
    "Exercise",
    "PaginatedWorkoutEvents",
    "PaginatedWorkouts",
    "PostWorkoutsRequestExercise",
    "PostWorkoutsRequestSet",
    "PostWorkoutsRequestWorkout",
    "Set",
    "Workout",
    "WorkoutCount",
]

_RPE_ALLOWED = {6, 7, 7.5, 8, 8.5, 9, 9.5, 10}


class Set(BaseModel):
    """A single logged set within a workout exercise (response shape)."""

    index: int = Field(
        description="Zero-based index indicating the order of the set in the workout.",
    )
    type: str = Field(
        description=(
            "The type of set. Typically one of 'normal', 'warmup', 'dropset', 'failure', "
            "but Hevy may return other string values in some contexts, so this is left "
            "as a free-form string."
        ),
    )
    weight_kg: float | None = Field(
        default=None,
        description="Weight lifted in kilograms, if recorded. May be null.",
    )
    reps: float | None = Field(
        default=None,
        description="Number of reps logged for the set. May be null.",
    )
    distance_meters: float | None = Field(
        default=None,
        description="Distance in meters logged for the set. May be null.",
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Duration in seconds logged for the set. May be null.",
    )
    rpe: float | None = Field(
        default=None,
        description="Rating of Perceived Exertion (RPE) logged for the set. May be null.",
    )
    custom_metric: float | None = Field(
        default=None,
        description=(
            "Custom metric logged for the set (e.g. floors or steps for stair machine "
            "exercises). May be null."
        ),
    )


class Exercise(BaseModel):
    """An exercise entry within a workout (response shape)."""

    index: int = Field(
        description="Zero-based index indicating the order of the exercise in the workout.",
    )
    title: str = Field(description="Title of the exercise.")
    notes: str | None = Field(
        default=None,
        description="Free-form notes attached to this exercise, if any.",
    )
    exercise_template_id: str = Field(
        description=(
            "The ID of the exercise template this exercise references. Use it with "
            "``get_exercise_template`` to fetch the template definition."
        ),
    )
    supersets_id: int | None = Field(
        default=None,
        description=(
            "The ID of the superset this exercise belongs to. Null if the exercise is "
            "not part of a superset."
        ),
    )
    sets: list[Set] = Field(
        default_factory=list,
        description="The sets logged for this exercise, in order.",
    )


class Workout(BaseModel):
    """A single completed workout (response shape)."""

    id: str = Field(description="The workout ID (UUID).")
    title: str = Field(description="The workout title.")
    routine_id: str | None = Field(
        default=None,
        description=(
            "The ID of the routine this workout was based on. May be null for "
            "ad-hoc workouts logged without an underlying routine."
        ),
    )
    description: str | None = Field(
        default=None,
        description="The workout description, if provided by the user.",
    )
    start_time: str = Field(
        description="ISO 8601 timestamp of when the workout started.",
    )
    end_time: str = Field(
        description="ISO 8601 timestamp of when the workout ended.",
    )
    updated_at: str = Field(
        description="ISO 8601 timestamp of when the workout was last updated.",
    )
    created_at: str = Field(
        description="ISO 8601 timestamp of when the workout was created.",
    )
    exercises: list[Exercise] = Field(
        default_factory=list,
        description="The exercises logged in this workout, in order.",
    )


class PaginatedWorkouts(BaseModel):
    """A paginated page of workouts."""

    page: int = Field(description="The current page number (1-indexed).")
    page_count: int = Field(description="The total number of pages available.")
    workouts: list[Workout] = Field(
        default_factory=list,
        description="The workouts on this page, newest-first.",
    )


class WorkoutCount(BaseModel):
    """The total number of workouts on the authenticated account."""

    workout_count: int = Field(
        description="Total count of workouts recorded on the account.",
    )


class DeletedWorkout(BaseModel):
    """A reference to a workout that was deleted (from workout-events)."""

    id: str = Field(description="The ID of the deleted workout.")
    deleted_at: str = Field(
        description="ISO 8601 timestamp of when the workout was deleted.",
    )


class PaginatedWorkoutEvents(BaseModel):
    """A paginated page of workout events, pre-split into updated and deleted lists.

    Hevy's raw API returns a single polymorphic ``events`` list where each item is
    either an 'updated' or 'deleted' event. This model pre-sorts them into two
    typed lists so callers don't have to branch on a discriminator.
    """

    page: int = Field(description="The current page number (1-indexed).")
    page_count: int = Field(description="The total number of pages available.")
    updated: list[Workout] = Field(
        default_factory=list,
        description=(
            "Workouts that were created or updated on this page, newest-first. "
            "Each entry is the full current ``Workout`` payload."
        ),
    )
    deleted: list[DeletedWorkout] = Field(
        default_factory=list,
        description=(
            "Workouts that were deleted on this page, newest-first. Each entry "
            "carries only the workout ``id`` and ``deleted_at`` timestamp."
        ),
    )


class PostWorkoutsRequestSet(BaseModel):
    """A set payload when creating or updating a workout."""

    type: SetType = Field(
        description="The type of the set (warmup, normal, failure, or dropset).",
    )
    weight_kg: float | None = Field(
        default=None,
        description="Weight lifted in kilograms. Null if not applicable.",
    )
    reps: int | None = Field(
        default=None,
        description="Number of repetitions. Null if not applicable.",
    )
    distance_meters: int | None = Field(
        default=None,
        description="Distance in meters. Null if not applicable.",
    )
    duration_seconds: int | None = Field(
        default=None,
        description="Duration in seconds. Null if not applicable.",
    )
    custom_metric: float | None = Field(
        default=None,
        description=(
            "Custom metric for the set. Currently used for steps and floors on "
            "stair machine exercises."
        ),
    )
    rpe: float | None = Field(
        default=None,
        description=(
            "Rating of Perceived Exertion. Must be one of 6, 7, 7.5, 8, 8.5, 9, "
            "9.5, or 10 when provided."
        ),
    )

    @field_validator("rpe")
    @classmethod
    def _validate_rpe(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value not in _RPE_ALLOWED:
            raise ValueError("rpe must be one of 6, 7, 7.5, 8, 8.5, 9, 9.5, 10")
        return value


class PostWorkoutsRequestExercise(BaseModel):
    """An exercise payload when creating or updating a workout."""

    exercise_template_id: str = Field(
        description="The ID of the exercise template this exercise references.",
    )
    superset_id: int | None = Field(
        default=None,
        description=(
            "The ID of the superset this exercise belongs to. Null if the "
            "exercise is not part of a superset."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Optional free-form notes for this exercise.",
    )
    sets: list[PostWorkoutsRequestSet] = Field(
        default_factory=list,
        description="The sets performed for this exercise, in order.",
    )


class PostWorkoutsRequestWorkout(BaseModel):
    """The inner ``workout`` object of the create/update workout request body.

    The tool wraps this under a top-level ``{"workout": ...}`` key when sending
    to the Hevy API.
    """

    title: str = Field(description="The title of the workout.")
    description: str | None = Field(
        default=None,
        description="Optional free-form description for the workout.",
    )
    start_time: str = Field(
        description="ISO 8601 timestamp of when the workout started.",
    )
    end_time: str = Field(
        description="ISO 8601 timestamp of when the workout ended.",
    )
    is_private: bool = Field(
        default=False,
        description="If true, the workout is private and not visible to other users.",
    )
    exercises: list[PostWorkoutsRequestExercise] = Field(
        default_factory=list,
        description="The exercises logged in this workout, in order.",
    )
