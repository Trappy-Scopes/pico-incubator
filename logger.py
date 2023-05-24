from machine import RTC

class Logger:
    
    channels = ["out", "in", "err"]
    
    
    def __init__(cls):
        
        cls.log = str()
        cls.rtc = RTC()
        cls.files = {}
        cls.debug = True
        cls.lcd_ = None
        cls.__lcd_i__ = 1
        
        for file in Logger.channels:
            cls.files[file] = open(f"{file}.txt", "r+a")
        
    def __get_item__(cls, key):
        return cls.files[key]
    
    def __call__(cls, key, log):
        cls.log = f"{cls.rtc.datetime()}, {log}"
        cls.files[key].write(log)
        cls.files[key].flush()
        
        if cls.debug:
            print(cls.log)
    
    def __del__(cls):
        for file in self.files:
            cls.files[file].close()
    
    def dump(cls, key):
        return cls.files[key].read()
    
    def lcd(cls, text):
        if display:
            if cls.__lcd_i__ % 3 == 1:
                self.display.top(f"{cls.__lcd_i__}. {text}")
                cls.__lcd_i__ += 1
                return
            elif cls.__lcd_i__ % 3 == 2:
                self.display.middle(f"{cls.__lcd_i__}. {text}")
                cls.__lcd_i__ += 1
                return
            else:
                self.display.middle(f"{cls.__lcd_i__}. {text}")
                cls.__lcd_i__ += 1
                return