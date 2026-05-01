#!/usr/bin/env Rscript

SCALE <- 2L
TIE_EPS <- 1e-9

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


clamp <- function(value, low, high) {
  max(low, min(high, value))
}


read_uint32_be <- function(raw_vec, pos) {
  bytes <- as.integer(raw_vec[pos:(pos + 3L)])
  bytes[1] * 16777216L + bytes[2] * 65536L + bytes[3] * 256L + bytes[4]
}


unzip_dataset <- function(zip_path, output_dir) {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  utils::unzip(zipfile = zip_path, exdir = output_dir)
}


load_mapping <- function(csv_path) {
  df <- utils::read.csv(csv_path, stringsAsFactors = FALSE)
  out <- as.integer(df$serial_number)
  names(out) <- as.character(df$drone_id)
  out
}


read_png_rgb <- function(path) {
  file_size <- file.info(path)$size
  png_raw <- readBin(path, what = "raw", n = file_size)
  png_sig <- as.raw(c(137, 80, 78, 71, 13, 10, 26, 10))

  if (length(png_raw) < 8L || any(png_raw[1:8] != png_sig)) {
    stop(sprintf("Invalid PNG signature: %s", path), call. = FALSE)
  }

  pos <- 9L
  width <- NA_integer_
  height <- NA_integer_
  bit_depth <- NA_integer_
  color_type <- NA_integer_
  compression_method <- NA_integer_
  filter_method <- NA_integer_
  interlace_method <- NA_integer_
  idat_parts <- list()

  while (pos <= length(png_raw)) {
    if (pos + 7L > length(png_raw)) {
      stop(sprintf("Truncated PNG chunk header: %s", path), call. = FALSE)
    }

    chunk_len <- read_uint32_be(png_raw, pos)
    pos <- pos + 4L
    chunk_type <- rawToChar(png_raw[pos:(pos + 3L)])
    pos <- pos + 4L

    if (chunk_len < 0L || pos + chunk_len - 1L > length(png_raw)) {
      stop(sprintf("Invalid PNG chunk length: %s", path), call. = FALSE)
    }

    if (chunk_len > 0L) {
      chunk_data <- png_raw[pos:(pos + chunk_len - 1L)]
      pos <- pos + chunk_len
    } else {
      chunk_data <- raw(0)
    }

    if (pos + 3L > length(png_raw)) {
      stop(sprintf("Missing PNG CRC: %s", path), call. = FALSE)
    }
    # Skip CRC (not validated here).
    pos <- pos + 4L

    if (chunk_type == "IHDR") {
      if (length(chunk_data) != 13L) {
        stop(sprintf("Unexpected IHDR length in PNG: %s", path), call. = FALSE)
      }
      width <- read_uint32_be(chunk_data, 1L)
      height <- read_uint32_be(chunk_data, 5L)
      bit_depth <- as.integer(chunk_data[9L])
      color_type <- as.integer(chunk_data[10L])
      compression_method <- as.integer(chunk_data[11L])
      filter_method <- as.integer(chunk_data[12L])
      interlace_method <- as.integer(chunk_data[13L])
    } else if (chunk_type == "IDAT") {
      idat_parts[[length(idat_parts) + 1L]] <- chunk_data
    } else if (chunk_type == "IEND") {
      break
    }
  }

  if (
    is.na(width) || is.na(height) ||
    length(idat_parts) == 0L
  ) {
    stop(sprintf("Incomplete PNG (IHDR/IDAT missing): %s", path), call. = FALSE)
  }

  if (bit_depth != 8L || color_type != 6L) {
    stop(
      sprintf(
        "Unsupported PNG format in %s (bit_depth=%s, color_type=%s)",
        path, bit_depth, color_type
      ),
      call. = FALSE
    )
  }
  if (compression_method != 0L || filter_method != 0L || interlace_method != 0L) {
    stop(sprintf("Unsupported PNG compression/filter/interlace in %s", path), call. = FALSE)
  }

  idat_stream <- do.call(c, idat_parts)
  decompressed <- tryCatch(
    memDecompress(idat_stream, type = "gzip"),
    error = function(...) memDecompress(idat_stream, type = "unknown")
  )

  stride <- width * 4L
  expected_len <- height * (1L + stride)
  if (length(decompressed) != expected_len) {
    stop(
      sprintf(
        "Unexpected decompressed PNG length in %s (got %d, expected %d)",
        path, length(decompressed), expected_len
      ),
      call. = FALSE
    )
  }

  rgb <- array(0L, dim = c(height, width, 3L))
  idx <- 1L
  for (y in seq_len(height)) {
    filter_type <- as.integer(decompressed[idx])
    idx <- idx + 1L
    if (filter_type != 0L) {
      stop(
        sprintf("Unsupported PNG scanline filter %d in %s", filter_type, path),
        call. = FALSE
      )
    }
    line_vals <- as.integer(decompressed[idx:(idx + stride - 1L)])
    idx <- idx + stride
    line_px <- matrix(line_vals, ncol = 4L, byrow = TRUE)
    rgb[y, , 1L] <- line_px[, 1L]
    rgb[y, , 2L] <- line_px[, 2L]
    rgb[y, , 3L] <- line_px[, 3L]
  }

  rgb
}


