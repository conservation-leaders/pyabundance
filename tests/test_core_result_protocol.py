from __future__ import annotations

import numpy as np
import pandas as pd
from pyabundance import pcount, pcount_df
from pyabundance.core import FitResultProtocol


def _matrix_fit(*, mixture: str = "poisson"):
    y = np.asarray(
        [
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 2.0],
            [0.0, 0.0, 1.0],
            [2.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
        ],
        dtype=np.float64,
    )
    n_sites, n_visits = y.shape
    X = np.ones((n_sites, 1), dtype=np.float64)
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    return pcount(y, X, W, K=12, mixture=mixture, method="BFGS")


def test_pcount_result_satisfies_shared_result_protocol():
    fit = _matrix_fit()
    assert isinstance(fit, FitResultProtocol)
    assert fit.model_spec.model == "pcount"
    assert tuple(block.name for block in fit.parameter_blocks) == ("lambda", "p")
    assert sum(block.size for block in fit.parameter_blocks) == fit.params.size
    for block in fit.parameter_blocks:
        assert fit.params[block.slice].size == block.size
    assert fit.model_spec.process("lambda").link == "log"
    assert fit.model_spec.process("p").link == "logit"


def test_poisson_pcount_parameter_blocks_align_with_existing_counts():
    fit = _matrix_fit()
    blocks = fit.parameter_blocks
    assert tuple(block.name for block in blocks) == ("lambda", "p")
    assert blocks[0].size == fit.n_abundance_params
    assert blocks[1].size == fit.n_detection_params
    assert sum(block.size for block in blocks) == fit.params.size
    assert {"lambda", "p"}.issubset(set(fit.model_spec.process_names))


def test_negative_binomial_pcount_has_r_process_and_block():
    fit = _matrix_fit(mixture="negative_binomial")
    assert tuple(block.name for block in fit.parameter_blocks) == ("lambda", "p", "r")
    block = fit.model_spec.block("r")
    assert block.columns == ("log_r",)
    assert fit.model_spec.process("r").link == "log"
    assert fit.model_spec.process("r").level == "global"


def test_zip_pcount_has_psi_process_and_block():
    fit = _matrix_fit(mixture="zero_inflated_poisson")
    assert tuple(block.name for block in fit.parameter_blocks) == ("lambda", "p", "psi")
    block = fit.model_spec.block("psi")
    assert block.columns == ("logit_psi",)
    assert fit.model_spec.process("psi").link == "logit"
    assert fit.model_spec.process("psi").level == "global"


def test_formula_pcount_model_spec_preserves_formulas_and_columns():
    site_data = pd.DataFrame(
        {
            "y1": [0, 1, 0, 2, 1, 0, 1, 2],
            "y2": [1, 1, 0, 1, 0, 1, 2, 1],
            "forest": [0.2, 0.5, 0.1, 0.8, 0.3, 0.4, 0.6, 0.9],
        }
    )
    fit = pcount_df(
        site_data=site_data,
        count_cols=["y1", "y2"],
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        K=12,
    )
    assert fit.model_spec.process("lambda").formula == "~ forest"
    assert fit.model_spec.process("p").formula == "~ visit - 1"
    assert fit.model_spec.process("lambda").columns == ("Intercept", "forest")
    assert fit.model_spec.process("p").columns == ("visit[y1]", "visit[y2]")
