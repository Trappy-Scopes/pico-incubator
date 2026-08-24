#!/usr/bin/env python3
"""
parse_logs.py - turn logs/<YYYY-MM-DD>/*.txt into two tidy CSVs.

Every record written by the Pico's Logger looks like:

    <channel>, (Y, M, D, weekday, hh, mm, ss, subsec), <message>

A bare channel name on its own line ("out") is the header the Logger writes at
import, i.e. one board restart.

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
    ("Transitioning to day",   "day"),
    ("Transitioning to night", "night"),
    ("Set Circadium Scheduler", "scheduler_set"),
    ("Phase detection",        "phase_detect"),
    ("Timer for Circadium",    "timer_set"),
    ("BOOT",                   "boot"),
    ("HB ",                    "heartbeat"),
    ("WDT",                    "wdt"),
    ("FS ",                    "filesystem"),
    ("Machine Reset",          "boot"),
)


def classify(msg):
    for needle, kind in KINDS:
        if msg.startswith(needle):
            return kind
    return "other"


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
                for lineno, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue

                    # bare channel name = Logger import = one board restart
                    # A bare channel name is untimestamped, so it needs the
                    # line number to stay distinct through de-duplication.
                    if line == channel:
                        events.append(
                            ["", retrieved, channel, "restart_marker",
                             f"line {lineno}", 0]
                        )
                        continue

                    m = REC.match(line)
                    if not m:
                        continue

                    ch, Y, M, D, hh, mm, ss, msg = m.groups()
                    ts = f"{int(Y):04d}-{int(M):02d}-{int(D):02d} {int(hh):02d}:{int(mm):02d}:{int(ss):02d}"
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
                        tandh.append(
                            [ts, retrieved, ch, v.get("temp"), v.get("humidity")]
                        )
                    else:
                        events.append(
                            [ts, retrieved, ch, classify(msg), msg, clock_ok]
                        )

    # de-duplicate: the same reading can appear in two retrievals
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

    print(f"tandh.csv   {len(tandh):>7} readings")
    print(f"events.csv  {len(events):>7} records")
    if tandh:
        print(f"            {tandh[0][0]}  ->  {tandh[-1][0]}")


if __name__ == "__main__":
    main()