find_drone_centers <- function(image_array) {
  mask <- (
    image_array[, , 1L] == 70L &
      image_array[, , 2L] == 122L &
      image_array[, , 3L] == 213L
  )

  h <- nrow(mask)
  w <- ncol(mask)
  visited <- matrix(FALSE, nrow = h, ncol = w)
  centers <- list()

  dx <- c(-1L, 0L, 1L, -1L, 1L, -1L, 0L, 1L)
  dy <- c(-1L, -1L, -1L, 0L, 0L, 1L, 1L, 1L)

  for (y1 in seq_len(h)) {
    for (x1 in seq_len(w)) {
      if (!mask[y1, x1] || visited[y1, x1]) {
        next
      }

      qx <- integer(h * w)
      qy <- integer(h * w)
      head <- 1L
      tail <- 1L
      qx[tail] <- x1
      qy[tail] <- y1
      visited[y1, x1] <- TRUE

      sum_x0 <- 0.0
      sum_y0 <- 0.0
      area <- 0L

      while (head <= tail) {
        cx1 <- qx[head]
        cy1 <- qy[head]
        head <- head + 1L

        # Store as 0-based to mirror Python math exactly.
        cx0 <- cx1 - 1L
        cy0 <- cy1 - 1L
        sum_x0 <- sum_x0 + cx0
        sum_y0 <- sum_y0 + cy0
        area <- area + 1L

        for (k in seq_along(dx)) {
          nx1 <- cx1 + dx[k]
          ny1 <- cy1 + dy[k]
          if (nx1 < 1L || nx1 > w || ny1 < 1L || ny1 > h) {
            next
          }
          if (!mask[ny1, nx1] || visited[ny1, nx1]) {
            next
          }
          visited[ny1, nx1] <- TRUE
          tail <- tail + 1L
          qx[tail] <- nx1
          qy[tail] <- ny1
        }
      }

      # Supports both old (r~8) and new (r~14) stage image styles.
      if (area >= 120L && area <= 980L) {
        centers[[length(centers) + 1L]] <- c(
          as.integer(round(sum_x0 / area)),
          as.integer(round(sum_y0 / area))
        )
      }
    }
  }

  if (length(centers) == 0L) {
    return(matrix(integer(0), ncol = 2L))
  }
  do.call(rbind, centers)
}


render_id_template <- function(drone_id) {
  text <- as.character(drone_id)
  width <- nchar(text) * 8L
  height <- 10L
  template <- matrix(0L, nrow = height, ncol = width)
  cursor <- 0L

  chars <- strsplit(text, "", fixed = TRUE)[[1]]
  for (char in chars) {
    pattern <- DIGIT_FONT[[char]]
    for (row_i in 0:4) {
      row_bits <- pattern[row_i + 1L]
      for (col_i in 0:2) {
        if (substr(row_bits, col_i + 1L, col_i + 1L) != "1") {
          next
        }
        for (sy in 0:(SCALE - 1L)) {
          for (sx in 0:(SCALE - 1L)) {
            template[
              row_i * SCALE + sy + 1L,
              cursor + col_i * SCALE + sx + 1L
            ] <- 1L
          }
        }
      }
    }
    cursor <- cursor + 8L
  }

  template
}


