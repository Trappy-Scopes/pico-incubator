#!/usr/bin/env python3
"""
make_plots.py - build the archive figures from tandh.csv and events.csv.

Outputs into plots/:
    temperature_humidity.png   Aug 2023 - Feb 2024, the sensor era
    actogram.png               day/night phase per date, whole archive
    restarts.png               board restarts per week
    instrument_temperature.png the controlled incubator on its own axis
    stability.png              s.d. vs averaging window, diurnal profile
    coverage.png               which periods have data, and the gaps
    interactive.html           Bokeh: pan / zoom / hover over every reading

The PNGs are what the README shows - GitHub renders those inline. It will NOT
render interactive.html: HTML in a README is sanitised, and files viewed in the
repo are shown as source. Download it and open it in a browser.

Run tools/parse_logs.py first.
"""

import csv
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import numpy as np
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
    """Rows of (timestamp, sensor, temp, humidity|None). Humidity is absent for
    instrument exports that only log temperature."""
    rows = []
    with open("tandh.csv") as fh:
        for r in csv.DictReader(fh):
            try:
                t = datetime.strptime(r["timestamp"], FMT)
                temp = float(r["temp_c"])
            except (ValueError, TypeError):
                continue
            try:
                rh = float(r["humidity_pct"])
            except (ValueError, TypeError):
                rh = None
            rows.append((t, r["sensor"], temp, rh))
    rows.sort(key=lambda r: (r[1], r[0]))
    return rows


def read_events():
    rows = []
    with open("events.csv") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    return rows


def _broken(points):
    """Insert a NaN wherever there is a gap, so matplotlib does not draw a
    straight diagonal across missing weeks and make it look like signal."""
    GAP = timedelta(hours=2)
    xs, ys, prev = [], [], None
    for t, v in points:
        if prev is not None and t - prev > GAP:
            xs.append(t); ys.append(float("nan"))
        xs.append(t); ys.append(v)
        prev = t
    return xs, ys


def plot_tandh(rows):
    if not rows:
        return
    by_sensor = defaultdict(list)
    for t, sensor, temp, rh in rows:
        by_sensor[sensor].append((t, temp, rh))

    palette = [TEMP_C, "#7a4fa3", "#2e7d5b", "#c77d1a"]
    span = (min(r[0] for r in rows), max(r[0] for r in rows))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    for n, (sensor, pts) in enumerate(sorted(by_sensor.items())):
        xs, ys = _broken([(t, c) for t, c, _ in pts])
        a1.plot(xs, ys, color=palette[n % len(palette)], linewidth=0.6,
                label=f"{sensor}  ({len(pts):,})")
    a1.set_ylabel("temperature (°C)", color=INK, fontsize=10)
    a1.legend(loc="upper left", fontsize=8, frameon=False)
    a1.set_title(
        f"Incubator temperature and humidity — {span[0]:%b %Y} to {span[1]:%b %Y}"
        f"  ({len(rows):,} readings)",
        color=INK, fontsize=12, loc="left", pad=12,
    )

    any_rh = False
    for n, (sensor, pts) in enumerate(sorted(by_sensor.items())):
        wet = [(t, h) for t, _, h in pts if h is not None]
        if not wet:
            continue
        any_rh = True
        xs, ys = _broken(wet)
        a2.plot(xs, ys, color=RH_C, linewidth=0.6, label=sensor)
    a2.set_ylabel("relative humidity (%)", color=INK, fontsize=10)
    if not any_rh:
        a2.text(0.5, 0.5, "no humidity channel", transform=a2.transAxes,
                ha="center", va="center", color=INK, fontsize=10)

    for a in (a1, a2):
        style(a)
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/temperature_humidity.png", dpi=150)
    plt.close(fig)


