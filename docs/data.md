# The data

## Repository layout

```
logs/YYYY-MM-DD/     one folder per retrieval, named for the day you pulled the files
legacy/              the original firmware (different circuit board)
tools/               parse_logs.py, make_plots.py
docs/                this site
tandh.csv            generated: every temperature reading
events.csv           generated: every event record
plots/               generated: the figures
```

## Generated files

Both CSVs are rebuilt from `logs/` on every push. Do not edit them by hand.

**`tandh.csv`** — `timestamp, retrieved, sensor, temp_c, humidity_pct`.
`humidity_pct` is empty for instrument exports that only log temperature.

**`events.csv`** — `timestamp, retrieved, channel, kind, detail, clock_ok`.
`kind` is one of `day`, `night`, `boot`, `restart_marker`, `scheduler_set`,
`phase_detect`, `timer_set`, `heartbeat`, `wdt`, `filesystem`, `instrument`, `other`.

## Log format — Pico

One record per line:

```
<channel>, (Y, M, D, weekday, hh, mm, ss, subsec), <message>
```

A bare channel name on its own line is the header written when the logger is imported —
**one board restart**. All four channels write a header at boot, so counting restarts
across every channel over-counts about fourfold. Only `out` is counted.

| file | content |
|---|---|
| `out.txt` | boots, scheduler setup, day/night transitions, heartbeats |
| `err.txt` | NTP clock-sync records |
| `tandh1.txt`, `tandh2.txt` | `{'humidity': 44, 'temp': 23}` |
| `in.txt`, `dtsync.txt` | headers only, in practice |

## Log format — Memmert ILP

```
ILP 115 SMART; IP11240004

date; temp.; status
2026.08.24  16:32; 25.01; set temp.
```

Semicolon separated, newest row first, ten-minute interval, no humidity channel. Any
status other than `set temp.` is emitted into `events.csv`, so alarms and door openings
are not lost. Some exports carry a doubled byte-order mark; the parser strips it.

## Four things that look like bugs and are not

**Temperature and humidity stop in February 2024.** Not data loss. A
temperature-controlled incubator arrived and the Pico's sensor was no longer needed.
Between then and June 2026 the record is light cycle and uptime only.

**Some records are stamped 2021-01-01.** That is the MicroPython RTC default, and it
means the NTP sync had not succeeded for that boot. There was no watchdog on this
hardware, so these are clock-sync failures and nothing more. They are kept in
`events.csv` with `clock_ok=0` — they still mark real restarts — and excluded from
`tandh.csv`, where an unusable timestamp makes a reading worthless.

**Retrieval windows do not overlap.** Each pull captured a distinct window, roughly a
week for the 2023 retrievals, rather than a cumulative file. All 82,781 Pico readings
are unique. Plots break the line across gaps instead of interpolating.

**The board reports negative free disk space.** `os.statvfs()` returns
`f_bfree = -52` out of 212 blocks, because MicroPython computes free blocks as
`f_blocks - lfs_fs_size()` and littlefs counts metadata pairs more than once. A file
walk gives the truth: 314 KB used of 848 KB. The firmware ignores `statvfs` and watches
the size of `out.txt` instead.

## How the site is built

`.github/workflows/pages.yml`, on every push touching `logs/`, `tools/` or `docs/`:

1. `tools/parse_logs.py` — walks `logs/*/`, writes `tandh.csv` and `events.csv`
2. `tools/make_plots.py` — writes the figures into `plots/`
3. copies `plots/` into `docs/`
4. `mkdocs gh-deploy` — publishes to the `gh-pages` branch

`parse_logs.py` is standard library only. `make_plots.py` needs matplotlib and numpy;
bokeh is optional and skipped if absent.

Nothing is committed back to `main`, so pushing never conflicts with the build.
