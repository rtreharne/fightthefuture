#!/usr/bin/env Rscript

suppressWarnings(suppressMessages({
  if (!requireNamespace("png", quietly = TRUE)) {
    stop("Package 'png' is required. Install with: install.packages('png')", call. = FALSE)
  }
}))

DIGIT_FONT <- list(
  "0" = c("111", "101", "101", "101", "111"),
  "1" = c("010", "110", "010", "010", "111"),
  "2" = c("111", "001", "111", "100", "111"),
  "3" = c("111", "001", "111", "001", "111"),
  "4" = c("101", "101", "111", "001", "001"),
  "5" = c("111", "100", "111", "001", "111"),
  "6" = c("111", "100", "111", "101", "111"),
  "7" = c("111", "001", "001", "001", "001"),
  "8" = c("111", "101", "111", "101", "111"),
  "9" = c("111", "101", "111", "001", "111")
)

SCALE <- 2L
MIN_SCORE <- 0.76
MAX_DRONE_ID <- 20L

clamp <- function(value, low, high) {
  max(low, min(high, value))
}

read_image_rgb <- function(image_path) {
  arr <- png::readPNG(image_path)
  if (length(dim(arr)) != 3 || dim(arr)[3] < 3) {
    stop("Expected an RGB/RGBA PNG image.", call. = FALSE)
  }
  arr[, , 1:3, drop = FALSE]
}

detect_blue_circles <- function(image_path) {
  arr <- read_image_rgb(image_path)
  h <- dim(arr)[1]
  w <- dim(arr)[2]

  blue_mask <- (arr[, , 1] < (100 / 255)) &
    (arr[, , 2] < (150 / 255)) &
    (arr[, , 3] > (150 / 255))

  visited <- matrix(FALSE, nrow = h, ncol = w)
  circles <- list()

  for (row in seq_len(h)) {
    for (col in seq_len(w)) {
      if (!blue_mask[row, col] || visited[row, col]) {
        next
      }

      q_row <- integer(0)
      q_col <- integer(0)
      q_head <- 1L
      q_row <- c(q_row, row)
      q_col <- c(q_col, col)
      pix_x <- numeric(0)
      pix_y <- numeric(0)

      while (q_head <= length(q_row)) {
        cr <- q_row[q_head]
        cc <- q_col[q_head]
        q_head <- q_head + 1L

        if (cr < 1L || cr > h || cc < 1L || cc > w) {
          next
        }
        if (visited[cr, cc] || !blue_mask[cr, cc]) {
          next
        }

        visited[cr, cc] <- TRUE
        pix_x <- c(pix_x, cc - 1) # zero-based x
        pix_y <- c(pix_y, cr - 1) # zero-based y

        q_row <- c(q_row, cr, cr, cr + 1L, cr - 1L)
        q_col <- c(q_col, cc + 1L, cc - 1L, cc, cc)
      }

      if (length(pix_x) > 50L) {
        circles[[length(circles) + 1L]] <- c(mean(pix_x), mean(pix_y))
      }
    }
  }

  if (length(circles) == 0L) {
    return(matrix(numeric(0), ncol = 2))
  }

  out <- do.call(rbind, circles)
  out <- out[order(out[, 2], out[, 1]), , drop = FALSE]
  out
}

render_template <- function(drone_id) {
  text <- as.character(drone_id)
  width <- nchar(text) * 8L
  height <- 10L
  template <- matrix(0L, nrow = height, ncol = width)
  cursor <- 0L

  chars <- strsplit(text, "", fixed = TRUE)[[1]]
  for (ch in chars) {
    pattern <- DIGIT_FONT[[ch]]
    for (row_i in seq_along(pattern)) {
      bits <- strsplit(pattern[row_i], "", fixed = TRUE)[[1]]
      for (col_i in seq_along(bits)) {
        if (bits[col_i] != "1") {
          next
        }
        y0 <- (row_i - 1L) * SCALE + 1L
        x0 <- cursor + (col_i - 1L) * SCALE + 1L
        template[y0:(y0 + SCALE - 1L), x0:(x0 + SCALE - 1L)] <- 1L
      }
    }
    cursor <- cursor + 8L
  }

  template
}

build_templates <- function() {
  ids <- seq_len(MAX_DRONE_ID)
  templates <- lapply(ids, render_template)
  names(templates) <- as.character(ids)
  templates
}

ID_TEMPLATES <- build_templates()

decode_drone_id <- function(center, black_mask, width, height) {
  cx <- as.integer(round(center[1]))
  cy <- as.integer(round(center[2]))
  best_id <- NA_integer_
  best_score <- -1

  for (id_key in names(ID_TEMPLATES)) {
    drone_id <- as.integer(id_key)
    template <- ID_TEMPLATES[[id_key]]
    th <- nrow(template)
    tw <- ncol(template)

    candidates <- list(
      c(clamp(cx - (tw %/% 2L), 0L, width - tw), clamp(cy - (th %/% 2L), 0L, height - th)),
      c(clamp(cx - (nchar(as.character(drone_id)) * 4L), 0L, width - tw), clamp(cy - 20L, 0L, height - th))
    )

    score <- -1
    for (cand in candidates) {
      x <- as.integer(cand[1])
      y <- as.integer(cand[2])
      roi <- black_mask[(y + 1L):(y + th), (x + 1L):(x + tw), drop = FALSE]
      if (!all(dim(roi) == dim(template))) {
        next
      }
      matches <- sum(roi == template)
      score <- max(score, matches / length(template))
    }

    if (score > best_score) {
      best_score <- score
      best_id <- drone_id
    }
  }

  list(drone_id = best_id, score = best_score)
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) < 1L) {
    cat("Usage: Rscript helper_extract_drone.R <image_path>\n")
    quit(status = 1)
  }

  image_path <- args[[1]]

  circles <- detect_blue_circles(image_path)
  if (nrow(circles) == 0L) {
    cat("No circles detected.\n")
    quit(status = 1)
  }

  arr <- read_image_rgb(image_path)
  h <- dim(arr)[1]
  w <- dim(arr)[2]
  black_mask <- ((arr[, , 1] < (20 / 255)) &
    (arr[, , 2] < (20 / 255)) &
    (arr[, , 3] < (20 / 255))) * 1L

  cat(sprintf("Detected %d circle(s):\n", nrow(circles)))
  cat("drone_id,x,y\n")

  decoded <- list()
  for (i in seq_len(nrow(circles))) {
    center <- circles[i, ]
    res <- decode_drone_id(center, black_mask, w, h)
    if (is.na(res$drone_id) || res$score < MIN_SCORE) {
      next
    }
    decoded[[length(decoded) + 1L]] <- list(
      drone_id = res$drone_id,
      score = res$score,
      x = center[1],
      y = center[2]
    )
  }

  best_by_id <- list()
  for (item in decoded) {
    key <- as.character(item$drone_id)
    prev <- best_by_id[[key]]
    if (is.null(prev) || item$score > prev$score) {
      best_by_id[[key]] <- item
    }
  }

  id_keys <- sort(as.integer(names(best_by_id)))
  for (id in id_keys) {
    item <- best_by_id[[as.character(id)]]
    cat(sprintf("%d,%d,%d\n", id, as.integer(round(item$x)), as.integer(round(item$y))))
  }
}

main()
