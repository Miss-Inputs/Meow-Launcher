from enum import Enum, auto

from mame_machines import get_mame_xml

class EmulationStatus(Enum):
	Good = auto()
	Imperfect = auto()
	Broken = auto()
	Unknown = auto()

#TODO: Can you please think of a less verbose way to word this
class SystemSpecificInfo():
	def __init__(self, name, value, should_output_in_launcher):
		self.name = name
		self.value = value
		self.should_output_in_launcher = should_output_in_launcher

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
		self.main_cpu = None
		self.input_method = None
		self.emulator_name = None
		self.extension = None
		self.platform = None
		self.categories = []

		#Not part of the little standard I invented on the wiki
		self.system_specific_info = []
		self.regions = []
		self.tv_type = None

	def get_system_specific_info(self, name, default=None):
		for metadatum in self.system_specific_info:
			if metadatum.name == name:
				return metadatum.value
		
		return default


	def to_launcher_fields(self):
		fields = {
			'Emulation-Status': self.emulation_status.name if self.emulation_status else None,
			'Genre': self.genre,
			'Subgenre': self.subgenre,
			'NSFW': self.nsfw,
			'Languages': self.languages,
			'Year': self.year,
			'Author': self.author,
			'Main-CPU': self.main_cpu,
			'Input-Method': self.input_method,
			'Emulator': self.emulator_name,
			'Extension': self.extension,
			'Categories': self.categories,
			'Platform': self.platform,
	
			'Regions': [region.name if region else 'None!' for region in self.regions],
			'TV-Type': self.tv_type.name if self.tv_type else None,
		}

		for system_specific_metadatum in self.system_specific_info:
			if system_specific_metadatum.should_output_in_launcher:
				fields[system_specific_metadatum.name] = system_specific_metadatum.value

		return fields

lookup_system_cpu_cache = {}
def lookup_system_cpu(driver_name):
	if driver_name in lookup_system_cpu_cache:
		return lookup_system_cpu_cache[driver_name]

	xml = get_mame_xml(driver_name)
	if not xml:
		lookup_system_cpu_cache[driver_name] = None
		return None
	machine = xml.find('machine')
	if not machine:
		lookup_system_cpu_cache[driver_name] = None
		return None

	main_cpu = mame_machines.find_main_cpu(machine)
	if main_cpu is not None: #"if main_cpu: doesn't work. Frig! Why not! Wanker! Sodding bollocks!
		main_cpu_name = main_cpu.attrib['name']
		lookup_system_cpu_cache[driver_name] = main_cpu_name
		return main_cpu_name

	return None
