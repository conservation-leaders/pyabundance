from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "benchmark"


def logistic(x: np.ndarray) -> np.ndarray:
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def main() -> None:
    seed = 20260603
    n_sites = 500
    n_visits = 3
    beta = np.array([0.2, 0.6], dtype=np.float64)
    detection_logits = np.array([-0.8, -0.2, 0.4], dtype=np.float64)
    k = 60

    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=n_sites)
    lam = np.exp(beta[0] + beta[1] * x)
    p = logistic(detection_logits)
    latent_n = rng.poisson(lam)
    y = np.column_stack([rng.binomial(latent_n, p_visit) for p_visit in p]).astype(int)

    W = np.zeros((n_sites, n_visits, n_visits), dtype=np.float64)
    for visit in range(n_visits):
        W[:, visit, visit] = 1.0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(y, columns=["y1", "y2", "y3"]).to_csv(DATA_DIR / "pcount_counts.csv", index=False)
    pd.DataFrame({"x": x}).to_csv(DATA_DIR / "pcount_site_covs.csv", index=False)
    np.save(DATA_DIR / "pcount_obs_design.npy", W)
    (DATA_DIR / "pcount_true_params.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "n_sites": n_sites,
                "n_visits": n_visits,
                "K": k,
                "beta": beta.tolist(),
                "detection_logits": detection_logits.tolist(),
                "detection_probabilities": p.tolist(),
                "max_observed_count": int(y.max()),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
