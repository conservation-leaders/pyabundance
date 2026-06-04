from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ALLOWED_REPORTS = {"reports/README.md"}
GENERATED_PREFIXES = (
    ".omx/",
    "benchmark_artifacts/",
    "data/benchmark/",
    "dist/",
    "target/",
    ".venv/",
    ".venv",
    "htmlcov/",
    "site/",
)
GENERATED_EXACT = {
    "coverage.xml",
    ".coverage",
}
GENERATED_REPORT_SUFFIXES = (".json", ".md", ".txt", ".xml")


def normalize_tracked_path(path: str) -> str:
    """Return a git-style relative path for hygiene checks."""
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_forbidden_tracked_path(path: str) -> bool:
    """Return True when a tracked path is generated/local state."""
    normalized = normalize_tracked_path(path)
    if normalized in GENERATED_EXACT:
        return True
    if any(normalized.startswith(prefix) for prefix in GENERATED_PREFIXES):
        return True
    if normalized.startswith("reports/") and normalized not in ALLOWED_REPORTS:
        return Path(normalized).suffix in GENERATED_REPORT_SUFFIXES
    return False


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
    return sorted(normalize_tracked_path(path) for path in files if is_forbidden_tracked_path(path))


def main() -> int:
    try:
        bad = generated_tracked(tracked_files())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if bad:
        print("Generated or local runtime artifacts are tracked by git:", file=sys.stderr)
        for path in bad:
            print(f"- {path}", file=sys.stderr)
        print("\nUntrack generated artifacts or move curated content into docs/.", file=sys.stderr)
        return 1
    print("Repository hygiene check passed: no generated artifacts tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
