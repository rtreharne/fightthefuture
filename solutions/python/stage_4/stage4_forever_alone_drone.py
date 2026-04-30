#!/usr/bin/env python3
import csv
import sys
import zipfile
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np
from PIL import Image


DIGIT_FONT = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "001", "001", "001"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
}

SCALE = 2
TIE_EPS = 1e-9


def clamp(value, low, high):
    return max(low, min(high, value))


def unzip_dataset(zip_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(output_dir)


def load_mapping(csv_path):
    mapping = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            mapping[int(row["drone_id"])] = int(row["serial_number"])
    return mapping


def find_drone_centers(image_array):
    # Drones are filled with exact RGB(70,122,213).
    mask = (
        (image_array[:, :, 0] == 70)
        & (image_array[:, :, 1] == 122)
        & (image_array[:, :, 2] == 213)
    )
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    centers = []

    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue
            queue = deque([(x, y)])
            visited[y, x] = True
            pts_x = []
            pts_y = []
            while queue:
                cx, cy = queue.popleft()
                pts_x.append(cx)
                pts_y.append(cy)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((nx, ny))
            area = len(pts_x)
            # Supports both old (r~8) and new (r~14) stage image styles.
            if 120 <= area <= 980:
                centers.append((int(round(sum(pts_x) / area)), int(round(sum(pts_y) / area))))
    return centers


def render_id_template(drone_id):
    text = str(drone_id)
    width = len(text) * 8
    height = 10
    template = np.zeros((height, width), dtype=np.uint8)
    cursor = 0
    for char in text:
        pattern = DIGIT_FONT[char]
        for row_i, row_bits in enumerate(pattern):
            for col_i, bit in enumerate(row_bits):
                if bit != "1":
                    continue
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        template[row_i * SCALE + sy, cursor + col_i * SCALE + sx] = 1
        cursor += 8
    return template


ID_TEMPLATES = {drone_id: render_id_template(drone_id) for drone_id in range(1, 100)}


def decode_drone_id(center, black_mask, width, height):
    cx, cy = center
    best_id = None
    best_score = -1.0

    for drone_id in range(1, 100):
        template = ID_TEMPLATES[drone_id]
        tw = template.shape[1]
        th = template.shape[0]

        candidates = [
            # New style: label centered in circle.
            (clamp(cx - (tw // 2), 0, width - tw), clamp(cy - (th // 2), 0, height - th)),
            # Legacy style: label above circle.
            (clamp(cx - (len(str(drone_id)) * 4), 0, width - tw), clamp(cy - 20, 0, height - th)),
        ]
        score = -1.0
        for x, y in candidates:
            roi = black_mask[y:y + th, x:x + tw]
            if roi.shape != template.shape:
                continue
            matches = (roi == template).sum()
            score = max(score, matches / template.size)
        if score > best_score:
            best_score = score
            best_id = drone_id

    return best_id, best_score


def average_distance_to_others(point, others):
    if not others:
        return 0.0
    px, py = point
    total = 0.0
    for ox, oy in others:
        dx = px - ox
        dy = py - oy
        total += ((dx * dx) + (dy * dy)) ** 0.5
    return total / len(others)


def compute_scores(sum_by_id, seen_by_id, drone_ids):
    scores = {}
    for drone_id in drone_ids:
        seen = seen_by_id.get(drone_id, 0)
        if seen > 0:
            scores[drone_id] = sum_by_id[drone_id] / seen
    return scores


def choose_winner(scores, drone_ids, eps=TIE_EPS):
    winner = min(drone_ids)
    winner_score = -1.0
    for drone_id in sorted(drone_ids):
        score = scores.get(drone_id, 0.0)
        if score > winner_score + eps:
            winner = drone_id
            winner_score = score
        elif abs(score - winner_score) <= eps and drone_id < winner:
            winner = drone_id
            winner_score = score
    return winner, winner_score


def save_average_distance_bar_chart(mapping, scores, target_drone_id, output_path):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    ordered_ids = sorted(mapping.keys(), key=lambda drone_id: scores.get(drone_id, 0.0), reverse=True)
    labels = [f"{mapping[drone_id]:06d}" for drone_id in ordered_ids]
    values = [scores.get(drone_id, 0.0) for drone_id in ordered_ids]
    colors = ["#d64545" if drone_id == target_drone_id else "#5b8ff9" for drone_id in ordered_ids]

    fig_width = max(16, len(ordered_ids) * 0.18)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    ax.bar(range(len(ordered_ids)), values, color=colors, edgecolor="#2f2f2f", linewidth=0.25)
    ax.set_xticks(range(len(ordered_ids)))
    ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_ylabel("Average Distance To Other Drones")
    ax.set_xlabel("Drone Serial Number")
    ax.set_title("Average Drone Separation by Serial (winner highlighted)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def solve(zip_path, extract_dir):
    unzip_dataset(zip_path, extract_dir)

    mapping_path = extract_dir / "drone_serials.csv"
    images_dir = extract_dir / "images"
    mapping = load_mapping(mapping_path)

    avg_dist_sum_by_id = defaultdict(float)
    frame_count_by_id = Counter()

    image_paths = sorted(images_dir.glob("*.png"))
    for image_path in image_paths:
        image = np.array(Image.open(image_path).convert("RGB"))
        h, w, _ = image.shape
        black_mask = (
            (image[:, :, 0] < 20)
            & (image[:, :, 1] < 20)
            & (image[:, :, 2] < 20)
        ).astype(np.uint8)

        centers = find_drone_centers(image)
        detections = []
        used_ids = set()
        for center in centers:
            drone_id, score = decode_drone_id(center, black_mask, w, h)
            if drone_id is None:
                continue
            if score < 0.76:
                continue
            # Avoid duplicates from occasional OCR collisions.
            if drone_id in used_ids:
                continue
            used_ids.add(drone_id)
            detections.append((drone_id, center))

        if len(detections) < 2:
            continue

        for drone_id, point in detections:
            others = [p for other_id, p in detections if other_id != drone_id]
            mean_dist = average_distance_to_others(point, others)
            avg_dist_sum_by_id[drone_id] += mean_dist
            frame_count_by_id[drone_id] += 1

    if not frame_count_by_id:
        raise RuntimeError("No valid drone detections were made from the image set.")

    all_drone_ids = sorted(mapping.keys())
    scores = compute_scores(avg_dist_sum_by_id, frame_count_by_id, all_drone_ids)
    target_drone_id, _ = choose_winner(scores, all_drone_ids, eps=TIE_EPS)
    chart_path = extract_dir / "drone_average_distance.png"
    save_average_distance_bar_chart(mapping, scores, target_drone_id, chart_path)
    serial = mapping[target_drone_id]
    print(f"{serial:06d}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python stage4_forever_alone_drone.py <stage4_zip_path> [extract_dir]")

    zip_path = Path(sys.argv[1])
    if not zip_path.exists():
        raise SystemExit(f"ZIP file not found: {zip_path}")

    if len(sys.argv) > 2:
        extract_dir = Path(sys.argv[2])
    else:
        extract_dir = zip_path.parent / "stage4_unzipped"

    solve(zip_path, extract_dir)


if __name__ == "__main__":
    main()
