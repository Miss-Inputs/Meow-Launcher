from meowlauncher.config.main_config import main_config

from .configured_runner import ConfiguredRunner
from .runner import Runner
from .runner_config import RunnerConfig


class _Wine(Runner):
	@property
	def name(self) -> str:
		return 'Wine'

	@property
	def is_emulated(self) -> bool:
		return True #Yeah, I know… I just think it makes more sene to call it one

	#TODO: We should do something with launch_with_wine

class _WineConfig(RunnerConfig):
	def __init__(self, exe_path: str):
		super().__init__(exe_path)

class Wine(ConfiguredRunner):
	def __init__(self, config: RunnerConfig):
		super().__init__(_Wine(), config)

class _ScummVM(Runner):
	@property
	def name(self) -> str:
		return 'ScummVM'

wine = Wine(_WineConfig(main_config.wine_path))
scummvm = _ScummVM()
