#!/usr/bin/env python3
"""
make_plots.py - build the archive figures from tandh.csv and events.csv.

Outputs into plots/:
    temperature_humidity.png   Aug 2023 - Feb 2024, the sensor era
    actogram.png               day/night phase per date, whole archive
    restarts.png               board restarts per week
    coverage.png               which periods have data, and the gaps

PNGs, because GitHub renders those inline in the README. Run
tools/parse_logs.py first.
"""

import csv
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

OUT = "plots"
FMT = "%Y-%m-%d %H:%M:%S"

INK = "#1a1a1a"
TEMP_C = "#b3423f"
RH_C = "#3a6ea5"
DAY_C = "#e8b62c"
NIGHT_C = "#2f3b52"
GRID = "#d8d8d8"


def style(ax):
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK, labelsize=9)


def read_tandh():
    rows = []
    with open("tandh.csv") as fh:
        for r in csv.DictReader(fh):
            try:
                t = datetime.strptime(r["timestamp"], FMT)
                rows.append((t, float(r["temp_c"]), float(r["humidity_pct"])))
            except (ValueError, TypeError):
                continue
    rows.sort()
    return rows


def read_events():
    rows = []
    with open("events.csv") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    return rows


def plot_tandh(rows):
    if not rows:
        return
    # Break the line across gaps, otherwise matplotlib draws a straight
    # diagonal across weeks of missing data and it reads as real signal.
    GAP = timedelta(hours=2)
    ts, temp, rh = [], [], []
    prev = None
    for t, c, h in rows:
        if prev is not None and t - prev > GAP:
            ts.append(t); temp.append(float("nan")); rh.append(float("nan"))
        ts.append(t); temp.append(c); rh.append(h)
        prev = t

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    a1.plot(ts, temp, color=TEMP_C, linewidth=0.6)
    a1.set_ylabel("temperature (°C)", color=INK, fontsize=10)
    a1.set_title(
        f"Incubator temperature and humidity — {ts[0]:%b %Y} to {ts[-1]:%b %Y}"
        f"  ({len(rows):,} readings)",
        color=INK, fontsize=12, loc="left", pad=12,
    )
    a2.plot(ts, rh, color=RH_C, linewidth=0.6)
    a2.set_ylabel("relative humidity (%)", color=INK, fontsize=10)
    for a in (a1, a2):
        style(a)
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/temperature_humidity.png", dpi=150)
    plt.close(fig)


def plot_actogram(events):
    """One row per calendar date; a bar from each transition to the next."""
    trans = []
    for r in events:
        if r["kind"] in ("day", "night") and r["clock_ok"] == "1" and r["timestamp"]:
            try:
                trans.append((datetime.strptime(r["timestamp"], FMT), r["kind"]))
            except ValueError:
                continue
    if not trans:
        return
    trans.sort()

    fig, ax = plt.subplots(figsize=(12, 7))
    for (t, kind) in trans:
        y = mdates.date2num(t.date())
        hour = t.hour + t.minute / 60 + t.second / 3600
        ax.barh(y, 0.35, left=hour, height=0.9,
                color=DAY_C if kind == "day" else NIGHT_C, linewidth=0)

    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 4))
    ax.set_xlabel("hour of day", color=INK, fontsize=10)
    ax.yaxis_date()
    ax.yaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.invert_yaxis()
    ax.set_title(
        f"Light phase transitions — {len(trans):,} logged\n"
        "gold = to day, navy = to night",
        color=INK, fontsize=12, loc="left", pad=12,
    )
    style(ax)
    fig.tight_layout()
    fig.savefig(f"{OUT}/actogram.png", dpi=150)
    plt.close(fig)


def plot_restarts(events):
    """Restarts per week. Count only the 'out' channel - every channel writes
    a header at boot, so counting all of them inflates the figure ~4x."""
    weeks = Counter()
    for r in events:
        if r["kind"] != "restart_marker" or r["channel"] != "out":
            continue
        try:
            d = datetime.strptime(r["retrieved"], "%Y-%m-%d")
        except ValueError:
            continue
        weeks[d - timedelta(days=d.weekday())] += 1
    if not weeks:
        return

    xs = sorted(weeks)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(xs, [weeks[x] for x in xs], width=5, color=NIGHT_C, linewidth=0)
    ax.set_ylabel("restarts", color=INK, fontsize=10)
    ax.set_title(
        f"Board restarts, by retrieval date — {sum(weeks.values()):,} total",
        color=INK, fontsize=12, loc="left", pad=12,
    )
    style(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/restarts.png", dpi=150)
    plt.close(fig)


def plot_coverage(tandh, events):
    """Which calendar days have data of each kind."""
    th_days = {t.date() for t, _, _ in tandh}
    ev_days = set()
    for r in events:
        if r["timestamp"] and r["clock_ok"] == "1":
            try:
                ev_days.add(datetime.strptime(r["timestamp"], FMT).date())
            except ValueError:
                pass
    if not (th_days or ev_days):
        return

    lo, hi = min(th_days | ev_days), max(th_days | ev_days)
    fig, ax = plt.subplots(figsize=(12, 2.4))
    for days, y, c, label in (
        (ev_days, 1, NIGHT_C, "event log"),
        (th_days, 0, TEMP_C, "temp / humidity"),
    ):
        ax.barh([y] * len(days), 1, left=sorted(days), height=0.6,
                color=c, linewidth=0)
        ax.text(-0.01, y, label, transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=9, color=INK)

    ax.set_yticks([])
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlim(lo - timedelta(days=10), hi + timedelta(days=10))
    ax.set_title(
        f"Archive coverage — {lo} to {hi}  "
        f"({len(th_days)} days of T/H, {len(ev_days)} days of events)",
        color=INK, fontsize=12, loc="left", pad=12,
    )
    style(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/coverage.png", dpi=150)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    tandh = read_tandh()
    events = read_events()
    plot_tandh(tandh)
    plot_actogram(events)
    plot_restarts(events)
    plot_coverage(tandh, events)
    print(f"wrote {len(os.listdir(OUT))} files to {OUT}/")


if __name__ == "__main__":
    main()
