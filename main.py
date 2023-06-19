from machine import Pin, Timer, RTC
from time import sleep, ticks_ms
import _thread
import time
import ntptime
import pyb

from action import Action
from tempandhumidity import get_temp_humidy, TandHSensor
from lcd import LCD_0inch96
from circadiumscheduler import CircadiumScheduler
from buzzer import Buzzer
from averager import Averager
from logger import Logger as Log

from wifi import Wifi
from neopixel import NeoPixel


import secrets
import pinassignments
import config


# Resources ---------------------------------------------------------    T0
relay = Pin(pinassignments.relay, Pin.OUT)
buzzer = Buzzer(pinassignments.buzzer, Pin.OUT)
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

# -------------------------------------------------------------------

# Switch triggers ---------------------------------------------------     T1 (disabled)
def toggle_relay(pin):
    print(f"Relay state to: {int(relay.value())}")
    relay.toggle()
    buzzer.buzz()

def toggle_lights(pin):
    print(f"Light state to: {int(led.value())}")
    led.toggle()
    buzzer.buzzfast(count=3)
#sw1_action = Action(sw1, callback=toggle_relay)
#sw2_action = Action(sw2, callback=toggle_lights)
# --------------------------------------------------------------------


# Clock synchronisation ----------------------------------------------    T2   ||  Timer 0
def dt_sync_callback(timer):
    if wifi.connected:
        Log.write("Local time before synchronization：%s" %str(rtc.datetime()))
        ntptime.settime()
        now = list(rtc.datetime())
        now[4] = (now[4] + 1) %24 #UTC+1 Timezone correction
        rtc.datetime(now)
        print("Local time after synchronization：%s" %str(rtc.datetime()))
        Log.write("out", "RTC synchronized by NTP server.")

dt_sync_callback(True)
dt_sync_tim = Timer(period=1000*config.dt_sync_period_s, mode=Timer.PERIODIC, callback=dt_sync_callback)
Log.write("out", f"RTC-NTP sync callback set: {dt_sync_tim}")
# ---------------------------------------------------------------------


# Circadium Rhythm Scheduler ------------------------------------------     T3   ||   Timer 1
scheduler = CircadiumScheduler(lightmatrix, buzzer)
scheduler.rtc.datetime(rtc.datetime())
scheduler.set_from_config()
scheduler.set_timers(mode="short")
# ---------------------------------------------------------------------


# Safety --------------------------------------------------------------     T4   ||   Timer 2
buzzer_safety_tim = Timer(period=1000*5*60, mode=Timer.PERIODIC, \
                          callback=lambda timer: buzzer.off())

# Wifi status
if wifi.connected:
    Log.write("out", "Wifi is connected: {wifi.info()}.")
else:
   Log.write("out", "Wifi could not be connected.") 

# ---------------------------------------------------------------------

# Temp and humidity monitors ------------------------------------------     T5   ||   Timer 3
try:
    sample = get_temp_humidy()
    temperature = Averager("temp", size=15, init=sample["temp"])
    humidity = Averager("humidity", size=15, init=sample["humidity"])
    def tandh_callback(timer):
        sample = get_temp_humidy()
        temperture.update(sample["temp"])
        humidity.update(sample["humidity"])
    # Set Timer
    tanh_tim = Timer(period=1000*config.tandh_sample_period_s, mode=Timer.PERIODIC, \
                     callback=tandh_callback)
except:
    Log.write("out", "T&H sensor could not be accessed. Would not log sensor data.")
# -------------------------------------------------------------------

# Processor 1 -------------------------------------------------------    T6   ||   Processor 1 Poll
global processor1_stop
processor1_stop = False

def processor1():
    global processor1_stop
    while not processor1_stop:
        global wifi
        if not wifi.connected:
            import secrets
            wifi.connect(secrets)
            if wifi.connected:
                Log.write("out", f"On Processor 1, wifi connected: {wifi.info()}.")
        else:
            time.sleep(1)
processor2_thread = _thread.start_new_thread(processor1, ())
Log.write("out", f"Processor thread 1 was started: {processor2_thread}")
# -------------------------------------------------------------------

# LCD Updates -------------------------------------------------------    T7
lcd_roll = []
def lcd_update(timer):
    pass
# -------------------------------------------------------------------

# Setup Finished ----------------------------------------------------    T8
buzzer.buzz(count=3)
if pyb.USB_VCP.isconnected():
    Log.write("out", "Device was connected to a PC terminal.")
else:
    Log.write("out", "Device was connected to mains power.")

Log.write("out", "Setup is finished.")
# -------------------------------------------------------------------

