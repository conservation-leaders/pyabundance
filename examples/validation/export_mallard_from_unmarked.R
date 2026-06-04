# Export unmarked::mallard locally for black-box validation against pyabundance.
# Generated CSVs are written under data/mallard/, which is git ignored.

required_packages <- c("unmarked")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages) > 0) {
  stop("Install R package(s) before running this validation: ", paste(missing_packages, collapse = ", "))
}

site_vars <- c("length", "elev", "forest")
obs_vars <- c("ivel", "date")
out_dir <- file.path("data", "mallard")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

data("mallard", package = "unmarked")

require_columns <- function(frame, columns, label) {
  missing <- setdiff(columns, names(frame))
  if (length(missing) > 0) {
    stop(label, " is missing required column(s): ", paste(missing, collapse = ", "))
  }
}

as_required_matrix <- function(obs_covs, name, n_sites, n_visits) {
  if (!name %in% names(obs_covs)) {
    stop("obsCovs is missing required variable: ", name)
  }
  value <- obs_covs[[name]]
  matrix_value <- as.matrix(value)
  if (!all(dim(matrix_value) == c(n_sites, n_visits))) {
    stop("obsCovs variable ", name, " has shape ", paste(dim(matrix_value), collapse = "x"),
         "; expected ", n_sites, "x", n_visits)
  }
  matrix_value
}

if (exists("mallard")) {
  y <- as.matrix(unmarked::getY(mallard))
  site_covs <- as.data.frame(unmarked::siteCovs(mallard))
  obs_covs <- unmarked::obsCovs(mallard)
} else if (exists("mallard.y") && exists("mallard.site") && exists("mallard.obs")) {
  y <- as.matrix(mallard.y)
  site_covs <- as.data.frame(mallard.site)
  obs_covs <- mallard.obs
} else {
  stop("Could not load Mallard data from unmarked; expected mallard or mallard.y/site/obs objects")
}
n_sites <- nrow(y)
n_visits <- ncol(y)
if (n_visits != 3) {
  stop("This Mallard walkthrough expects exactly 3 visits; got ", n_visits)
}
require_columns(site_covs, site_vars, "siteCovs(mallard)")
obs_mats <- lapply(
  obs_vars,
  function(name) as_required_matrix(obs_covs, name, n_sites = n_sites, n_visits = n_visits)
)
names(obs_mats) <- obs_vars

site_keep <- stats::complete.cases(site_covs[, site_vars, drop = FALSE])
count_keep <- stats::complete.cases(y)
obs_keep <- rep(TRUE, n_sites)
for (name in obs_vars) {
  obs_keep <- obs_keep & apply(!is.na(obs_mats[[name]]), 1, all)
}
keep <- count_keep & site_keep & obs_keep
original_site_index <- seq_len(n_sites)
site_id_all <- sprintf("site_%03d", original_site_index)

filter_frame <- data.frame(
  original_site_index = original_site_index,
  site_id = site_id_all,
  included = keep,
  stringsAsFactors = FALSE
)
utils::write.csv(filter_frame, file.path(out_dir, "analysis_site_filter.csv"), row.names = FALSE)

kept_indices <- which(keep)
site_data <- data.frame(
  site_id = site_id_all[keep],
  original_site_index = original_site_index[keep],
  y1 = y[keep, 1],
  y2 = y[keep, 2],
  y3 = y[keep, 3],
  site_covs[keep, site_vars, drop = FALSE],
  stringsAsFactors = FALSE
)
utils::write.csv(site_data, file.path(out_dir, "site_data_for_py.csv"), row.names = FALSE)

visit_labels <- paste0("v", seq_len(n_visits))
obs_rows <- vector("list", length(kept_indices) * n_visits)
row_index <- 1
for (site_pos in seq_along(kept_indices)) {
  original_index <- kept_indices[site_pos]
  for (visit_index in seq_len(n_visits)) {
    obs_rows[[row_index]] <- data.frame(
      site_id = site_id_all[original_index],
      original_site_index = original_index,
      visit = visit_labels[visit_index],
      visit_index = visit_index,
      ivel = obs_mats[["ivel"]][original_index, visit_index],
      date = obs_mats[["date"]][original_index, visit_index],
      stringsAsFactors = FALSE
    )
    row_index <- row_index + 1
  }
}
obs_data <- do.call(rbind, obs_rows)
utils::write.csv(obs_data, file.path(out_dir, "obs_data_for_py.csv"), row.names = FALSE)

cat("Mallard export complete\n")
cat("Included sites:", sum(keep), "of", length(keep), "\n")
cat("Dropped original site indices:", paste(which(!keep), collapse = ", "), "\n")
cat("Wrote", file.path(out_dir, "site_data_for_py.csv"), "\n")
cat("Wrote", file.path(out_dir, "obs_data_for_py.csv"), "\n")
cat("Wrote", file.path(out_dir, "analysis_site_filter.csv"), "\n")
