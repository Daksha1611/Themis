"""GitHub App authentication: the app JWT and cached installation tokens."""

import time

import jwt

from app.config import get_settings
from app.github import client as gh

# Installation tokens expire after 60 minutes; refresh 10 minutes early.
_TOKEN_TTL_SECONDS = 50 * 60
_token_cache: dict[int, tuple[str, float]] = {}


def get_jwt() -> str:
    """A short-lived JWT that authenticates as the GitHub App itself."""
    settings = get_settings()
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": settings.github_app_id}
    return jwt.encode(payload, settings.github_private_key.get_secret_value(), algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    """An installation access token, cached for 50 minutes."""
    cached = _token_cache.get(installation_id)
    if cached is not None and cached[1] > time.monotonic():
        return cached[0]

    response = await gh.get_client().post(
        f"/app/installations/{installation_id}/access_tokens",
        headers=gh.github_headers(get_jwt()),
    )
    gh.raise_if_rate_limited(response, f"installation {installation_id} token")
    response.raise_for_status()
    token: str = response.json()["token"]
    _token_cache[installation_id] = (token, time.monotonic() + _TOKEN_TTL_SECONDS)
    return token
