from __future__ import annotations

import pandas as pd
from pyabundance import load_example_pcount, pcount


def test_coef_table_as_dataframe_options_and_extra_parameters():
    data = load_example_pcount("negative_binomial", n_sites=30)
    nb = pcount(data.y, data.X, data.W, K="auto", mixture="negative_binomial", se=True)
    table = nb.coef_table(as_dataframe=True)
    assert isinstance(table, pd.DataFrame)
    assert "log_r" in set(table["parameter"])
    records = nb.coef_table(as_dataframe=False)
    assert isinstance(records, list)
    assert any(row["parameter"] == "log_r" for row in records)
    assert "std.error" in table.columns

    zip_fit = pcount(data.y, data.X, data.W, K="auto", mixture="zip")
    assert "logit_psi" in set(zip_fit.coef_table()["parameter"])
