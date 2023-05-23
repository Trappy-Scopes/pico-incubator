from machine import RTC

class CircadiumScheduler:
    """
    Sets up 
    """
    def __init__(self):
        self.day_start   = [7, 0]  # hh, mm
        self.night_start = [20, 0]
        self.cycles      = 0

        self.lightmap = {"day" :[255, 255, 255], "night" :[0, 0, 0] , "night_view" : [255, 0, 0]}
        self.rtc = RTC()
        
        self.timer = None
        
        self.phase_map = {"day":0, "night":1}
        self.phase = self.phase_map["day"]
      
    
    def time_based(self, day_start, night_start, cycles=0):
      """
      Input hours::minutes in 24 hour format.
      cycles = 0 : Run cycle forever.
      """
      
      def str_to_time(string):
          # Format should be hh:mm
          if isinstance(string, list):
              return string
          string = string.strip(" ").split(":")
          time_ = [int(t) for t in string]
          return time_[:2]
      
      def is_valid_time(time):
          return (time[0] >= 0 and time[0] <= 23) and
                 (time[1] >= 0 and time[1] <= 60)
      
      day_start = str_to_time(day_start)
      night_start = str_to_time(night_start)
      
      if is_valid_time(day_start) and is_valid_time(night_start):
        self.day_start   = day_start
        self.night_start = night_start
        self.cycles      = cycles
        
    else:
        print("Invalid time entry!")    
          
      with open("circadium.config") as file:
        file.write(f"{day_start}\n{night_start}\n{cycles}\n")
    
    
    
    def set_from_config(self):
        """
        Sets time values from the circadium.config state file.
        """
        data = None
        with open(circadium.config) as file:
            data = file.read()
        data.rstrip("\n")
        lines = data.split("\n")
        self.time_based(lines[0], lines[1], cycles=int(lines[2]))
        
    def set_timers(self):
          pass
        
        
    def timer_callback(self, timer):
        
        # Calculate difference
        now = self.rtc.datetime()
        
        if self.phase == "night":
            # Boa Noite!
            
            self.ledmatrix.fill()
        
        # Set timer
        
        #
    
        
          