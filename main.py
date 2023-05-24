from machine import Pin, Timer, RTC
from time import sleep, ticks_ms
import _thread
import time
import ntptime

from action import Action
from tempandhumidity import get_temp_humidy, TandHSensor
from lcd import LCD_0inch96
from circadiumscheduler import CircadiumScheduler


from wifi import Wifi
from neopixel import Neopixel


import secrets
import pinassignments
import config

# Resources ---------------------------------------------------------
relay = Pin(pinassignments.relay, Pin.OUT)
buzzer = Pin(pinassignments.buzzer, Pin.OUT)
buzzer.off()
sw1 = Pin(pinassignments.sw1, Pin.IN)
sw2 = Pin(pinassignments.sw2, Pin.IN)
led = Pin("LED", Pin.OUT)

wifi = Wifi(secrets=secrets)
rtc = RTC()

lcd = LCD_0inch96()
lcd.top(lcd.center("Cell Incubator"))
lcd.middle(lcd.center("Trappy Scope-Sys"))
lcd.bottom(lcd.center("Living Physics Lab"))

lightpin = Pin(pinassignments.lights)
lightmatrix = NeoPixel(lightpin, 21, bpp=3, timing=1)

NeoPixel.fill(lightmatrix, (255, 0, 0)) # R
NeoPixel.fill(lightmatrix, (255, 0, 0)) # G
NeoPixel.fill(lightmatrix, (255, 0, 0)) # B
NeoPixel.fill(lightmatrix, (255, 0, 0)) # W
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
        print("Local time before synchronization：%s" %str(rtc.datetime()))
        ntptime.settime()
        now = list(rtc.datetime())
        now[4] = (now[4] + 1) %24 #UTC+1 Timezone correction
        rtc.datetime(now)
        print("Local time after synchronization：%s" %str(rtc.datetime()))
dt_sync_callback(True)
dt_sync_tim = Timer(period=1000*config.dt_sync_period_s, mode=Timer.PERIODIC, callback=dt_sync_callback)
# --------------------------------------------------------------------- T0


# Circadium Rhythm Scheduler ------------------------------------------
scheduler = CircadiumScheduler()
scheduler.rtc.datetime(rtc.datetime())
scheduler.set_from_config()
scheduler.set_timers(mode="short")
# --------------------------------------------------------------------- T1


# Safety -------------------------------------------------------------

# 1. Disable buzzer every 5 mins
buzzer_safety_tim = Timer(period=1000*5*60, mode=Timer.PERIODIC, callback=lambda timer: buzzer.off())

# 2. Fire Safety Alarm
#def fire_alarm_callback():
#    pass
#firealarm_tim = Timer(period=1000*config.fire_check_period_s, mode=Timer.PERIODIC, callback=fire_alarm_callback)
# --------------------------------------------------------------------- T3

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
# ------------------------------------------------------------------- T4


# LCD Updates ------------------------------------------------------
lcd_roll = []
def lcd_update(timer):
    pass




