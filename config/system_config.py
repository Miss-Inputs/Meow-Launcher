import configparser
import os

from common_paths import config_dir
from info.system_info import computer_systems, systems
from io_utils import ensure_exist

from ._config_utils import parse_path_list, parse_string_list, parse_value

_system_config_path = os.path.join(config_dir, 'systems.ini')

class SystemConfig():
	def __init__(self, name):
		self.name = name
		self.paths = []
		self.chosen_emulators = []
		self.specific_config = {}

	@property
	def is_available(self):
		return bool(self.paths) and bool(self.chosen_emulators)

class SystemConfigs():
	class __SystemConfigs():
		def __init__(self):
			self.configs = {} #This will be an array of SystemConfig objects and that's fine and I don't think I need to refactor that right now
			self.read_configs_from_file()

		def read_configs_from_file(self):
			parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			parser.optionxform = str

			ensure_exist(_system_config_path)
			parser.read(_system_config_path)

			for system_name in parser.sections():
				self.configs[system_name] = SystemConfig(system_name)

				section = parser[system_name]
				self.configs[system_name].paths = parse_path_list(section.get('paths', ''))
				chosen_emulators = []
				for s in parse_string_list(section.get('emulators', '')):
					if s in ('MAME', 'Mednafen', 'VICE'):
					#Allow for convenient shortcut
						s = '{0} ({1})'.format(s, system_name)
					chosen_emulators.append(s)
				self.configs[system_name].chosen_emulators = chosen_emulators
				if system_name in systems:
					#Hmm… having to import systems for this doesn't seem right
					specific_configs = systems[system_name].specific_configs
					for k, v in specific_configs.items():
						self.configs[system_name].specific_config[k] = parse_value(section, k, v.type, v.default_value)
				elif system_name in computer_systems:
					specific_configs = computer_systems[system_name].specific_configs
					for k, v in specific_configs.items():
						self.configs[system_name].specific_config[k] = parse_value(section, k, v.type, v.default_value)
						
	__instance = None

	@staticmethod
	def getConfigs():
		if SystemConfigs.__instance is None:
			SystemConfigs.__instance = SystemConfigs.__SystemConfigs()
		return SystemConfigs.__instance

system_configs = SystemConfigs.getConfigs().configs
