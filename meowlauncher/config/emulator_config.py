import configparser
import os

from meowlauncher.common_paths import config_dir
from meowlauncher.common_types import ConfigValueType
from meowlauncher.data.emulators import all_emulators
from meowlauncher.runner_config import EmulatorConfig
from meowlauncher.util.io_utils import ensure_exist

from ._config_utils import parse_value

_emulator_config_path = os.path.join(config_dir, 'emulators.ini')

class EmulatorConfigs():
	class __EmulatorConfigs():
		def __init__(self) -> None:
			self.configs: dict[str, EmulatorConfig] = {}
			self.read_configs_from_file()

		def read_configs_from_file(self) -> None:
			parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			parser.optionxform = str #type: ignore[assignment]

			ensure_exist(_emulator_config_path)
			parser.read(_emulator_config_path)

			for name, emulator in all_emulators.items():
				#Every emulator will need its own entry in this dict
				exe_path: str
				options = {}

				if name in parser:
					section = parser[name]
					exe_path = parse_value(section, 'path', ConfigValueType.String, emulator.default_exe_name)
					for k, v in emulator.configs.items():
						options[k] = parse_value(section, k, v.type, v.default_value)
				else:
					exe_path = emulator.default_exe_name
					for k, v in emulator.configs.items():
						options[k] = v.default_value
				self.configs[name] = EmulatorConfig(exe_path, options)

	__instance = None

	@staticmethod
	def getConfigs():
		if EmulatorConfigs.__instance is None:
			EmulatorConfigs.__instance = EmulatorConfigs.__EmulatorConfigs()
		return EmulatorConfigs.__instance

emulator_configs = EmulatorConfigs.getConfigs().configs
