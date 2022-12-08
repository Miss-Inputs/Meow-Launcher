import shutil
from pathlib import PurePath
from typing import TYPE_CHECKING, final

from meowlauncher.config.config import main_config

from .launch_command import (LaunchCommand, MultiLaunchCommands,
                             launch_with_wine)
from .runner import HostPlatform

if TYPE_CHECKING:
	from meowlauncher.config_types import RunnerConfig

	from .runner import Runner

class ConfiguredRunner():
	"""Combination of Runner (the info about it) and the configuration for it (including where it is etc), ready to be used to run things"""
	def __init__(self, runner: 'Runner', config: 'RunnerConfig'):
		self.runner = runner
		self.config = config

	@final
	@property
	def name(self) -> str:
		"""This is just runner.name, and has no reason to be anything else"""
		return self.runner.name

	@property
	def is_path_valid(self) -> bool:
		"""Returns true if the default exe name is available on the system path, or if the configured exe path points to a valid executable"""
		return shutil.which(self.config.exe_path) is not None

	def set_wrapper_options(self, command: LaunchCommand) -> LaunchCommand:
		"""Applies wrappers according to configuration such as gamemoderun/mangohud, or Wine if this Runner is for Windows, etc"""
		if self.runner.host_platform == HostPlatform.Windows:
			if isinstance(command, MultiLaunchCommands):
				command = MultiLaunchCommands(command.pre_commands, launch_with_wine(main_config.wine_path, main_config.wineprefix, command.main_command.exe_name, command.main_command.exe_args), command.post_commands)
			else:
				command = launch_with_wine(main_config.wine_path, main_config.wineprefix, command.exe_name, command.exe_args)
		elif self.runner.host_platform == HostPlatform.DotNet:
			command = command.wrap(PurePath('mono'))

		#Need to make sure that if runner uses MultiLaunchCommands, the inner command will be run with mangohud:
		#do_setup && mangohud actual_emulator && do_things_after - it does, good
		#But if it is using Wine I need to make Wine itself run through mangohud and not try and do "wine mangohud blah.exe" - it does, good
		if self.config.options.get('mangohud', False):
			command = command.wrap(PurePath('mangohud'))
			command.set_env_var('MANGOHUD_DLSYM', '1')
		if self.config.options.get('gamemode', False):
			command = command.wrap(PurePath('gamemoderun'))
		if self.config.options.get('force_opengl_version', False):
			command.set_env_var('MESA_GL_VERSION_OVERRIDE', '4.3')
		return command	

	def __hash__(self) -> int:
		return self.runner.__hash__()
		
__doc__ = ConfiguredRunner.__doc__ or ConfiguredRunner.__name__
