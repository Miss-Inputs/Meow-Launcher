import configparser
import os

from common_paths import config_dir
from info.emulator_info import emulators
from io_utils import ensure_exist
from common_types import ConfigValueType

from ._config_utils import parse_value

_emulator_config_path = os.path.join(config_dir, 'emulators.ini')

class EmulatorConfig():
	def __init__(self, name):
		self.name = name
		self.exe_path = None
		self.options = {}

class EmulatorConfigs():
	class __EmulatorConfigs():
		def __init__(self):
			self.configs = {}
			self.read_configs_from_file()

		def read_configs_from_file(self):
			parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			parser.optionxform = str

			ensure_exist(_emulator_config_path)
			parser.read(_emulator_config_path)

			for name, emulator in emulators.items():
				#Every emulator will need its own entry in this dict
				self.configs[name] = EmulatorConfig(name)
				if name in parser:
					section = parser[name]
					self.configs[name].exe_path = parse_value(section, 'path', ConfigValueType.String, emulator.default_exe_name)
					for k, v in emulator.configs.items():
						self.configs[name].options[k] = parse_value(section, k, v.type, v.default_value)
				else:
					self.configs[name].exe_path = emulator.default_exe_name
					for k, v in emulator.configs.items():
						self.configs[name].options[k] = v.default_value

	__instance = None

	@staticmethod
	def getConfigs():
		if EmulatorConfigs.__instance is None:
			EmulatorConfigs.__instance = EmulatorConfigs.__EmulatorConfigs()
		return EmulatorConfigs.__instance

emulator_configs = EmulatorConfigs.getConfigs().configs
