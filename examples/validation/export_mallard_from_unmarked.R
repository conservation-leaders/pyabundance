# Export unmarked::mallard locally for black-box validation.
# Outputs are intentionally written to data/mallard/, which is git ignored.
dir.create("data/mallard", recursive = TRUE, showWarnings = FALSE)
if (!requireNamespace("unmarked", quietly = TRUE)) {
  stop("Install R package 'unmarked' to export mallard data")
}
data("mallard", package = "unmarked")
# The exact object structure can vary by unmarked version; keep this script explicit/manual.
print(mallard)
message("Inspect the object above and export local CSVs appropriate for the validation scripts.")
