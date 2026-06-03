from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Check built distribution metadata.")
    parser.add_argument("dist", nargs="?", default="dist")
    args = parser.parse_args()
    dist = Path(args.dist)
    if not dist.exists():
        raise SystemExit(f"dist directory does not exist: {dist}")
    artifacts = sorted(
        [p for p in dist.iterdir() if p.suffix in {".whl", ".gz"} or p.name.endswith(".tar.gz")]
    )
    if not artifacts:
        raise SystemExit(f"no wheel/sdist artifacts found in {dist}")
    subprocess.run([sys.executable, "-m", "twine", "check", *map(str, artifacts)], check=True)
    import pyabundance

    expected = pyabundance.__version__
    print("Distribution artifacts:")
    for artifact in artifacts:
        print(f"- {artifact.name}")
        expected_fragment = f"pyabundance-{expected}"
        if expected_fragment not in artifact.name:
            raise AssertionError(
                f"{artifact.name} does not contain expected version fragment {expected_fragment}"
            )
    print(f"dist metadata check passed for pyabundance {expected}")


if __name__ == "__main__":
    main()