build_id_templates <- function() {
  out <- vector("list", 99L)
  names(out) <- as.character(1:99)
  for (drone_id in 1:99) {
    out[[drone_id]] <- render_id_template(drone_id)
  }
  out
}


decode_drone_id <- function(center0, black_mask, width, height, id_templates) {
  cx <- center0[1]
  cy <- center0[2]
  best_id <- NA_integer_
  best_score <- -1.0

  for (drone_id in 1:99) {
    template <- id_templates[[drone_id]]
    tw <- ncol(template)
    th <- nrow(template)

    # Candidate top-left coordinates in 0-based space.
    candidates <- rbind(
      c(
        clamp(cx - (tw %/% 2L), 0L, width - tw),
        clamp(cy - (th %/% 2L), 0L, height - th)
      ),
      c(
        clamp(cx - (nchar(as.character(drone_id)) * 4L), 0L, width - tw),
        clamp(cy - 20L, 0L, height - th)
      )
    )

    score <- -1.0
    for (k in seq_len(nrow(candidates))) {
      x0 <- candidates[k, 1L]
      y0 <- candidates[k, 2L]
      x1 <- x0 + 1L
      y1 <- y0 + 1L

      roi <- black_mask[y1:(y1 + th - 1L), x1:(x1 + tw - 1L), drop = FALSE]
      matches <- sum(roi == template)
      candidate_score <- matches / length(template)
      if (candidate_score > score) {
        score <- candidate_score
      }
    }

    if (score > best_score) {
      best_score <- score
      best_id <- drone_id
    }
  }

  list(id = best_id, score = best_score)
}


average_distance_to_others <- function(point0, others0) {
  if (is.null(dim(others0)) || nrow(others0) == 0L) {
    return(0.0)
  }
  dx <- point0[1] - others0[, 1L]
  dy <- point0[2] - others0[, 2L]
  mean(sqrt(dx * dx + dy * dy))
}


compute_scores <- function(sum_by_id, seen_by_id, drone_ids) {
  scores <- setNames(rep(NA_real_, length(drone_ids)), as.character(drone_ids))
  for (drone_id in drone_ids) {
    key <- as.character(drone_id)
    seen <- seen_by_id[[key]]
    if (!is.na(seen) && seen > 0L) {
      scores[[key]] <- sum_by_id[[key]] / seen
    }
  }
  scores
}


choose_winner <- function(scores, drone_ids, eps = TIE_EPS) {
  winner <- min(drone_ids)
  winner_score <- -1.0
  for (drone_id in sort(drone_ids)) {
    key <- as.character(drone_id)
    score <- scores[[key]]
    if (is.na(score)) {
      score <- 0.0
    }
    if (score > winner_score + eps) {
      winner <- drone_id
      winner_score <- score
    } else if (abs(score - winner_score) <= eps && drone_id < winner) {
      winner <- drone_id
      winner_score <- score
    }
  }
  list(id = winner, score = winner_score)
}


save_average_distance_bar_chart <- function(mapping, scores, target_drone_id, output_path) {
  all_ids <- as.integer(names(mapping))
  sortable <- setNames(rep(0.0, length(all_ids)), as.character(all_ids))
  for (drone_id in all_ids) {
    key <- as.character(drone_id)
    val <- scores[[key]]
    if (!is.na(val)) {
      sortable[[key]] <- val
    }
  }

  ordered_ids <- as.integer(names(sort(sortable, decreasing = TRUE)))
  labels <- sprintf("%06d", as.integer(mapping[as.character(ordered_ids)]))
  values <- as.numeric(sortable[as.character(ordered_ids)])
  colors <- ifelse(ordered_ids == target_drone_id, "#d64545", "#5b8ff9")

  png(
    filename = output_path,
    width = max(1600L, length(ordered_ids) * 18L),
    height = 700L
  )
  old_par <- par(no.readonly = TRUE)
  on.exit({
    par(old_par)
    dev.off()
  }, add = TRUE)

  par(mar = c(10, 5, 4, 2))
  y_max <- max(values)
  if (!is.finite(y_max) || y_max <= 0) {
    y_max <- 1
  }
  barplot(
    values,
    col = colors,
    border = "#2f2f2f",
    names.arg = labels,
    las = 2,
    cex.names = 0.6,
    ylab = "Average Distance To Other Drones",
    xlab = "Drone Serial Number",
    main = "Average Drone Separation by Serial (winner highlighted)",
    ylim = c(0, y_max * 1.1)
  )
  grid(nx = NA, ny = NULL, lty = 3, col = "gray80")
}


