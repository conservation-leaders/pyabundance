from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install an sdist into a temporary venv and smoke-test it."
    )
    parser.add_argument("path", nargs="?", default="dist", help="sdist file or dist directory")
    args = parser.parse_args()
    path = Path(args.path)
    if path.is_dir():
        sdists = sorted(path.glob("*.tar.gz"))
        if not sdists:
            raise SystemExit(f"no .tar.gz sdist files found in {path}")
        sdist = sdists[0]
    else:
        sdist = path
    with tempfile.TemporaryDirectory(prefix="pyabundance-sdist-") as tmp:
        venv = Path(tmp) / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(python), "-m", "pip", "install", str(sdist)], check=True)
        code = """
from pyabundance import __version__, load_example_pcount, pcount_df
print('pyabundance', __version__)
data = load_example_pcount('poisson', n_sites=10, seed=20260611)
fit = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula=data.detection_formula,
    K=data.K,
)
assert fit.success
assert fit.posterior_abundance().shape == (10, data.K + 1)
print('sdist smoke test passed')
"""
        subprocess.run([str(python), "-c", code], check=True)


if __name__ == "__main__":
    main()
