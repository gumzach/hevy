"""Models for exercise templates, exercise history, and routine folders."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

__all__ = [
    "CreateCustomExerciseRequestExercise",
    "CreateExerciseTemplateResponse",
    "CustomExerciseType",
    "EquipmentCategory",
    "ExerciseHistoryEntry",
    "ExerciseHistoryResponse",
    "ExerciseTemplate",
    "MuscleGroup",
    "PaginatedExerciseTemplates",
    "PaginatedRoutineFolders",
    "PostRoutineFolderRequestFolder",
    "RoutineFolder",
]


class CustomExerciseType(StrEnum):
    """Exercise type for a custom exercise template. Mirrors Hevy's ``CustomExerciseType`` enum."""

    WEIGHT_REPS = "weight_reps"
    REPS_ONLY = "reps_only"
    BODYWEIGHT_REPS = "bodyweight_reps"
    BODYWEIGHT_ASSISTED_REPS = "bodyweight_assisted_reps"
    DURATION = "duration"
    WEIGHT_DURATION = "weight_duration"
    DISTANCE_DURATION = "distance_duration"
    SHORT_DISTANCE_WEIGHT = "short_distance_weight"


class MuscleGroup(StrEnum):
    """Muscle group enum used by custom exercise templates."""

    ABDOMINALS = "abdominals"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    CALVES = "calves"
    GLUTES = "glutes"
    ABDUCTORS = "abductors"
    ADDUCTORS = "adductors"
    LATS = "lats"
    UPPER_BACK = "upper_back"
    TRAPS = "traps"
    LOWER_BACK = "lower_back"
    CHEST = "chest"
    CARDIO = "cardio"
    NECK = "neck"
    FULL_BODY = "full_body"
    OTHER = "other"


class EquipmentCategory(StrEnum):
    """Equipment category enum used by custom exercise templates."""

    NONE = "none"
    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    KETTLEBELL = "kettlebell"
    MACHINE = "machine"
    PLATE = "plate"
    RESISTANCE_BAND = "resistance_band"
    SUSPENSION = "suspension"
    OTHER = "other"


class ExerciseTemplate(BaseModel):
    """A Hevy exercise template — either built-in or user-created (``is_custom=True``)."""

    id: str = Field(description="The exercise template ID (string, e.g. '05293BCA').")
    title: str = Field(description="The exercise title, e.g. 'Bench Press (Barbell)'.")
    type: str = Field(
        description=(
            "The exercise type. One of: 'weight_reps', 'reps_only', 'bodyweight_reps', "
            "'bodyweight_assisted_reps', 'duration', 'weight_duration', "
            "'distance_duration', 'short_distance_weight'."
        ),
    )
    primary_muscle_group: str = Field(
        description="The primary muscle group of the exercise (e.g. 'chest', 'lats').",
    )
    secondary_muscle_groups: list[str] = Field(
        default_factory=list,
        description="Secondary muscle groups of the exercise. Empty list if none.",
    )
    is_custom: bool = Field(
        description="True if this is a user-created custom exercise template.",
    )


class PaginatedExerciseTemplates(BaseModel):
    """A page of exercise templates returned by ``GET /v1/exercise_templates``."""

    page: int = Field(description="Current page number (1-indexed).")
    page_count: int = Field(description="Total number of pages available.")
    exercise_templates: list[ExerciseTemplate] = Field(
        description="The exercise templates on this page.",
    )


class CreateCustomExerciseRequestExercise(BaseModel):
    """Body of the ``exercise`` key in a POST ``/v1/exercise_templates`` request."""

    title: str = Field(description="The title of the new custom exercise template.")
    exercise_type: CustomExerciseType = Field(
        description="The exercise type (how sets are logged — reps, duration, etc.).",
    )
    equipment_category: EquipmentCategory = Field(
        description="The equipment category for the exercise (e.g. 'barbell', 'dumbbell').",
    )
    muscle_group: MuscleGroup = Field(
        description="The primary muscle group targeted by the exercise.",
    )
    other_muscles: list[MuscleGroup] = Field(
        default_factory=list,
        description="Additional (secondary) muscle groups. Empty list if none.",
    )


class CreateExerciseTemplateResponse(BaseModel):
    """Response body from POST ``/v1/exercise_templates``.

    Note: per the Hevy OpenAPI spec this returns ``{"id": <int>}``, even though
    ``ExerciseTemplate.id`` elsewhere is a string. The integer may not be directly
    usable with ``get_exercise_template``; verify empirically if you need to fetch
    the newly created template by id.
    """

    id: int = Field(
        description=(
            "The numeric ID returned by the create-custom-exercise endpoint. "
            "May not match the string ID shape used by get_exercise_template."
        ),
    )


class ExerciseHistoryEntry(BaseModel):
    """A single set logged against a specific exercise template, across any workout."""

    workout_id: str = Field(description="ID of the workout this entry was logged in.")
    workout_title: str = Field(description="Title of the workout this entry was logged in.")
    workout_start_time: str = Field(
        description="ISO 8601 timestamp when the workout was recorded to have started.",
    )
    workout_end_time: str = Field(
        description="ISO 8601 timestamp when the workout was recorded to have ended.",
    )
    exercise_template_id: str = Field(
        description="ID of the exercise template this entry belongs to.",
    )
    weight_kg: float | None = Field(
        default=None,
        description="Weight lifted in kilograms, or null if not applicable.",
    )
    reps: int | None = Field(
        default=None,
        description="Number of reps logged, or null if not applicable.",
    )
    distance_meters: int | None = Field(
        default=None,
        description="Distance in meters, or null if not applicable.",
    )
    duration_seconds: int | None = Field(
        default=None,
        description="Duration in seconds, or null if not applicable.",
    )
    rpe: float | None = Field(
        default=None,
        description="Rating of Perceived Exertion (e.g. 6, 7, 7.5, 8, 8.5, 9, 9.5, 10), or null.",
    )
    custom_metric: float | None = Field(
        default=None,
        description="Custom metric for the set (e.g. floors/steps on a stair machine), or null.",
    )
    set_type: str = Field(
        description="Set type: one of 'warmup', 'normal', 'failure', 'dropset'.",
    )


class ExerciseHistoryResponse(BaseModel):
    """Response body from GET ``/v1/exercise_history/{exerciseTemplateId}``."""

    exercise_history: list[ExerciseHistoryEntry] = Field(
        description="All history entries for this exercise template (optionally date-filtered).",
    )


class RoutineFolder(BaseModel):
    """A Hevy routine folder — a named grouping of routines."""

    id: int = Field(description="The routine folder ID (integer).")
    index: int = Field(
        description="Display order of the folder in the user's folder list (0-based).",
    )
    title: str = Field(description="The routine folder title.")
    updated_at: str = Field(description="ISO 8601 timestamp when the folder was last updated.")
    created_at: str = Field(description="ISO 8601 timestamp when the folder was created.")


class PaginatedRoutineFolders(BaseModel):
    """A page of routine folders returned by ``GET /v1/routine_folders``."""

    page: int = Field(description="Current page number (1-indexed).")
    page_count: int = Field(description="Total number of pages available.")
    routine_folders: list[RoutineFolder] = Field(
        description="The routine folders on this page.",
    )


class PostRoutineFolderRequestFolder(BaseModel):
    """Body of the ``routine_folder`` key in a POST ``/v1/routine_folders`` request."""

    title: str = Field(description="The title of the new routine folder.")
