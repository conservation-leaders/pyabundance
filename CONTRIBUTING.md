# Contributing

Contributions must be original work or compatible with Apache-2.0. Do not copy, translate,
or paraphrase GPL R/C++/TMB/Stan source code. R package outputs may be used only as black-box
validation targets.

Project issues and specifications are tracked in the
[pyabundance Linear project](https://linear.app/conservation-leaders/project/project-goanna-map-visualisation-and-pyabundance-e7ea0b817b0b).
GitHub is used for pull requests and CI rather than duplicate issue tracking.

Before submitting changes, run:

```bash
python scripts/check_all.py
```

Install the `dev` and `docs` extras first. The command rebuilds the editable native extension,
then runs the complete Rust, Python, typing, stub-parity, documentation, coverage, and repository
policy gate used by CI.
