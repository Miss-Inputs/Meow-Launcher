"""Helpers for data/emulators.py to define emulators that don't need anything tricky"""
from collections.abc import Callable, Collection, Mapping, Sequence
from functools import cache
from pathlib import PurePath
from typing import TYPE_CHECKING

from meowlauncher.emulator import (
	BaseEmulatorConfig,
	Emulator,
	EmulatorGameType_co,
	EmulatorStatus,
	StandardEmulator,
)
from meowlauncher.exceptions import EmulationNotSupportedError
from meowlauncher.games.common.emulator_command_line_helpers import (
	mame_driver_base,
	mednafen_module_launch,
	verify_supported_gb_mappers,
)
from meowlauncher.games.roms.rom_game import ROMGame

from .launch_command import LaunchCommand, rom_path_argument

if TYPE_CHECKING:
	from meowlauncher.config_types import TypeOfConfigValue
	from meowlauncher.game import Game
	from meowlauncher.runner import HostPlatform

	LibretroFrontendLaunchCommandFunc = Callable[
		[Game, Mapping[str, TypeOfConfigValue]], LaunchCommand
	]

	GenericLaunchCommandFunc = Callable[
		[EmulatorGameType_co, 'Emulator[EmulatorGameType_co]'], LaunchCommand
	]
	ROMGameLaunchFunc = Callable[[ROMGame, 'StandardEmulator'], LaunchCommand]
_standalone_emulator_types: dict[str, type[StandardEmulator]] = {}


def standalone_emulator(
	name: str,
	exe_name: str,
	launch_game_func: 'ROMGameLaunchFunc | Sequence[str | PurePath] | None',
	supported_extensions: 'Collection[str]',
	supported_compression: 'Collection[str] | None' = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	config_class: type[BaseEmulatorConfig] | None = None,
	host_platform: 'HostPlatform | None' = None,
	info_name: str | None = None,
	check_game_func: 'Callable[[ROMGame, StandardEmulator], None] | None' = None,
) -> type[StandardEmulator]:
	"""Creates a simple StandaloneEmulator, because typing them all out would suck a lot of balls"""
	if name in _standalone_emulator_types:
		return _standalone_emulator_types[name]

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
		def host_platform(cls) -> 'HostPlatform':
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
	if name in _standalone_emulator_types:
		return _standalone_emulator_types[name]

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

		def get_game_command(self, game: 'Game') -> 'LaunchCommand':
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


@cache
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


_mame_driver_types: dict[str, type[BaseMAMEDriver]] = {}


def mame_driver(
	name: str,
	launch_game_func: 'Callable[[ROMGame, BaseMAMEDriver], LaunchCommand] | tuple[str, str]',
	supported_extensions: 'Collection[str]',
	config_class: type[BaseMAMEDriverConfig] | None = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	check_func: 'Callable[[ROMGame, BaseMAMEDriver], None] | None' = None,
	**kwargs,
) -> type[BaseMAMEDriver]:
	if name in _mame_driver_types:
		return _mame_driver_types[name]

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
				return mame_driver_base(game, self, driver, slot, **kwargs)
			return launch_game_func(game, self)

		def check_game(self, game: ROMGame) -> None:
			if check_func:
				check_func(game, self)
			return super().check_game(game)

	_mame_driver_types[name] = MAMEDriver
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


def simple_gb_emulator(
	name: str,
	exe_name: str,
	args: Sequence[str],
	mappers: 'Collection[str]',
	detectable_mappers: 'Collection[str]',
	supported_extensions: 'Collection[str]',
	supported_compression: 'Collection[str] | None' = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	host_platform: 'HostPlatform | None' = None,
) -> 'type[StandardEmulator]':
	def check_func(game: 'ROMGame', _):
		verify_supported_gb_mappers(game, mappers, detectable_mappers)

	return standalone_emulator(
		name,
		exe_name,
		args,
		supported_extensions,
		supported_compression,
		status,
		None,
		host_platform,
		check_game_func=check_func,
	)


def simple_mega_drive_emulator(
	name: str,
	exe_name: str,
	args: Sequence[str],
	unsupported_mappers: 'Collection[str]',
	supported_extensions: 'Collection[str]',
	supported_compression: 'Collection[str] | None' = None,
	status: EmulatorStatus = EmulatorStatus.Good,
	host_platform: 'HostPlatform | None' = None,
) -> 'type[StandardEmulator]':
	def check_func(game: 'ROMGame', _):
		mapper = game.info.specific_info.get('Mapper')
		if mapper and mapper in unsupported_mappers:
			raise EmulationNotSupportedError(f'{mapper} not supported')

	return standalone_emulator(
		name,
		exe_name,
		args,
		supported_extensions,
		supported_compression,
		status,
		None,
		host_platform,
		check_game_func=check_func,
	)
