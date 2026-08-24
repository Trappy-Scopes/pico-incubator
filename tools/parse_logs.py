#!/usr/bin/env python3
"""
parse_logs.py - turn logs/<YYYY-MM-DD>/*.txt into two tidy CSVs.

Every record written by the Pico's Logger looks like:

    <channel>, (Y, M, D, weekday, hh, mm, ss, subsec), <message>

A bare channel name on its own line is the header the Logger writes when it is
imported, i.e. one board restart. It carries no timestamp of its own, so it is
dated from the first usable record of that boot - the next timestamped line in
the same file. Restarts whose clock never synced cannot be dated at all and are
kept with clock_ok=0.

Note the folder name is only the date the logs were RETRIEVED. It says nothing
about when anything in them happened, so it is carried through as a provenance
column and never used as a time axis.

Outputs, at the repo root:
    tandh.csv   timestamp, retrieved, sensor, temp_c, humidity_pct
    events.csv  timestamp, retrieved, channel, kind, detail, clock_ok

Records stamped before 2023 come from a board whose RTC was still at the
MicroPython 2021-01-01 default, i.e. the NTP / dtsync clock sync had not
succeeded for that boot. There was no watchdog on this hardware, so these are
sync failures and nothing more. They are kept with clock_ok=0 because they mark
boots whose clock never came good - but they are excluded from tandh.csv, where
an unusable timestamp makes the reading worthless.

Standard library only. No arguments; run it from the repo root.
"""

import ast
import csv
import os
import re

LOGS = "logs"
REC = re.compile(
    r"^(\w+), \((\d+), (\d+), (\d+), \d+, (\d+), (\d+), (\d+), \d+\), (.*)$"
)

# out.txt message -> event kind
KINDS = (
    ("Transitioning to day",    "day"),
    ("Transitioning to night",  "night"),
    ("Set Circadium Scheduler", "scheduler_set"),
    ("Phase detection",         "phase_detect"),
    ("Timer for Circadium",     "timer_set"),
    ("BOOT",                    "boot"),
    ("HB ",                     "heartbeat"),
    ("WDT",                     "wdt"),
    ("FS ",                     "filesystem"),
    ("Machine Reset",           "boot"),
)


def classify(msg):
    for needle, kind in KINDS:
        if msg.startswith(needle):
            return kind
    return "other"


def stamp(Y, M, D, hh, mm, ss):
    return (f"{int(Y):04d}-{int(M):02d}-{int(D):02d} "
            f"{int(hh):02d}:{int(mm):02d}:{int(ss):02d}")


def date_of_boot(lines, i):
    """Timestamp of the first usable record after a restart marker at index i.

    Returns ("", 0) if the clock never synced during that boot.
    """
    for ahead in lines[i + 1:]:
        m = REC.match(ahead)
        if not m:
            continue
        _, Y, M, D, hh, mm, ss, _ = m.groups()
        if int(Y) < 2023:
            return "", 0
        return stamp(Y, M, D, hh, mm, ss), 1
    return "", 0


def main():
    tandh, events = [], []

    for retrieved in sorted(os.listdir(LOGS)):
        folder = os.path.join(LOGS, retrieved)
        if not os.path.isdir(folder):
            continue

        for name in sorted(os.listdir(folder)):
            if not name.endswith(".txt"):
                continue
            channel = name[:-4]
            path = os.path.join(folder, name)

            with open(path, errors="replace") as fh:
                lines = [ln.strip() for ln in fh]

            for i, line in enumerate(lines):
                if not line:
                    continue

                if line == channel:
                    ts, ok = date_of_boot(lines, i)
                    # line number keeps undated markers distinct through dedup
                    events.append([ts, retrieved, channel, "restart_marker",
                                   f"line {i + 1}", ok])
                    continue

                m = REC.match(line)
                if not m:
                    continue

                ch, Y, M, D, hh, mm, ss, msg = m.groups()
                ts = stamp(Y, M, D, hh, mm, ss)
                clock_ok = 1 if int(Y) >= 2023 else 0

                if ch.startswith("tandh"):
                    if not clock_ok:
                        continue
                    try:
                        v = ast.literal_eval(msg)
                    except Exception:
                        continue
                    if not isinstance(v, dict):
                        continue
                    tandh.append([ts, retrieved, ch,
                                  v.get("temp"), v.get("humidity")])
                else:
                    events.append([ts, retrieved, ch,
                                   classify(msg), msg, clock_ok])

    # the same record can appear in two retrievals
    tandh = sorted(set(map(tuple, tandh)))
    events = sorted(set(map(tuple, events)), key=lambda r: (r[0], r[1], r[2]))

    with open("tandh.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "retrieved", "sensor", "temp_c", "humidity_pct"])
        w.writerows(tandh)

    with open("events.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["timestamp", "retrieved", "channel", "kind", "detail", "clock_ok"])
        w.writerows(events)

    boots = [e for e in events if e[3] == "restart_marker" and e[2] == "out"]
    dated = sum(1 for b in boots if b[5] == 1)
    print(f"tandh.csv   {len(tandh):>7} readings")
    print(f"events.csv  {len(events):>7} records")
    print(f"            {len(boots)} restarts ({dated} dated, "
          f"{len(boots) - dated} with no clock)")
    if tandh:
        print(f"            {tandh[0][0]}  ->  {tandh[-1][0]}")


if __name__ == "__main__":
    main()
