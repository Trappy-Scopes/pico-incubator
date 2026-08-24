import dht
from machine import Pin

#import pinassignments


# Depreciate
def get_temp_humidy():
    print(pinassignments.th_sensor)
    d = dht.DHT22(Pin(pinassignments.th_sensor))
    


class TandHSensor:
    
    def __init__(self, pin, type_):
        self.pin = pin
        self.offset = {"temp": 0, "humidity":0}
        
        if type_.lower() == "dh11":
            self.sensor = dht.DHT11(Pin(self.pin))
        elif type_.lower() == "dh22":
            self.sensor = dht.DHT22(Pin(self.pin))
        print(self.sensor)
            
    def read(self): #Add Exception handling
        d = self.sensor.measure()
        return {"temp"     : self.sensor.temperature() + self.offset["temp"],
                "humidity" :self.sensor.humidity()  + self.offset["humidity"]
                }
