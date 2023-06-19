from machine import RTC, Timer
import math
from neopixel import NeoPixel

import config
from logger import Logger as Log

"""
TODO
----

1. Implement Finite Cycles
2. Possibility of having multiple schedules. Name based file assignments.
3. Status sheet for LCD display

"""

class CircadiumScheduler:
    """
    Sets up Circadium Rhythm Scheduler.
    lightmatrix: Neopixel Array to control
    buzzer: used for auditary feedback on processes.
    """
    def __init__(self, lightmatrix, buzzer, name=None):
        
        self.name = name
        
        self.day_start   = [7, 0]  # hh, mm
        self.night_start = [20, 0]
        self.cycles      = 0       # 0 means infinite recurring cycles
        self.remaining_cycles = 20000

        self.lightmap = {"day" :[255, 255, 255], "night" :[0, 0, 0] , "night_view" : [255, 0, 0]}
        self.rtc = RTC()
        
        self.timer = Timer()
        self.buzzer = buzzer
        self.lightmatrix = lightmatrix
        self.phase = "day"
        self.phase_map = {"day": 0, "night": 1}
        
        
        self.is_active = True
        
        # Bookeeping and Interrupt Usage
        self.last_day_callback = (0,0,0,0,0,0,0,0)
        self.last_night_callback = (0,0,0,0,0,0,0,0)
      
    
    def time_based(self, day_start, night_start, cycles=0):
        """
        Set a time based Schedule.
        Input [hours, minute]s in 24 hour format.
        cycles = 0 : Run cycle forever.
        """
        self.last_day_callback = (0,0,0,0,0,0,0,0)
        self.last_night_callback = (0,0,0,0,0,0,0,0)
        
        #--------
        def str_to_time(string):
            # Format should be hh:mm
            if isinstance(string, list):
                return string
            
            
            string = string.strip(" ").split(",")
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
            self.remaining_cycles = self.cycles
            if self.cycles == 0:
                self.remaining_cycles = 2000
            Log.write("out", f"Set Circadium Scheduler: {self.day_start}, {self.night_start}, {self.cycles}")
        else:
            Log.write("out", "Invalid time entry!")
            self.buzzer(count=10)
            return
          
        with open("circadium.config") as file:
            file.write(f"{day_start}\n{night_start}\n{cycles}\n")
            self.is_active = True
            
        # Set the current state as per the time
        now = self.rtc.datetime()
        if self.phase_detect(now) == "day":
            Log.write("out", "Phase detection: day")
            self.__set_day__(now)
        elif self.phase_detect(now) == "night":
            Log.write("out", "Phase detection: night")
            self.__set_night__(now)
        else:
            Log.write("out", "Could not detect phase.")
    
    
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
        """
        Set a timer to query scheduler state.
        mode == "short" : queries state every config.cs_callback_s seconds.
        mode == "long"  : executes two callbacks every single cycle based on
                           precise time calculations. [TODO]
        """
        if mode == "short":
            self.timer.init(mode=Timer.PERIODIC, period=config.cs_callback_s*1000, callback=self.short_callback)
            Log.write("out", f"Timer for Circadium Scheduler set: {self.timer}")
        
        elif mode == "long":
            
            # Determine what mode it is now
            # Flick the phase switch
            # setup timer
            
            Log.write("out", "CircadiumScheduler: Timer mode long is not implemented.")
            return
            

    def short_callback(self, timer):
        
        now = self.rtc.datetime()
        print("Scheduler Callback!")
        
        print(self.__minute_diff__(now, self.day_start))
        print(self.__minute_diff__(now, self.night_start))
        

        
        # Is it day?
        if math.fabs(self.__minute_diff__(now, self.day_start))*60 <= config.cs_callback_s and \
           math.fabs(self.__minute_diff__(now, self.last_day_callback)) > 5 and \
           self.is_active:
            # Bom Dia!
            self.__set_day__(now)
        
        
        # Is it night?
        if math.fabs(self.__minute_diff__(now, self.night_start))*60 <= config.cs_callback_s and \
           math.fabs(self.__minute_diff__(now, self.last_night_callback)) > 5 and \
           self.is_active:
            # Bon Noite!
            self.__set_night__(now)
        
        # Test for cycles
        if self.remaining_cycles == 0:
            self.is_active = False
        
            
                
            
    # ------------
    def __set_day__(self, now):    
        print("Bom Dia!")
        self.buzzer.buzz(count=5)
        NeoPixel.fill(self.lightmatrix, self.lightmap["day"])
        self.phase = "day"
        Log.write("out", f"Transitioning to day light conditions: {self.lightmap['day']}")
        self.last_day_callback = now
        self.remaining_cycles = float(self.remaining_cycles) - 0.5
    
    def __set_night__(self, now):
        #print("diff", self.__minute_diff__(now, self.last_night_callback))
        print("Boa Noite!")
        self.buzzer.buzz(count=5)
        NeoPixel.fill(self.lightmatrix, self.lightmap["night"])
        self.phase = "night"
        Log.write("out", f"Transitioning to night light conditions: {self.lightmap['night']}")
        self.last_night_callback = now
        self.remaining_cycles = float(self.remaining_cycles) - 0.5
        
    def phase_detect(self, now):
        
        if self.__minute_diff__(now, self.day_start) >= 0 and \
           self.__minute_diff__(now, self.night_start) <= 0:
            return "day"
        else:
            return "night"
            
     
    def __minute_diff__(self, t1, t2):
        """
        Outputs t1 - t2 in minutes.Only [hh,mm]'s difference is calculated.
        time values can be machine.RTC() datetime tuple or [hh,mm].
        """
        def selector(time):
            if len(time) == 2:
                return time
            else: # Assume machine.RTC() datetime tuple
                return (time[4], time[5])
        t1 = selector(t1)
        t2 = selector(t2)
        
        diff = ((t2[0]*60)+t2[1]) - ((t1[0]*60)+t1[1])
        
        hours_diff = (t1[0] - t2[0] + 24) % 24
        min_diff = (t1[1] - t2[1] + 60) % 60
        #return (hours_diff * 60) + min_diff
        #print(diff)
        return diff
    
    
    
        
          

