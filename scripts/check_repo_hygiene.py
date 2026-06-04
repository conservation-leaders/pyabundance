from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ALLOWED_REPORTS = {"reports/README.md"}
GENERATED_PREFIXES = (
    "benchmark_artifacts/",
    "data/benchmark/",
    "dist/",
    "target/",
    ".venv/",
    ".venv",
    "htmlcov/",
)
GENERATED_EXACT = {
    "coverage.xml",
    ".coverage",
}
GENERATED_REPORT_SUFFIXES = (".json", ".md", ".txt", ".xml")


def tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("git ls-files failed; run this check inside a git checkout") from exc
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def generated_tracked(files: list[str]) -> list[str]:
    bad: list[str] = []
    for path in files:
        if path in GENERATED_EXACT:
            bad.append(path)
            continue
        if any(path.startswith(prefix) for prefix in GENERATED_PREFIXES):
            bad.append(path)
            continue
        if path.startswith("reports/") and path not in ALLOWED_REPORTS:
            if Path(path).suffix in GENERATED_REPORT_SUFFIXES:
                bad.append(path)
    return sorted(bad)


def main() -> int:
    try:
        bad = generated_tracked(tracked_files())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if bad:
        print("Generated artifacts are tracked by git:", file=sys.stderr)
        for path in bad:
            print(f"- {path}", file=sys.stderr)
        print("\nUntrack generated artifacts or move curated content into docs/.", file=sys.stderr)
        return 1
    print("Repository hygiene check passed: no generated artifacts tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
