from abc import abstractmethod
from collections.abc import Sequence
from enum import Enum
from functools import cache
from pathlib import PurePath
from typing import TYPE_CHECKING, TypeVar

from meowlauncher.exceptions import EmulationNotSupportedError, ExtensionNotSupportedError
from meowlauncher.games.common.emulator_command_line_helpers import (
	mame_base,
	mednafen_module_launch,
)
from meowlauncher.games.roms.rom_game import ROMGame

from .game import Game
from .launch_command import LaunchCommand, rom_path_argument
from .runner import BaseRunnerConfig, HostPlatform, Runner

EmulatorGameType_co = TypeVar('EmulatorGameType_co', bound=Game, covariant=True)
if TYPE_CHECKING:
	from collections.abc import Callable, Collection, Mapping

	from meowlauncher.config_types import TypeOfConfigValue

	LibretroFrontendLaunchCommandFunc = Callable[
		[Game, Mapping[str, TypeOfConfigValue]], LaunchCommand
	]

	GenericLaunchCommandFunc = Callable[
		[EmulatorGameType_co, 'Emulator[EmulatorGameType_co]'], LaunchCommand
	]
	ROMGameLaunchFunc = Callable[[ROMGame, 'StandardEmulator'], LaunchCommand]


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


_standalone_emulator_types: dict[str, type[StandardEmulator]] = {}


def standalone_emulator(
	name: str,
	exe_name: str,
	launch_game_func: 'ROMGameLaunchFunc | Sequence[str | PurePath] | None',
	supported_extensions: 'Collection[str]',
	supported_compression: 'Collection[str] | None' = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	config_class: type[BaseEmulatorConfig] | None = None,
	host_platform: HostPlatform | None = None,
	info_name: str | None = None,
	check_game_func: 'Callable[[ROMGame, StandardEmulator], None] | None' = None,
) -> type[StandardEmulator]:
	"""Creates a simple StandaloneEmulator, because typing them all out would suck a lot of balls"""

	class StandaloneEmulator(StandardEmulator):
		@classmethod
		def name(cls) -> str:
			return name

		@classmethod
		def exe_name(cls) -> str:
			return exe_name

		@classmethod
		def supported_extensions(cls) -> 'Collection[str]':
			return supported_extensions

		@classmethod
		def supported_compression(cls) -> 'Collection[str]':
			return (
				supported_compression if supported_compression else super().supported_compression()
			)

		@classmethod
		def status(cls) -> EmulatorStatus:
			return status

		@classmethod
		def host_platform(cls) -> HostPlatform:
			return host_platform if host_platform else super().host_platform()

		@classmethod
		def config_class(cls) -> type[BaseEmulatorConfig]:
			return config_class if config_class else super().config_class()

		def get_game_command(self, game: ROMGame) -> 'LaunchCommand':
			if launch_game_func is None:
				return LaunchCommand(self.exe_path, [rom_path_argument])
			if isinstance(launch_game_func, Sequence):
				return LaunchCommand(self.exe_path, launch_game_func)
			return launch_game_func(game, self)

		@classmethod
		def info_name(cls) -> str:
			return info_name if info_name else name

		def check_game(self, game: ROMGame) -> None:
			if check_game_func:
				check_game_func(game, self)
			return super().check_game(game)

	return _standalone_emulator_types.setdefault(name, StandaloneEmulator)


class MednafenConfig(BaseEmulatorConfig):
	"""Config shared between all Mednafen modules"""

	# TODO: Override __init__ or settings_customize_sources or whichever to update from a global [Mednafen] config section

	@classmethod
	def section(cls) -> str:
		return 'Mednafen'

	@classmethod
	def prefix(cls) -> str:
		return 'mednafen'


