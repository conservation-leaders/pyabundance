# Triage labels

The skills use five canonical triage roles. The names below exist on the Linear Engineering team
and are the repository mapping.

| Label in `mattpocock/skills` | Label in this repository | Meaning                                  |
| ---------------------------- | ------------------------ | ---------------------------------------- |
| `needs-triage`               | `needs-triage`           | Maintainer needs to evaluate this issue  |
| `needs-info`                 | `needs-info`             | Waiting on reporter for more information |
| `ready-for-agent`            | `ready-for-agent`        | Fully specified, ready for an AFK agent  |
| `ready-for-human`            | `ready-for-human`        | Requires human implementation            |
| `wontfix`                    | `wontfix`                | Will not be actioned                     |

When a skill mentions a role, use the corresponding label in the right-hand column.

Linear workflow statuses and category labels such as `Bug`, `Feature`, and `Improvement` do not
replace these triage roles. `/triage` does not create labels; if a mapped label is missing, stop and
have a maintainer restore the exact name instead of substituting a different label.

## Wayfinder work types

Wayfinder issues use one additional label describing their role:

| Label | Use |
| --- | --- |
| `wayfinder:map` | Parent destination and decision log |
| `wayfinder:research` | Public-source evidence gathering |
| `wayfinder:prototype` | Disposable interaction or state exploration |
| `wayfinder:grilling` | Human decision and stress test |
| `wayfinder:task` | Bounded retained investigation or setup work |

Use exactly one Wayfinder type on each map/child issue. An unresolved `wayfinder:grilling` child
also carries `ready-for-human`. A completely specified AFK research or retained-evidence child
carries `ready-for-agent`; its native blockers still determine whether it is on the frontier.
Implementation tickets use `ready-for-agent` only when they satisfy the delivery playbook's
ready-ticket contract. Read `docs/agents/unmarked-delivery.md` before using these labels for the
realignment program.
