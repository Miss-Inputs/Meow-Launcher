from typing import TYPE_CHECKING
from meowlauncher.common_paths import config_dir
from meowlauncher.config_types import PlatformConfig
from meowlauncher.data.emulated_platforms import (manually_specified_platforms,
                                                  platforms)
from meowlauncher.util.io_utils import ensure_exist
from meowlauncher.util.utils import NoNonsenseConfigParser

from ._config_utils import parse_path_list, parse_string_list, parse_value

if TYPE_CHECKING:
	import configparser

_platform_config_path = config_dir.joinpath('platforms.ini')

def _get_config(section: 'configparser.SectionProxy', platform_name: str) -> PlatformConfig:
	paths = parse_path_list(section.get('paths', ''))
	chosen_emulators = tuple(f'{chosen_emulator} ({platform_name})' if chosen_emulator in {'MAME', 'Mednafen', 'VICE'} else chosen_emulator for chosen_emulator in parse_string_list(section.get('emulators', '')))
	options = {}
	if platform_name in platforms:
		option_definitions = platforms[platform_name].options
		for k, v in option_definitions.items():
			options[k] = parse_value(section, k, v.type, v.default_value)
	elif platform_name in manually_specified_platforms:
		option_definitions = manually_specified_platforms[platform_name].options
		for k, v in option_definitions.items():
			options[k] = parse_value(section, k, v.type, v.default_value)
	return PlatformConfig(platform_name, paths, chosen_emulators, options)

class PlatformConfigs():
	class __PlatformConfigs():
		def __init__(self) -> None:
			parser = NoNonsenseConfigParser(allow_no_value=True)
			ensure_exist(_platform_config_path)
			parser.read(_platform_config_path)

			self.configs = {platform_name: _get_config(section, platform_name) for platform_name, section in parser.items()}
						
	__instance = None

	@staticmethod
	def getConfigs() -> __PlatformConfigs:
		if PlatformConfigs.__instance is None:
			PlatformConfigs.__instance = PlatformConfigs.__PlatformConfigs()
		return PlatformConfigs.__instance

platform_configs = PlatformConfigs.getConfigs().configs
