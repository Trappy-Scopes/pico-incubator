# Temperature

Two sensors, two and a half years apart, measuring two quite different things.

## Pico DHT sensor — Aug 2023 to Feb 2024

![Pico DHT temperature and humidity](plots/temperature_tandh1.png)

82,781 readings of an **uncontrolled room**. Temperature ranged 19–28 °C and humidity
36–68 %. The blocks are the retrieval windows: each pull captured a distinct stretch of
roughly a week, and the line breaks across the gaps rather than interpolating, so what
you see is what was recorded.

This sensor was retired in February 2024 when a temperature-controlled incubator
arrived.

## Memmert ILP 115 SMART — Jun 2026 to present

![ILP 115 SMART temperature](plots/temperature_ILP115SMART_IP11240004.png)

10,000 readings at ten-minute intervals, holding a 25 °C set point. No humidity
channel. The vertical scale here is a fraction of a degree — this is a controlled
chamber, and the plot is showing you its control loop rather than the weather.

## Stability

![Stability analysis](plots/stability.png)

**Left — standard deviation of block means against block length.** A flat line means
noise that averaging cannot remove; a falling line means averaging helps. The old setup
is flat at roughly 1.5 °C, which is not sensor noise — it is a room with no temperature
control, and no amount of averaging makes a room a thermostat. The ILP 115 sits far
below it and continues to average down over days.

**Right — mean temperature by hour of day, as a deviation from each sensor's own mean.**
The two profiles have different causes and this is the most interesting figure on the
site.

The old trace is a broad curve peaking in the late afternoon: building heating and
solar gain, a room following the day.

The ILP 115 trace does something else. It **steps at 08:00 and drops at 20:00** —
precisely on the light transitions, marked by the shaded bands. The incubator's control
loop is good to a few hundredths of a degree, so this is not drift. It is the 132-LED
matrix warming the chamber when it turns on, by roughly **0.3 °C peak-to-trough**.

That has a biological consequence worth stating plainly: the cells are not on a pure
light cycle. They are on a light cycle with a small, perfectly phase-locked temperature
cycle riding on top of it. Whether 0.3 °C matters depends on the experiment, but it is
a confound that was invisible until the instrument's own export was merged with the
light log — neither record shows it alone.

## Interactive

Pan, zoom, hover for values, and click legend entries to toggle series.

<iframe src="../plots/interactive.html" width="100%" height="700" style="border:none;"
        title="Interactive temperature and humidity"></iframe>

[Open full screen →](plots/interactive.html){ .md-button }
