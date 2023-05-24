class Buzzer:
    
    
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