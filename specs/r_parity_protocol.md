# R Parity Protocol

R `unmarked::pcount` is used only as a black-box behavioural/statistical reference.

Allowed:

- Run R fits on generated data.
- Compare log-likelihoods, coefficients, convergence messages, and runtime.
- Record package versions and platform metadata.

Not allowed:

- Opening, copying, translating, or paraphrasing GPL R/C++/TMB/Stan source code.
- Treating benchmark results as proof of general performance superiority.

The default CI does not require R or `unmarked`; parity benchmarking is optional/manual.
