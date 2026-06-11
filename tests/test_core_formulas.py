from __future__ import annotations

import numpy as np
import pandas as pd
import pyabundance
import pytest
from formulaic import model_matrix
from pyabundance.core import (
    ProcessDesign,
    ProcessSpec,
    build_process_design,
    build_process_designs,
    validate_rhs_formula,
)


def _site_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "site_id": ["s1", "s2", "s3"],
            "forest": [0.2, 0.4, 0.8],
            "elevation": [100.0, 125.0, 150.0],
        }
    )


def _obs_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "site_id": ["s1", "s1", "s2", "s2", "s3", "s3"],
            "visit": ["v1", "v2", "v1", "v2", "v1", "v2"],
            "wind": [0.1, 0.2, 0.3, 0.2, 0.5, 0.4],
        }
    )


def test_build_lambda_site_design_from_process_spec():
    spec = ProcessSpec(name="lambda", formula="~ forest", link="log", level="site")
    data = _site_data()

    design = build_process_design(spec, data)
    expected = model_matrix("~ forest", data, na_action="raise")

    assert isinstance(design, ProcessDesign)
    assert design.process == "lambda"
    assert design.level == "site"
    assert design.link == "log"
    assert design.formula == "~ forest"
    assert design.columns == tuple(str(column) for column in expected.columns)
    np.testing.assert_allclose(design.matrix, np.asarray(expected, dtype=np.float64))


def test_build_p_observation_design_without_intercept():
    spec = ProcessSpec(name="p", formula="~ visit - 1", link="logit", level="observation")
    data = _obs_data()

    design = build_process_design(spec, data)
    expected = model_matrix("~ visit - 1", data, na_action="raise")

    assert design.process == "p"
    assert design.level == "observation"
    assert design.link == "logit"
    assert design.columns == ("visit[v1]", "visit[v2]")
    assert design.columns == tuple(str(column) for column in expected.columns)
    np.testing.assert_allclose(design.matrix, np.asarray(expected, dtype=np.float64))


def test_build_process_designs_for_pcount_like_process_mapping():
    processes = {
        "lambda": ProcessSpec(name="lambda", formula="~ forest", link="log", level="site"),
        "p": ProcessSpec(name="p", formula="~ visit - 1", link="logit", level="observation"),
    }

    designs = build_process_designs(
        processes,
        {
            "site": _site_data(),
            "observation": _obs_data(),
        },
    )

    assert tuple(designs) == ("lambda", "p")
    assert designs["lambda"].columns == ("Intercept", "forest")
    assert designs["p"].columns == ("visit[v1]", "visit[v2]")
    assert designs["lambda"].matrix.shape == (3, 2)
    assert designs["p"].matrix.shape == (6, 2)


def test_process_design_matrices_are_float64_and_contiguous():
    spec = ProcessSpec(name="lambda", formula="~ forest", link="log", level="site")

    design = build_process_design(spec, _site_data())

    assert design.matrix.dtype == np.float64
    assert design.matrix.flags["C_CONTIGUOUS"]


@pytest.mark.parametrize(
    "formula",
    [
        "count ~ forest",
        "count ~",
    ],
)
def test_validate_rhs_formula_rejects_non_rhs_formula(formula: str):
    with pytest.raises(ValueError, match="RHS-only|response-side"):
        validate_rhs_formula(formula)


@pytest.mark.parametrize("formula", ["", "   ", "~", "~   "])
def test_validate_rhs_formula_rejects_empty_formula(formula: str):
    with pytest.raises(ValueError, match="non-empty|right-hand side"):
        validate_rhs_formula(formula)


@pytest.mark.parametrize(
    "formula",
    [
        "~ .",
        "~ offset(wind)",
        "~ bs(forest)",
        "~ cs(forest)",
        "~ cr(forest)",
        "~ s(forest)",
        "~ (1 | site_id)",
    ],
)
def test_validate_rhs_formula_rejects_unsupported_features(formula: str):
    with pytest.raises(ValueError, match="unsupported formula feature"):
        validate_rhs_formula(formula)


def test_build_process_designs_missing_level_data_raises_clear_error():
    processes = {
        "lambda": ProcessSpec(name="lambda", formula="~ forest", link="log", level="site"),
        "p": ProcessSpec(name="p", formula="~ visit", link="logit", level="observation"),
    }

    with pytest.raises(ValueError, match="missing data.*observation.*p"):
        build_process_designs(processes, {"site": _site_data()})


def test_build_process_designs_requested_formula_less_global_process_raises():
    processes = {
        "lambda": ProcessSpec(name="lambda", formula="~ forest", link="log", level="site"),
        "r": ProcessSpec(name="r", formula=None, link="log", level="global"),
    }

    with pytest.raises(ValueError, match="process 'r'.*has no formula"):
        build_process_designs(
            processes,
            {"site": _site_data()},
            process_names=["r"],
        )


def test_build_process_designs_skips_formula_less_processes_by_default():
    processes = {
        "lambda": ProcessSpec(name="lambda", formula="~ forest", link="log", level="site"),
        "psi": ProcessSpec(name="psi", formula=None, link="logit", level="global"),
    }

    designs = build_process_designs(processes, {"site": _site_data()})

    assert tuple(designs) == ("lambda",)


def test_process_design_copies_metadata_and_columns_defensively():
    metadata = {"source": "spec"}
    spec = ProcessSpec(
        name="lambda",
        formula="~ forest",
        link="log",
        level="site",
        metadata=metadata,
    )
    design = build_process_design(spec, _site_data())
    metadata["source"] = "changed"

    assert design.metadata["source"] == "spec"
    with pytest.raises(TypeError):
        design.metadata["source"] = "mutated"


def test_top_level_all_does_not_expose_experimental_formula_builder_names():
    for name in [
        "ProcessDesign",
        "validate_rhs_formula",
        "build_process_design",
        "build_process_designs",
    ]:
        assert name not in pyabundance.__all__
