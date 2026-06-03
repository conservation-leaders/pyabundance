# Alpha Release Checklist

Status: READY FOR EXTERNAL ALPHA REVIEW

- [x] version bumped to 0.9.0
- [x] tests pass
- [x] coverage >= 80
- [x] docs build
- [x] wheels build locally
- [x] wheel smoke tests pass locally
- [x] TestPyPI workflow present
- [x] TestPyPI publish attempted or clearly marked not run
- [x] TestPyPI install workflow present
- [x] external alpha guide exists
- [x] issue templates exist
- [x] PR template exists
- [x] R parity refreshed or marked partial
- [x] benchmark artifacts preserved
- [x] API freeze review done
- [x] no R/GPL source copied
- [x] performance claims conservative

Notes:
- Live TestPyPI publish was not attempted locally; it requires GitHub Actions Trusted Publishing configuration.
- Cross-platform wheels are configured in CI; only the local macOS arm64 wheel was built and smoke-tested locally.
- v0.9 did not add a new ecological model family.
