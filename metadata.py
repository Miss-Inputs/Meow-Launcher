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

class InputType(Enum):
	Digital = auto()
	Analog = auto()
	Biological = auto() #e.g. MindLink for 2600 (which actually just senses your eyebrow muscles) or N64 heart rate sensor
	Dial = auto()
	Gambling = auto()
	Hanafuda = auto()
	Keyboard = auto()
	Keypad = auto()
	LightGun = auto()
	Mahjong = auto()
	MotionControls = auto()
	Mouse = auto()
	Paddle = auto()
	Pedal = auto()
	Positional = auto()
	SteeringWheel = auto()
	Touchscreen = auto()
	Trackball = auto()
	Custom = auto()

class InputInfo():
	def __init__(self):
		self.inputs = []
		self.buttons = 0
		self._known = False

	@property
	def known(self):
		#Need a better name for this. Basically determines if this has been initialized and hence the information is not missing
		return self.inputs or self.buttons or self._known

	@property
	def is_standard(self):
		"""
		If this input setup is compatible with a standard modern controller: 4 face buttons, 2 shoulder buttons, 2 analog triggers, 2 analog sticks, one dpad, start + select. Dunno how I feel about clickable analog sticks. Also any "guide" or "home" button doesn't count, because that should be free for emulator purposes instead of needing the game to map to it. Hmm. Maybe analog triggers aren't that standard. Some modern gamepads just have 2 more shoulder buttons instead, after all.
		So if your gamepad has more stuff than this "standard" one, which it probably does, that's great, it just means it can support non-standard emulated controls.
		"""
		#TODO: Get more involved with the placement of buttons, analog triggers, all of that stuff. Go all out.
		#Right now, 6 buttons all placed in a single row would be considered fine, even though they wouldn't, and even though I would have to invent some representation of a button layout in code (but I would totes be down for that). Also analog triggers are not fine.
		#Also some EPROM programmers are listed as "standard". I mean... I guess? They got two buttons? But like... no
		digitals = len([input for input in self.inputs if input == InputType.Digital])
		analogs = len([input for input in self.inputs if input == InputType.Analog])
		anything_else = [input for input in self.inputs if input not in (InputType.Analog, InputType.Digital)]
		if anything_else:
			return False

		if analogs > 2:
			return False
		if digitals > 1:
			if (digitals + analogs) > 3:
				#It's okay to have two digital joysticks if one can just be mapped to one of the analog sticks
				return False

		return self.buttons > 0 and self.buttons <= 6

	def set_known(self):
		self._known = True

	def describe(self):
		if self.is_standard:
			return ['Standard']

		input_set = set(self.inputs)
		if not input_set:
			return ['Only Buttons'] if self.buttons else ['Nothing']
		description = set()
		for my_input in input_set:
			if my_input == InputType.LightGun:
				description.add('Light Gun')
			elif my_input == InputType.MotionControls:
				description.add('Motion Controls')
			elif my_input == InputType.SteeringWheel:
				description.add('Steering Wheel')
			else:
				description.add(my_input.name)
		return list(description)

class Metadata():
	def __init__(self):
		#Watch pylint whine that I have "too many instance attributes", I'm calling it now
		self.genre = None
		self.subgenre = None
		self.nsfw = False
		self.languages = []
		self.year = None
		self.month = None
		self.day = None
		self.developer = None
		self.publisher = None
		self.emulator_name = None
		self.extension = None
		self.platform = None
		self.categories = []
		self.save_type = SaveType.Unknown
		self.revision = None
		self.product_code = None
		self.regions = []
		self.media_type = None

		#Set this up later with the respective objects
		#TODO: Set cpu_info and screen_info up right here, and just keep track of whether they're "known" or not like input_info does
		self.cpu_info = None
		self.screen_info = None
		self.input_info = InputInfo()

		#I guess you could call this internal use only
		self.specific_info = {} #Stuff specific to indivdidual systems
		self.tv_type = None
		self.ignored_filename_tags = []

	def to_launcher_fields(self):
		fields = {
			'Genre': self.genre,
			'Subgenre': self.subgenre,
			'NSFW': self.nsfw,
			'Languages': [language.native_name for language in self.languages if language],
			'Year': self.year,
			'Month': self.month,
			'Day': self.day,
			'Emulator': self.emulator_name,
			'Extension': self.extension,
			'Categories': self.categories,
			'Platform': self.platform,
			'Save-Type': ('Memory Card' if self.save_type == SaveType.MemoryCard else self.save_type.name) if self.save_type else 'Nothing',
			'Revision': self.revision,
			'Publisher': self.publisher,
			'Developer': self.developer,
			'Product-Code': self.product_code,
			'Regions': [region.name if region else 'None!' for region in self.regions] if self.regions else [],
			'Media-Type': self.media_type.name if self.media_type else None,

			'Ignored-Tags': self.ignored_filename_tags,
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

		if self.input_info.known:
			fields['Number-of-Buttons'] = self.input_info.buttons
			fields['Input-Methods'] = self.input_info.describe()

		for k, v in self.specific_info.items():
			fields[k] = v.name if isinstance(v, Enum) else v

		return fields
