---
name: label-report-dev-2026-10-03
description: "Label report for the dev split: kept/dropped, drop reasons, categories, heuristic agreement, primary-range coverage, suspicious clean cases, label noise, owner verification."
type: reliability
status: done
tags: [reliability, benchmark]
related:
  - "[[Benchmark]]"
  - "[[Label Noise]]"
  - "[[Metrics]]"
---

# Label report: dev split

- Split: `dev` (`evals/benchmark/data/dev.jsonl`, sha256 `e923501468af`)
- Labels: `evals/benchmark/data/labels_human.jsonl` (sha256 `ec8b9c27e48f`); the latest record per case counts
- Labelled by: assistant, evidence-grounded (143)
- Generated: 2026-10-03 by `python -m evals.benchmark.label_report --split dev`

## 1. Kept and dropped buggy cases

102 buggy cases labelled: **80 kept (78.4%)**, **22 dropped (21.6%)**. 41 clean cases labelled (143 cases in all).

| Repo | Buggy | Kept | Dropped | Kept % | Clean |
|---|---|---|---|---|---|
| Textualize/rich | 10 | 7 | 3 | 70.0% | 10 |
| agronholm/anyio | 33 | 25 | 8 | 75.8% | 8 |
| fastapi/fastapi | 25 | 23 | 2 | 92.0% | 11 |
| marshmallow-code/marshmallow | 9 | 8 | 1 | 88.9% | 2 |
| pallets/click | 25 | 17 | 8 | 68.0% | 10 |
| **All** | 102 | 80 | 22 | 78.4% | 41 |

## 2. Drop reasons

| Reason | Count | Share of drops |
|---|---|---|
| `f` feature | 2 | 9.1% |
| `t` typing-only | 8 | 36.4% |
| `r` refactor | 1 | 4.5% |
| `n` not-a-bug | 2 | 9.1% |
| `o` other | 9 | 40.9% |

`o` notes (9; 8 are `external-compat`):

