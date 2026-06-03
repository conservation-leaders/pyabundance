# Numerical Stability

- Detection probabilities use a branch-stable inverse-logit.
- Site likelihoods are evaluated in log space.
- Latent abundance summation uses log-sum-exp.
- Binomial probabilities are clamped to `[1e-15, 1 - 1e-15]` before taking logs.
- v0.1 prioritizes correctness and clear validation over aggressive optimization.
