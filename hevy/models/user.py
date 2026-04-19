"""Models for the ``/v1/user/info`` endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["UserInfo", "UserInfoResponse"]


class UserInfo(BaseModel):
    """Basic info about a Hevy user."""

    id: str = Field(description="The user ID (UUID) assigned by Hevy.")
    name: str = Field(description="The user's display name.")
    url: str = Field(description="The user's public Hevy profile URL.")


class UserInfoResponse(BaseModel):
    """Wrapper matching the Hevy API's ``{\"data\": UserInfo}`` response envelope."""

    data: UserInfo = Field(description="The authenticated user's info.")
