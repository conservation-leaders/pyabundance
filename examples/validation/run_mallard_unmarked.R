# Run R unmarked Mallard fits as a black-box comparison target.
dir.create("results/mallard", recursive = TRUE, showWarnings = FALSE)
if (!requireNamespace("unmarked", quietly = TRUE)) {
  stop("Install R package 'unmarked' to run Mallard validation")
}
message("Fit pcount models with unmarked here and write results/mallard/unmarked_results.csv")
