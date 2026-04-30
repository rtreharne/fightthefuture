#!/usr/bin/env python3
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def group_by_district(rows):
    signals = defaultdict(list)
    codes = defaultdict(set)
    for row in rows:
        district = row.get("district")
        if not district:
            continue
        signals[district].append(float(row.get("signal_strength", 0.0)))
        if row.get("district_code"):
            codes[district].add(int(float(row["district_code"])))
    return signals, codes


def welch_stats(a, b):
    if len(a) < 2 or len(b) < 2:
        return 0.0, 1.0
    mean_a, mean_b = statistics.mean(a), statistics.mean(b)
    var_a, var_b = statistics.variance(a), statistics.variance(b)
    se = math.sqrt((var_a / len(a)) + (var_b / len(b)))
    if se == 0:
        return 0.0, 1.0
    t = abs((mean_a - mean_b) / se)
    p = math.erfc(t / math.sqrt(2.0))  # fast normal-approx two-sided p
    return t, p


def pick_abnormal_district(signals):
    districts = sorted(signals)
    ranked = []
    for district in districts:
        pairs = [welch_stats(signals[district], signals[other]) for other in districts if other != district]
        if not pairs:
            continue
        n_tests = len(pairs)
        corrected_ps = [min(1.0, p * n_tests) for _, p in pairs]  # Bonferroni correction
        sig_count = sum(1 for p in corrected_ps if p < 0.05)
        avg_abs_t = statistics.mean(t for t, _ in pairs)
        med_p = statistics.median(corrected_ps)
        ranked.append((sig_count, avg_abs_t, -med_p, district))
    if not ranked:
        return None, []
    ranked.sort(reverse=True)
    return ranked[0][3], ranked


def save_boxplot(signals, codes, abnormal_district, output_path):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except ImportError:
        return

    districts = sorted(signals)
    data = [signals[d] for d in districts]
    colors = ["#d64545" if d == abnormal_district else "#5b8ff9" for d in districts]
    pos = list(range(1, len(districts) + 1))

    fig, ax = plt.subplots(figsize=(max(14, len(districts) * 0.6), 6))
    bp = ax.boxplot(data, positions=pos, widths=0.7, patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks(pos)
    labels = []
    for district in districts:
        code_values = sorted(code for code in codes.get(district, set()) if code > 0)
        code_label = str(code_values[0]) if code_values else "?"
        labels.append(f"{district} [{code_label}]")
    ax.set_xticklabels(labels, rotation=60, ha="right")
    ax.set_ylabel("Signal Strength")
    ax.set_xlabel("District")
    ax.set_title(f"Stage 3 Signal Pattern (identified: {abnormal_district})")
    ax.legend(
        handles=[
            Patch(facecolor="#d64545", alpha=0.7, label="Identified district"),
            Patch(facecolor="#5b8ff9", alpha=0.7, label="Other districts"),
        ],
        loc="upper right",
    )
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def default_plot_path(dataset_path):
    src = Path(dataset_path)
    return str(src.with_name(f"{src.stem}_boxplot.png"))


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python stage3_signal_readings.py <dataset_path> [plot_output_path]")

    dataset_path = sys.argv[1]
    plot_path = sys.argv[2] if len(sys.argv) > 2 else default_plot_path(dataset_path)
    rows = load_rows(dataset_path)
    if not rows:
        raise SystemExit("Dataset is empty")

    signals, codes = group_by_district(rows)
    abnormal_district, ranked = pick_abnormal_district(signals)
    if not abnormal_district:
        raise SystemExit("Could not identify abnormal district")

    district_codes = {c for c in codes.get(abnormal_district, set()) if c > 0}
    if len(district_codes) != 1:
        raise SystemExit("Abnormal district code is missing or inconsistent")

    print("Top post-hoc candidates (Bonferroni-corrected):", file=sys.stderr)
    for sig, avg_t, neg_med_p, district in ranked[:5]:
        print(
            f"  {district}: significant_pairs={sig}, avg_|t|={avg_t:.3f}, median_p≈{-neg_med_p:.4f}",
            file=sys.stderr,
        )
    print(f"Identified district: {abnormal_district}", file=sys.stderr)

    save_boxplot(signals, codes, abnormal_district, plot_path)
    print(f"{next(iter(district_codes)) % 1_000_000:06d}")


if __name__ == "__main__":
    main()
