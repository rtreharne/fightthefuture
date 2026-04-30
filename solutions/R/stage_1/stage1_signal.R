args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop("Usage: Rscript stage1_signal.R <dataset_path>")
}

dataset_path <- args[[1]]
df <- read.csv(dataset_path, stringsAsFactors = FALSE)

signals <- df[df$keep == 1, ]
signals <- signals[order(signals$pos), ]

decode_digit <- function(encoded, key, pos) {
  (encoded - key - (pos * 3)) %% 10
}

digits <- mapply(decode_digit, signals$encoded, signals$key, signals$pos)
cat(paste0(digits, collapse = ""), "\n")