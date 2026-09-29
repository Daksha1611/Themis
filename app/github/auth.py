"""GitHub App authentication: the app JWT and cached installation tokens."""

import time

import httpx
import jwt

from app.config import get_settings

GITHUB_API = "https://api.github.com"
# Installation tokens expire after 60 minutes; refresh 10 minutes early.
_TOKEN_TTL_SECONDS = 50 * 60
_token_cache: dict[int, tuple[str, float]] = {}


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=GITHUB_API, timeout=10.0)


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

    async with http_client() as client:
        response = await client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers=github_headers(get_jwt()),
        )
    response.raise_for_status()
    token: str = response.json()["token"]
    _token_cache[installation_id] = (token, time.monotonic() + _TOKEN_TTL_SECONDS)
    return token
