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
        
        # Block if cycles are over
        if self.remining_cycles == 0:
            self.is_active = False