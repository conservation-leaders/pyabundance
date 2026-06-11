from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pyabundance.core import FitResultProtocol, ModelFrame, ModelSpec, ParameterBlock, ProcessSpec


def test_core_names_importable_from_subpackage():
    assert ModelSpec is not None
    assert ProcessSpec is not None
    assert ParameterBlock is not None
    assert FitResultProtocol is not None


def test_process_spec_stores_metadata():
    spec = ProcessSpec(
        name="lambda",
        formula="~ forest",
        link="log",
        level="site",
        columns=("Intercept", "forest"),
    )
    assert spec.name == "lambda"
    assert spec.formula == "~ forest"
    assert spec.link == "log"
    assert spec.level == "site"
    assert spec.columns == ("Intercept", "forest")


def test_parameter_block_size_and_slice():
    block = ParameterBlock(
        name="lambda",
        start=0,
        stop=2,
        link="log",
        columns=("Intercept", "forest"),
        process="lambda",
    )
    assert block.size == 2
    assert block.slice == slice(0, 2)


@pytest.mark.parametrize(
    ("start", "stop"),
    [(-1, 1), (2, 1)],
)
def test_parameter_block_rejects_invalid_ranges(start: int, stop: int):
    with pytest.raises(ValueError):
        ParameterBlock(name="bad", start=start, stop=stop, link="log")


def test_parameter_block_rejects_mismatched_column_count():
    with pytest.raises(ValueError, match="column count"):
        ParameterBlock(name="lambda", start=0, stop=2, link="log", columns=("Intercept",))


def test_model_spec_process_names_and_block_lookup():
    lambda_process = ProcessSpec(name="lambda", formula="~ forest", link="log", level="site")
    p_process = ProcessSpec(name="p", formula="~ visit", link="logit", level="observation")
    lambda_block = ParameterBlock(name="lambda", start=0, stop=2, link="log", process="lambda")
    p_block = ParameterBlock(name="p", start=2, stop=3, link="logit", process="p")
    spec = ModelSpec(
        model="pcount",
        processes={"lambda": lambda_process, "p": p_process},
        parameter_blocks=(lambda_block, p_block),
        response="count",
    )
    assert spec.process_names == ("lambda", "p")
    assert spec.process("lambda") is lambda_process
    assert spec.block("p") is p_block


def test_model_spec_missing_block_raises_key_error():
    spec = ModelSpec(
        model="pcount",
        processes={"lambda": ProcessSpec(name="lambda", formula=None, link="log", level="site")},
    )
    with pytest.raises(KeyError):
        spec.block("missing")


def test_model_frame_response_shape_and_n_sites():
    y = np.asarray([[1.0, 2.0], [0.0, 1.0]], dtype=np.float64)
    frame = ModelFrame(y=y, metadata={"model": "test"})
    assert frame.response_shape == (2, 2)
    assert frame.n_sites == 2
    assert frame.site_data is None
    assert frame.obs_data is None
    assert frame.metadata["model"] == "test"


def test_model_frame_allows_optional_data_frames():
    y = np.asarray([[1.0]], dtype=np.float64)
    site_data = pd.DataFrame({"forest": [0.4]})
    obs_data = pd.DataFrame({"visit": ["v1"]})
    frame = ModelFrame(y=y, site_data=site_data, obs_data=obs_data, site_ids=("s1",))
    assert frame.site_data is site_data
    assert frame.obs_data is obs_data
    assert frame.site_ids == ("s1",)
