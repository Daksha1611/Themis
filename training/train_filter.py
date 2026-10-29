"""Train and cross-validate the precision filter on the dev training set (M5, ADR-030).

    python -m training.train_filter [--no-encoder]

Two models, compared on out-of-fold scores:
- **features:** a logistic regression over finding features (category, severity,
  `raw_llm_confidence`, message and suggestion length, span, changed line vs context, hunk size,
  diff size); the reference;
- **codebert:** frozen `microsoft/codebert-base` embeddings (mean-pooled, CPU) of the finding
  text plus its diff snippet, with a logistic-regression head (ADR-008).

Cross-validation is grouped by case ID: every scored dev case is assigned to one of 5 folds
(seeded, stratified by buggy/clean), so a case's findings from different runs never sit in both
train and test. The threshold is chosen inside each outer fold, on inner out-of-fold scores of
the training folds only (Q17): the highest precision whose detection rate stays within
`MAX_DETECTION_DROP` of unfiltered. Every reported number is therefore out-of-fold.
"""

import argparse
import hashlib
import json
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from app.taxonomy import ALLOWED_CATEGORIES
from evals.benchmark.label import LABELS, load_labels
from evals.runner import scored_cases
from training.build_training_set import OUT as TRAINING_SET
from training.build_training_set import holdout_ids, require_dev_only

FOLDS = 5
SEED = 20261029
MAX_DETECTION_DROP = 0.05  # Q17: detection may fall at most 5 points below unfiltered
SEVERITY = {"low": 0, "medium": 1, "high": 2, "critical": 3}
ENCODER = "microsoft/codebert-base"
EMBEDDING_CACHE = Path("training/.cache")
C_GRID = (0.001, 0.01, 0.1, 1.0, 10.0)

Rows = list[dict[str, Any]]


def load_rows(path: Path = TRAINING_SET) -> Rows:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    require_dev_only({r["case_id"] for r in rows}, holdout_ids())
    return rows


def assign_folds(
    cases: list[dict[str, Any]], folds: int = FOLDS, seed: int = SEED
) -> dict[str, int]:
    """case ID -> fold, seeded, buggy and clean cases dealt round-robin separately."""
    out: dict[str, int] = {}
    for kind in ("buggy", "clean"):
        ids = sorted(c["case_id"] for c in cases if c["kind"] == kind)
        random.Random(f"{seed}-{kind}").shuffle(ids)  # noqa: S311 (reproducible folds)
        out.update({cid: i % folds for i, cid in enumerate(ids)})
    return out


def feature_matrix(rows: Rows) -> np.ndarray:
    categories = sorted(ALLOWED_CATEGORIES)
    out = []
    for r in rows:
        f = r["features"]
        out.append(
            [
                *(float(f["category"] == c) for c in categories),
                float(SEVERITY.get(f["severity"], 1)),
                f["raw_llm_confidence"],
                np.log1p(f["message_chars"]),
                np.log1p(f["suggestion_chars"]),
                np.log1p(f["span_lines"]),
                f["on_changed_line"],
                np.log1p(f["hunk_changed_lines"]),
                np.log1p(f["diff_changed_lines"]),
            ]
        )
    return np.array(out, dtype=float)


def finding_text(r: dict[str, Any]) -> str:
    f = r["finding"]
    return (
        f"{f['category']} {f['severity']}: {f['message']}\n"
        f"suggestion: {f.get('suggestion') or ''}\n{r['snippet']}"
    )


def encoder_matrix(rows: Rows, model_name: str = ENCODER) -> np.ndarray:
    """Mean-pooled last hidden states, cached on disk by the texts' hash."""
    texts = [finding_text(r) for r in rows]
    digest = hashlib.sha256(("\0".join([model_name, *texts])).encode()).hexdigest()[:16]
    cached = EMBEDDING_CACHE / f"{model_name.replace('/', '__')}-{digest}.npy"
    if cached.exists():
        return np.asarray(np.load(cached), dtype=float)
    import torch  # noqa: PLC0415 (heavy; only for the encoder)
    from transformers import AutoModel, AutoTokenizer  # noqa: PLC0415

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    vectors = []
    with torch.no_grad():
        for start in range(0, len(texts), 16):
            batch = tokenizer(
                texts[start : start + 16],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=256,
            )
            hidden = model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).float()
            vectors.append(((hidden * mask).sum(1) / mask.sum(1)).numpy())
    matrix = np.concatenate(vectors)
    EMBEDDING_CACHE.mkdir(parents=True, exist_ok=True)
    np.save(cached, matrix)
    return matrix


