#!/usr/bin/env Rscript

# Install png if needed
if (!require("png", quietly = TRUE)) {
  install.packages("png", repos = "http://cran.r-project.org")
  library(png)
}

# Find blue circles in image
# Blue drones have high blue channel, low red/green
find_blue_circles <- function(image_data) {
  if (length(dim(image_data)) < 3) {
    return(list())
  }
  
  h <- nrow(image_data)
  w <- ncol(image_data)
  
  # Scale to 0-255 if needed
  if (max(image_data) <= 1) {
    image_data <- image_data * 255
  }
  
  r <- image_data[, , 1]
  g <- image_data[, , 2]
  b <- image_data[, , 3]
  
  # Blue detection: high B, low R, low G
  # Adjust thresholds as needed
  blue_mask <- (b > 100) & (r < 150) & (g < 150) & (b > r) & (b > g)
  
  # Connected component labeling via flood fill
  labeled <- matrix(0L, nrow = h, ncol = w)
  circles <- list()
  label_id <- 0L
  
  for (y in 1:h) {
    for (x in 1:w) {
      if (blue_mask[y, x] && labeled[y, x] == 0L) {
        label_id <- label_id + 1L
        
        # BFS flood fill
        queue <- list(c(x, y))
        idx <- 1L
        pts_x <- numeric()
        pts_y <- numeric()
        
        while (idx <= length(queue)) {
          cur <- queue[[idx]]
          cx <- cur[1]
          cy <- cur[2]
          idx <- idx + 1L
          
          if (cx < 1 || cx > w || cy < 1 || cy > h) next
          if (labeled[cy, cx] != 0L) next
          if (!blue_mask[cy, cx]) next
          
          labeled[cy, cx] <- label_id
          pts_x <- c(pts_x, cx)
          pts_y <- c(pts_y, cy)
          
          # Add 4-neighbors
          queue[[length(queue) + 1L]] <- c(cx - 1, cy)
          queue[[length(queue) + 1L]] <- c(cx + 1, cy)
          queue[[length(queue) + 1L]] <- c(cx, cy - 1)
          queue[[length(queue) + 1L]] <- c(cx, cy + 1)
        }
        
        # Keep regions with reasonable size (circles should have 50-2000 pixels)
        n_pts <- length(pts_x)
        if (n_pts >= 50 && n_pts <= 2000) {
          cx <- mean(pts_x)
          cy <- mean(pts_y)
          circles[[length(circles) + 1L]] <- list(x = cx, y = cy, size = n_pts)
        }
      }
    }
  }
  
  return(circles)
}

# Extract drone ID from sanity check or by proximity matching
get_drone_id_from_sanity <- function(x, y, sanity_subset) {
  if (nrow(sanity_subset) == 0) return(NA)
  
  # Find nearest sanity point
  distances <- sqrt((x - sanity_subset$x)^2 + (y - sanity_subset$y)^2)
  min_idx <- which.min(distances)
  min_dist <- distances[min_idx]
  
  # Only match if close enough (within 20 pixels)
  if (min_dist < 20) {
    return(sanity_subset$drone_id[min_idx])
  }
  return(NA)
}

