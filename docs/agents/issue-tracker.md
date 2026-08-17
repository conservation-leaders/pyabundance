# Issue tracker: GitHub

Issues and specs for this repository live as GitHub issues in
`conservation-leaders/pyabundance`. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for
  multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also
  fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`.
- **Apply or remove labels**: `gh issue edit <number> --add-label "..."` or
  `--remove-label "..."`.
- **Close an issue**: `gh issue close <number> --comment "..."`.

The `origin` remote identifies the repository, so `gh` resolves it automatically from this
checkout.

## Pull requests as a triage surface

**PRs as a request surface: no.** Set this to `yes` if external pull requests should enter the
same triage queue as issues.

When set to `yes`, use the corresponding `gh pr` commands:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>`.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`, keeping only `authorAssociation` values `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE`.
- **Comment, label, or close**: use `gh pr comment`, `gh pr edit --add-label` or
  `--remove-label`, and `gh pr close`.

GitHub shares one number space across issues and PRs. Resolve a bare `#42` with
`gh pr view 42`, falling back to `gh issue view 42`.

## Skill operations

- **Publish to the issue tracker**: create a GitHub issue.
- **Fetch the relevant ticket**: run `gh issue view <number> --comments`.

## Wayfinding operations

`/wayfinder` stores a map as one GitHub issue and each child ticket as a linked issue.

- **Map**: create one issue labelled `wayfinder:map`, with Notes, Decisions-so-far, and Fog in
  its body.
- **Child ticket**: link an issue to the map as a GitHub sub-issue. If sub-issues are disabled,
  add it to a task list in the map and put `Part of #<map>` at the top of the child body. Label
  it `wayfinder:<type>`, where type is `research`, `prototype`, `grilling`, or `task`.
- **Blocking**: use GitHub's native issue dependencies. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where the database ID comes from `gh api repos/<owner>/<repo>/issues/<n> --jq .id`. If native dependencies are unavailable, use a `Blocked by: #<n>, #<n>` line at the top of the body.
- **Frontier**: inspect the map's open children, discard assigned tickets and tickets with open
  blockers, and take the first remaining ticket in map order.
- **Claim**: run `gh issue edit <n> --add-assignee @me` as the session's first write.
- **Resolve**: comment with the answer, close the child, then append a concise decision pointer
  and link to the map's Decisions-so-far section.
