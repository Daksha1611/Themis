"""GitHub webhook endpoint: verify, filter, enqueue, return. No review work happens here."""

import hashlib
import hmac
import json
import logging
from typing import Annotated

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.observability.tracing import Observation, observe, update
from app.schemas import ReviewJob, WebhookPayload
from app.worker.queue import REVIEW_JOB

logger = logging.getLogger(__name__)
router = APIRouter()

HANDLED_ACTIONS = frozenset({"opened", "synchronize"})


def get_queue(request: Request) -> ArqRedis:
    queue: ArqRedis = request.app.state.arq_pool
    return queue


def verify_signature(body: bytes, signature_header: str | None, secret: str) -> bool:
    """Check GitHub's `X-Hub-Signature-256: sha256=<hex>` HMAC of the raw body."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _ignored() -> JSONResponse:
    # 200, not 400: an event Themis chooses to ignore is not a failed delivery.
    return JSONResponse(status_code=200, content={"ignored": True})


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    queue: Annotated[ArqRedis, Depends(get_queue)],
    x_github_event: Annotated[str | None, Header()] = None,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    with observe("webhook.received", input={"event": x_github_event}) as trace:
        try:
            response = await _handle(request, queue, trace, x_github_event, x_hub_signature_256)
        except Exception as exc:
            logger.exception("Unhandled error processing webhook (event=%s)", x_github_event)
            update(trace, level="ERROR", status_message=repr(exc))
            response = JSONResponse(status_code=500, content={"error": "internal error"})
        update(
            trace,
            output={"status_code": response.status_code, "body": json.loads(bytes(response.body))},
        )
    return response


async def _handle(
    request: Request,
    queue: ArqRedis,
    trace: Observation | None,
    event: str | None,
    signature: str | None,
) -> JSONResponse:
    body = await request.body()
    secret = get_settings().github_webhook_secret.get_secret_value()
    if not verify_signature(body, signature, secret):
        logger.warning("Rejected webhook with missing or invalid signature (event=%s)", event)
        return JSONResponse(status_code=403, content={"error": "invalid signature"})

    if event != "pull_request":
        return _ignored()

    try:
        data = json.loads(body)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "invalid JSON"})
    action = data.get("action") if isinstance(data, dict) else None
    if action not in HANDLED_ACTIONS:
        return _ignored()

    try:
        payload = WebhookPayload.model_validate(data)
    except ValidationError:
        logger.warning("pull_request payload missing required fields (action=%s)", action)
        return JSONResponse(status_code=400, content={"error": "invalid payload"})

    job = ReviewJob.from_payload(payload)
    update(
        trace,
        input={
            "event": event,
            "action": action,
            "repo": job.repo_full_name,
            "pr_number": job.pr_number,
        },
    )

    try:
        await queue.enqueue_job(REVIEW_JOB, job.model_dump())
    except Exception:
        logger.exception(
            "Failed to enqueue review job for %s#%s", job.repo_full_name, job.pr_number
        )
        return JSONResponse(status_code=500, content={"error": "could not enqueue job"})

    return JSONResponse(status_code=202, content={"queued": True, "pr": job.pr_number})
