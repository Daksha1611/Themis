---
type: component
status: in-progress
tags: [component]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Context Builder]]"
  - "[[Precision Filter]]"
  - "[[Guardrails]]"
  - "[[Storage]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
---

# GitHub Integration

**Purpose:** own every call Themis makes to GitHub.

**Responsibilities**
- GitHub App authentication (JWT → installation token)
- Fetch PR diffs for the [[Context Builder]]
- Post review comments with the filtered findings from the [[Precision Filter]]
- Post the single [[Guardrails]] notice when suspicious instruction-like content is detected
- Read finding-outcome signals (later commits, thread resolution, reactions) for [[ADR-011 Finding outcomes as precision-filter labels]]

**Inputs:** PR identity from the [[Job Queue]]; findings to post.
**Outputs:** PR diffs; posted review comments; outcome signals stored in [[Storage]].

**Planned code location:** `app/github/`.

**Code location (M2):** `app/github/client.py` (shared httpx client, headers, rate-limit detection), `auth.py` (JWT, installation token), `diff.py` (`fetch_pr_diff`, `commentable_lines`), `comments.py` (`post_findings`: one PR review with line comments, out-of-diff findings in the body, 422 fallback; `post_review_comment`: PR-level comment).

**Required GitHub App permissions:** Pull requests (Read & write), Contents (Read-only), Metadata (Read-only). Subscribed event: Pull request. Contents: Read-only is required for diff fetching (GitHub's diff media type) and was missing from the original spec.

**Dependencies:** GitHub App credentials. Webhook signature verification stays in the [[Webhook Service]].
