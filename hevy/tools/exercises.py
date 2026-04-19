"""Tools for exercise templates, exercise history, and routine folders."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from hevy.models.exercises import (
    CreateCustomExerciseRequestExercise,
    CreateExerciseTemplateResponse,
    ExerciseHistoryResponse,
    ExerciseTemplate,
    PaginatedExerciseTemplates,
    PaginatedRoutineFolders,
    PostRoutineFolderRequestFolder,
    RoutineFolder,
)
from hevy.utils.client import hevy_request

_EXERCISE_TEMPLATES_PAGE_SIZE_MAX = 100
_ROUTINE_FOLDERS_PAGE_SIZE_MAX = 10


async def list_exercise_templates(
    page: Annotated[
        int | None,
        Field(description="Page number (1-indexed). Omit to use the Hevy API default."),
    ] = None,
    page_size: Annotated[
        int | None,
        Field(
            description=(
                "Number of items per page. Max 100 for this endpoint (higher than the "
                "typical Hevy cap of 10). Omit to use the Hevy API default."
            ),
        ),
    ] = None,
) -> PaginatedExerciseTemplates:
    """List exercise templates available on the authenticated account.

    Returns a paginated list of both built-in Hevy exercise templates and any
    custom templates the user has created.

    Args:
        page: 1-indexed page number. Must be >= 1 if provided.
        page_size: Items per page. Must be between 1 and 100 if provided.
    """
    if page is not None and page < 1:
        raise ValueError("page must be >= 1")
    if page_size is not None and not (1 <= page_size <= _EXERCISE_TEMPLATES_PAGE_SIZE_MAX):
        raise ValueError(
            f"page_size must be between 1 and {_EXERCISE_TEMPLATES_PAGE_SIZE_MAX}",
        )
    data = await hevy_request(
        "GET",
        "/v1/exercise_templates",
        params={"page": page, "pageSize": page_size},
    )
    return PaginatedExerciseTemplates.model_validate(data)


async def get_exercise_template(
    template_id: Annotated[
        str,
        Field(description="The exercise template ID (string) to fetch."),
    ],
) -> ExerciseTemplate:
    """Get a single exercise template by ID.

    Args:
        template_id: The string ID of the exercise template (e.g. '05293BCA').
    """
    data = await hevy_request("GET", f"/v1/exercise_templates/{template_id}")
    return ExerciseTemplate.model_validate(data)


async def create_custom_exercise_template(
    exercise: Annotated[
        CreateCustomExerciseRequestExercise,
        Field(
            description=(
                "The custom exercise payload: title, exercise_type, equipment_category, "
                "muscle_group, and optional other_muscles."
            ),
        ),
    ],
) -> CreateExerciseTemplateResponse:
    """Create a new custom exercise template on the authenticated account.

    Note: the Hevy OpenAPI spec says this endpoint returns ``{"id": <int>}``, but the
    ``ExerciseTemplate.id`` field elsewhere is a string. The returned integer ID may
    need to be converted or may not be directly usable with ``get_exercise_template``
    (which expects a string ID). Spec is ambiguous; test empirically with the live smoke.

    Raises:
        HevyAPIError: 400 on invalid body; 403 when the account's custom exercise
            limit has been exceeded.

    Args:
        exercise: The custom exercise definition to create.
    """
    body = {"exercise": exercise.model_dump(exclude_none=True, mode="json")}
    data = await hevy_request("POST", "/v1/exercise_templates", json_body=body)
    return CreateExerciseTemplateResponse.model_validate(data)


async def get_exercise_history(
    template_id: Annotated[
        str,
        Field(description="The exercise template ID (string) to fetch history for."),
    ],
    start_date: Annotated[
        str | None,
        Field(
            description=(
                "Optional ISO 8601 datetime lower bound (e.g. '2024-01-01T00:00:00Z'). "
                "Only entries on or after this moment are returned."
            ),
        ),
    ] = None,
    end_date: Annotated[
        str | None,
        Field(
            description=(
                "Optional ISO 8601 datetime upper bound (e.g. '2024-12-31T23:59:59Z'). "
                "Only entries on or before this moment are returned."
            ),
        ),
    ] = None,
) -> ExerciseHistoryResponse:
    """Get all history entries (sets across workouts) for a given exercise template.

    Args:
        template_id: The exercise template string ID.
        start_date: Optional ISO 8601 datetime lower bound.
        end_date: Optional ISO 8601 datetime upper bound.
    """
    data = await hevy_request(
        "GET",
        f"/v1/exercise_history/{template_id}",
        params={"start_date": start_date, "end_date": end_date},
    )
    return ExerciseHistoryResponse.model_validate(data)


async def list_routine_folders(
    page: Annotated[
        int | None,
        Field(description="Page number (1-indexed). Omit to use the Hevy API default."),
    ] = None,
    page_size: Annotated[
        int | None,
        Field(
            description=(
                "Number of items per page (max 10). Omit to use the Hevy API default."
            ),
        ),
    ] = None,
) -> PaginatedRoutineFolders:
    """List routine folders on the authenticated account.

    Args:
        page: 1-indexed page number. Must be >= 1 if provided.
        page_size: Items per page. Must be between 1 and 10 if provided.
    """
    if page is not None and page < 1:
        raise ValueError("page must be >= 1")
    if page_size is not None and not (1 <= page_size <= _ROUTINE_FOLDERS_PAGE_SIZE_MAX):
        raise ValueError(
            f"page_size must be between 1 and {_ROUTINE_FOLDERS_PAGE_SIZE_MAX}",
        )
    data = await hevy_request(
        "GET",
        "/v1/routine_folders",
        params={"page": page, "pageSize": page_size},
    )
    return PaginatedRoutineFolders.model_validate(data)


async def get_routine_folder(
    folder_id: Annotated[
        int,
        Field(description="The integer ID of the routine folder to fetch."),
    ],
) -> RoutineFolder:
    """Get a single routine folder by ID.

    Args:
        folder_id: The integer routine folder ID.
    """
    data = await hevy_request("GET", f"/v1/routine_folders/{folder_id}")
    return RoutineFolder.model_validate(data)


async def create_routine_folder(
    routine_folder: Annotated[
        PostRoutineFolderRequestFolder,
        Field(description="The routine folder payload (currently just a title)."),
    ],
) -> RoutineFolder:
    """Create a new routine folder.

    The new folder is created at index 0; all other folders have their indexes
    incremented by one.

    Args:
        routine_folder: The folder payload (title).
    """
    body = {"routine_folder": routine_folder.model_dump(exclude_none=True, mode="json")}
    data = await hevy_request("POST", "/v1/routine_folders", json_body=body)
    return RoutineFolder.model_validate(data)


TOOLS = [
    list_exercise_templates,
    get_exercise_template,
    create_custom_exercise_template,
    get_exercise_history,
    list_routine_folders,
    get_routine_folder,
    create_routine_folder,
]


async def _smoke_reads(session, ctx: dict) -> None:
    """Smoke probe for exercise-template/history/folder reads."""
    from tests.smoke_reads import _call
    print("\n── exercise_templates / history / folders ──")
    tpl_page = await _call(session, "list_exercise_templates", {"page_size": 1})
    if tpl_page and tpl_page.get("exercise_templates"):
        ctx["exercise_template_id"] = tpl_page["exercise_templates"][0]["id"]
        await _call(
            session,
            "get_exercise_template",
            {"template_id": ctx["exercise_template_id"]},
        )
        await _call(
            session,
            "get_exercise_history",
            {"template_id": ctx["exercise_template_id"]},
        )
    folder_page = await _call(session, "list_routine_folders", {"page_size": 1})
    if folder_page and folder_page.get("routine_folders"):
        ctx["folder_id"] = folder_page["routine_folders"][0]["id"]
        await _call(session, "get_routine_folder", {"folder_id": ctx["folder_id"]})


async def _smoke_writes(session, created: dict) -> None:
    """Smoke probe for custom exercise + folder creation."""
    from tests.smoke_writes import SMOKE_TAG, _call
    print("\n── exercise_templates / folders (writes) ──")
    folder_result = await _call(
        session,
        "create_routine_folder",
        {"routine_folder": {"title": f"{SMOKE_TAG} test folder"}},
    )
    if folder_result and folder_result.get("id") is not None:
        created["routine_folder_id"] = folder_result["id"]
    ex_result = await _call(
        session,
        "create_custom_exercise_template",
        {
            "exercise": {
                "title": f"{SMOKE_TAG} test exercise",
                "exercise_type": "weight_reps",
                "equipment_category": "barbell",
                "muscle_group": "chest",
                "other_muscles": ["triceps"],
            }
        },
    )
    if ex_result and ex_result.get("id") is not None:
        created["custom_exercise_template_id"] = ex_result["id"]
