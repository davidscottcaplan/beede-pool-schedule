import io
import math
from datetime import date, timedelta

import matplotlib
matplotlib.use("Agg")  # non-interactive backend required for server use
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from config import DISPLAY_START_MIN, DISPLAY_END_MIN, SLOT_MINUTES, POOL_HOURS

# Colour palette (matches reference image)
COLOR_AVAILABLE = "#AED6F1"   # light blue
COLOR_BLOCKED   = "#F1948A"   # salmon red
COLOR_CLOSED    = "#D5D8DC"   # light grey

N_SLOTS = (DISPLAY_END_MIN - DISPLAY_START_MIN) // SLOT_MINUTES  # 32 half-hour slots
N_LANES = 8


def _build_day_grid(day_schedule: dict, weekday: int) -> np.ndarray:
    """
    Return (N_SLOTS, N_LANES) int array:  0=available  1=blocked  2=closed
    day_schedule: {'lane_1': [events], ..., 'lane_8': [events]}
    """
    grid = np.zeros((N_SLOTS, N_LANES), dtype=int)

    pool_hours = POOL_HOURS.get(weekday)
    if pool_hours is None:
        grid[:] = 2          # pool closed all day
        return grid

    pool_open, pool_close = pool_hours

    # Mark slots before opening / after closing as grey
    open_slot  = math.ceil((pool_open  - DISPLAY_START_MIN) / SLOT_MINUTES)
    close_slot = (pool_close - DISPLAY_START_MIN) // SLOT_MINUTES
    if open_slot > 0:
        grid[:open_slot, :] = 2
    if close_slot < N_SLOTS:
        grid[close_slot:, :] = 2

    # Overlay blocked (red) events
    for lane_num in range(1, N_LANES + 1):
        col = lane_num - 1
        for ev in day_schedule.get(f"lane_{lane_num}", []):
            s0 = (ev["start"] - DISPLAY_START_MIN) // SLOT_MINUTES
            s1 = math.ceil((ev["end"] - DISPLAY_START_MIN) / SLOT_MINUTES)
            for s in range(max(0, s0), min(N_SLOTS, s1)):
                if grid[s, col] != 2:          # don't paint over closed
                    grid[s, col] = 1

    return grid


def create_weekly_image(schedule: dict, week_start: date) -> bytes:
    """
    schedule: {date_iso: {'lane_1': [...], ..., 'lane_8': [...]}}
    Returns PNG bytes ready to embed or serve.
    """
    week_end = week_start + timedelta(days=6)

    cmap = mcolors.ListedColormap([COLOR_AVAILABLE, COLOR_BLOCKED, COLOR_CLOSED])
    norm = mcolors.BoundaryNorm([0, 0.5, 1.5, 2.5], cmap.N)

    fig, axes = plt.subplots(
        1, 7, figsize=(18, 9), sharey=True,
        gridspec_kw={"wspace": 0.04},
    )

    # ── Title ────────────────────────────────────────────────────────────────
    fig.text(
        0.5, 0.99,
        "Beede Lap Pool Lane Availability Guide",
        ha="center", va="top", fontsize=13, fontweight="bold",
    )
    fig.text(
        0.5, 0.955,
        "Blue = likely free for lap swim;   Red = scheduled/blocked;   Gray = pool closed",
        ha="center", va="top", fontsize=9, color="#555555",
    )

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day_idx in range(7):
        ax  = axes[day_idx]
        day = week_start + timedelta(days=day_idx)
        grid = _build_day_grid(
            schedule.get(day.isoformat(), {}),
            day.weekday(),
        )

        ax.pcolormesh(
            grid,
            cmap=cmap, norm=norm,
            edgecolors="white", linewidth=0.3,
        )

        ax.set_xlim(0, N_LANES)
        ax.set_ylim(N_SLOTS, 0)          # inverted: slot 0 at top = earliest time

        # ── Column header ────────────────────────────────────────────────────
        ax.set_title(
            f"{day_names[day_idx]}\n{day.strftime('%b %-d')}",
            fontsize=9, pad=4,
        )

        # ── X axis (lane numbers) ────────────────────────────────────────────
        ax.set_xticks(np.arange(N_LANES) + 0.5)
        ax.set_xticklabels([str(i) for i in range(1, N_LANES + 1)], fontsize=8)
        ax.xaxis.set_tick_params(length=0)
        ax.set_xlabel("Lane", fontsize=8, labelpad=3)

        # ── Border ──────────────────────────────────────────────────────────
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color("#aaaaaa")

    # ── Y axis (shared, left panel only) ────────────────────────────────────
    ax0 = axes[0]
    hour_ticks = list(range(0, N_SLOTS + 1, 2))  # every 2 slots = 1 hour
    ax0.set_yticks(hour_ticks)

    def _slot_to_label(slot: int) -> str:
        total = DISPLAY_START_MIN + slot * SLOT_MINUTES
        h, m  = divmod(total, 60)
        period = "AM" if h < 12 else "PM"
        h12    = h % 12 or 12
        return f"{h12:02d}:{m:02d} {period}"

    ax0.set_yticklabels([_slot_to_label(t) for t in hour_ticks], fontsize=7)
    ax0.yaxis.set_tick_params(length=2, pad=2)
    ax0.set_ylabel("Time of Day", fontsize=9, labelpad=4)

    # ── Week label (bottom centre) ───────────────────────────────────────────
    week_label = (
        f"Week of {week_start.strftime('%B %-d')}–"
        f"{week_end.strftime('%-d, %Y')}"
    )
    fig.text(0.5, 0.01, week_label, ha="center", fontsize=10, style="italic")

    plt.subplots_adjust(top=0.88, bottom=0.07, left=0.06, right=0.99)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