def plot_instrument(rows):
    """The controlled incubator on its own axis. On the three-year plot its
    trace is a flat line, which hides how tight the regulation actually is."""
    pts = [(t, c) for t, sensor, c, _ in rows if sensor != "tandh1"]
    if not pts:
        return
    pts.sort()
    name = sorted({s for _, s, _, _ in rows if s != "tandh1"})[0]
    xs, ys = _broken(pts)
    vals = [v for v in ys if v == v]
    lo, hi = min(vals), max(vals)
    mean = sum(vals) / len(vals)

    fig, ax = plt.subplots(figsize=(12, 3.6))
    ax.plot(xs, ys, color=TEMP_C, linewidth=0.7)
    ax.axhline(mean, color=INK, linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_ylabel("temperature (°C)", color=INK, fontsize=10)
    ax.set_title(
        f"{name} — {len(pts):,} readings, "
        f"mean {mean:.2f} °C, range {lo:.2f}–{hi:.2f} °C",
        color=INK, fontsize=12, loc="left", pad=12,
    )
    style(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/instrument_temperature.png", dpi=150)
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
    """Restarts per month, dated from the first record of each boot.

    Count only the 'out' channel - every channel writes a header at boot, so
    counting all of them inflates the figure about fourfold. The folder name is
    only the retrieval date and is never used here.
    """
    months = Counter()
    undated = 0
    for r in events:
        if r["kind"] != "restart_marker" or r["channel"] != "out":
            continue
        if r["clock_ok"] != "1" or not r["timestamp"]:
            undated += 1
            continue
        try:
            d = datetime.strptime(r["timestamp"], FMT)
        except ValueError:
            undated += 1
            continue
        months[datetime(d.year, d.month, 1)] += 1
    if not months:
        return

    lo, hi = min(months), max(months)
    xs, cur = [], lo
    while cur <= hi:                      # keep empty months visible
        xs.append(cur)
        cur = datetime(cur.year + (cur.month == 12),
                       cur.month % 12 + 1, 1)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(xs, [months.get(x, 0) for x in xs], width=22,
           color=NIGHT_C, linewidth=0)
    ax.set_ylabel("restarts", color=INK, fontsize=10)
    ax.set_title(
        f"Board restarts per month — {sum(months.values()):,} dated"
        + (f", {undated} undatable (clock never synced)" if undated else ""),
        color=INK, fontsize=12, loc="left", pad=12,
    )
    style(ax)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    fig.savefig(f"{OUT}/restarts.png", dpi=150)
    plt.close(fig)


def plot_coverage(tandh, events):
    """Which calendar days have data of each kind."""
    th_days = {t.date() for t, _, _, _ in tandh}
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


def plot_stability(rows):
    """How stable is the temperature, and on what timescale?

    Left: standard deviation of block means against block length. A flat line
    means the noise is white and averaging longer does not help; a rise at long
    tau means slow drift dominates.
    Right: mean temperature by hour of day, which exposes anything locked to
    the 24 h cycle.
    """
    by_sensor = defaultdict(list)
    for t, sensor, temp, _ in rows:
        by_sensor[sensor].append((t, temp))
    if not by_sensor:
        return

    taus = [("10 min", 600), ("30 min", 1800), ("1 h", 3600), ("3 h", 10800),
            ("6 h", 21600), ("12 h", 43200), ("1 d", 86400), ("3 d", 259200),
            ("7 d", 604800)]
    palette = [TEMP_C, "#7a4fa3", "#2e7d5b", "#c77d1a"]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))

    for n, (sensor, pts) in enumerate(sorted(by_sensor.items())):
        pts.sort()
        colour = palette[n % len(palette)]
        t0 = pts[0][0]
        secs = np.array([(t - t0).total_seconds() for t, _ in pts])
        vals = np.array([v for _, v in pts], dtype=float)

        xs, ys = [], []
        for label, tau in taus:
            blocks = (secs // tau).astype(np.int64)
            means = [vals[blocks == b].mean()
                     for b in np.unique(blocks)
                     if (blocks == b).sum() >= 3]
            if len(means) >= 3:
                xs.append(tau / 3600.0)
                ys.append(float(np.std(means, ddof=1)))
        if xs:
            a1.plot(xs, ys, marker="o", markersize=4, linewidth=1.2,
                    color=colour, label=sensor)

        hours = np.array([t.hour for t, _ in pts])
        prof = [vals[hours == h].mean() if (hours == h).any() else np.nan
                for h in range(24)]
        prof = np.array(prof) - np.nanmean(vals)
        a2.plot(range(24), prof, marker="o", markersize=3, linewidth=1.2,
                color=colour, label=sensor)

    a1.set_xscale("log")
    a1.set_yscale("log")
    a1.set_xlabel("averaging window (hours)", color=INK, fontsize=10)
    a1.set_ylabel("s.d. of window means (°C)", color=INK, fontsize=10)
    a1.set_title("Stability vs timescale", color=INK, fontsize=11,
                 loc="left", pad=10)
    a1.legend(fontsize=8, frameon=False)

    a2.axvline(8, color=DAY_C, linewidth=6, alpha=0.35)
    a2.axvline(20, color=NIGHT_C, linewidth=6, alpha=0.35)
    a2.axhline(0, color=INK, linewidth=0.8, alpha=0.4)
    a2.set_xticks(range(0, 25, 4))
    a2.set_xlabel("hour of day", color=INK, fontsize=10)
    a2.set_ylabel("deviation from mean (°C)", color=INK, fontsize=10)
    a2.set_title("Diurnal profile  (bands = 08:00 / 20:00 light change)",
                 color=INK, fontsize=11, loc="left", pad=10)

    for a in (a1, a2):
        style(a)
    fig.tight_layout()
    fig.savefig(f"{OUT}/stability.png", dpi=150)
    plt.close(fig)


def plot_interactive(rows):
    """Bokeh, written to plots/interactive.html.

    GitHub cannot run this: README HTML is sanitised and repo file views show
    source. Download the file and open it locally.
    """
    try:
        from bokeh.plotting import figure, output_file, save
        from bokeh.models import ColumnDataSource, HoverTool
        from bokeh.layouts import column
    except ImportError:
        print("bokeh not installed - skipping interactive.html")
        return
    if not rows:
        return

    by_sensor = defaultdict(list)
    for t, sensor, temp, rh in rows:
        by_sensor[sensor].append((t, temp, rh))

    palette = [TEMP_C, "#7a4fa3", "#2e7d5b", "#c77d1a"]
    tools = "pan,box_zoom,wheel_zoom,reset,save"

    p1 = figure(x_axis_type="datetime", height=340, width=1150, tools=tools,
                title="Temperature (°C) — drag to pan, scroll to zoom")
    for n, (sensor, pts) in enumerate(sorted(by_sensor.items())):
        src = ColumnDataSource(dict(t=[p[0] for p in pts],
                                    v=[p[1] for p in pts],
                                    s=[sensor] * len(pts)))
        p1.line("t", "v", source=src, line_width=1,
                color=palette[n % len(palette)], legend_label=sensor)
    p1.add_tools(HoverTool(
        tooltips=[("sensor", "@s"), ("time", "@t{%F %T}"), ("temp", "@v{0.00} °C")],
        formatters={"@t": "datetime"}, mode="vline"))
    p1.legend.click_policy = "hide"
    p1.legend.label_text_font_size = "9pt"

    p2 = figure(x_axis_type="datetime", height=280, width=1150, tools=tools,
                title="Relative humidity (%)", x_range=p1.x_range)
    for sensor, pts in sorted(by_sensor.items()):
        wet = [(t, h) for t, _, h in pts if h is not None]
        if not wet:
            continue
        src = ColumnDataSource(dict(t=[w[0] for w in wet],
                                    v=[w[1] for w in wet],
                                    s=[sensor] * len(wet)))
        p2.line("t", "v", source=src, line_width=1, color=RH_C,
                legend_label=sensor)
    p2.add_tools(HoverTool(
        tooltips=[("sensor", "@s"), ("time", "@t{%F %T}"), ("RH", "@v{0.0} %")],
        formatters={"@t": "datetime"}, mode="vline"))
    p2.legend.click_policy = "hide"
    p2.legend.label_text_font_size = "9pt"

    for p in (p1, p2):
        p.toolbar.logo = None
        p.xgrid.grid_line_color = GRID
        p.ygrid.grid_line_color = GRID

    output_file(f"{OUT}/interactive.html",
                title="Incubator archive — temperature and humidity")
    save(column(p1, p2))


def main():
    os.makedirs(OUT, exist_ok=True)
    tandh = read_tandh()
    events = read_events()
    plot_tandh(tandh)
    plot_instrument(tandh)
    plot_actogram(events)
    plot_restarts(events)
    plot_stability(tandh)
    plot_coverage(tandh, events)
    plot_interactive(tandh)
    print(f"wrote {len(os.listdir(OUT))} files to {OUT}/")


if __name__ == "__main__":
    main()
