#!/usr/bin/env python3
"""
Helper: Extract drone IDs and positions from a single image.
"""
import sys
from PIL import Image
import numpy as np

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
MIN_SCORE = 0.76
MAX_DRONE_ID = 20


def detect_blue_circles(image_path):
    """Detect blue circles and extract positions."""
    img = Image.open(image_path).convert('RGB')
    arr = np.array(img, dtype=np.uint8)
    
    # Find blue pixels: R < 100, G < 150, B > 150
    blue_mask = (arr[:, :, 0] < 100) & (arr[:, :, 1] < 150) & (arr[:, :, 2] > 150)
    
    circles = []
    visited = set()
    
    for y in range(blue_mask.shape[0]):
        for x in range(blue_mask.shape[1]):
            if blue_mask[y, x] and (y, x) not in visited:
                # BFS to find circle region
                queue = [(y, x)]
                pixels = []
                while queue:
                    cy, cx = queue.pop(0)
                    if (cy, cx) in visited or cy < 0 or cy >= blue_mask.shape[0] or cx < 0 or cx >= blue_mask.shape[1]:
                        continue
                    if not blue_mask[cy, cx]:
                        continue
                    visited.add((cy, cx))
                    pixels.append((cx, cy))
                    queue.extend([(cy+dy, cx+dx) for dy, dx in [(0,1), (0,-1), (1,0), (-1,0)]])
                
                if len(pixels) > 50:
                    cx = sum(p[0] for p in pixels) / len(pixels)
                    cy = sum(p[1] for p in pixels) / len(pixels)
                    circles.append((cx, cy))
    
    # Sort by position
    circles.sort(key=lambda c: (c[1], c[0]))
    return circles


def render_template(drone_id):
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
                y = row_i * SCALE
                x = cursor + col_i * SCALE
                template[y:y + SCALE, x:x + SCALE] = 1
        cursor += 8
    return template


ID_TEMPLATES = {drone_id: render_template(drone_id) for drone_id in range(1, MAX_DRONE_ID + 1)}


def clamp(value, low, high):
    return max(low, min(high, value))


def decode_drone_id(center, black_mask, width, height):
    cx = int(round(center[0]))
    cy = int(round(center[1]))
    best_id = None
    best_score = -1.0

    for drone_id, template in ID_TEMPLATES.items():
        tw = template.shape[1]
        th = template.shape[0]
        candidates = [
            (clamp(cx - (tw // 2), 0, width - tw), clamp(cy - (th // 2), 0, height - th)),
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 helper_extract_drone_v2.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    # Detect circles
    circles = detect_blue_circles(image_path)
    
    if not circles:
        print("No circles detected.")
        sys.exit(1)
    
    arr = np.array(Image.open(image_path).convert('RGB'), dtype=np.uint8)
    h, w, _ = arr.shape
    black_mask = (
        (arr[:, :, 0] < 20)
        & (arr[:, :, 1] < 20)
        & (arr[:, :, 2] < 20)
    ).astype(np.uint8)

    print(f"Detected {len(circles)} circle(s):")
    print("drone_id,x,y")

    # Decode ID text from each circle.
    decoded = []
    for cx, cy in circles:
        drone_id, score = decode_drone_id((cx, cy), black_mask, w, h)
        if drone_id is None or score < MIN_SCORE:
            continue
        decoded.append((drone_id, score, cx, cy))

    # Resolve duplicate ID collisions by keeping best OCR score per ID.
    best_by_id = {}
    for drone_id, score, cx, cy in decoded:
        prev = best_by_id.get(drone_id)
        if prev is None or score > prev[0]:
            best_by_id[drone_id] = (score, cx, cy)

    for drone_id in sorted(best_by_id):
        _, cx, cy = best_by_id[drone_id]
        print(f"{drone_id},{round(cx)},{round(cy)}")


if __name__ == '__main__':
    main()
