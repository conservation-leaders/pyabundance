"""Clean-room ecological abundance models with a Rust numerical core."""

from pyabundance.bootstrap import BootstrapResult, parametric_bootstrap
from pyabundance.datasets import ExamplePCountData, list_example_datasets, load_example_pcount
from pyabundance.formula import PCountMatrices, build_pcount_matrices, pcount_df
from pyabundance.model_selection import ModelComparison, aic_table, compare_models
from pyabundance.pcount import pcount
from pyabundance.ranef import TotalAbundancePosterior
from pyabundance.reporting import export_model_report, model_report, report_markdown
from pyabundance.result import PCountResult
from pyabundance.simulate import simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip

try:
    from pyabundance._core import __version__ as _rust_version
except Exception:  # pragma: no cover - extension may be absent before build
    _rust_version = "unknown"

__all__ = [
    "BootstrapResult",
    "ExamplePCountData",
    "ModelComparison",
    "PCountMatrices",
    "PCountResult",
    "TotalAbundancePosterior",
    "aic_table",
    "build_pcount_matrices",
    "compare_models",
    "export_model_report",
    "list_example_datasets",
    "load_example_pcount",
    "model_report",
    "parametric_bootstrap",
    "pcount",
    "pcount_df",
    "report_markdown",
    "simulate_pcount",
    "simulate_pcount_negbin",
    "simulate_pcount_zip",
]
__version__ = "1.0.0rc1"
__rust_version__ = _rust_version
