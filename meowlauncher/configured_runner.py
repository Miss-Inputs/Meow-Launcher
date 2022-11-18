import os
import shutil
from typing import TYPE_CHECKING

from meowlauncher.config.main_config import main_config

from .launch_command import (LaunchCommand, MultiLaunchCommands,
                             launch_with_wine)
from .runner import HostPlatform

if TYPE_CHECKING:
	from meowlauncher.config_types import RunnerConfig

	from .runner import Runner

class ConfiguredRunner():
	def __init__(self, runner: 'Runner', config: 'RunnerConfig'):
		self.runner = runner
		self.config = config

	@property
	def name(self) -> str:
		return self.runner.name

	@property
	def is_emulated(self) -> bool:
		return self.runner.is_emulated

	@property
	def is_path_valid(self) -> bool:
		if os.path.isfile(self.config.exe_path):
			return True
		if shutil.which(self.config.exe_path):
			return True
		return False

	def set_wrapper_options(self, command: LaunchCommand) -> LaunchCommand:
		if self.runner.host_platform == HostPlatform.Windows:
			if isinstance(command, MultiLaunchCommands):
				command = MultiLaunchCommands(command.pre_commands, launch_with_wine(main_config.wine_path, main_config.wineprefix, command.main_command.exe_name, command.main_command.exe_args), command.post_commands)
			else:
				command = launch_with_wine(main_config.wine_path, main_config.wineprefix, command.exe_name, command.exe_args)
		elif self.runner.host_platform == HostPlatform.DotNet:
			command = command.wrap('mono')

		#Need to make sure that if runner uses MultiLaunchCommands, the inner command will be run with mangohud:
		#do_setup && mangohud actual_emulator && do_things_after - it does, good
		#But if it is using Wine I need to make Wine itself run through mangohud and not try and do "wine mangohud blah.exe" - it does, good
		if self.config.options.get('mangohud', False):
			command = command.wrap('mangohud')
			command.set_env_var('MANGOHUD_DLSYM', '1')
		if self.config.options.get('gamemode', False):
			command = command.wrap('gamemoderun')
		if self.config.options.get('force_opengl_version', False):
			command.set_env_var('MESA_GL_VERSION_OVERRIDE', '4.3')
		return command	

	def __hash__(self) -> int:
		return self.runner.__hash__()
		