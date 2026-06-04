from __future__ import annotations

import pyabundance
from pyabundance import compare_models, load_example_pcount, pcount, pcount_df


def test_power_user_matrix_and_dataframe_apis_still_work():
    data = load_example_pcount("poisson", n_sites=20)
    matrix_fit = pcount(data.y, data.X, data.W, K=data.K)
    df_fit = pcount_df(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        visit_labels=["v1", "v2", "v3"],
        K=data.K,
    )
    assert matrix_fit.success
    assert df_fit.success
    comparison = compare_models({"matrix": matrix_fit, "dataframe": df_fit})
    assert comparison.best_model_name in {"matrix", "dataframe"}
    assert matrix_fit.coef_table().shape[0] == matrix_fit.params.size
    assert "_core" not in pyabundance.__all__
