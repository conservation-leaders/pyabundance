import numpy as np
import pandas as pd
from pyabundance import build_pcount_matrices


def test_build_formula_matrices_basic_visit_design():
    df = pd.DataFrame(
        {
            "y1": [0, 1, 2],
            "y2": [1, np.nan, 2],
            "y3": [0, 2, 3],
            "x": [-1.0, 0.0, 1.0],
        }
    )
    matrices = build_pcount_matrices(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ visit - 1",
    )
    assert matrices.y.shape == (3, 3)
    assert matrices.X.shape == (3, 2)
    assert matrices.W.shape == (3, 3, 3)
    assert matrices.abundance_column_names == ["Intercept", "x"]
    assert matrices.detection_column_names == ["visit[y1]", "visit[y2]", "visit[y3]"]
    assert matrices.visit_labels == ["y1", "y2", "y3"]
    np.testing.assert_allclose(matrices.W[0], np.eye(3))
