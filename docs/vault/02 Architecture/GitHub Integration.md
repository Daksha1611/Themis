---
name: GitHub Integration
description: "Owns every GitHub call: App auth, diff fetch, posting reviews; the required App permissions."
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
- Post review comments with the findings. **Built (M2):** every valid finding is posted. **Planned (M5):** only findings that pass the [[Precision Filter]].
- **Planned:** post the single [[Guardrails]] notice when suspicious instruction-like content is detected
- **Planned:** read finding-outcome signals (later commits, thread resolution, reactions) for [[ADR-011 Finding outcomes as precision-filter labels]]

**Inputs:** PR identity from the [[Job Queue]]; findings to post.
**Outputs:** PR diffs; posted review comments; outcome signals stored in [[Storage]] (planned).

**Code location:** `app/github/client.py` (shared httpx client, headers, rate-limit detection), `auth.py` (JWT, installation token), `diff.py` (`fetch_pr_diff`, `commentable_lines`), `comments.py` (`post_findings`: one PR review with line comments, out-of-diff findings in the body, 422 fallback; `post_review_comment`: PR-level comment).

**Required GitHub App permissions:** Pull requests (Read & write), Contents (Read-only), Metadata (Read-only). Subscribed event: Pull request. Contents: Read-only is required for diff fetching (GitHub's diff media type) and was missing from the original spec.

**Dependencies:** GitHub App credentials. Webhook signature verification stays in the [[Webhook Service]].
