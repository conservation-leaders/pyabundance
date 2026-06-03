args0 <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args0[grep("^--file=", args0)])
script_dir <- if (length(file_arg) > 0) dirname(normalizePath(file_arg)) else getwd()
root <- normalizePath(file.path(script_dir, ".."), mustWork = TRUE)
reports <- file.path(root, "reports")
data_dir <- file.path(root, "data", "benchmark")
dir.create(reports, showWarnings = FALSE, recursive = TRUE)

json_escape <- function(x) {
  x <- gsub('\\\\', '\\\\\\\\', x)
  x <- gsub('"', '\\"', x)
  x <- gsub('\n', ' ', x)
  x
}
json_vec <- function(v) paste0("[", paste(format(v, digits = 17), collapse = ", "), "]")

write_payload <- function(status, message, extra = "") {
  payload <- paste0(
    '{\n',
    '  "status": "', status, '",\n',
    '  "message": "', json_escape(as.character(message)), '",\n',
    extra,
    '  "R_version": "', json_escape(R.version.string), '",\n',
    '  "platform": "', json_escape(R.version$platform), '"\n',
    '}\n'
  )
  writeLines(payload, file.path(reports, "r_ranef_comparison.json"))
}

if (!requireNamespace("unmarked", quietly = TRUE)) {
  install_result <- tryCatch({
    install.packages("unmarked", repos = "https://cloud.r-project.org")
    TRUE
  }, error = function(e) e)
  if (inherits(install_result, "error") || !requireNamespace("unmarked", quietly = TRUE)) {
    write_payload("not_run", paste("unmarked is not installed and installation failed:", install_result))
    quit(status = 0)
  }
}

result <- tryCatch({
  library(unmarked)
  counts <- read.csv(file.path(data_dir, "pcount_counts.csv"))
  covs <- read.csv(file.path(data_dir, "pcount_site_covs.csv"))
  y <- as.matrix(counts[, c("y1", "y2", "y3")])
  n_sites <- nrow(y)
  siteCovs <- data.frame(x = covs$x)
  obsCovs <- data.frame(
    visit = factor(rep(c("v1", "v2", "v3"), times = n_sites), levels = c("v1", "v2", "v3"))
  )
  umf <- unmarkedFramePCount(y = y, siteCovs = siteCovs, obsCovs = obsCovs)
  fit <- pcount(~ visit - 1 ~ x, data = umf, K = 60, starts = rep(0, 5), mixture = "P", se = FALSE, engine = "C", threads = 1, method = "BFGS")
  re <- ranef(fit)
  means <- tryCatch({ as.numeric(bup(re, stat = "mean")) }, error = function(e) e)
  modes <- tryCatch({ as.numeric(bup(re, stat = "mode")) }, error = function(e) e)
  if (inherits(means, "error")) {
    extra <- paste0(
      '  "logLik": ', format(as.numeric(logLik(fit)), digits = 17), ',\n',
      '  "unmarked_version": "', as.character(utils::packageVersion("unmarked")), '",\n',
      '  "dataset": {"n_sites": ', nrow(y), ', "n_visits": ', ncol(y), ', "K": 60},\n'
    )
    write_payload("partial", paste("ranef mean extraction failed:", conditionMessage(means)), extra)
  } else {
    if (inherits(modes, "error")) modes <- rep(NA_real_, length(means))
    payload <- paste0(
      '{\n',
      '  "status": "completed",\n',
      '  "logLik": ', format(as.numeric(logLik(fit)), digits = 17), ',\n',
      '  "posterior_means": ', json_vec(means), ',\n',
      '  "posterior_modes": ', json_vec(modes), ',\n',
      '  "R_version": "', json_escape(R.version.string), '",\n',
      '  "unmarked_version": "', as.character(utils::packageVersion("unmarked")), '",\n',
      '  "platform": "', json_escape(R.version$platform), '",\n',
      '  "dataset": {"n_sites": ', nrow(y), ', "n_visits": ', ncol(y), ', "K": 60}\n',
      '}\n'
    )
    writeLines(payload, file.path(reports, "r_ranef_comparison.json"))
  }
  TRUE
}, error = function(e) e)

if (inherits(result, "error")) {
  write_payload("not_run", conditionMessage(result))
}
