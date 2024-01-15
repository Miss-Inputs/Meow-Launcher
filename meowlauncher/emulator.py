from abc import abstractmethod
from collections.abc import Collection
from enum import Enum
from functools import cache
from typing import TypeVar

from meowlauncher.exceptions import ExtensionNotSupportedError
from meowlauncher.games.roms.rom_game import ROMGame

from .game import Game
from .runner import BaseRunnerConfig, Runner

EmulatorGameType_co = TypeVar('EmulatorGameType_co', bound=Game, covariant=True)


class EmulatorStatus(Enum):
	"""How good an emulator is last time we checked and decided to form an opinion on it. Hmm I'm not sure why I needed this, maybe for a frontend to choose the allegedly best emulator automatically? Yeah it'd probs be that
	I have not actually thought of concrete definitions for what these mean"""

	Good = 6
	Imperfect = 5
	ExperimentalButSeemsOkay = 4
	Experimental = 3
	Janky = 2  # Weird to set up or launch normally… hmm this would indicate there is a "compatibility status" as well as a "usability status", in an ideal world where I'm not just putting all this here for either source code as reference, or future use for frontends
	Borked = 1


class BaseEmulatorConfig(BaseRunnerConfig):
	"""Not really much different than BaseRunnerConfig other than the default config_file_name, but might make things easier"""

	@classmethod
	def section(cls) -> str:
		return cls.__name__.removesuffix('Config')

	@classmethod
	def prefix(cls) -> str:
		return cls.__name__.removesuffix('Config').lower()

	@classmethod
	def config_file_name(cls) -> str:
		return 'emulators'


@cache
def _make_default_config(name: str) -> type[BaseEmulatorConfig]:
	"""The cache is important here because who knows what screwiness would result if you just returned a new class every time you accessed config_class"""

	class EmulatorConfig(BaseEmulatorConfig):
		_is_boilerplate = True

		@classmethod
		def section(cls) -> str:
			return name

		@classmethod
		def prefix(cls) -> str:
			return name.lower()

	return EmulatorConfig


class Emulator(Runner[EmulatorGameType_co]):
	@classmethod
	def config_class(cls) -> type[BaseEmulatorConfig]:
		return _make_default_config(cls.name())

	@classmethod
	def status(cls) -> EmulatorStatus:
		return EmulatorStatus.Good

	@classmethod
	def info_name(cls) -> str:
		"""Return a name which should be added to the Emulator key of a launcher's info"""
		return cls.name()


class StandardEmulator(Emulator[ROMGame]):
	"""Not very well named, but I mean like "something that by itself you give a ROM as a path and it launches it" or something among those lines"""

	@classmethod
	@abstractmethod
	def supported_extensions(cls) -> 'Collection[str]':
		...

	@classmethod
	def supported_compression(cls) -> 'Collection[str]':
		return frozenset()

	def supports_extension(self, extension: str) -> bool:
		# Is there a need for this to be a method and not classmethod? Would we ever change it dynamically depending on config?
		return extension in self.supported_extensions()

	def supports_compressed_extension(self, extension: str) -> bool:
		return extension in self.supported_compression()

	@property
	def supports_folders(self) -> bool:
		return '/' in self.supported_extensions()

	def check_game(self, game: ROMGame) -> None:
		"""Raises GameNotSupportedError/ExtensionNotSupportedError/etc for any reason the game is not supported, or do nothing if the game is supported
		:raises GameNotSupportedError: If the game is not supported"""
		if game.rom.is_folder and not self.supports_folders:
			raise ExtensionNotSupportedError(f'{self} does not support folders')
		if not self.supports_extension(game.rom.extension):
			raise ExtensionNotSupportedError(
				f'{self} does not support extension {game.rom.extension}'
			)


class LibretroCore(Emulator[Game]):
	pass
	# def __init__(
	# 	self,
	# 	name: str,
	# 	status: EmulatorStatus,
	# 	default_exe_name: str,
	# 	launch_command_func: 'GenericLaunchCommandFunc[Game] | None',
	# 	supported_extensions: 'Collection[str]',
	# 	configs=None,
	# ):
	# 	self.supported_extensions = supported_extensions

	# 	# TODO: XXX: main_config.libretro_cores_directory (need to screw around with circular imports)
	# 	# Maybe resolve it somewhere else, since this would potentially be able to have its own Settings class
	# 	default_path = default_exe_name + '_libretro.so'
	# 	super().__init__(
	# 		name,
	# 		status,
	# 		str(default_path),
	# 		launch_command_func,
	# 		config_name=name + ' (libretro)',
	# 		configs=configs,
	# 	)

	# @property
	# def friendly_type_name(self) -> str:
	# 	return 'libretro core'


class LibretroFrontend(Runner[Game]):
	pass
	# def __init__(
	# 	self,
	# 	name: str,
	# 	status: EmulatorStatus,
	# 	default_exe_name: str,
	# 	launch_command_func: 'LibretroFrontendLaunchCommandFunc',
	# 	supported_compression: 'Collection[str] | None' = None,
	# 	host_platform: HostPlatform = HostPlatform.Linux,
	# ):
	# 	self._name = name
	# 	self.status = status
	# 	self.default_exe_name = default_exe_name
	# 	self.launch_command_func = launch_command_func
	# 	self.supported_compression = supported_compression if supported_compression else ()
	# 	self.config_name = name  # emulator_configs needs this, as we have decided that frontends can have their own config
	# 	self.configs = {}  # TODO: XXX: this is just here to make it work for now
	# 	super().__init__(host_platform)

	# @property
	# def name(self) -> str:
	# 	return self._name
