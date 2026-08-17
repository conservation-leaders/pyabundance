from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LINEAR_PROJECT_URL = (
    "https://linear.app/conservation-leaders/project/"
    "project-goanna-map-visualisation-and-pyabundance-e7ea0b817b0b"
)
CANONICAL_LABELS = {
    "needs-triage",
    "needs-info",
    "ready-for-agent",
    "ready-for-human",
    "wontfix",
    "wayfinder:map",
    "wayfinder:research",
    "wayfinder:prototype",
    "wayfinder:grilling",
    "wayfinder:task",
}


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_agents_points_to_linear_as_the_authoritative_tracker() -> None:
    agents = read("AGENTS.md")

    assert "tracked in Linear" in agents
    assert "Engineering (`ENG`)" in agents
    assert "GitHub Issues for `conservation-leaders/pyabundance`" not in agents
    assert "Planning and tracker-only sessions use" in agents


def test_tracker_guide_pins_the_linear_destination_and_map() -> None:
    tracker = read("docs/agents/issue-tracker.md")

    assert "# Issue tracker: Linear" in tracker
    assert "Engineering (`ENG`)" in tracker
    assert "Project Goanna - Map Visualisation and pyabundance" in tracker
    assert LINEAR_PROJECT_URL in tracker
    assert "`ENG-18`" in tracker
    assert "Do not fall back to GitHub Issues" in tracker
    assert "`get_issue` with relations" in tracker
    assert "`save_issue`" in tracker
    assert "`parentId`" in tracker
    assert "`blockedBy`" in tracker
    assert "`createdAt` ascending" in tracker
    assert "assign it to `me`" in tracker
    assert "leave `delegate` unset" in tracker
    assert "`feat/eng-42-short-description`" in tracker
    assert "`feature/eng-42" not in tracker


def test_linear_label_vocabulary_is_complete() -> None:
    label_guide = read("docs/agents/triage-labels.md")

    for label in CANONICAL_LABELS:
        assert f"`{label}`" in label_guide
    assert "exist on the Linear Engineering team" in label_guide
    assert "completely specified AFK research" in label_guide


def test_github_issue_creation_redirects_to_linear() -> None:
    template_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
    files = {path.name for path in template_dir.iterdir() if path.is_file()}

    assert files == {"config.yml"}
    config = yaml.safe_load(read(".github/ISSUE_TEMPLATE/config.yml"))
    assert config["blank_issues_enabled"] is False
    assert any(link["url"] == LINEAR_PROJECT_URL for link in config["contact_links"])


def test_pull_request_template_uses_linear_ticket_identity() -> None:
    template = read(".github/pull_request_template.md")

    assert "Linear issue (`ENG-…`)" in template
    assert "Closes #" not in template


def test_package_and_spec_metadata_use_linear_identity() -> None:
    package = read("pyproject.toml")
    specification = read("specs/TEMPLATE.md")

    assert f'Issues = "{LINEAR_PROJECT_URL}"' in package
    assert "github.com/conservation-leaders/pyabundance/issues" not in package
    assert "Governing Linear issue (`ENG-…`)" in specification
