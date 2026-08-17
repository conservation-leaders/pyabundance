# Issue tracker: Linear

Linear is the authoritative tracker for issues, specifications, and Wayfinder maps. GitHub hosts
source, pull requests, releases, and CI; do not duplicate project work in GitHub Issues.

## Destination

- Workspace: `conservation-leaders`
- Team: Engineering (`ENG`), ID `c7385d78-5319-49da-acab-2a8b9b7361ce`
- Project: [Project Goanna - Map Visualisation and pyabundance](https://linear.app/conservation-leaders/project/project-goanna-map-visualisation-and-pyabundance-e7ea0b817b0b)
- Project ID: `a8785575-89c3-450b-b8c3-4c7eb16e93f5`
- Current unmarked realignment map:
  [Decide the behavior-complete clean-room unmarked compatibility surface](https://linear.app/conservation-leaders/issue/ENG-18/decide-the-behavior-complete-clean-room-unmarked-compatibility-surface)

Use the connected Linear tools. If Linear is unavailable or authentication fails, stop and ask the
user to connect it. Do not fall back to GitHub Issues, local Markdown tickets, or a second Linear
project.

Use `get_issue` with relations and `list_comments` for a complete read. Use `list_issues` for
structured project queries, `save_issue` for issue writes, and `save_comment` for discussion or
resolution records. Always scope label discovery to the Engineering team: team labels may be
absent from an unscoped label listing.

## Read before write

Resolve the team, project, issue, status, labels, assignee, delegate, and blocking relations before
mutating tracker state. For a Wayfinder claim, load only the map and enough child metadata to
establish the frontier, then claim before reading the selected child's full body or doing work. For
other mutations, read the full issue and comments first. Search the project for an existing
semantic match before creating an issue.

When creating or updating work:

- use the Engineering team and the project above;
- keep new unclaimed work in `Backlog`, with no assignee, priority, cycle, estimate, or due date
  unless the governing workflow supplies one;
- treat an issue label update as replacement of the complete label set;
- use Linear comments for discussion and resolution records;
- use `Done` for resolved work, `Canceled` for work explicitly ruled out, and `Duplicate` only with
  a canonical replacement;
- refer to issues as linked names in human-facing prose, retaining the `ENG-…` identifier inside
  the link.

Linear relation additions are append-only. Use `removeBlockedBy` or `removeBlocks` to remove an
edge, and use one `blockedBy` orientation consistently when constructing a graph. If a blocker is
canceled or marked duplicate, reconcile its outgoing edges before treating downstream work as
frontier.

## Pull requests

Pull requests remain on GitHub and are not a triage surface. Every implementation PR links its
Linear issue and its specification or ADR. GitHub review state and CI do not replace Linear issue
state; update the Linear issue when implementation starts, enters review, or is completed.

A bare `ENG-42` means a Linear issue. A bare `#42` means a GitHub pull request only; never infer a
Linear identifier from a GitHub number.

Linear's generated `gitBranchName` may violate the repository branch policy. Treat it as a title
hint only. When a governing ticket is known, use its real lowercase identifier; for example, this
migration could use `chore/eng-40-configure-linear-tracker`. Otherwise omit the identifier. Validate
the final branch name and start it from the default branch as required by `AGENTS.md`.

## Skill operations

- **Publish to the issue tracker**: create a Linear issue on Engineering in the configured project.
- **Fetch a ticket**: read the issue, comments, parent, labels, and blocking relations.
- **Claim a ticket**: as the session's first write, assign it to `me`; move it to `In Progress` in
  the same write or immediately afterward. Either an assignee or delegate makes an issue claimed;
  leave `delegate` unset unless the user explicitly delegates to Linear's own agent.
- **Hand off for review**: move an implemented ticket to `In Review` and link the GitHub PR.
- **Resolve a ticket**: record the outcome in a comment, move it to `Done`, and update its parent
  artifact when the workflow requires it.

## Wayfinding operations

`/wayfinder` stores one Linear map issue and its decision/evidence tickets as child issues.

- **Map**: use one issue labelled `wayfinder:map`, with Destination, Notes, Decisions so far, Not
  yet specified, and Out of scope in its description. The current realignment map is
  [Decide the behavior-complete clean-room unmarked compatibility surface](https://linear.app/conservation-leaders/issue/ENG-18/decide-the-behavior-complete-clean-room-unmarked-compatibility-surface).
- **Child ticket**: create the issue in the same team and project with the map as `parentId`. Apply
  exactly one `wayfinder:<type>` label. Unresolved grilling tickets also carry `ready-for-human`;
  completely specified AFK research and evidence tasks also carry `ready-for-agent`. Native
  blockers, not the readiness label, determine when an AFK ticket is takeable.
- **Blocking**: create every child first, then add native `blockedBy` relations in a second pass.
  Do not encode a second dependency graph in issue descriptions.
- **Frontier**: list the map's open children and sort by `createdAt` ascending, using the numeric
  identifier as a deterministic tie-breaker. Discard assigned or delegated children and those with
  any non-terminal blocker. The remaining unclaimed children are the frontier. Preserve an
  explicit map order only when the map description deliberately overrides creation order; do not
  trust connector return order.
- **Claim**: assign one frontier ticket to `me` before reading beyond the map and selected ticket.
- **Resolve**: post the answer as a resolution comment, move the child to `Done`, then append a
  linked one-line gist to the map's Decisions so far section.
- **Rule out**: move a ticket beyond the destination to `Canceled`, and add a linked explanation to
  the map's Out of scope section rather than Decisions so far.

Charting stops after the approved map, children, and dependency graph are verified. Research may
run from approved research tickets; other frontier tickets are resolved one per fresh session.

## Triage conventions

Incoming bugs use Linear's `Bug` category label; incoming enhancements use `Improvement`. `Feature`
is available as an additional product category but is not the canonical `/triage` enhancement
mapping. Category labels coexist with exactly one applicable Matt state label from
`docs/agents/triage-labels.md`.
