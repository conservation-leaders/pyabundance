from __future__ import annotations

import numpy as np
import pandas as pd
from pyabundance import pcount_df, simulate_pcount

rng = np.random.default_rng(42)
n_sites = 100
x = rng.normal(size=n_sites)
X = np.column_stack([np.ones(n_sites), x])
W = np.zeros((n_sites, 3, 3), dtype=float)
for visit in range(3):
    W[:, visit, visit] = 1.0

y = simulate_pcount(X, W, beta=[0.2, 0.5], alpha=[-0.8, -0.2, 0.4], seed=43)
df = pd.DataFrame({"y1": y[:, 0], "y2": y[:, 1], "y3": y[:, 2], "x": x})

fit = pcount_df(
    site_data=df,
    count_cols=["y1", "y2", "y3"],
    abundance_formula="~ x",
    detection_formula="~ visit - 1",
    mixture="poisson",
    K=60,
)
print(fit.summary())
