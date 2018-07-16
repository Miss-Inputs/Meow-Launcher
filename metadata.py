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
		self.save_type = SaveType.Unknown

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
			'Languages': self.languages,
			'Year': self.year,
			'Author': self.author,
			'Main-CPU': self.main_cpu,
			'Input-Method': self.input_method,
			'Emulator': self.emulator_name,
			'Extension': self.extension,
			'Categories': self.categories,
			'Platform': self.platform,
			'Save-Type': ('Memory Card' if self.save_type == SaveType.MemoryCard else self.save_type.name) if self.save_type else 'Nothing',
	
			'Regions': [region.name if region else 'None!' for region in self.regions],
			'TV-Type': self.tv_type.name if self.tv_type else None,
		}

		for k, v in self.specific_info.items():
			fields[k] = v.name if isinstance(v, Enum) else v

		return fields
