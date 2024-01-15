from pathlib import Path
from typing import Generic, TypeVar

from meowlauncher.exceptions import EmulationNotSupportedError
from meowlauncher.game import Game
from meowlauncher.launch_command import LaunchCommand, MultiLaunchCommands

from .runnable import HostPlatform, Runnable

GameType_co = TypeVar('GameType_co', bound=Game, covariant=True)


class Runner(Runnable, Generic[GameType_co]):
	"""Base class for a runner (an emulator, compatibility layer, anything that runs a Game)"""

	def get_wrapped_command(self, command: 'LaunchCommand') -> 'LaunchCommand':
		"""Return a LaunchCommand that launches the runner by itself.
		Applies wrappers according to configuration such as gamemoderun/mangohud, or Wine if this Runner is for Windows, etc"""
		if self.host_platform() == HostPlatform.Windows:
			from .global_runners import Wine

			if isinstance(command, MultiLaunchCommands):
				command = MultiLaunchCommands(
					command.pre_commands,
					Wine().launch_windows_exe(
						command.main_command.exe_name, command.main_command.exe_args
					),
					command.post_commands,
				)
			else:
				command = Wine().launch_windows_exe(command.exe_name, command.exe_args)
		elif self.host_platform() == HostPlatform.DotNet:
			command = command.wrap(Path('mono'))

		# Need to make sure that if runner uses MultiLaunchCommands, the inner command will be run with mangohud:
		# do_setup && mangohud actual_emulator && do_things_after
		# But if it is using Wine I need to make Wine itself run through mangohud and not try and do "wine mangohud blah.exe"
		if self.config.mangohud:
			command = command.wrap(Path('mangohud'))
			command.set_env_var('MANGOHUD_DLSYM', '1')  # Might not be needed, but just in caseq
		if self.config.gamemode:
			command = command.wrap(Path('gamemoderun'))
		if self.config.force_opengl_version:
			command.set_env_var('MESA_GL_VERSION_OVERRIDE', '4.3')
		return command

	def get_game_command(self, game: GameType_co) -> 'LaunchCommand':
		"""Return a LaunchCommand for launching this game with this runner, or raise EmulationNotSupportedError, etc"""
		raise EmulationNotSupportedError(
			f'Default implementation of get_game_command does not launch anything, argument = {game}'
		)


__doc__ = Runner.__doc__ or Runner.__name__
