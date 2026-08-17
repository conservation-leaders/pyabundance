# Triage labels

The skills use five canonical triage roles. This table maps each role to the GitHub label name
for this repository.

| Label in `mattpocock/skills` | Label in this repository | Meaning                                  |
| ---------------------------- | ------------------------ | ---------------------------------------- |
| `needs-triage`               | `needs-triage`           | Maintainer needs to evaluate this issue  |
| `needs-info`                 | `needs-info`             | Waiting on reporter for more information |
| `ready-for-agent`            | `ready-for-agent`        | Fully specified, ready for an AFK agent  |
| `ready-for-human`            | `ready-for-human`        | Requires human implementation            |
| `wontfix`                    | `wontfix`                | Will not be actioned                     |

When a skill mentions a role, use the corresponding label in the right-hand column.

The mapping assumes those labels already exist in GitHub. `/triage` does not create labels; if
a mapped label is missing, stop and have a maintainer create it instead of substituting a
different label.
