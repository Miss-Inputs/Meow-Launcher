import configparser
from collections.abc import Mapping
from typing import cast

from meowlauncher.common_paths import config_dir
from meowlauncher.common_types import ConfigValueType
from meowlauncher.data.emulators import all_emulators
from meowlauncher.runner_config import EmulatorConfig, RunnerConfigValue
from meowlauncher.util.io_utils import ensure_exist

from ._config_utils import parse_value

_emulator_config_path = config_dir.joinpath('emulators.ini')

class EmulatorConfigs():
	class __EmulatorConfigs():
		def __init__(self) -> None:
			self.configs: dict[str, EmulatorConfig] = {}
			parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			parser.optionxform = str #type: ignore[assignment]

			ensure_exist(_emulator_config_path)
			parser.read(_emulator_config_path)

			for emulator in all_emulators:
				#Every emulator will need its own entry in this dict
				self._add_config(parser, emulator.config_name, emulator.default_exe_name, emulator.configs)
				
		def _add_config(self, parser: configparser.ConfigParser, config_name: str, default_exe_name: str, configs: Mapping[str, RunnerConfigValue]):
			options = {}
				
			if config_name in parser:
				section = parser[config_name]
				exe_path = parse_value(section, 'path', ConfigValueType.String, default_exe_name)
				if not isinstance(exe_path, str): #It should be a str because it could just be default_exe_name, but then maybe that's not good
					raise AssertionError(f'exe_path is not a string!! It is {type(exe_path)} {repr(exe_path)}')
				for k, v in configs.items():
					options[k] = parse_value(section, k, v.type, v.default_value)
			else:
				exe_path = default_exe_name
				for k, v in configs.items():
					options[k] = v.default_value
			self.configs[config_name] = EmulatorConfig(exe_path, options)

	__instance = None

	@staticmethod
	def getConfigs():
		if EmulatorConfigs.__instance is None:
			EmulatorConfigs.__instance = EmulatorConfigs.__EmulatorConfigs()
		return EmulatorConfigs.__instance

emulator_configs = EmulatorConfigs.getConfigs().configs
