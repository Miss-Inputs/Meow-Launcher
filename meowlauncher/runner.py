import shutil
from abc import ABC, abstractmethod
from enum import Enum, auto
from functools import cache
from pathlib import Path
from typing import Generic, TypeVar

from meowlauncher.exceptions import EmulationNotSupportedError
from meowlauncher.game import Game
from meowlauncher.launch_command import LaunchCommand, MultiLaunchCommands
from meowlauncher.settings.settings import Settings


class HostPlatform(Enum):
	"""Platforms that runners/emulators could use"""

	Linux = auto()  # Assume this means x86 for now
	Windows = auto()
	DotNet = auto()
	Java = auto()
	Love = auto()
	HTML = auto()
	DOS = auto()


class BaseRunnerConfig(Settings):
	"""All runners would have this config. Section not defined here, so it is still abstract"""

	path: Path | None = None
	"""Path to the runner's executable, or if None, use the default exe name and the launcher can look for it in the system path when run"""

	gamemode: bool = False
	"""Run this with gamemoderun"""

	mangohud: bool = False
	"""Run this with MangoHUD"""

	force_opengl_version: bool = False
	"""Forces Mesa OpenGL version to 4.3 via environment variable if you need it
	Is this still needed? I don't know"""


@cache
def _make_default_config(name: str) -> type[BaseRunnerConfig]:
	"""The cache is important here because who knows what screwiness would result if you just returned a new class every time you accessed config_class"""

	class RunnerConfig(BaseRunnerConfig):
		_is_boilerplate = True

		@classmethod
		def section(cls) -> str:
			return name

		@classmethod
		def prefix(cls) -> str:
			return name.lower()

	return RunnerConfig


GameType = TypeVar('GameType', bound=Game)


class Runner(ABC, Generic[GameType]):
	"""Base class for a runner (an emulator, compatibility layer, anything that runs a thing)"""

	def __init__(self) -> None:
		from meowlauncher.config import current_config

		config_class = self.config_class()
		self.config = current_config(config_class)

	@classmethod
	def host_platform(cls) -> HostPlatform:
		"""The platform that this runs on, by default will be Linux"""
		return HostPlatform.Linux

	@classmethod
	def name(cls) -> str:
		"""Name (readable) of this runner"""
		return cls.__name__

	@classmethod
	@abstractmethod
	def exe_name(cls) -> str:
		"""Executable name of this runner, which will be the default path if not set to something else"""

	@classmethod
	def config_class(cls) -> type[BaseRunnerConfig]:
		"""If you have special settings, derive from BaseRunnerConfig and put them in here"""
		return _make_default_config(cls.name())

	@property
	def is_path_valid(self) -> bool:
		"""Returns true if the default exe name is available on the system path, or if the configured exe path points to a valid executable"""
		return (
			self.config.path.is_file()
			if self.config.path
			else shutil.which(self.exe_name()) is not None
		)

	@property
	def exe_path(self) -> Path:
		return self.config.path if self.config.path else Path(self.exe_name())

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

	def get_game_command(self, game: GameType) -> 'LaunchCommand':
		"""Return a LaunchCommand for launching this game with this runner, or raise EmulationNotSupportedError, etc"""
		raise EmulationNotSupportedError(
			f'Default implementation of get_game_command does not launch anything, argument = {game}'
		)


__doc__ = Runner.__doc__ or Runner.__name__
