import configparser
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from meowlauncher.common_paths import config_dir
from meowlauncher.common_types import TypeOfConfigValue
from meowlauncher.data.emulated_platforms import pc_platforms, platforms
from meowlauncher.util.io_utils import ensure_exist

from ._config_utils import parse_path_list, parse_string_list, parse_value

_platform_config_path = config_dir.joinpath('platforms.ini')

class PlatformConfig():
	def __init__(self, name: str, paths: Iterable[Path], chosen_emulators: Sequence[str], options: Mapping[str, TypeOfConfigValue]) -> None:
		self.name = name
		self.paths = paths
		self.chosen_emulators = chosen_emulators
		self.options = options

	@property
	def is_available(self) -> bool:
		return bool(self.paths) and bool(self.chosen_emulators)

def _get_config(section: configparser.SectionProxy, platform_name: str) -> PlatformConfig:
	paths = parse_path_list(section.get('paths', ''))
	chosen_emulators = tuple(f'{chosen_emulator} ({platform_name})' if chosen_emulator in {'MAME', 'Mednafen', 'VICE'} else chosen_emulator for chosen_emulator in parse_string_list(section.get('emulators', '')))
	options = {}
	if platform_name in platforms:
		option_definitions = platforms[platform_name].options
		for k, v in option_definitions.items():
			options[k] = parse_value(section, k, v.type, v.default_value)
	elif platform_name in pc_platforms:
		option_definitions = pc_platforms[platform_name].options
		for k, v in option_definitions.items():
			options[k] = parse_value(section, k, v.type, v.default_value)
	return PlatformConfig(platform_name, paths, chosen_emulators, options)

class PlatformConfigs():
	class __PlatformConfigs():
		def __init__(self) -> None:
			parser = configparser.ConfigParser(interpolation=None, delimiters='=', allow_no_value=True)
			parser.optionxform = str #type: ignore[assignment]

			ensure_exist(_platform_config_path)
			parser.read(_platform_config_path)

			self.configs = {platform_name: _get_config(section, platform_name) for platform_name, section in parser.items()}
						
	__instance = None

	@staticmethod
	def getConfigs():
		if PlatformConfigs.__instance is None:
			PlatformConfigs.__instance = PlatformConfigs.__PlatformConfigs()
		return PlatformConfigs.__instance

platform_configs = PlatformConfigs.getConfigs().configs