def fit(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> Any:
    """Standardised logistic regression; C chosen by grouped inner CV on average precision."""
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    from sklearn.metrics import average_precision_score  # noqa: PLC0415
    from sklearn.model_selection import GroupKFold  # noqa: PLC0415
    from sklearn.pipeline import make_pipeline  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

    splits = list(GroupKFold(n_splits=4).split(x, y, groups))
    best_c, best_score = C_GRID[0], -1.0
    for c in C_GRID:
        scores = np.zeros(len(y))
        for train, test in splits:
            model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=5000))
            model.fit(x[train], y[train])
            scores[test] = model.predict_proba(x[test])[:, 1]
        score = average_precision_score(y, scores)
        if score > best_score:
            best_c, best_score = c, score
    model = make_pipeline(StandardScaler(), LogisticRegression(C=best_c, max_iter=5000))
    model.fit(x, y)
    model.chosen_c = best_c
    return model


def detection(rows: Rows, keep: np.ndarray, buggy_cases: set[str], runs: list[str]) -> float:
    """Mean over runs of the share of `buggy_cases` with at least one kept finding."""
    if not buggy_cases:
        return 0.0
    per_run = []
    for run in runs:
        detected = {
            r["case_id"]
            for r, k in zip(rows, keep, strict=True)
            if k and r["run"] == run and r["case_id"] in buggy_cases
        }
        per_run.append(len(detected) / len(buggy_cases))
    return float(np.mean(per_run))


def choose_threshold(
    rows: Rows, scores: np.ndarray, buggy_cases: set[str], max_drop: float = MAX_DETECTION_DROP
) -> float:
    """The threshold with the highest pooled precision whose detection rate is at most
    `max_drop` below unfiltered; ties go to the lower threshold (fewer findings dropped)."""
    runs = sorted({r["run"] for r in rows})
    labels = np.array([r["label"] for r in rows])
    base = detection(rows, np.ones(len(rows), dtype=bool), buggy_cases, runs)
    best_t, best_p = 0.0, labels.mean() if len(labels) else 0.0
    for t in sorted(set(scores.tolist())):
        keep = scores >= t
        if not keep.any() or detection(rows, keep, buggy_cases, runs) < base - max_drop - 1e-9:
            continue
        precision = labels[keep].mean()
        if precision > best_p + 1e-12:
            best_t, best_p = t, precision
    return float(best_t)


def cross_validate(
    rows: Rows, x: np.ndarray, folds: dict[str, int], buggy: set[str]
) -> dict[str, Any]:
    """Out-of-fold scores, plus the threshold chosen inside each outer fold."""
    y = np.array([r["label"] for r in rows])
    fold = np.array([folds[r["case_id"]] for r in rows])
    groups = np.array([r["case_id"] for r in rows])
    scores = np.zeros(len(rows))
    thresholds: dict[int, float] = {}
    chosen_c: dict[int, float] = {}
    for k in range(FOLDS):
        train, test = np.where(fold != k)[0], np.where(fold == k)[0]
        inner = np.zeros(len(train))  # inner out-of-fold scores, for the threshold
        for j in sorted(set(fold[train].tolist())):
            inner_train = train[fold[train] != j]
            inner_test_mask = fold[train] == j
            model = fit(x[inner_train], y[inner_train], groups[inner_train])
            inner[inner_test_mask] = model.predict_proba(x[train][inner_test_mask])[:, 1]
        train_rows = [rows[i] for i in train]
        train_buggy = {cid for cid in buggy if folds[cid] != k}
        thresholds[k] = choose_threshold(train_rows, inner, train_buggy)
        model = fit(x[train], y[train], groups[train])
        chosen_c[k] = model.chosen_c
        scores[test] = model.predict_proba(x[test])[:, 1]
    return {"scores": scores, "thresholds": thresholds, "chosen_c": chosen_c, "fold": fold}


