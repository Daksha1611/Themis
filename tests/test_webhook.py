import hashlib
import hmac
import json
from typing import Any
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.worker.queue import REVIEW_JOB
from tests.conftest import WEBHOOK_SECRET


def pr_payload(action: str = "opened") -> dict[str, Any]:
    return {
        "action": action,
        "number": 7,
        "pull_request": {"number": 7, "title": "Fix parser", "head": {"sha": "abc123"}},
        "repository": {"full_name": "octo/widgets"},
        "installation": {"id": 99},
    }


def sign(body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def post(
    client: TestClient,
    payload: dict[str, Any],
    event: str = "pull_request",
    signature: str | None = "",
) -> Any:
    body = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": event, "Content-Type": "application/json"}
    if signature == "":
        headers["X-Hub-Signature-256"] = sign(body)
    elif signature is not None:
        headers["X-Hub-Signature-256"] = signature
    return client.post("/webhook", content=body, headers=headers)


def test_valid_signature_returns_202(client: TestClient) -> None:
    assert post(client, pr_payload()).status_code == 202


def test_wrong_signature_returns_403(client: TestClient, queue: AsyncMock) -> None:
    body = json.dumps(pr_payload()).encode()
    response = post(client, pr_payload(), signature=sign(body, secret="wrong-secret"))
    assert response.status_code == 403
    queue.enqueue_job.assert_not_called()


def test_missing_signature_returns_403(client: TestClient, queue: AsyncMock) -> None:
    response = post(client, pr_payload(), signature=None)
    assert response.status_code == 403
    queue.enqueue_job.assert_not_called()


def test_non_pr_event_is_ignored(client: TestClient, queue: AsyncMock) -> None:
    response = post(client, {"ref": "refs/heads/main"}, event="push")
    assert response.status_code == 200
    assert response.json() == {"ignored": True}
    queue.enqueue_job.assert_not_called()


def test_closed_pr_is_ignored(client: TestClient, queue: AsyncMock) -> None:
    response = post(client, pr_payload(action="closed"))
    assert response.status_code == 200
    assert response.json() == {"ignored": True}
    queue.enqueue_job.assert_not_called()


def test_opened_pr_enqueues_job(client: TestClient, queue: AsyncMock) -> None:
    response = post(client, pr_payload(action="opened"))
    assert response.status_code == 202
    assert response.json() == {"queued": True, "pr": 7}
    queue.enqueue_job.assert_awaited_once_with(
        REVIEW_JOB,
        {
            "installation_id": 99,
            "repo_full_name": "octo/widgets",
            "pr_number": 7,
            "head_sha": "abc123",
            "pr_title": "Fix parser",
        },
    )


def test_enqueue_failure_returns_500(client: TestClient, queue: AsyncMock) -> None:
    queue.enqueue_job.side_effect = ConnectionError("redis down")
    response = post(client, pr_payload())
    assert response.status_code == 500


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
