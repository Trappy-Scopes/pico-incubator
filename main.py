from machine import Pin, Timer, RTC
from time import sleep, ticks_ms
import _thread
import time
import ntptime

import pinassignments
import config
from action import Action
from tempandhumidity import get_temp_humidy
from lcd import LCD_0inch96
from circadiumscheduler import CircadiumScheduler
import secrets
from wifi import Wifi
# Resources ---------------------------------------------------------
#global relay, buzzer, sw1, sw2
relay = Pin(pinassignments.relay, Pin.OUT)
buzzer = Pin(pinassignments.buzzer, Pin.OUT)
buzzer.off()
sw1 = Pin(pinassignments.sw1, Pin.IN)
sw2 = Pin(pinassignments.sw2, Pin.IN)
led = Pin("LED", Pin.OUT)
lcd = LCD_0inch96()
lcd.intro_seq()

wifi = Wifi(secrets=secrets)
rtc = RTC()
# -------------------------------------------------------------------

# Feedback functions ------------------------------------------------
def buzz(count=1):
    global buzzer
    for _ in range(count):
        buzzer.on()
        sleep(0.75)
        buzzer.off()
        sleep(0.2)
def buzzfast(count=1):
    global buzzer
    for _ in range(count):
        buzzer.on()
        sleep(0.2)
        buzzer.off()
        sleep(0.1)
def buzz_(t):
    buzzfast(count=1)
# -------------------------------------------------------------------


# Switch triggers ---------------------------------------------------
def toggle_relay(pin):
    print(f"Relay state to: {int(relay.value())}")
    relay.toggle()
    buzz()

def toggle_lights(pin):
    print(f"Light state to: {int(led.value())}")
    led.toggle()
    buzzfast(count=3)
#sw1_action = Action(sw1, callback=toggle_relay)
#sw2_action = Action(sw2, callback=toggle_lights)
# --------------------------------------------------------------------

# Clock synchronisation ----------------------------------------------
def dt_sync_callback(timer):
    if wifi.connected:
        print("Local time before synchronization：%s" %str(time.localtime()))
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))

dt_sync_tim = Timer(period=1000*config.dt_sync_period_s, mode=Timer.PERIODIC, callback=dt_sync_callback)

scheduler = CircadiumScheduler()
scheduler.rtc.datetime(rtc.datetime())
scheduler.set_from_config()
schedulers.set_timers(mode="short")

# ---------------------------------------------------------------------


# Safety -------------------------------------------------------------

# 1. Disable buzzer every 5 mins
buzzer_safety_tim = Timer(period=1000*5*60, mode=Timer.PERIODIC, callback=lambda timer: buzzer.off())

# 2. Fire Safety Alarm
def fire_alarm_callback():
    pass
firealarm_tim = Timer(period=1000*config.fire_check_period_s, mode=Timer.PERIODIC, callback=fire_alarm_callback)
# ---------------------------------------------------------------------

# Temp and humidity monitors ----------------------------------------
sample = get_temp_humidy()
temperature = Averager("temp", size=15, init=sample["temp"])
humidity = Averager("humidity", size=15, init=sample["humidity"])
def tandh_callback(timer):
    sample = get_temp_humidy()
    temperture.update(sample["temp"])
    humidity.update(sample["humidity"])
# Set Timer
tanh_tim = Timer(period=1000*config.tandh_sample_period_s, mode=Timer.PERIODIC, callback=tandh_callback)
# -------------------------------------------------------------------