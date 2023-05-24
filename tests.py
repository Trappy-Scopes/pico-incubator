from utime import sleep
import pinassignments
from machine import Pin, PWM

def sample_switches(sw1, sw2):
    for i in range(100):
        print(sw1.value(), sw2.value())
        sleep(0.05)

def buzzer():
    buzzer = PWM(Pin(pinassignments.buzzer, Pin.OUT))
    buzzer.duty_u16(25000)
    for i in range(1, 10):
        buzzer.freq(100*i)
        sleep(0.05)
        
    freqs = list(range(1, 10))
    freqs.reverse()
    
    for i in freqs:
        buzzer.freq(100*i)
        sleep(0.05)
        
    buzzer.deinit()