def mednafen_module(
	name: str,
	supported_extensions: 'Collection[str]',
	launch_game_func: 'ROMGameLaunchFunc | str',
	supported_compression: 'Collection[str] | None' = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	check_game_func: 'Callable[[ROMGame, StandardEmulator], None] | None' = None,
) -> type[StandardEmulator]:
	class MednafenModule(StandardEmulator):
		@classmethod
		def name(cls) -> str:
			return f'Mednafen ({name})'

		@classmethod
		def exe_name(cls) -> str:
			return 'mednafen'

		@classmethod
		def supported_extensions(cls) -> 'Collection[str]':
			return supported_extensions

		@classmethod
		def supported_compression(cls) -> 'Collection[str]':
			return (
				supported_compression if supported_compression else super().supported_compression()
			)

		@classmethod
		def status(cls) -> EmulatorStatus:
			return status

		@classmethod
		def config_class(cls) -> type[BaseEmulatorConfig]:
			# TODO: Specific config for each module, which also has the default options, but gets updated with MednafenConfig() (will need to play around with MednafenModule.__init__)
			return MednafenConfig

		def get_game_command(self, game: Game) -> 'LaunchCommand':
			if not isinstance(game, ROMGame):
				raise EmulationNotSupportedError('This only supports ROMs')
			if isinstance(launch_game_func, str):
				return mednafen_module_launch(launch_game_func, self.exe_path)
			return launch_game_func(game, self)

		def check_game(self, game: ROMGame) -> None:
			if check_game_func:
				check_game_func(game, self)
			return super().check_game(game)

	return _standalone_emulator_types.setdefault(name, MednafenModule)


class BaseMAMEDriverConfig(BaseEmulatorConfig):
	# TODO: Override __init__ or settings_customize_sources or whichever to update from global MAME config
	software_compatibility_threshold: int | None = 1
	# TODO: This should be an enum, and also make sure there's a way to set None in the ini file that will be validated properly
	"""0 = broken 1 = imperfect 2 = working other value = ignore; anything in the software list needs this to be considered compatible or None to ignore"""
	skip_unknown: bool = False
	"Skip anything that doesn't have a match in the software list"


def _make_mame_driver_config(name: str) -> type[BaseMAMEDriverConfig]:
	class MAMEDriverConfig(BaseMAMEDriverConfig):
		@classmethod
		def section(cls) -> str:
			return name

		@classmethod
		def prefix(cls) -> str:
			return name.lower()

	return MAMEDriverConfig


class BaseMAMEDriver(StandardEmulator):
	config: BaseMAMEDriverConfig

	@classmethod
	def exe_name(cls) -> str:
		return 'mame'

	@classmethod
	def supported_compression(cls) -> 'Collection[str]':
		return {'7z', 'zip'}


def mame_driver(
	name: str,
	launch_game_func: 'Callable[[ROMGame, BaseMAMEDriver], LaunchCommand] | tuple[str, str]',
	supported_extensions: 'Collection[str]',
	config_class: type[BaseMAMEDriverConfig] | None = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	**kwargs
) -> type[BaseMAMEDriver]:
	class MAMEDriver(BaseMAMEDriver):
		@classmethod
		def name(cls) -> str:
			return f'MAME ({name})'

		@classmethod
		def supported_extensions(cls) -> 'Collection[str]':
			return supported_extensions

		@classmethod
		def status(cls) -> EmulatorStatus:
			return status

		@classmethod
		def config_class(cls) -> type[BaseMAMEDriverConfig]:
			return config_class if config_class else _make_mame_driver_config(name)

		def get_game_command(self, game: ROMGame) -> 'LaunchCommand':
			if isinstance(launch_game_func, tuple):
				driver, slot = launch_game_func
				return LaunchCommand(self.exe_path, mame_base(driver, slot, **kwargs))
			return launch_game_func(game, self)

	_standalone_emulator_types[name] = MAMEDriver
	return MAMEDriver


def vice_emulator(
	name: str,
	exe_name: str,
	func: 'ROMGameLaunchFunc',
	status: EmulatorStatus = EmulatorStatus.Good,
) -> type[StandardEmulator]:
	# TODO: Override __init__ or settings_customize_sources or whichever to update from global [VICE] config section
	vice_extensions = {
		'd64',
		'g64',
		'x64',
		'p64',
		'd71',
		'd81',
		'd80',
		'd82',
		'd1m',
		'd2m',
		'20',
		'40',
		'60',
		'70',
		'80',
		'a0',
		'b0',
		'e0',
		'crt',
		'bin',
		'p00',
		'prg',
		'tap',
		't64',
	}
	# TODO: Also does z and zoo compression but I haven't done those in archives.py yet
	# TODO: Maybe just put z and zoo in the ordinary file extensions if we don't want to do that just yet? I dunno who even uses those, and if a file was compressed with that, would we even be able to read it in Python
	# WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
	# Does support compressed tapes/disks (gz/bz2/zip/tgz) but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here. So for now we pretend it supports no compression so we end up getting 7z to put the thing in a temporarily folder regardless
	return standalone_emulator(f'VICE ({name})', exe_name, func, vice_extensions, status=status)


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


class LibretroFrontend(Runner):
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
