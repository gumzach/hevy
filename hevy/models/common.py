"""Shared Hevy models and enums reused across domains."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from hevy.utils.client import HevyAPIError

__all__ = [
    "HevyAPIError",
    "OperationStatus",
    "RepRange",
    "SetType",
]


class SetType(StrEnum):
    """Hevy set type. Mirrors the ``set_type`` enum used across workouts and routines."""

    WARMUP = "warmup"
    NORMAL = "normal"
    FAILURE = "failure"
    DROPSET = "dropset"


class RepRange(BaseModel):
    """Inclusive rep range for a routine set (both bounds optional)."""

    start: float | None = Field(
        default=None,
        description="Lower bound of the rep range (inclusive). May be null if unset.",
    )
    end: float | None = Field(
        default=None,
        description="Upper bound of the rep range (inclusive). May be null if unset.",
    )


class OperationStatus(BaseModel):
    """Generic success/message envelope used by tools whose API call returns no body."""

    success: bool = Field(
        description="True if the underlying Hevy API call completed with a 2xx status.",
    )
    message: str = Field(
        description="Human-readable summary of the operation result.",
    )
