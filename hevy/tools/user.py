"""User info tool."""

from hevy.models.user import UserInfoResponse
from hevy.utils.client import hevy_request


async def get_user_info() -> UserInfoResponse:
    """
    Get info about the authenticated Hevy user.

    Returns the user's Hevy account ID, display name, and public profile URL.
    """
    data = await hevy_request("GET", "/v1/user/info")
    return UserInfoResponse.model_validate(data)


TOOLS = [get_user_info]
