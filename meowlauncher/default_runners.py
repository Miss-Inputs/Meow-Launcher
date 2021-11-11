from typing import Iterable, Optional
from meowlauncher.config.main_config import main_config
from meowlauncher.launcher import LaunchCommand
from meowlauncher.runner import Runner

class _Wine(Runner):
	@property
	def name(self) -> str:
		return 'Wine'

	@property
	def is_emulated(self) -> bool:
		return True

	#TODO: We should do something with this
	def get_wine_launch_params(self, exe_path: str, exe_args: Iterable[str], working_directory: Optional[str]=None) -> LaunchCommand:
		env_vars = None
		if main_config.wineprefix:
			env_vars = {'WINEPREFIX': main_config.wineprefix}

		args = ['start']
		if working_directory:
			args += ['/d', working_directory]
		args += ['/unix', exe_path]
		args += exe_args
		return LaunchCommand(main_config.wine_path, args, env_vars)

wine = _Wine()
