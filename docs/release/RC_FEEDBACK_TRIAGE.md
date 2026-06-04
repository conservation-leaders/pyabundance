# RC feedback triage

## Fix before v1.0 final

- install failures;
- wheel/TestPyPI failures;
- crashes in documented workflows;
- incorrect likelihood/logLik/parameter results;
- misleading statistical output;
- broken docs that block quickstart;
- public API inconsistency;
- clean-room/legal concern.

## Defer after v1.0 final

- open/dynamic N-mixture;
- distance sampling;
- spatial models;
- random effects;
- full Bayesian posterior parameter uncertainty;
- large API redesigns;
- major performance work not tied to correctness;
- new plotting system.

## Requirements for fixes

- every blocker fix needs a test;
- rerun CI;
- rerun wheel matrix if packaging is affected;
- rerun R parity if model code is affected;
- preserve clean-room policy;
- do not broaden performance claims.
