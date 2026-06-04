"""Dataset helpers for pyabundance examples and benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from pyabundance.simulate import simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip

ExampleName = Literal["poisson", "negative_binomial", "zip"]


@dataclass(frozen=True)
class ExamplePCountData:
    name: str
    site_data: pd.DataFrame
    obs_data: pd.DataFrame
    count_cols: list[str]
    X: NDArray[np.float64]
    W: NDArray[np.float64]
    y: NDArray[np.float64]
    true_params: dict[str, object]
    abundance_formula: str
    detection_formula: str
    K: int


def benchmark_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "benchmark"


def list_example_datasets() -> list[str]:
    return ["poisson", "negative_binomial", "zip"]


def load_example_pcount(
    name: ExampleName = "poisson", *, n_sites: int = 120, seed: int = 20260606
) -> ExamplePCountData:
    """Generate a deterministic bundled synthetic pcount example dataset.

    The data are generated on demand to avoid shipping large files while keeping examples
    reproducible. The returned object includes both pandas DataFrames and matrix/tensor inputs.
    """
    if name not in {"poisson", "negative_binomial", "zip"}:
        raise ValueError("name must be 'poisson', 'negative_binomial', or 'zip'")
    rng = np.random.default_rng(seed)
    n_visits = 3
    site_id = [f"site_{i + 1:03d}" for i in range(n_sites)]
    forest = rng.normal(size=n_sites)
    elevation = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), forest, elevation]).astype(np.float64)
    visit_labels = ["v1", "v2", "v3"]
    W = np.zeros((n_sites, n_visits, n_visits), dtype=np.float64)
    for visit_index in range(n_visits):
        W[:, visit_index, visit_index] = 1.0
    beta = np.array([0.2, 0.5, -0.25], dtype=np.float64)
    detection = np.array([-0.8, -0.2, 0.35], dtype=np.float64)
    if name == "poisson":
        y = simulate_pcount(X, W, beta=beta, alpha=detection, seed=seed + 1)
        true_params: dict[str, object] = {"beta": beta.tolist(), "detection": detection.tolist()}
        K = 70
    elif name == "negative_binomial":
        r = 1.6
        y = simulate_pcount_negbin(X, W, beta=beta, detection=detection, r=r, seed=seed + 2)
        true_params = {"beta": beta.tolist(), "detection": detection.tolist(), "r": r}
        K = 100
    else:
        psi = 0.25
        y = simulate_pcount_zip(X, W, beta=beta, detection=detection, psi=psi, seed=seed + 3)
        true_params = {"beta": beta.tolist(), "detection": detection.tolist(), "psi": psi}
        K = 100
    count_cols = ["y1", "y2", "y3"]
    site_data = pd.DataFrame(
        {
            "site_id": site_id,
            "y1": y[:, 0],
            "y2": y[:, 1],
            "y3": y[:, 2],
            "forest": forest,
            "elevation": elevation,
        }
    )
    obs_rows = []
    for site in site_id:
        for visit_label in visit_labels:
            obs_rows.append({"site_id": site, "visit": visit_label})
    obs_data = pd.DataFrame(obs_rows)
    obs_data["visit"] = pd.Categorical(obs_data["visit"], categories=visit_labels, ordered=True)
    return ExamplePCountData(
        name=name,
        site_data=site_data,
        obs_data=obs_data,
        count_cols=count_cols,
        X=X,
        W=W,
        y=y,
        true_params=true_params,
        abundance_formula="~ forest + elevation",
        detection_formula="~ visit - 1",
        K=K,
    )
