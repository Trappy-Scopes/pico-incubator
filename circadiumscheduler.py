from machine import RTC, Timer
import math
from neopixel import NeoPixel

import config
from logger import Logger

class CircadiumScheduler:
    """
    Sets up Circadium Rhythm Scheduler.
    """
    def __init__(self, lightmatrix):
        self.day_start   = [7, 0]  # hh, mm
        self.night_start = [20, 0]
        self.cycles      = 0

        self.lightmap = {"day" :[255, 255, 255], "night" :[0, 0, 0] , "night_view" : [255, 0, 0]}
        self.rtc = RTC()
        
        self.timer = Timer()
        self.lightmatrix = lightmatrix
        self.phase_map = {"day": 0, "night": 1}
        self.phase = "day"
      
    
    def time_based(self, day_start, night_start, cycles=0):
        """
        Input [hours, minute]s in 24 hour format.
        cycles = 0 : Run cycle forever.
        """
      
        #--------
        def str_to_time(string):
            # Format should be hh:mm
            if isinstance(string, list):
                return string
            
            
            string = string.strip(" ").split(",")
            print(string)
            time_ = [int(t) for t in string]
            return time_[:2]
        
        def is_valid_time(time):
            return (time[0] >= 0 and time[0] <= 23) and \
                   (time[1] >= 0 and time[1] <= 60)
        #--------

        day_start = str_to_time(day_start)
        night_start = str_to_time(night_start)
      
        if is_valid_time(day_start) and is_valid_time(night_start):
            self.day_start   = day_start
            self.night_start = night_start
            self.cycles      = cycles
            Logger("out", f"Set Circadium Scheduler: {self.day_start}, {self.night_start}, {self.cycles}")
        else:
            Logger("out", "Invalid time entry!")    
          
        with open("circadium.config") as file:
            file.write(f"{day_start}\n{night_start}\n{cycles}\n")
    
    
    
    def set_from_config(self):
        """
        Sets time values from the circadium.config state file.
        """
        data = None
        with open("circadium.config") as file:
            data = file.read()
        data.rstrip("\n")
        
        lines = data.split("\n")
        lines = [line.lstrip("[").rstrip("]") for line in lines]
        self.time_based(lines[0], lines[1], cycles=int(lines[2]))
        
    def set_timers(self, mode="short"):
        if mode == "short":
            # Callback every 45 seconds.
            
            self.timer = Timer.init(mode=Timer.PERIODIC, period=config.cs_callback_s*1000, callback=self.short_callback)
            Logger("out", f"Timer for Circadium Scheduler set: {self.timer}")
        
        elif mode == "long":
            pass
            # Determine what mode it is now
            
            # Flick the phase switch
            
            # setup timer
            
    def short_callback(self, timer):
        
        now = self.rtc.datetime()
        print("Scheduler Callback")
        
        print(now[4] - self.day_start[0], math.fabs(now[5] - self.day_start[1]))
        
        if self.phase == "night":
            # Bom Dia!
            if now[4] - self.day_start[0] == 0 and math.fabs(now[5] - self.day_start[1]) <= 1:
                print("Bom Dia!")
                
                NeoPixel.fill(self.ledmatrix, self.lightmap["day"])
                self.phase = "day"
                Logger("out", f"Transitioning to day light conditions: {lightmap['day']}")
                return
        
        if self.phase == "day":
            # Boa Noite!
            if now[4] - self.night_start[0] == 0 and math.fabs(now[5] - self.night_start[1]) <= 1:
                print("Boa Noite!")
                
                NeoPixel.fill(self.ledmatrix, self.lightmap["night"])
                self.phase = "night"
                Logger("out", f"Transitioning to night light conditions: {lightmap['night']}")
                return
            
    
    
    def long_callback(self, timer):
        # Not being maintained
        # Might not work as timers are being adjusted in the same callback.
        if self.phase == "night":
            # Bom Dia!
            self.ledmatrix.fill(self.lightmap["day"])
            self.timer.deinit()
            
            now = self.rtc.datetime()
            hours = (self.night_start[0] - now[4] + 24) % 24
            minutes = (self.night_start[0] - now[5] + 60) % 60
            next_period_ms = (hours*60 + minutes) * 60 * 1000
            
            self.timer.init(mode=Timer.ONE_SHOT, period=next_period_ms, callback=self.timer_callback)
            self.phase = "day"
            return
        
        if self.phase == "day":
            # Boa Noite!
            self.ledmatrix.fill(self.lightmap["night"])
            self.timer.deinit()
            
            now = self.rtc.datetime()
            hours = (self.night_start[0] - now[4] + 24) % 24
            minutes = (self.night_start[0] - now[5] + 60) % 60
            next_period_ms = (hours*60 + minutes) * 60 * 1000
            
            self.timer.init(mode=Timer.ONE_SHOT, period=next_period_ms, callback=self.timer_callback)
            self.phase = "day"
            return
    
    
    
        
          