# Calculate average distance to other drones
avg_dist_to_others <- function(x, y, others_x, others_y) {
  if (length(others_x) == 0) return(0)
  distances <- sqrt((x - others_x)^2 + (y - others_y)^2)
  mean(distances)
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  
  if (length(args) < 1) {
    stop("Usage: Rscript stage4_solution.R <path_to_zip>")
  }
  
  zip_path <- args[1]
  
  # Extract ZIP
  extract_dir <- file.path(dirname(zip_path), "stage4_extracted")
  dir.create(extract_dir, showWarnings = FALSE, recursive = TRUE)
  
  cat("Extracting ZIP...\n", file = stderr())
  unzip(zip_path, exdir = extract_dir)
  
  # Load mappings
  mapping_file <- file.path(extract_dir, "drone_serials.csv")
  mapping_data <- read.csv(mapping_file, stringsAsFactors = FALSE)
  mapping <- setNames(mapping_data$serial_number, mapping_data$drone_id)
  
  # Load sanity check
  sanity_file <- file.path(extract_dir, "sanity_check.csv")
  sanity_data <- read.csv(sanity_file, stringsAsFactors = FALSE)
  
  cat(sprintf("Loaded %d drone serial mappings\n", nrow(mapping_data)), file = stderr())
  cat(sprintf("Loaded %d sanity check observations\n", nrow(sanity_data)), file = stderr())
  
  # Get images directory
  images_dir <- file.path(extract_dir, "images")
  png_files <- sort(list.files(images_dir, pattern = "\\.png$", full.names = TRUE))
  
  cat(sprintf("Found %d PNG images\n", length(png_files)), file = stderr())
  
  # Initialize accumulators
  distance_sum_by_drone <- list()
  frame_count_by_drone <- list()
  
  # Process each image
  for (img_file in png_files) {
    img_name <- basename(img_file)
    
    cat(sprintf("Processing %s...\n", img_name), file = stderr())
    
    # Read image
    image <- readPNG(img_file)
    
    # Find blue circles
    circles <- find_blue_circles(image)
    cat(sprintf("  Detected %d blue circles\n", length(circles)), file = stderr())
    
    if (length(circles) < 2) {
      cat(sprintf("  Skipped (need at least 2 drones)\n"), file = stderr())
      next
    }
    
    # Get sanity data for this image if available
    sanity_subset <- sanity_data[sanity_data$image_name == img_name, ]
    
    # Match circles to drone IDs
    drone_ids <- numeric(length(circles))
    for (i in seq_along(circles)) {
      circle <- circles[[i]]
      drone_id <- get_drone_id_from_sanity(circle$x, circle$y, sanity_subset)
      
      if (is.na(drone_id)) {
        # For now, if we can't match, skip this circle
        drone_ids[i] <- NA
      } else {
        drone_ids[i] <- drone_id
      }
    }
    
    # Filter to only matched drones
    valid_idx <- !is.na(drone_ids)
    valid_circles <- circles[valid_idx]
    valid_drone_ids <- drone_ids[valid_idx]
    
    cat(sprintf("  Matched %d drones\n", length(valid_drone_ids)), file = stderr())
    
    if (length(valid_circles) < 2) {
      cat(sprintf("  Skipped (fewer than 2 matched drones)\n"), file = stderr())
      next
    }
    
    # Calculate distances for each drone
    for (i in seq_along(valid_circles)) {
      drone_id <- valid_drone_ids[i]
      circle <- valid_circles[[i]]
      
      # Get coordinates of other drones
      others_x <- sapply(valid_circles[-i], function(c) c$x)
      others_y <- sapply(valid_circles[-i], function(c) c$y)
      
      # Calculate average distance
      avg_dist <- avg_dist_to_others(circle$x, circle$y, others_x, others_y)
      
      drone_key <- as.character(drone_id)
      if (!(drone_key %in% names(distance_sum_by_drone))) {
        distance_sum_by_drone[[drone_key]] <- 0
        frame_count_by_drone[[drone_key]] <- 0
      }
      
      distance_sum_by_drone[[drone_key]] <- distance_sum_by_drone[[drone_key]] + avg_dist
      frame_count_by_drone[[drone_key]] <- frame_count_by_drone[[drone_key]] + 1
      
      cat(sprintf("    Drone %d: avg_dist = %.2f\n", drone_id, avg_dist), file = stderr())
    }
  }
  
  # Compute overall averages
  overall_distances <- numeric(length(distance_sum_by_drone))
  names(overall_distances) <- names(distance_sum_by_drone)
  
  for (drone_key in names(distance_sum_by_drone)) {
    count <- frame_count_by_drone[[drone_key]]
    if (count > 0) {
      overall_distances[drone_key] <- distance_sum_by_drone[[drone_key]] / count
    }
  }
  
  if (length(overall_distances) == 0) {
    stop("No drones processed")
  }
  
  # Find most isolated drone
  most_isolated_idx <- which.max(overall_distances)
  most_isolated_id <- as.integer(names(overall_distances)[most_isolated_idx])
  max_distance <- overall_distances[most_isolated_idx]
  
  cat(sprintf("\nMost isolated drone: %d (avg distance: %.2f)\n", most_isolated_id, max_distance), file = stderr())
  
  # Get serial number
  serial <- as.integer(mapping[as.character(most_isolated_id)])
  
  # Generate bar chart
  tryCatch({
    drone_ids <- as.integer(names(overall_distances))
    serials <- sapply(drone_ids, function(id) as.integer(mapping[as.character(id)]))
    distances <- as.numeric(overall_distances)
    
    sort_idx <- order(distances, decreasing = TRUE)
    sorted_serials <- sprintf("%06d", serials[sort_idx])
    sorted_distances <- distances[sort_idx]
    sorted_ids <- drone_ids[sort_idx]
    
    colors <- ifelse(sorted_ids == most_isolated_id, "#d64545", "#5b8ff9")
    
    plot_path <- file.path(extract_dir, "stage4_distance_chart.png")
    png(plot_path, width = max(1000, length(sorted_serials) * 40), height = 600, res = 100)
    
    barplot(sorted_distances,
            names.arg = sorted_serials,
            col = colors,
            las = 2,
            cex.axis = 0.8,
            main = "Drone Isolation by Serial Number",
            xlab = "Serial Number",
            ylab = "Average Distance to Other Drones")
    
    legend("topright",
           legend = c("Most Isolated", "Other Drones"),
           fill = c("#d64545", "#5b8ff9"))
    
    dev.off()
    cat(sprintf("Bar chart saved to %s\n", plot_path), file = stderr())
  }, error = function(e) {
    cat(sprintf("Warning: Could not create chart: %s\n", e$message), file = stderr())
  })
  
  # Output result
  cat(sprintf("%06d\n", serial %% 1000000))
}

main()
