from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pyabundance
import pytest
from pyabundance import pcount_df
from pyabundance.pcount_mapping import (
    PCountParameterMapping,
    pcount_parameter_map,
    pcount_parameter_mapping,
    pcount_parameter_mapping_table,
)
from pyabundance.result import PCountResult


def _result(*, mixture: str = "poisson") -> PCountResult:
    params = [0.25, 0.1, -0.5, 0.2]
    if mixture == "negative_binomial":
        params.append(math.log(2.5))
    elif mixture == "zero_inflated_poisson":
        params.append(0.0)
    y = np.asarray([[0.0, 1.0], [1.0, 2.0], [0.0, 0.0]], dtype=np.float64)
    X = np.asarray([[1.0, 0.1], [1.0, 0.5], [1.0, 0.3]], dtype=np.float64)
    W = np.ones((3, 2, 2), dtype=np.float64)
    W[:, 0, 1] = 0.0
    W[:, 1, 1] = 1.0
    return PCountResult(
        params=np.asarray(params, dtype=np.float64),
        n_abundance_params=2,
        n_detection_params=2,
        loglik=-10.0,
        success=True,
        message="fixture",
        K=12,
        mixture=mixture,  # type: ignore[arg-type]
        X=X,
        W=W,
        method="BFGS",
        nfev=1,
        nit=1,
        y=y,
        abundance_column_names=["Intercept", "forest"],
        detection_column_names=["visit[y1]", "visit[y2]"],
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        from_dataframe=True,
        param_names=["Intercept", "forest", "visit[y1]", "visit[y2]"]
        + (["log_r"] if mixture == "negative_binomial" else [])
        + (["logit_psi"] if mixture == "zero_inflated_poisson" else []),
    )


def test_poisson_pcount_mapping_includes_lambda_and_p_rows_and_blocks():
    mapping = pcount_parameter_mapping(_result())
    assert isinstance(mapping, PCountParameterMapping)
    table = mapping.table

    assert list(table["process"]) == ["lambda", "lambda", "p", "p"]
    assert list(table["block"].unique()) == ["lambda", "p"]
    assert list(table["coefficient_source"].unique()) == [
        "result.beta",
        "result.detection / result.alpha",
    ]
    assert "abundance state / lambda coefficients" in set(table["unmarked_term"])
    assert "detection probability coefficients" in set(table["unmarked_term"])
    assert mapping.summary()["processes"] == ["lambda", "p"]


def test_negative_binomial_mapping_includes_r_log_r_and_transformed_r():
    fit = _result(mixture="negative_binomial")
    table = pcount_parameter_mapping_table(fit)
    r_row = table.loc[table["process"] == "r"].iloc[0]

    assert r_row["parameter"] == "log_r"
    assert r_row["link"] == "log"
    assert r_row["level"] == "global"
    assert r_row["transformed_name"] == "r"
    assert r_row["transformed_estimate"] == pytest.approx(fit.r)
    assert r_row["fitted_block"] == "r ParameterBlock"


def test_zip_mapping_includes_psi_logit_psi_and_transformed_psi():
    fit = _result(mixture="zero_inflated_poisson")
    table = pcount_parameter_mapping_table(fit)
    psi_row = table.loc[table["process"] == "psi"].iloc[0]

    assert psi_row["parameter"] == "logit_psi"
    assert psi_row["link"] == "logit"
    assert psi_row["level"] == "global"
    assert psi_row["transformed_name"] == "psi"
    assert psi_row["transformed_estimate"] == pytest.approx(fit.psi)
    assert psi_row["fitted_block"] == "psi ParameterBlock"


def test_indices_and_parameter_block_ranges_align_with_result_blocks():
    fit = _result(mixture="negative_binomial")
    table = pcount_parameter_mapping_table(fit)

    assert list(table["index"]) == list(range(fit.params.size))
    assert list(table["parameter_vector_index"]) == list(range(fit.params.size))
    for block in fit.parameter_blocks:
        block_rows = table.loc[table["block"] == block.name]
        assert set(block_rows["block_start"]) == {block.start}
        assert set(block_rows["block_stop"]) == {block.stop}
        assert list(block_rows["block_index"]) == list(range(block.size))
        assert list(block_rows["parameter"]) == list(block.columns)


def test_links_and_process_levels_match_pcount_terms():
    fit = _result(mixture="zero_inflated_poisson")
    table = pcount_parameter_mapping_table(fit)
    expected = {
        "lambda": ("log", "site"),
        "p": ("logit", "observation"),
        "psi": ("logit", "global"),
    }
    observed = {
        process: (rows["link"].iloc[0], rows["level"].iloc[0])
        for process, rows in table.groupby("process", sort=False)
    }
    assert observed == expected

    nb_table = pcount_parameter_mapping_table(_result(mixture="negative_binomial"))
    r_row = nb_table.loc[nb_table["process"] == "r"].iloc[0]
    assert (r_row["link"], r_row["level"]) == ("log", "global")


def test_formula_fit_preserves_formulas_and_column_names_in_mapping():
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

    table = pcount_parameter_mapping_table(fit)
    lambda_rows = table.loc[table["process"] == "lambda"]
    p_rows = table.loc[table["process"] == "p"]
    assert set(lambda_rows["formula"]) == {"~ forest"}
    assert set(p_rows["formula"]) == {"~ visit - 1"}
    assert list(lambda_rows["column"]) == ["Intercept", "forest"]
    assert list(p_rows["column"]) == ["visit[y1]", "visit[y2]"]
    assert lambda_rows.iloc[0]["model_spec_process"]["columns"] == ("Intercept", "forest")
    assert p_rows.iloc[0]["process_columns"] == ("visit[y1]", "visit[y2]")


def test_unsupported_object_raises_clear_type_error():
    with pytest.raises(TypeError, match="requires a PCountResult"):
        pcount_parameter_mapping(object())


def test_mapping_table_and_alias_helpers():
    fit = _result()
    assert pcount_parameter_map(fit).table.equals(pcount_parameter_mapping(fit).table)
    assert list(pcount_parameter_mapping_table(fit)["parameter"]) == [
        "Intercept",
        "forest",
        "visit[y1]",
        "visit[y2]",
    ]


def test_top_level_pyabundance_all_does_not_expose_parameter_mapping_names():
    assert "pcount_parameter_mapping" not in pyabundance.__all__
    assert "pcount_parameter_mapping_table" not in pyabundance.__all__
    assert "pcount_parameter_map" not in pyabundance.__all__
    assert "PCountParameterMapping" not in pyabundance.__all__
    assert "ParameterMappingRow" not in pyabundance.__all__
