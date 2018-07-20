from enum import Enum, auto

class EmulationStatus(Enum):
	Good = auto()
	Imperfect = auto()
	Broken = auto()
	Unknown = auto()

class SaveType(Enum):
	Nothing = auto()
	Cart = auto()
	Floppy = auto()
	MemoryCard = auto()
	Internal = auto()
	Unknown = auto()

class CPUInfo():
	def __init__(self):
		self.main_cpu = None
		self.clock_speed = None

	@staticmethod
	def format_clock_speed(hertz, precision=4):
		if hertz >= 1_000_000_000:
			return ('{0:.' + str(precision) + 'g} GHz').format(hertz / 1_000_000_000)
		elif hertz >= 1_000_000:
			return ('{0:.' + str(precision) + 'g} MHz').format(hertz / 1_000_000)
		elif hertz >= 1_000:
			return ('{0:.' + str(precision) + 'g} KHz').format(hertz / 1_000)
		
		return ('{0:.' + str(precision) + 'g} Hz').format(hertz)

	def get_formatted_clock_speed(self):
		if self.clock_speed:
			return CPUInfo.format_clock_speed(self.clock_speed)
		return None

	def load_from_xml(self, xml):
		self.main_cpu = xml.attrib['name']
		if xml.attrib['name'] != 'Netlist CPU Device' and 'clock' in xml.attrib:
			try:
				self.clock_speed = int(xml.attrib['clock'])
			except ValueError:
				pass

class Screen():
	def __init__(self):
		self.width = None
		self.height = None
		self.type = None
		self.tag = None
		self.refresh_rate = None

	def get_screen_resolution(self):
		if self.type == 'raster' or self.type == 'lcd':
			return '{0:.0f}x{1:.0f}'.format(self.width, self.height)
		#Other types are vector (Asteroids, etc) or svg (Game & Watch games, etc)
		return self.type.capitalize() if self.type else None

	def load_from_xml(self, xml):
		self.type = xml.attrib['type']
		self.tag = xml.attrib['tag']
		if self.type == 'raster' or self.type == 'lcd':
			self.width = float(xml.attrib['width'])
			self.height = float(xml.attrib['height'])
		
		if 'refresh' in xml.attrib:
			try:
				self.refresh_rate = float(xml.attrib['refresh'])
			except ValueError:
				pass

	def get_formatted_refresh_rate(self):
		if self.refresh_rate:
			return CPUInfo.format_clock_speed(self.refresh_rate)
		return None

	def get_aspect_ratio(self):
		if self.width and self.height:
			return Screen.find_aspect_ratio(self.width, self.height)
		return None

	@staticmethod
	def find_aspect_ratio(width, height):
		for i in reversed(range(1, max(int(width), int(height)) + 1)):
			if (width % i) == 0 and (height % i) == 0:
				return '{0:.0f}:{1:.0f}'.format(width // i, height // i)

		#This wouldn't happen unless one of the arguments is 0 or something silly like that
		return None
	
class ScreenInfo():
	def __init__(self):
		self.screens = []
	
	def get_number_of_screens(self):
		return len(self.screens)

	def load_from_xml_list(self, xmls):
		for display in xmls:
			screen = Screen()
			screen.load_from_xml(display)
			self.screens.append(screen)

	def get_screen_resolutions(self):
		return ' + '.join(screen.get_screen_resolution() for screen in self.screens if screen.get_screen_resolution())

	def get_refresh_rates(self):
		return ' + '.join(screen.get_formatted_refresh_rate() for screen in self.screens if screen.get_formatted_refresh_rate())

	def get_aspect_ratios(self):
		return ' + '.join(screen.get_aspect_ratio() for screen in self.screens if screen.get_aspect_ratio())

	def get_display_types(self):
		return ' + '.join(screen.type for screen in self.screens if screen.type)

	def get_display_tags(self):
		return ' + '.join(screen.tag for screen in self.screens if screen.tag)

	

class Metadata():
	def __init__(self):
		#Watch pylint whine that I have "too many instance attributes", I'm calling it now
		self.emulation_status = EmulationStatus.Unknown
		self.genre = None
		self.subgenre = None
		self.nsfw = False
		self.languages = []
		self.year = None
		self.author = None
		self.input_method = None
		self.emulator_name = None
		self.extension = None
		self.platform = None
		self.categories = []
		self.save_type = SaveType.Unknown
		
		#Set this up later with the respective objects
		self.cpu_info = None
		self.screen_info = None

		#Not part of the little standard I invented on the wiki
		self.specific_info = {} #Stuff specific to indivdidual systems
		self.regions = []
		self.tv_type = None

	def to_launcher_fields(self):
		fields = {
			'Emulation-Status': self.emulation_status.name if self.emulation_status else None,
			'Genre': self.genre,
			'Subgenre': self.subgenre,
			'NSFW': self.nsfw,
			'Languages': [language.name if language else 'None!' for language in self.languages],
			'Year': self.year,
			'Author': self.author,
			'Input-Method': self.input_method,
			'Emulator': self.emulator_name,
			'Extension': self.extension,
			'Categories': self.categories,
			'Platform': self.platform,
			'Save-Type': ('Memory Card' if self.save_type == SaveType.MemoryCard else self.save_type.name) if self.save_type else 'Nothing',
	
			'Regions': [region.name if region else 'None!' for region in self.regions],
			'TV-Type': self.tv_type.name if self.tv_type else None,
		}

		if self.cpu_info:
			fields['Main-CPU'] = self.cpu_info.main_cpu
			fields['Clock-Speed'] = self.cpu_info.get_formatted_clock_speed()

		if self.screen_info:
			fields['Screen-Resolution'] = self.screen_info.get_screen_resolutions()
			fields['Refresh-Rate'] = self.screen_info.get_refresh_rates()
			fields['Number-of-Screens'] = self.screen_info.get_number_of_screens()
			fields['Aspect-Ratio'] = self.screen_info.get_aspect_ratios()

			fields['Screen-Type'] = self.screen_info.get_display_types()
			fields['Screen-Tag'] = self.screen_info.get_display_tags()

		
		for k, v in self.specific_info.items():
			fields[k] = v.name if isinstance(v, Enum) else v

		return fields
