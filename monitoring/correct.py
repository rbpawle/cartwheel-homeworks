"""Bias-corrected failure prevalence for a monitoring period."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def corrected_mode_prevalence(
    sample_preds: Sequence[int],
    test_labels: Sequence[int],
    test_preds: Sequence[int],
    confidence: float = 0.95,
    bootstrap_iterations: int = 20000,
    seed: int | None = 7,
) -> dict[str, Any]:
    """Bias-corrected live prevalence for one mode from sampled verdicts.

    The contract, precisely:

      1. ``raw`` is the uncorrected flag rate: ``mean(sample_preds)``.
      2. Compute the frozen judge's failure sensitivity and pass specificity
         from ``test_labels`` and ``test_preds``. Both use the monitoring
         convention that 1 means a failure is present. Failure sensitivity is
         the flagged fraction of human-labeled failures. Pass specificity is
         the unflagged fraction of human-labeled passes.
      3. Compute the Rogan-Gladen point estimate, then resample the held-out
         records and sampled predictions to obtain a percentile-bootstrap
         interval. Use a seeded NumPy generator so the committed result is
         reproducible.
      4. Resample the monitoring predictions and the paired held-out records
         independently with replacement. Keep their original sample sizes.
         Discard a draw if the correction cannot be computed. Clamp each
         retained estimate to [0, 1], then take the percentile interval.
         Raise ``ValueError`` if no replicate is valid.

    Args:
        sample_preds: the judge's 0/1 verdicts over the UNIFORM BASE sample
            only (never the risk strata; they are biased toward failure by
            design).
        test_labels: human labels for the frozen Homework 5 judge's test
            split.
        test_preds: the frozen judge's predictions on that test split.
        confidence: interval confidence level.
        bootstrap_iterations: number of percentile-bootstrap replicates.
        seed: numpy seed for a reproducible interval; None leaves the RNG
            untouched.

    Returns:
        {"raw", "corrected", "ci_low", "ci_high", "confidence",
         "failure_sensitivity", "pass_specificity", "n_sample"}
        with "corrected" clamped to [0, 1] and rates rounded to 4 places.

    Raises:
        ValueError: if an input is empty, the held-out inputs have different
            lengths, a value is not 0 or 1, a class is absent, the judge is
            missing a usable correction, or no bootstrap replicate is valid.
    """
    sample = np.asarray(sample_preds, dtype=int)
    labels = np.asarray(test_labels, dtype=int)
    preds = np.asarray(test_preds, dtype=int)
    if sample.size == 0 or labels.size == 0:
        raise ValueError("sample and held-out inputs must be nonempty")
    if labels.size != preds.size:
        raise ValueError("test_labels and test_preds must have the same length")
    for name, values in (("sample_preds", sample), ("test_labels", labels), ("test_preds", preds)):
        if not np.isin(values, (0, 1)).all():
            raise ValueError(f"{name} must contain only 0 or 1")
    if labels.all() or not labels.any():
        raise ValueError("held-out labels need both failures and passes")

    def rogan_gladen(raw, labels, preds):
        """Vectorized over the last axis; NaN where no usable correction exists."""
        failures = labels.sum(axis=-1)
        passes = labels.shape[-1] - failures
        with np.errstate(divide="ignore", invalid="ignore"):
            sensitivity = (labels * preds).sum(axis=-1) / failures
            specificity = ((1 - labels) * (1 - preds)).sum(axis=-1) / passes
            youden = sensitivity + specificity - 1
            corrected = (raw + specificity - 1) / youden
        usable = (failures > 0) & (passes > 0) & (youden > 0)
        return np.where(usable, corrected, np.nan), sensitivity, specificity

    raw = sample.mean()
    point, sensitivity, specificity = rogan_gladen(raw, labels, preds)
    if np.isnan(point):
        raise ValueError("judge has no usable correction (sensitivity + specificity <= 1)")

    # Resample the monitoring verdicts and the paired held-out records
    # independently, so the interval carries both sources of uncertainty.
    rng = np.random.default_rng(seed)
    sample_idx = rng.integers(0, sample.size, size=(bootstrap_iterations, sample.size))
    test_idx = rng.integers(0, labels.size, size=(bootstrap_iterations, labels.size))
    replicates, _, _ = rogan_gladen(
        sample[sample_idx].mean(axis=1), labels[test_idx], preds[test_idx]
    )
    replicates = np.clip(replicates[~np.isnan(replicates)], 0.0, 1.0)
    if replicates.size == 0:
        raise ValueError("no bootstrap replicate produced a usable correction")
    alpha = 1 - confidence
    ci_low, ci_high = np.percentile(replicates, [100 * alpha / 2, 100 * (1 - alpha / 2)])

    return {
        "raw": round(float(raw), 4),
        "corrected": round(float(np.clip(point, 0.0, 1.0)), 4),
        "ci_low": round(float(ci_low), 4),
        "ci_high": round(float(ci_high), 4),
        "confidence": confidence,
        "failure_sensitivity": round(float(sensitivity), 4),
        "pass_specificity": round(float(specificity), 4),
        "n_sample": int(sample.size),
    }
