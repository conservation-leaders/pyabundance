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
    seed = 20260605
    n_sites = 500
    n_visits = 3
    beta = np.array([0.2, 0.6], dtype=np.float64)
    detection_logits = np.array([-0.8, -0.2, 0.4], dtype=np.float64)
    psi = 0.25
    k = 100

    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=n_sites)
    lam = np.exp(beta[0] + beta[1] * x)
    p = logistic(detection_logits)
    structural_zero = rng.binomial(1, psi, size=n_sites).astype(bool)
    latent_n = rng.poisson(lam)
    latent_n[structural_zero] = 0
    y = np.column_stack([rng.binomial(latent_n, p_visit) for p_visit in p]).astype(int)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(y, columns=["y1", "y2", "y3"]).to_csv(
        DATA_DIR / "pcount_zip_counts.csv", index=False
    )
    pd.DataFrame({"x": x}).to_csv(DATA_DIR / "pcount_zip_site_covs.csv", index=False)
    (DATA_DIR / "pcount_zip_true_params.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "n_sites": n_sites,
                "n_visits": n_visits,
                "K": k,
                "beta": beta.tolist(),
                "detection_logits": detection_logits.tolist(),
                "detection_probabilities": p.tolist(),
                "psi": psi,
                "logit_psi": float(np.log(psi / (1.0 - psi))),
                "max_observed_count": int(y.max()),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
