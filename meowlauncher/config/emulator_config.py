from typing import TYPE_CHECKING

from meowlauncher.common_paths import config_dir
from meowlauncher.config_types import EmulatorConfig, RunnerConfigValue
from meowlauncher.data.emulators import all_emulators
from meowlauncher.util.io_utils import ensure_exist
from meowlauncher.util.utils import NoNonsenseConfigParser

from ._config_utils import parse_value

if TYPE_CHECKING:
	import configparser
	from collections.abc import Mapping


_emulator_config_path = config_dir.joinpath('emulators.ini')

def _get_config(parser: 'configparser.RawConfigParser', config_name: str, default_exe_name: str, configs: 'Mapping[str, RunnerConfigValue]') -> EmulatorConfig:
	options = {}
		
	if config_name in parser:
		section = parser[config_name]
		exe_path = parse_value(section, 'path', str, default_exe_name)
		assert isinstance(exe_path, str), f'exe_path is not a string!! It is {type(exe_path)} {exe_path!r}' #It should be a str because it could just be default_exe_name, but then maybe that's not good, or is it
		for k, v in configs.items():
			options[k] = parse_value(section, k, v.type, v.default_value)
	else:
		exe_path = default_exe_name
		for k, v in configs.items():
			options[k] = v.default_value
	return EmulatorConfig(exe_path, options)

class EmulatorConfigs():
	class __EmulatorConfigs():
		def __init__(self) -> None:
			parser = NoNonsenseConfigParser(allow_no_value=True)
			ensure_exist(_emulator_config_path)
			parser.read(_emulator_config_path)

			self.configs = {emulator.config_name: _get_config(parser, emulator.config_name, emulator.default_exe_name, emulator.configs) for emulator in all_emulators}
				
	__instance = None

	@staticmethod
	def getConfigs() -> __EmulatorConfigs:
		if EmulatorConfigs.__instance is None:
			EmulatorConfigs.__instance = EmulatorConfigs.__EmulatorConfigs()
		return EmulatorConfigs.__instance

emulator_configs = EmulatorConfigs.getConfigs().configs
