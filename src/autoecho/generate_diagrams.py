"""High-fidelity, novice-friendly conceptual diagrams for the Auto-Echo
dissertation. One coherent style, aligned with the delivered method:
K-Means + Silhouette COUNTS the memory levels and change-point LOCALISES each
cache's capacity (no manual penalty), validated across architectures.

Run:  python -m autoecho.generate_diagrams
Writes PNGs to ../../data/ (referenced from docs/Draft_Dissertation.md).
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]

C = {
    "cpu": "#2C3E50", "l1": "#3498DB", "l2": "#2980B9", "l3": "#1ABC9C",
    "dram": "#16A085", "bg": "#FFFFFF", "text": "#34495E", "arrow": "#7F8C8D",
    "node": "#ECF0F1", "accent": "#E74C3C", "good": "#27AE60", "muted": "#BDC3C7",
}


def _shadow():
    return [pe.SimplePatchShadow(offset=(2, -2), alpha=0.18, shadow_rgbFace="black"),
            pe.Normal()]


def _box(ax, xy, w, h, text, fc, tc="white", dashed=False, fs=12, title=None):
    box = patches.FancyBboxPatch(xy, w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                 linewidth=1.5, edgecolor=fc, facecolor=fc,
                                 linestyle="--" if dashed else "-", path_effects=_shadow())
    ax.add_patch(box)
    cx, cy = xy[0] + w / 2, xy[1] + h / 2
    if title:
        ax.text(cx, xy[1] + h - 0.34, title, ha="center", va="center",
                color=tc, fontweight="bold", fontsize=fs + 1)
        ax.text(cx, cy - 0.22, text, ha="center", va="center", color=tc, fontsize=fs - 1)
    else:
        ax.text(cx, cy, text, ha="center", va="center", color=tc,
                fontweight="bold", fontsize=fs)


def _arrow(ax, a, b, color=None, lw=2.5):
    ax.add_patch(patches.FancyArrowPatch(
        a, b, arrowstyle="-|>,head_width=4,head_length=7",
        color=color or C["arrow"], lw=lw, mutation_scale=1))


def _save(fig, path):
    plt.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=C["bg"])
    plt.close(fig)
    print(f"  saved {os.path.basename(path)}")


# 1 --------------------------------------------------------------------------
def hierarchy(path):
    """General CPU memory hierarchy: faster+smaller near the CPU, slower+larger
    below. A concept figure, not machine-specific."""
    fig, ax = plt.subplots(figsize=(11, 6.6), facecolor=C["bg"])
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.7); ax.axis("off")
    tiers = [
        ("CPU core / registers", "instant", C["cpu"], 4.6, 6.0),
        ("L1 cache", "tens of KB  ·  ~1 ns", C["l1"], 5.2, 5.0),
        ("L2 cache", "hundreds of KB–MB  ·  ~4–10 ns", C["l2"], 5.8, 4.0),
        ("L3 cache", "tens of MB  ·  ~15–40 ns", C["l3"], 6.4, 3.0),
        ("Main memory (DRAM)", "many GB  ·  ~100+ ns", C["dram"], 7.0, 2.0),
    ]
    for label, sub, col, w, y in tiers:
        _box(ax, (5.5 - w / 2, y), w, 0.9, f"{label}\n{sub}", col, fs=12)
    _arrow(ax, (0.8, 6.3), (0.8, 2.2), color=C["text"], lw=2)
    ax.text(0.45, 4.2, "slower", rotation=90, va="center", ha="center",
            color=C["text"], fontsize=11, style="italic")
    _arrow(ax, (10.2, 2.2), (10.2, 6.3), color=C["text"], lw=2)
    ax.text(10.55, 4.2, "smaller", rotation=90, va="center", ha="center",
            color=C["text"], fontsize=11, style="italic")
    ax.text(5.5, 7.35, "The CPU memory hierarchy: each level down is bigger but slower",
            ha="center", fontsize=14, fontweight="bold", color=C["cpu"])
    ax.text(5.5, 1.1, "Auto-Echo discovers where these levels sit — their sizes and "
            "speeds — from ordinary user-space code,\nwith no special privileges and "
            "no knowledge of the machine.", ha="center", fontsize=11, color=C["text"])
    _save(fig, path)


# 2 --------------------------------------------------------------------------
def staircase(path):
    """THE core intuition: as the working set grows past each cache, average
    access latency jumps up — a staircase whose steps mark the cache sizes."""
    fig, ax = plt.subplots(figsize=(11, 6.2), facecolor=C["bg"])
    caps = [0.13, 12.0, 40.0]           # MB boundaries (L1, L2, L3)
    lats = [1.5, 9.0, 30.0, 120.0]      # ns plateaus
    xs = np.geomspace(0.008, 512, 600)  # MB
    y = np.piecewise(xs,
                     [xs <= caps[0],
                      (xs > caps[0]) & (xs <= caps[1]),
                      (xs > caps[1]) & (xs <= caps[2]),
                      xs > caps[2]],
                     lats)
    ax.set_xscale("log"); ax.set_yscale("log")
    bands = [(0.008, caps[0], C["l1"]), (caps[0], caps[1], C["l2"]),
             (caps[1], caps[2], C["l3"]), (caps[2], 512, C["dram"])]
    labels = ["fits in L1\n→ fastest", "spills to L2", "spills to L3",
              "spills to DRAM\n→ slowest"]
    for (lo, hi, col), lab, yv in zip(bands, labels, lats):
        ax.axvspan(lo, hi, color=col, alpha=0.14)
        ax.text(np.sqrt(lo * hi), yv * 1.22, lab, ha="center", va="bottom",
                fontsize=10.5, color=col, fontweight="bold")
    ax.plot(xs, y, color=C["cpu"], lw=3, solid_joinstyle="round")
    for cap in caps:
        ax.axvline(cap, color=C["accent"], ls="--", lw=1.6, alpha=0.9)
        txt = f"  size = {cap*1024:.0f} KB" if cap < 1 else f"  size = {cap:.0f} MB"
        ax.text(cap, 165, txt, color=C["accent"], fontsize=9, va="top", ha="left",
                fontweight="bold")
    ax.set_xlabel("Working-set size  (bigger →)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average access latency (ns)  (slower →)", fontsize=12, fontweight="bold")
    ax.set_title("Why latency reveals the cache sizes: the memory “staircase”",
                 fontsize=14, fontweight="bold", color=C["cpu"], pad=30)
    ax.text(0.5, 1.05, "Each step up happens exactly when the data outgrows a cache — "
            "so the step locations ARE the cache capacities.",
            transform=ax.transAxes, ha="center", fontsize=10.5, color=C["text"])
    ax.set_ylim(1, 230)
    ax.grid(True, which="both", alpha=0.2)
    _save(fig, path)


# 3 --------------------------------------------------------------------------
def pointer_chase(path):
    """Why pointer-chasing is used: a data-dependent random chain defeats the
    hardware prefetcher, so the timer sees the TRUE memory latency."""
    fig, ax = plt.subplots(figsize=(11, 6.4), facecolor=C["bg"])
    ax.set_xlim(0, 11); ax.set_ylim(0, 7.2); ax.axis("off")
    ax.text(5.5, 6.9, "How Auto-Echo measures true latency", ha="center",
            fontsize=15, fontweight="bold", color=C["cpu"])

    def cells(y, order, col, tag, good):
        for i in range(8):
            b = patches.FancyBboxPatch((2.1 + i * 0.9, y), 0.78, 0.78,
                                       boxstyle="round,pad=0,rounding_size=0.08",
                                       linewidth=1.4, edgecolor=C["text"], facecolor=C["node"],
                                       path_effects=_shadow())
            ax.add_patch(b)
            ax.text(2.49 + i * 0.9, y + 0.39, str(i), ha="center", va="center",
                    fontsize=10, color=C["text"], fontweight="bold")
        for a, b in zip(order, order[1:]):
            x1, x2 = 2.49 + a * 0.9, 2.49 + b * 0.9
            r = 0.5 if b > a else -0.5
            ax.add_patch(patches.FancyArrowPatch(
                (x1, y + 0.78), (x2, y + 0.78), connectionstyle=f"arc3,rad={r}",
                arrowstyle="-|>,head_width=3,head_length=6", color=col, lw=1.7,
                mutation_scale=1))
        ax.text(1.9, y + 0.39, tag, ha="right", va="center", fontsize=11,
                fontweight="bold", color=col)
        note = ("PROBLEM:  prefetcher guesses the next address → hides real latency"
                if not good else
                "WORKS:  next address is unknown until the current load returns →\n"
                "prefetcher cannot run ahead, so the true latency is exposed")
        ax.text(5.55, y - (0.42 if not good else 0.6), note,
                ha="center", va="top", fontsize=10.3,
                color=(C["accent"] if not good else C["good"]))

    cells(5.3, list(range(8)), C["muted"], "Sequential\n(naive)", good=False)
    cells(3.0, [0, 4, 1, 6, 2, 7, 3, 5], C["accent"], "Random chain\n(Auto-Echo)", good=True)

    _box(ax, (1.8, 0.3), 7.9, 1.05,
         "Then time 1,000,000 dependent hops together and divide by 1,000,000\n"
         "→ recovers sub-nanosecond latency despite a coarse (~42 ns) hardware timer",
         C["cpu"], fs=11)
    _save(fig, path)


# 4 --------------------------------------------------------------------------
def pipeline(path):
    """The delivered pipeline: probe → calibrate → COUNT (silhouette) →
    LOCALISE (change-point) → validate."""
    fig, ax = plt.subplots(figsize=(13, 4.4), facecolor=C["bg"])
    ax.set_xlim(0, 13); ax.set_ylim(0, 4.4); ax.axis("off")
    ax.text(6.5, 4.05, "The Auto-Echo pipeline", ha="center", fontsize=15,
            fontweight="bold", color=C["cpu"])
    steps = [
        ("1 · Probe", "sweep working-set\nsizes by pointer\nchasing", C["cpu"]),
        ("2 · Calibrate", "convert timer ticks\nto nanoseconds\nat runtime", C["l1"]),
        ("3 · Count", "K-Means + Silhouette\ncount the levels\n(works on any CPU)", C["l2"]),
        ("4 · Localise", "change-point finds\neach cache's size\n(no manual knob)", C["l3"]),
        ("5 · Validate", "check sizes against\nthe OS-reported\nground truth", C["dram"]),
    ]
    w, gap = 2.2, 0.35
    for i, (title, body, col) in enumerate(steps):
        x = 0.4 + i * (w + gap)
        _box(ax, (x, 1.0), w, 1.95, body, col, fs=10, title=title)
        if i < len(steps) - 1:
            _arrow(ax, (x + w + 0.02, 1.97), (x + w + gap - 0.02, 1.97))
    ax.text(6.5, 0.45, "“Clustering counts the levels; change-point locates them” — "
            "the count adapts to the machine, so one tool works on Mac, Linux and x86.",
            ha="center", fontsize=10.5, color=C["text"])
    _save(fig, path)


# 5 --------------------------------------------------------------------------
def crossplatform(path):
    """One method, different machines: the number of levels adapts to the
    hardware (4 on x86, 3 on Apple M1, 2 on a virtual machine)."""
    fig, ax = plt.subplots(figsize=(12, 5.8), facecolor=C["bg"])
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")
    ax.text(6, 5.6, "Same method, any machine: the level count adapts to the hardware",
            ha="center", fontsize=14, fontweight="bold", color=C["cpu"])
    panels = [
        ("Intel / AMD (x86)", ["L1", "L2", "L3", "DRAM"],
         [C["l1"], C["l2"], C["l3"], C["dram"]], "4 levels"),
        ("Apple M1 (ARM)", ["L1", "L2 + SLC", "DRAM"],
         [C["l1"], C["l2"], C["dram"]], "3 levels\n(L2 & SLC blur together)"),
        ("Virtual machine", ["L1", "DRAM"],
         [C["l1"], C["dram"]], "2 levels\n(virtual timer flattens the rest)"),
    ]
    pw = 3.4
    for p, (title, levels, cols, note) in enumerate(panels):
        x0 = 0.6 + p * (pw + 0.55)
        ax.text(x0 + pw / 2, 4.9, title, ha="center", fontsize=12,
                fontweight="bold", color=C["cpu"])
        n = len(levels)
        bh = 3.1 / n
        for i, (lv, col) in enumerate(zip(levels, cols)):
            y = 1.5 + (n - 1 - i) * bh
            _box(ax, (x0, y), pw, bh - 0.12, lv, col, fs=11)
        ax.text(x0 + pw / 2, 1.05, note, ha="center", va="top", fontsize=10,
                color=C["accent"], fontweight="bold")
    _save(fig, path)


def main():
    out = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(out, exist_ok=True)
    print("Generating Auto-Echo dissertation diagrams...")
    hierarchy(os.path.join(out, "diagram_hierarchy.png"))
    staircase(os.path.join(out, "diagram_staircase.png"))
    pointer_chase(os.path.join(out, "diagram_pointer_chase.png"))
    pipeline(os.path.join(out, "diagram_pipeline.png"))
    crossplatform(os.path.join(out, "diagram_crossplatform.png"))
    print("Done.")


if __name__ == "__main__":
    main()
