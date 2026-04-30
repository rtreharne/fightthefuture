#!/usr/bin/env Rscript

# Get command-line arguments
args <- commandArgs(trailingOnly = TRUE)

# Check if dataset path is provided
if (length(args) < 1) {
  stop("Usage: Rscript stage2_ghost_audit.R <dataset_path>")
}

dataset_path <- args[1]

# Read the CSV file
data <- read.csv(dataset_path, stringsAsFactors = FALSE)

# Check if dataset is empty
if (nrow(data) == 0) {
  stop("Dataset is empty")
}

# Get bias_key from first row
bias_key <- as.integer(data$bias_key[1])

# Filter and calculate total
filtered <- data[
  data$status == "ACTIVE" & 
  as.integer(data$authentic) == 1 & 
  as.integer(data$priority) >= 4,
]

total <- sum(as.integer(filtered$units) * as.integer(filtered$multiplier))

# Calculate code
code <- (total + bias_key) %% 1000000

# Print with leading zeros (6 digits)
cat(sprintf("%06d\n", code))
