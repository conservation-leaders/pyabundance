# Clean-room Policy

pyabundance is an Apache-2.0 clean-room implementation.

Rules:

- Do not copy R source code from `unmarked` or other GPL packages.
- Do not translate GPL R, C++, TMB, Stan, or other source code into Rust or Python.
- Use independent mathematical specifications, public documentation, published equations, and original implementation work.
- R and `unmarked` may be used only as black-box validation targets through fitted outputs, likelihood values, and benchmark timings.
- Contributors must certify that submitted code is original work or is compatible with Apache-2.0.
- If a contributor has inspected incompatible source for a feature, they should not implement that feature here without a separate clean-room specification written by someone else.