- `05cc8a6bbaa9630b` (anyio): external-compat: only broke with pytest<=6.1.2 (issue #1028)
- `0f097b6d4ac12b55` (click): dual-option arbitration policy redesign; upstream disputes whether 8.3 behaviour is a bug (issue #3403: 'working correctly in 8.3.3'); bug not isolable to one range
- `2a8644ee90c47f60` (anyio): external-compat: worker and portal threads inherit the caller's context on free-threaded Python 3.14t; PR titled 'support free-threaded python3.14' (issue #1220)
- `3811ac234bb6c989` (anyio): external-compat: Path.copy()/copy_into() failing on Python 3.14.0a7 pre-release
- `58326beef95afce9` (anyio): external-compat: Python 3.15 pathlib API changes (is_reserved removed, __vfspath__ added), PR #1065, issue #1061
- `59c2f7b75738992e` (rich): external-compat: Style meta marshal to pickle and hash rework inside PR #3861 'bump for Python3.14'; CHANGELOG 14.2.0 lists only 'Python3.14 compatibility'
- `6a31dd18a51e7ec9` (fastapi): external-compat: TYPE_CHECKING annotations under Python 3.14 deferred evaluation (PEP 649) need annotation_format=FORWARDREF (PR #14789, label bug)
- `8c79d2c242de8303` (rich): external-compat: functools.cache missing on Python 3.8 (still supported then); a fix-up commit inside feature PR #3930 (graphemes) before merge, so never released broken
- `90263b328f6189da` (anyio): external-compat: _interpqueues API changed in Python 3.14.0b2 (issue #926, PR #927)

## 3. Categories of kept buggy cases

| Category | Count | Share |
|---|---|---|
| type-or-contract | 34 | 42.5% |
| control-flow | 17 | 21.2% |
| concurrency-or-async | 9 | 11.2% |
| error-handling | 7 | 8.8% |
| null-or-none-handling | 4 | 5.0% |
| off-by-one-or-boundary | 3 | 3.8% |
| arithmetic-or-numeric | 2 | 2.5% |
| resource-leak | 2 | 2.5% |
| CWE-20 | 1 | 1.2% |
| CWE-400 | 1 | 1.2% |

No kept cases: CWE-22, CWE-78, CWE-79, CWE-89, CWE-94, CWE-200, CWE-502, CWE-798, CWE-918, security-other.

## 4. Heuristic category vs final label (kept cases)

- Agreed: 20
- Overrode: 13
- Heuristic was null: 47

Overrides (heuristic → label):

- concurrency-or-async → error-handling: 2
- off-by-one-or-boundary → type-or-contract: 2
- concurrency-or-async → CWE-400: 1
- concurrency-or-async → arithmetic-or-numeric: 1
- concurrency-or-async → null-or-none-handling: 1
- concurrency-or-async → type-or-contract: 1
- control-flow → resource-leak: 1
- control-flow → type-or-contract: 1
- null-or-none-handling → control-flow: 1
- type-or-contract → control-flow: 1
- type-or-contract → null-or-none-handling: 1

## 5. Primary-range coverage (kept cases)

- Single labelled range: 27
- Several ranges, one clear primary: 21
- Several ranges, contested (other ranges hold the same bug just as much: its other half, or the same mistake on a parallel code path): 32

**Clear primary range: 48/80 (60.0%)**; contested: 32/80 (40.0%). Contested ranges are recorded per case in `primary_contested_with`.

## 6. Suspicious clean cases

3 of 41 clean cases marked suspicious (they stay clean cases):

- `1368e5b14e17732e` (anyio): incomplete change: allows 0 tokens only in the asyncio backend setter; CapacityLimiterAdapter (limiters created outside an event loop) still rejected 0 until a later fix (PR #1183). The diff's own lines are correct; the bug is an omission in another file
- `3350b7f5558de194` (rich): Live._nested is set True when started nested but never reset; a Live reused later as the top-level live keeps _nested=True, so refresh() calls _live_stack[0].refresh() on itself (unbounded recursion) and stop() returns before stopping the refresh thread. Unchanged at upstream HEAD (checked 2026-10-03 in the local clone); upstream issues were not searched. clear_live() also pops the last entry, not necessarily self
- `3fe0fe03cd5c9e75` (click): likely buggy: eagerly replaces default=True with flag_value for every flag with a flag_value. Negative boolean flags (flag_value=False, default=True) become always False (issue #3111, later fixed by 446f5800db554d12) and callable flag_values such as classes get instantiated (issue #3121, PR #3225). SZZ missed it because the fixes changed relocated code in get_default

## 7. Estimated label noise

- **Upper bound: 22/102 = 21.6%** of mined bug-fix cases were not usable bugs (every drop reason).
- Excluding `o` (some of which may be genuine bugs that could not be classified): 13/102 = 12.7%.
- Dropped as `n` not-a-bug alone: 2/102 = 2.0%.

## 8. Macro-recall eligible categories (≥5 kept cases)

concurrency-or-async (9), control-flow (17), error-handling (7), type-or-contract (34)

Below the threshold: null-or-none-handling (4), off-by-one-or-boundary (3), resource-leak (2), arithmetic-or-numeric (2), CWE-20 (1), CWE-400 (1).

## 9. Owner verification

Stratified sample of 25 kept cases (`evals/benchmark/data/verification_sample.md`; `python -m evals.benchmark.verify_sample --score`):

| Field | Agree | Decided | Agreement | 95% lower bound (Wilson) |
|---|---|---|---|---|
| validity | 25 | 25 | 100.0% | 86.7% |
| category | 25 | 25 | 100.0% | 86.7% |
| primary range | 25 | 25 | 100.0% | 86.7% |

Borderline cases (owner's choice, scored separately): validity 3/3 agree; category 1/1 agree; primary range 1/1 agree.
