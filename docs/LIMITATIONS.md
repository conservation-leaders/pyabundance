# Current Limitations

pyabundance is an alpha-stage clean-room ecological abundance modelling library.

Current limitations:

- only single-season pcount-style N-mixture models are implemented;
- supported mixtures are Poisson, negative-binomial, and zero-inflated Poisson;
- no open/dynamic N-mixture models yet;
- no distance-sampling models yet;
- no spatial models yet;
- no random effects yet;
- formulas build fixed-effect design matrices only;
- asymptotic standard errors can be unreliable with weak data or poorly identified models;
- empirical-Bayes posterior abundance outputs condition on fitted parameters and do not include full parameter uncertainty;
- local synthetic benchmarks are not general performance claims;
- R/unmarked comparisons are black-box validation targets only.

Users should inspect convergence, diagnostics, uncertainty warnings, and sensitivity to `K` before relying on a model for applied decisions.
