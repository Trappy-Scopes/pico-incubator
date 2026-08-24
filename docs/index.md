# pico-incubator

Permanent record of a cell-culture incubator at the Instituto Gulbenkian de Ciência:
its 12/12 light cycle, its temperature, and the reliability of the microcontroller
that runs it. Three years of logs, from August 2023 to the present.

!!! info "This is an archive"
    The firmware that produced these logs is no longer developed here — it was folded
    into `pico_firmware`, which unified all Pico-controlled devices in the lab. The
    original code is kept on the [`legacy` branch](https://github.com/Trappy-Scopes/pico-incubator/tree/legacy)
    and in `legacy/`. It targets a **different circuit board** to the one in service now.

## What is here

| | |
|---|---|
| Retrievals | 18, from 2023-08-26 to 2026-08-24 |
| Temperature readings | 92,781 |
| — Pico DHT sensor | 82,781, Aug 2023 → Feb 2024, with humidity |
| — Memmert ILP 115 SMART | 10,000, Jun 2026 → Aug 2026, temperature only |
| Event records | ~29,000 |
| Board restarts | 1,406 |

## Coverage

![Archive coverage](plots/coverage.png)

The temperature record has two distinct eras with a two-year gap between them. The
Pico's own sensor logged an **uncontrolled room** through the winter of 2023–24; it was
retired when a temperature-controlled incubator arrived. Between February 2024 and June
2026 the record is light cycle and uptime only.

## Three findings

**The LED matrix heats the chamber.** Mean temperature by hour of day steps sharply at
08:00 and drops at 20:00, exactly on the light transitions — about 0.3 °C
peak-to-trough. The cells experience a small thermal cycle locked to the light cycle.
[See the stability analysis →](temperature.md#stability)

**Board restarts jumped in July 2026.** Twenty to forty a month is typical; July 2026
had 81. The same escalation shows up independently in the device's own log as a cluster
of restarts between 02:00 and 07:00 — the hours when the host Raspberry Pi runs its
overnight housekeeping. [See reliability →](reliability.md)

**The light schedule is more reliable than the board.** Transitions land within seconds
of 08:00 and 20:00 essentially whenever the board is running. What fails is the board,
not the schedule. [See the light cycle →](light-cycle.md)

## Adding logs

1. Pull the files off the device.
2. Drop them into a folder named for the date you retrieved them: `logs/YYYY-MM-DD/`.
3. Commit and push.

Everything on this site regenerates itself. Both the Pico's `.txt` logs and instrument
CSV exports go in the same folder — the parser recognises each by shape.

---

*Parser, figures, analysis and this site were built by Claude, reviewed by Yatharth
Bhasin.*
