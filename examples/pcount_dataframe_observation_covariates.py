from __future__ import annotations

import numpy as np
import pandas as pd
from pyabundance import pcount_df, simulate_pcount_negbin

rng = np.random.default_rng(44)
n_sites = 120
site_id = [f"s{i}" for i in range(n_sites)]
forest = rng.normal(size=n_sites)
elevation = rng.normal(size=n_sites)
X = np.column_stack([np.ones(n_sites), forest, elevation])
W = np.ones((n_sites, 3, 1), dtype=float)

y = simulate_pcount_negbin(X, W, beta=[0.2, 0.4, -0.1], detection=[-0.3], r=1.5, seed=45)
site_df = pd.DataFrame(
    {
        "site_id": site_id,
        "v1": y[:, 0],
        "v2": y[:, 1],
        "v3": y[:, 2],
        "forest": forest,
        "elevation": elevation,
    }
)
obs_rows = []
for sid in site_id:
    for visit in ["v1", "v2", "v3"]:
        obs_rows.append({"site_id": sid, "visit": visit, "wind": rng.normal(), "observer": "A"})
obs_df = pd.DataFrame(obs_rows)

fit = pcount_df(
    site_data=site_df,
    obs_data=obs_df,
    site_id_col="site_id",
    visit_col="visit",
    count_cols=["v1", "v2", "v3"],
    abundance_formula="~ forest + elevation",
    detection_formula="~ wind + observer",
    mixture="negative_binomial",
    K=100,
)
print(fit.summary())
