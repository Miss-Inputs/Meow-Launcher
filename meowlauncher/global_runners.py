from meowlauncher.config.main_config import main_config
from meowlauncher.config_types import (ConfigValueType, RunnerConfig,
                                       RunnerConfigValue)

from .configured_runner import ConfiguredRunner
from .runner import Runner


class _Wine(Runner):
	def __init__(self) -> None:
		super().__init__()
		self.configs.update({
			#TODO: We should find a way to just get this description etc from main_config.wineprefix
			'wineprefix': RunnerConfigValue(ConfigValueType.FolderPath, None, 'WINEPREFIX env var')
		})

	@property
	def name(self) -> str:
		return 'Wine'

	@property
	def is_emulated(self) -> bool:
		return True #Yeah, I know… I just think it makes more sene to call it one

	#TODO: We should do something with launch_with_wine

class _WineConfig(RunnerConfig):
	def __init__(self, exe_path: str, wineprefix: str=None):
		super().__init__(exe_path, {'wineprefix': wineprefix})

class Wine(ConfiguredRunner):
	def __init__(self, config: RunnerConfig):
		super().__init__(_Wine(), config)

class _ScummVM(Runner):
	@property
	def name(self) -> str:
		return 'ScummVM'

class ScummVM(ConfiguredRunner):
	def __init__(self) -> None:
		config = RunnerConfig(str(main_config.scummvm_exe_path))
		super().__init__(_ScummVM(), config)

wine = Wine(_WineConfig(main_config.wine_path, main_config.wineprefix))
scummvm = ScummVM()
