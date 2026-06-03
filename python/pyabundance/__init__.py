"""Clean-room ecological abundance models with a Rust numerical core."""

from pyabundance.pcount import pcount
from pyabundance.result import PCountResult
from pyabundance.simulate import simulate_pcount

try:
    from pyabundance._core import __version__ as _rust_version
except Exception:  # pragma: no cover - extension may be absent before build
    _rust_version = "unknown"

__all__ = ["PCountResult", "pcount", "simulate_pcount"]
__version__ = "0.1.0"
__rust_version__ = _rust_version
