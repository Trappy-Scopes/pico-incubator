import dht
from machine import Pin
import utime
import pinassignments

def get_temp_humidy():
    print(pinassignments.th_sensor)
    d = dht.DHT22(Pin(pinassignments.th_sensor))
    d.measure()
    return {"temp": d.temperature(), "humidity":d.humidity()}