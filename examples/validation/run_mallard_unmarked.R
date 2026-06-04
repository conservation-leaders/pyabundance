# Run R/unmarked Mallard pcount fits as a black-box comparison target.
# Outputs are written under results/mallard/, which is git ignored.

if (!requireNamespace("unmarked", quietly = TRUE)) {
  stop("Install R package 'unmarked' to run Mallard validation")
}

source(file.path("examples", "validation", "export_mallard_from_unmarked.R"))

data_dir <- file.path("data", "mallard")
results_dir <- file.path("results", "mallard")
dir.create(results_dir, recursive = TRUE, showWarnings = FALSE)
# Expected outputs include r_poisson_meta.csv, r_poisson_coef.csv,
# r_nb_meta.csv, and r_nb_coef.csv.

site_data <- utils::read.csv(file.path(data_dir, "site_data_for_py.csv"))
obs_data <- utils::read.csv(file.path(data_dir, "obs_data_for_py.csv"))
count_cols <- c("y1", "y2", "y3")
visit_labels <- c("v1", "v2", "v3")

matrix_from_long <- function(frame, value_col) {
  wide <- reshape(
    frame[, c("site_id", "visit", value_col)],
    idvar = "site_id",
    timevar = "visit",
    direction = "wide"
  )
  wide <- wide[match(site_data$site_id, wide$site_id), ]
  cols <- paste0(value_col, ".", visit_labels)
  as.matrix(wide[, cols])
}

y <- as.matrix(site_data[, count_cols])
site_covs <- site_data[, c("length", "elev", "forest")]
obs_covs <- list(
  ivel = matrix_from_long(obs_data, "ivel"),
  date = matrix_from_long(obs_data, "date")
)
umf <- unmarked::unmarkedFramePCount(y = y, siteCovs = site_covs, obsCovs = obs_covs)

safe_loglik <- function(fit) {
  value <- tryCatch(stats::logLik(fit), error = function(e) numeric(0))
  if (length(value) == 0 || is.na(value[1])) {
    -as.numeric(methods::slot(fit, "negLogLike"))
  } else {
    as.numeric(value)
  }
}

safe_coef <- function(fit) {
  estimates <- methods::slot(methods::slot(fit, "estimates"), "estimates")
  rows <- list()
  for (block in names(estimates)) {
    estimate <- methods::slot(estimates[[block]], "estimates")
    cov_mat <- methods::slot(estimates[[block]], "covMat")
    se_values <- sqrt(diag(cov_mat))
    rows[[block]] <- data.frame(
      parameter = names(estimate),
      block = block,
      estimate = as.numeric(estimate),
      std_error = as.numeric(se_values),
      stringsAsFactors = FALSE
    )
  }
  do.call(rbind, rows)
}

safe_aic <- function(fit, loglik, n_params) {
  value <- tryCatch(stats::AIC(fit), error = function(e) numeric(0))
  if (length(value) == 0 || is.na(value[1])) {
    slot_value <- tryCatch(methods::slot(fit, "AIC"), error = function(e) NA_real_)
    if (is.na(slot_value)) {
      -2 * loglik + 2 * n_params
    } else {
      as.numeric(slot_value)
    }
  } else {
    as.numeric(value[1])
  }
}

fit_and_write <- function(label, formula, mixture) {
  start_time <- proc.time()["elapsed"]
  fit <- unmarked::pcount(
    formula,
    data = umf,
    K = 30,
    mixture = mixture,
    se = TRUE,
    engine = "C",
    method = "BFGS"
  )
  runtime <- as.numeric(proc.time()["elapsed"] - start_time)
  coef_frame <- safe_coef(fit)
  loglik <- safe_loglik(fit)
  opt <- methods::slot(fit, "opt")
  meta <- data.frame(
    model = label,
    mixture = mixture,
    logLik = loglik,
    AIC = safe_aic(fit, loglik, nrow(coef_frame)),
    n_params = nrow(coef_frame),
    K = 30,
    runtime_seconds = runtime,
    convergence = ifelse(is.null(opt$convergence), NA, opt$convergence),
    message = ifelse(is.null(opt$message), NA, opt$message),
    stringsAsFactors = FALSE
  )
  utils::write.csv(meta, file.path(results_dir, paste0("r_", label, "_meta.csv")), row.names = FALSE)
  utils::write.csv(coef_frame, file.path(results_dir, paste0("r_", label, "_coef.csv")), row.names = FALSE)
  fit
}

poisson_formula <- ~ ivel + date + I(date^2) ~ length + elev + forest
nb_formula <- ~ date + I(date^2) ~ length + elev

invisible(fit_and_write("poisson", poisson_formula, "P"))
invisible(fit_and_write("nb", nb_formula, "NB"))

cat("Wrote R/unmarked Mallard results to", results_dir, "\n")
