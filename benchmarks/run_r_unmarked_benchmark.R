args0 <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args0[grep("^--file=", args0)])
script_dir <- if (length(file_arg) > 0) dirname(normalizePath(file_arg)) else getwd()
root <- normalizePath(file.path(script_dir, ".."), mustWork = TRUE)
reports <- file.path(root, "reports")
data_dir <- file.path(root, "data", "benchmark")
dir.create(reports, showWarnings = FALSE, recursive = TRUE)

json_escape <- function(x) {
  x <- gsub('\\\\', '\\\\\\\\', x)
  x <- gsub('"', '\\\\"', x)
  x <- gsub('\n', ' ', x)
  x
}

json_vec <- function(v) paste0("[", paste(format(v, digits = 17), collapse = ", "), "]")

write_not_run <- function(message) {
  payload <- paste0(
    '{\n',
    '  "status": "not_run",\n',
    '  "message": "', json_escape(as.character(message)), '",\n',
    '  "R_version": "', json_escape(R.version.string), '",\n',
    '  "platform": "', json_escape(R.version$platform), '"\n',
    '}\n'
  )
  writeLines(payload, file.path(reports, "r_benchmark.json"))
}

if (Sys.which("R") == "") {
  write_not_run("R executable was not found")
  quit(status = 0)
}

if (!requireNamespace("unmarked", quietly = TRUE)) {
  install_result <- tryCatch({
    install.packages("unmarked", repos = "https://cloud.r-project.org")
    TRUE
  }, error = function(e) e)
  if (inherits(install_result, "error") || !requireNamespace("unmarked", quietly = TRUE)) {
    write_not_run(paste("unmarked is not installed and installation failed:", install_result))
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
  seconds <- c()
  fits <- list()
  for (i in 1:3) {
    elapsed <- system.time({
      fits[[i]] <- pcount(~ visit - 1 ~ x, data = umf, K = 60, starts = rep(0, 5), mixture = "P", se = FALSE, engine = "C", threads = 1, method = "BFGS")
    })
    seconds <- c(seconds, as.numeric(elapsed["elapsed"]))
  }
  fit <- fits[[3]]
  coefs <- coef(fit)
  payload <- paste0(
    '{\n',
    '  "status": "completed",\n',
    '  "seconds": ', json_vec(seconds), ',\n',
    '  "median_seconds": ', format(median(seconds), digits = 17), ',\n',
    '  "logLik": ', format(as.numeric(logLik(fit)), digits = 17), ',\n',
    '  "coefficients": ', json_vec(as.numeric(coefs)), ',\n',
    '  "coefficient_names": ["', paste(json_escape(names(coefs)), collapse = '", "'), '"],\n',
    '  "R_version": "', json_escape(R.version.string), '",\n',
    '  "unmarked_version": "', as.character(utils::packageVersion("unmarked")), '",\n',
    '  "platform": "', json_escape(R.version$platform), '",\n',
    '  "dataset": {"n_sites": ', nrow(y), ', "n_visits": ', ncol(y), ', "K": 60, "repetitions": 3}\n',
    '}\n'
  )
  writeLines(payload, file.path(reports, "r_benchmark.json"))
  TRUE
}, error = function(e) e)

if (inherits(result, "error")) {
  write_not_run(conditionMessage(result))
}
