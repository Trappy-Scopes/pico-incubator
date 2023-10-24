
class ParallelScheduler:
	
	def __init__(self, channels=12, schedulefile):

		self.schedulefile = schedulefile
		self.schedule = {
							#channel1: {"day": {"time": [08, 00], color:[255, 255, 255],
							#			"night": {"time": [20,00], color:[255, 0, 0]}

						}
		time = rtc.now()
		self.time = [time[], time[]]

		self.current_colors = []
		#[[R1, G1, B1], [R2, G2, B2], [R3, G3, B3]]
		self.current_phase = []

		# or
		# {1: [state, R1, G1, B1]}

		self.channels = channels
		self.ledmatrix = Neopixel()

		## Set initial conditions
		self.init()

	def init(self):
		pass


	def update(self):
		"""
		Checks the current time against the schedule. 
		"""

		## Update the current time.
		time = rtc.now()
		self.time = [time[], time[]]

		for i, sch in enumerate(schedule):
			if self.schedule[sch]["day"]["time"] == self.time:
				self.current_phase[i] == "day"
				self.current_colors[i] = self.schedule[sch]["day"]["color"]
				## Beep -  ...i

			elif self.schedule[sch]["night"]["time"] == self.time:
				self.current_phase[i] == "night"
				self.current_colors[i] = self.schedule[sch]["night"]["color"]
				## Beep -- ...i
			else:
				pass

		for i in range(self.channels):
			self.ledmatrix[i] = self.current_colors[i]
		self.ledmatrix.write()


	def set_ch(self, channel, phase, time, light=None):
		
		try:
			self.schedule[channel][phase]["time"] = time

			if light != None and len(light) == 3:
				self.schedule[channel][phase]["light"] = light

			self.__dump__(self.schedulefile)
		except:
			print("Exception! Schedule change failed! Reinit")
			self.init()
	
	def __load__(self, file):
		with open(file, "r") as f:
			data = json.load(f)
		return data

	def __dump__(self, file):
		try:
			with open(file, "w") as f:
				json.dump(self.schedule, f)
			return True
		except:
			return False