solve <- function(zip_path, extract_dir) {
  unzip_dataset(zip_path, extract_dir)

  mapping_path <- file.path(extract_dir, "drone_serials.csv")
  images_dir <- file.path(extract_dir, "images")
  mapping <- load_mapping(mapping_path)

  all_drone_ids <- sort(as.integer(names(mapping)))
  if (length(all_drone_ids) == 0L) {
    stop("No drone mapping rows found.", call. = FALSE)
  }

  id_templates <- build_id_templates()

  max_id <- max(max(all_drone_ids), 99L)
  avg_dist_sum_by_id <- setNames(rep(0.0, max_id), as.character(seq_len(max_id)))
  frame_count_by_id <- setNames(rep(0L, max_id), as.character(seq_len(max_id)))

  image_paths <- sort(list.files(images_dir, pattern = "\\.png$", full.names = TRUE))
  for (image_path in image_paths) {
    image <- read_png_rgb(image_path)
    h <- dim(image)[1L]
    w <- dim(image)[2L]

    black_mask <- (
      image[, , 1L] < 20L &
        image[, , 2L] < 20L &
        image[, , 3L] < 20L
    )
    storage.mode(black_mask) <- "integer"

    centers <- find_drone_centers(image)
    detections <- list()
    used_ids <- integer(0)

    if (nrow(centers) > 0L) {
      for (i in seq_len(nrow(centers))) {
        center0 <- centers[i, ]
        decoded <- decode_drone_id(center0, black_mask, w, h, id_templates)
        drone_id <- decoded$id
        score <- decoded$score
        if (is.na(drone_id) || score < 0.76 || drone_id %in% used_ids) {
          next
        }
        used_ids <- c(used_ids, drone_id)
        detections[[length(detections) + 1L]] <- list(id = drone_id, point = center0)
      }
    }

    if (length(detections) < 2L) {
      next
    }

    detected_ids <- vapply(detections, function(item) item$id, integer(1))
    detected_points <- do.call(rbind, lapply(detections, function(item) item$point))

    for (idx in seq_along(detected_ids)) {
      drone_id <- detected_ids[idx]
      point0 <- detected_points[idx, ]
      others0 <- detected_points[-idx, , drop = FALSE]
      mean_dist <- average_distance_to_others(point0, others0)
      key <- as.character(drone_id)
      avg_dist_sum_by_id[[key]] <- avg_dist_sum_by_id[[key]] + mean_dist
      frame_count_by_id[[key]] <- frame_count_by_id[[key]] + 1L
    }
  }

  if (!any(frame_count_by_id > 0L)) {
    stop("No valid drone detections were made from the image set.", call. = FALSE)
  }

  scores <- compute_scores(avg_dist_sum_by_id, frame_count_by_id, all_drone_ids)
  winner <- choose_winner(scores, all_drone_ids, eps = TIE_EPS)

  chart_path <- file.path(extract_dir, "drone_average_distance.png")
  save_average_distance_bar_chart(mapping, scores, winner$id, chart_path)

  serial <- as.integer(mapping[[as.character(winner$id)]])
  cat(sprintf("%06d\n", serial))
}


main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) < 1L) {
    stop(
      "Usage: Rscript stage4_forever_alone_drone.R <stage4_zip_path> [extract_dir]",
      call. = FALSE
    )
  }

  zip_path <- args[[1L]]
  if (!file.exists(zip_path)) {
    stop(sprintf("ZIP file not found: %s", zip_path), call. = FALSE)
  }

  extract_dir <- if (length(args) >= 2L) {
    args[[2L]]
  } else {
    file.path(dirname(zip_path), "stage4_unzipped")
  }

  solve(zip_path, extract_dir)
}


main()
