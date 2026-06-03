import json
from pathlib import Path


def test_r_parity_output_if_present_is_well_formed():
    path = Path("reports/r_benchmark.json")
    if not path.exists():
        return
    data = json.loads(path.read_text())
    assert "status" in data
