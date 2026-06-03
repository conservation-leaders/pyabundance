from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ARTIFACTS = ROOT / "benchmark_artifacts"
STATUS_RE = re.compile(r"^Status:\s*(.+)$", re.MULTILINE)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _status(path: Path) -> str | None:
    if path.suffix.lower() != ".md":
        return None
    match = STATUS_RE.search(path.read_text(errors="replace"))
    return match.group(1).strip() if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Preserve benchmark reports for a release.")
    parser.add_argument("--version", required=True, help="Release version, e.g. 1.0.0rc1")
    args = parser.parse_args()
    out = ARTIFACTS / f"v{args.version}"
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for pattern in ["*.md", "*.json", "*.txt", "*.xml"]:
        for src in REPORTS.glob(pattern):
            dst = out / src.name
            shutil.copy2(src, dst)
            files.append(
                {
                    "name": src.name,
                    "sha256": _sha256(dst),
                    "bytes": dst.stat().st_size,
                    "status": _status(dst),
                }
            )
    manifest = {
        "version": args.version,
        "created_at": datetime.now(UTC).isoformat(),
        "files": sorted(files, key=lambda item: item["name"]),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Preserved {len(files)} benchmark/report artifacts in {out}")


if __name__ == "__main__":
    main()
