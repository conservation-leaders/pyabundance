from __future__ import annotations

import runpy


def test_guided_workflow_tutorial_runs():
    runpy.run_path("docs/tutorials/guided_pcount_analysis.py", run_name="__main__")
