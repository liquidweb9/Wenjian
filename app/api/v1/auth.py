"""Auth placeholder — GET /me returns anonymous user.

Swap the hardcoded response for real token validation when auth is
implemented.
"""

from fastapi import APIRouter

router = APIRouter(tags=["auth"])


@router.get("/me")
async def get_current_user():
    """Return the current user profile.

    Currently returns a hardcoded anonymous user.  Replace with JWT /
    session-based resolution when the auth system is added.
    """
    return {
        "user_id": "anon",
        "name": "Anonymous User",
        "email": None,
    }
