# Inspired by: https://gist.github.com/jedie/8564e62b0b8349ff9051d7c5a1312ed7


from machine import Pin
import pinassignments
import utime


class Action:
    def __init__(self, pin, callback, trigger=Pin.IRQ_FALLING, debounce_ms=300):
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.pin = pin
        
        self._blocked = False
        self._next_call = utime.ticks_ms() + self.debounce_ms

        pin.irq(trigger=trigger, handler=self.debounce_handler)

    def __call__(self, pin):
        self.callback(pin)

    def debounce_handler(self, pin):
        if utime.ticks_ms() > self._next_call:
            self._next_call = utime.ticks_ms() + self.debounce_ms
            self.__call__(pin)
        #else:
        #    print("debounce: %s" % (self._next_call - time.ticks_ms()))
    

if __name__ == "__main__":
    buzzer = Pin(pinassignments.buzzer, Pin.OUT)
    relay2 = Action(Pin(pinassignments.sw1), lambda pin: buzzer.toggle())
    relay = Action(Pin(pinassignments.sw2), lambda pin: buzzer.toggle())
