"""Power of the exact McNemar test for paired ablation comparisons (no LLM calls).

    python -m evals.power

Model: every case independently lands in one of three cells: changed for the worse (b, the
earlier run only), changed for the better (c, the later run only) or unchanged. Pure noise
splits the measured discordance rate pd evenly: P(b) = P(c) = pd / 2. A real effect of Δ net
fixes over n cases moves P(c) to pd / 2 + Δ / n. Power is the probability that the exact
McNemar test rejects at α, summed exactly over the multinomial distribution of (b, c). The
minimum detectable effect (MDE) is the smallest Δ with power at least 80%.
"""

import math

from evals.metrics import mcnemar

ALPHA = 0.05
TARGET_POWER = 0.80


def mcnemar_p(b: int, c: int) -> float:
    return float(mcnemar([True] * b + [False] * c, [False] * b + [True] * c)["p_value"])


def power(n: int, pd: float, delta: int, alpha: float = ALPHA) -> float:
    """P(exact McNemar rejects) with noise discordance pd and Δ net fixes among n cases."""
    p_b, p_c = pd / 2, pd / 2 + delta / n
    if p_b + p_c > 1:
        return float("nan")
    total = 0.0
    log_n = math.lgamma(n + 1)
    for b in range(n + 1):
        for c in range(n + 1 - b):
            rest = n - b - c
            if (b and p_b == 0) or (c and p_c == 0) or (rest and p_b + p_c >= 1):
                continue  # impossible cell: probability 0
            log_p = (
                log_n
                - math.lgamma(b + 1)
                - math.lgamma(c + 1)
                - math.lgamma(rest + 1)
                + (b * math.log(p_b) if b else 0.0)
                + (c * math.log(p_c) if c else 0.0)
                + (rest * math.log(1 - p_b - p_c) if rest else 0.0)
            )
            if log_p < -40:
                continue
            if c > b and mcnemar_p(b, c) < alpha:
                total += math.exp(log_p)
    return total


def minimum_detectable(n: int, pd: float, target: float = TARGET_POWER) -> int | None:
    """Smallest Δ (net cases fixed) giving at least `target` power, or None if none fits."""
    for delta in range(1, n + 1):
        value = power(n, pd, delta)
        if math.isnan(value):
            return None
        if value >= target:
            return delta
    return None


# Noise discordance between v1 and its identical no-cache rerun (Q63; b + c over n).
NOISE = {"detected": (6, 80), "strict_category": (19, 80), "flagged": (12, 41)}
# Falsification split: the 64 cases that reference external definitions (46 buggy, 18 clean)
# and the 57 that do not (34 buggy, 23 clean).
GROUPS = {
    "all": (80, 41),
    "references external definitions (64)": (46, 18),
    "no external references (57)": (34, 23),
}


def table(scale: dict[str, float] | None = None) -> list[tuple[str, str, int, float, int | None]]:
    """(group, measure, n, pd, MDE) for every group and measure; `scale` multiplies pd."""
    rows = []
    for group, (buggy, clean) in GROUPS.items():
        for measure, (disagree, n_noise) in NOISE.items():
            n = clean if measure == "flagged" else buggy
            pd = disagree / n_noise * (scale or {}).get(measure, 1.0)
            rows.append((group, measure, n, pd, minimum_detectable(n, pd)))
    return rows


def main() -> int:
    for group, measure, n, pd, mde in table():
        shown = f"{mde} ({mde / n:.0%})" if mde else "not reachable"
        print(f"{group:40s} {measure:16s} n={n:3d} pd={pd:.3f} MDE={shown}")
    return 0


# --- k-run aggregation (ADR-029): paired permutation test on per-case means ------------------


def case_mixture(both_true: int, both_false: int, flipped: int) -> tuple[int, int, int]:
    """Stable-true, stable-false and unstable case counts implied by two identical runs.

    An unstable case is modelled as a coin flip per call (p = 0.5): two calls disagree with
    probability 1/2, so U = 2 * flipped unstable cases, and the U/2 that agreed are removed from
    the stable counts in proportion (half agreed true, half false)."""
    unstable = min(2 * flipped, flipped + both_true + both_false)
    agreed_unstable = unstable - flipped
    stable_true = max(0, both_true - agreed_unstable // 2)
    stable_false = max(0, both_false - (agreed_unstable - agreed_unstable // 2))
    return stable_true, stable_false, unstable


def permutation_power(
    mixture: tuple[int, int, int],
    delta: int,
    k: int,
    sims: int = 400,
    perms: int = 1000,
    alpha: float = ALPHA,
    seed: int = 1,
) -> float:
    """Power of a two-sided paired sign-flip permutation test on per-case means of k runs.

    The baseline arm has the given mixture of per-case success probabilities (1, 0, 0.5). The
    treatment arm turns `delta` cases into stable successes, taken from stable failures first,
    then from unstable cases: the effect is "delta net cases fixed"."""
    import numpy as np  # noqa: PLC0415 (only for the simulation)

    stable_true, stable_false, unstable = mixture
    base = np.array([1.0] * stable_true + [0.0] * stable_false + [0.5] * unstable)
    treat = base.copy()
    order = [i for i in range(len(base)) if base[i] == 0.0] + [
        i for i in range(len(base)) if base[i] == 0.5
    ]
    for i in order[:delta]:
        treat[i] = 1.0
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(sims):
        a = rng.binomial(k, base) / k
        b = rng.binomial(k, treat) / k
        diff = b - a
        observed = diff.sum()
        signs = rng.choice((-1.0, 1.0), size=(perms, len(diff)))
        null = (signs * diff).sum(axis=1)
        if (np.sum(np.abs(null) >= abs(observed)) + 1) / (perms + 1) < alpha:
            hits += 1
    return hits / sims


def permutation_mde(
    mixture: tuple[int, int, int], k: int, target: float = TARGET_POWER
) -> int | None:
    n = sum(mixture)
    for delta in range(1, n + 1):
        if permutation_power(mixture, delta, k) >= target:
            return delta
    return None


if __name__ == "__main__":
    raise SystemExit(main())
