import collections

from enum import Enum, auto
from input_metadata import InputInfo
from common_types import MediaType, SaveType
from launchers import metadata_section_name, image_section_name

class EmulationStatus(Enum):
	Good = auto()
	Imperfect = auto()
	Broken = auto()
	Unknown = auto()

class CPU():
	def __init__(self):
		self.chip_name = None
		self.clock_speed = None
		self.tag = None

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
			return CPU.format_clock_speed(self.clock_speed)
		return None

	def load_from_xml(self, xml):
		self.chip_name = xml.attrib.get('name')
		self.tag = xml.attrib.get('tag')
		if xml.attrib['name'] != 'Netlist CPU Device' and 'clock' in xml.attrib:
			try:
				self.clock_speed = int(xml.attrib['clock'])
			except ValueError:
				pass

def _format_count(list_of_something):
	counter = collections.Counter(list_of_something)
	if len(counter) == 1:
		if list(counter.keys())[0] is None:
			return None
	return ' + '.join([value if count == 1 else '{0} * {1}'.format(value, count) for value, count in counter.items() if value])

class CPUInfo():
	def __init__(self):
		self.cpus = []
		self._inited = False

	@property
	def is_inited(self):
		return self.cpus or self._inited

	def set_inited(self):
		self._inited = True

	@property
	def main_chip(self):
		if not self.cpus:
			return None
		return self.cpus[0]

	@property
	def number_of_cpus(self):
		return len(self.cpus)

	@property
	def chip_names(self):
		return _format_count([cpu.chip_name for cpu in self.cpus])

	@property
	def clock_speeds(self):
		return _format_count([cpu.get_formatted_clock_speed() for cpu in self.cpus])

	@property
	def tags(self):
		return _format_count([cpu.tag for cpu in self.cpus])

	def add_cpu(self, cpu):
		self.cpus.append(cpu)

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
			return CPU.format_clock_speed(self.refresh_rate)
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
		#TODO: Set screen_info up right here, and just keep track of whether it's inited or not
		self.cpu_info = CPUInfo()
		self.screen_info = None
		self.input_info = InputInfo()

		#I guess you could call this internal use only
		self.specific_info = {} #Stuff specific to indivdidual systems (in theory, or just when I'm too lazy to put it as an attribute here)
		self.tv_type = None
		self.ignored_filename_tags = []

		self.images = {}

	def to_launcher_fields(self):
		fields = {}

		metadata_fields = {
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
			'Media-Type': ('Optical Disc' if self.media_type == MediaType.OpticalDisc else self.media_type.name) if self.media_type else None,

			'Ignored-Tags': self.ignored_filename_tags,
			'TV-Type': self.tv_type.name if self.tv_type else None,
		}

		if self.cpu_info.is_inited:
			metadata_fields['Number-of-CPUs'] = self.cpu_info.number_of_cpus
			if self.cpu_info.number_of_cpus:
				metadata_fields['Main-CPU'] = self.cpu_info.chip_names
				metadata_fields['Clock-Speed'] = self.cpu_info.clock_speeds
				metadata_fields['CPU-Tags'] = self.cpu_info.tags

		if self.screen_info:
			num_screens = self.screen_info.get_number_of_screens()
			metadata_fields['Number-of-Screens'] = num_screens

			if num_screens:
				metadata_fields['Screen-Resolution'] = self.screen_info.get_screen_resolutions()
				metadata_fields['Refresh-Rate'] = self.screen_info.get_refresh_rates()
				metadata_fields['Aspect-Ratio'] = self.screen_info.get_aspect_ratios()

				metadata_fields['Screen-Type'] = self.screen_info.get_display_types()
				metadata_fields['Screen-Tag'] = self.screen_info.get_display_tags()

		if self.input_info.is_inited:
			metadata_fields['Standard-Input'] = self.input_info.has_standard_inputs
			metadata_fields['Input-Methods'] = self.input_info.describe()

		for k, v in self.specific_info.items():
			metadata_fields[k] = v.name if isinstance(v, Enum) else v

		fields[metadata_section_name] = metadata_fields

		if self.images:
			fields[image_section_name] = {}
			for k, v in self.images.items():
				fields[image_section_name][k] = v

		return fields
