Benchmark Results
Status: COMPLETED
Dataset:
	•	n_sites: 500
	•	n_visits: 3
	•	K: 60
	•	repetitions: 3
Correctness:
	•	Python logLik: -1351.31
	•	R unmarked logLik: -1351.31
	•	absolute logLik difference: 1.59162e-09
	•	max coefficient absolute difference: 4.12509e-06
	•	parity status: close
Performance:
	•	Python full fit median time: 0.0611265
	•	R full fit median time: 0.519
	•	speed ratio R/Python: 8.4906
	•	Python optimizer method: BFGS
	•	Python function evaluations: 96
	•	Python optimizer iterations: 12
	•	Python optimizer message: Optimization terminated successfully.
	•	Python direct likelihood median time: 0.619812 ms (619.812 µs)
Environment:
	•	OS: macOS-26.5.1-arm64-arm-64bit-Mach-O
	•	CPU if available: arm
	•	Python: 3.14.5 (main, May 10 2026, 10:21:34) [Clang 21.0.0 (clang-2100.0.123.102)]
	•	Rust: rustc 1.83.0 (90b35a623 2024-11-26)
	•	R: R version 4.6.0 (2026-04-24)
	•	unmarked: 1.5.1
Notes:
	•	This is a simple end-to-end fit benchmark, not a comprehensive benchmark.
	•	Optimizer implementations and convergence paths may differ.
	•	Bottleneck appears dominated by optimizer likelihood calls: nfev × direct likelihood median ≈ 0.0595s (97.3% of median fit time).
