#!/usr/bin/env Rscript

# Get command-line arguments
args <- commandArgs(trailingOnly = TRUE)

# Check if dataset path is provided
if (length(args) < 1) {
  stop("Usage: Rscript stage3_signal_readings.R <dataset_path> [plot_output_path]")
}

dataset_path <- args[1]

# Determine plot output path
if (length(args) > 1) {
  plot_path <- args[2]
} else {
  base_name <- tools::file_path_sans_ext(basename(dataset_path))
  dir_name <- dirname(dataset_path)
  plot_path <- file.path(dir_name, paste0(base_name, "_boxplot.png"))
}

# Load the dataset
data <- read.csv(dataset_path, stringsAsFactors = FALSE)

if (nrow(data) == 0) {
  stop("Dataset is empty")
}

# Group by district
districts <- sort(unique(data$district))

# Create signals list
signals <- list()
codes <- list()

for (district in districts) {
  subset_data <- data[data$district == district, ]
  signals[[district]] <- as.numeric(subset_data$signal_strength)
  
  district_code_vals <- as.integer(as.numeric(subset_data$district_code[!is.na(subset_data$district_code)]))
  if (length(district_code_vals) > 0) {
    codes[[district]] <- unique(district_code_vals)
  }
}

# One-way ANOVA + Tukey HSD post-hoc (adjusted p-values included).
anova_model <- aov(signal_strength ~ district, data = data)
tukey <- TukeyHSD(anova_model, "district")$district

pairwise_rows <- data.frame(
  pair = rownames(tukey),
  diff = tukey[, "diff"],
  p_adj = tukey[, "p adj"],
  stringsAsFactors = FALSE
)

ranked <- list()
for (district in districts) {
  district_rows <- pairwise_rows[
    grepl(sprintf("^%s-", district), pairwise_rows$pair) |
    grepl(sprintf("-%s$", district), pairwise_rows$pair),
    ,
    drop = FALSE
  ]
  if (nrow(district_rows) == 0) {
    next
  }

  sig_count <- sum(district_rows$p_adj < 0.05)
  avg_abs_diff <- mean(abs(district_rows$diff))
  med_p <- median(district_rows$p_adj)

  ranked[[district]] <- data.frame(
    sig_count = sig_count,
    avg_abs_diff = avg_abs_diff,
    med_p = med_p,
    district = district,
    stringsAsFactors = FALSE
  )
}

ranked_df <- do.call(rbind, ranked)
ranked_df <- ranked_df[order(-ranked_df$sig_count, -ranked_df$avg_abs_diff, ranked_df$med_p), ]

if (nrow(ranked_df) == 0) {
  stop("Could not identify abnormal district")
}

abnormal_district <- ranked_df$district[1]

# Get district codes
district_codes <- codes[[abnormal_district]]
district_codes <- district_codes[district_codes > 0]

if (length(district_codes) != 1) {
  stop("Abnormal district code is missing or inconsistent")
}

# Print ranking info to stderr
cat("Top post-hoc candidates (TukeyHSD-adjusted):\n", file = stderr())
for (i in seq_len(min(5, nrow(ranked_df)))) {
  cat(sprintf("  %s: significant_pairs=%d, avg_|diff|=%.3f, median_p≈%.4f\n",
              ranked_df$district[i],
              ranked_df$sig_count[i],
              ranked_df$avg_abs_diff[i],
              ranked_df$med_p[i]),
      file = stderr())
}
cat(sprintf("Identified district: %s\n", abnormal_district), file = stderr())

# Create boxplot
tryCatch({
  png(plot_path, width = max(1400, length(districts) * 60), height = 600, res = 100)
  
  data_list <- lapply(districts, function(d) signals[[d]])
  colors <- ifelse(districts == abnormal_district, "#d64545", "#5b8ff9")
  
  # Create labels with district codes
  labels <- character(length(districts))
  for (i in seq_along(districts)) {
    dist <- districts[i]
    code_vals <- codes[[dist]]
    if (!is.null(code_vals)) {
      code_vals <- sort(code_vals[code_vals > 0])
      code_label <- if (length(code_vals) > 0) as.character(code_vals[1]) else "?"
    } else {
      code_label <- "?"
    }
    labels[i] <- sprintf("%s [%s]", dist, code_label)
  }
  
  boxplot(data_list,
          names = labels,
          main = sprintf("Stage 3 Signal Pattern (identified: %s)", abnormal_district),
          ylab = "Signal Strength",
          xlab = "District",
          col = colors,
          las = 2,
          cex.axis = 0.8)
  
  # Add legend
  legend("topright",
         legend = c("Identified district", "Other districts"),
         fill = c("#d64545", "#5b8ff9"))
  
  dev.off()
}, error = function(e) {
  cat(sprintf("Warning: Could not create boxplot: %s\n", e$message), file = stderr())
})

# Output the recovery code
code_value <- district_codes[1] %% 1000000
cat(sprintf("%06d\n", code_value))