def ranking_quality(y: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import average_precision_score, roc_auc_score  # noqa: PLC0415

    return {
        "roc_auc": float(roc_auc_score(y, scores)),
        "average_precision": float(average_precision_score(y, scores)),
        "base_rate": float(y.mean()),
    }


def run(encoder: bool = True, out_dir: Path | None = None) -> dict[str, Any]:
    labels = load_labels(LABELS)
    cases = scored_cases("dev", labels)
    rows = load_rows()
    folds = assign_folds(cases)
    buggy = {c["case_id"] for c in cases if c["kind"] == "buggy"}
    y = np.array([r["label"] for r in rows])
    matrices: dict[str, Callable[[], np.ndarray]] = {"features": lambda: feature_matrix(rows)}
    if encoder:
        matrices["codebert"] = lambda: encoder_matrix(rows)
    results: dict[str, Any] = {}
    for name, make in matrices.items():
        cv = cross_validate(rows, make(), folds, buggy)
        results[name] = {
            "quality": ranking_quality(y, cv["scores"]),
            "thresholds": cv["thresholds"],
            "chosen_c": cv["chosen_c"],
            "scores": cv["scores"].tolist(),
        }
    out = {
        "rows": len(rows),
        "real": int(y.sum()),
        "folds": folds,
        "max_detection_drop": MAX_DETECTION_DROP,
        "models": results,
        "row_keys": [[r["run"], r["case_id"], r["finding_index"]] for r in rows],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "cv.json").write_text(json.dumps(out) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-encoder", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("evals/results/filter-dev"))
    args = parser.parse_args(argv)
    result = run(encoder=not args.no_encoder, out_dir=args.out)
    for name, model in result["models"].items():
        q = model["quality"]
        print(
            f"{name}: ROC AUC {q['roc_auc']:.3f}, average precision {q['average_precision']:.3f} "
            f"(base rate {q['base_rate']:.3f}); thresholds {model['thresholds']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def fine_tune_scores(
    rows: Rows, folds: dict[str, int], epochs: int = 3, model_name: str = ENCODER
) -> np.ndarray:
    """Out-of-fold scores from CodeBERT fine-tuned end to end (classification head) on each
    outer fold's training cases. Ranking quality only: choosing thresholds would need inner
    fine-tunes per fold, which is too slow on CPU unless the ranking beats the reference."""
    import torch  # noqa: PLC0415
    from transformers import AutoModelForSequenceClassification, AutoTokenizer  # noqa: PLC0415

    torch.manual_seed(SEED)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    texts = [finding_text(r) for r in rows]
    y = np.array([r["label"] for r in rows])
    fold = np.array([folds[r["case_id"]] for r in rows])
    scores = np.zeros(len(rows))
    for k in range(FOLDS):
        train, test = np.where(fold != k)[0], np.where(fold == k)[0]
        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
        optimiser = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
        rng = np.random.default_rng(SEED + k)
        model.train()
        for _ in range(epochs):
            shuffled = rng.permutation(train)
            for start in range(0, len(shuffled), 8):
                order = shuffled[start : start + 8]
                enc = tokenizer(
                    [texts[i] for i in order],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=256,
                )
                loss = model(**enc, labels=torch.tensor(y[order])).loss
                loss.backward()
                optimiser.step()
                optimiser.zero_grad()
        model.eval()
        with torch.no_grad():
            for start in range(0, len(test), 16):
                idx = test[start : start + 16]
                enc = tokenizer(
                    [texts[i] for i in idx],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=256,
                )
                scores[idx] = torch.softmax(model(**enc).logits, -1)[:, 1].numpy()
        print(f"fine-tune fold {k} done", flush=True)
    return scores
