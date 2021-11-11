import configparser
import os
from typing import Any

from meowlauncher.common_paths import config_dir
from meowlauncher.data.emulated_platforms import pc_platforms, platforms
from meowlauncher.util.io_utils import ensure_exist

from ._config_utils import parse_path_list, parse_string_list, parse_value

_platform_config_path = os.path.join(config_dir, 'platforms.ini')

class PlatformConfig():
	def __init__(self, name: str) -> None:
		self.name = name
		self.paths: list[str] = []
		self.chosen_emulators: list[str] = []
		self.options: dict[str, Any] = {}

	@property
	def is_available(self) -> bool:
		return bool(self.paths) and bool(self.chosen_emulators)

class PlatformConfigs():
	class __PlatformConfigs():
		def __init__(self) -> None:
			self.configs: dict[str, PlatformConfig] = {}
			self.read_configs_from_file()

		def read_configs_from_file(self) -> None:
			parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			parser.optionxform = str #type: ignore

			ensure_exist(_platform_config_path)
			parser.read(_platform_config_path)

			for system_name in parser.sections():
				self.configs[system_name] = PlatformConfig(system_name)

				section = parser[system_name]
				self.configs[system_name].paths = parse_path_list(section.get('paths', ''))
				chosen_emulators = []
				for s in parse_string_list(section.get('emulators', '')):
					if s in ('MAME', 'Mednafen', 'VICE'):
					#Allow for convenient shortcut
						s = '{0} ({1})'.format(s, system_name)
					chosen_emulators.append(s)
				self.configs[system_name].chosen_emulators = chosen_emulators
				if system_name in platforms:
					options = platforms[system_name].options
					for k, v in options.items():
						self.configs[system_name].options[k] = parse_value(section, k, v.type, v.default_value)
				elif system_name in pc_platforms:
					options = pc_platforms[system_name].options
					for k, v in options.items():
						self.configs[system_name].options[k] = parse_value(section, k, v.type, v.default_value)
						
	__instance = None

	@staticmethod
	def getConfigs():
		if PlatformConfigs.__instance is None:
			PlatformConfigs.__instance = PlatformConfigs.__PlatformConfigs()
		return PlatformConfigs.__instance

platform_configs = PlatformConfigs.getConfigs().configs
