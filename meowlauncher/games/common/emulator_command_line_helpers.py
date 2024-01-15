from collections.abc import Collection, Mapping
from functools import cache
from itertools import chain
from pathlib import PurePath
from typing import TYPE_CHECKING

from meowlauncher.exceptions import EmulationNotSupportedError
from meowlauncher.games.mame_common.mame import MAME
from meowlauncher.games.mame_common.software_list import Software, get_software_list_by_name
from meowlauncher.launch_command import LaunchCommand, rom_path_argument

if TYPE_CHECKING:
	from meowlauncher.emulator_helpers import BaseMAMEDriver
	from meowlauncher.games.roms.rom_game import ROMGame


def verify_supported_gb_mappers(
	game: 'ROMGame', supported_mappers: Collection[str], detected_mappers: Collection[str]
) -> None:
	mapper = game.info.specific_info.get('Mapper', None)

	if not mapper:
		# If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		raise EmulationNotSupportedError('Mapper is not detected at all')

	if mapper == 'ROM only':
		# Literally everything will work with this
		return

	if game.info.specific_info.get('Override Mapper?', False) and mapper not in detected_mappers:
		# If the mapper in the ROM header is different than what the mapper actually is, it won't work, since we can't override it from the command line or anything
		# But it'll be okay if the mapper is something that gets autodetected outside of the header anyway
		raise EmulationNotSupportedError(f'Overriding the mapper to {mapper} is not supported')

	if mapper not in supported_mappers and mapper not in detected_mappers:
		raise EmulationNotSupportedError(f'Mapper {mapper} not supported')


def verify_mgba_mapper(game: 'ROMGame') -> None:
	supported_mappers = {
		'MBC1',
		'MBC2',
		'MBC3',
		'HuC1',
		'MBC5',
		'HuC3',
		'MBC6',
		'MBC7',
		'Pocket Camera',
		'Bandai TAMA5',
	}
	detected_mappers = {
		'MBC1 Multicart',
		'MMM01',
		'Wisdom Tree',
		'Pokemon Jade/Diamond bootleg',
		'BBD',
		'Hitek',
	}

	verify_supported_gb_mappers(game, supported_mappers, detected_mappers)


@cache
def _is_software_available(software_list_name: str, software_name: str) -> bool:
	# TODO: This should take a ConfiguredMAME (or both configuration/executable, get the software list from the configuration and use executable instead of default)
	mame = MAME()
	if not mame.is_available:
		return False

	software_list = get_software_list_by_name(software_list_name)
	if not software_list:
		return False
	return any(
		software.name == software_name for software in software_list.iter_available_software(mame)
	)


def is_highscore_cart_available() -> bool:
	return _is_software_available('a7800', 'hiscore')
	# FIXME: This is potentially wrong for A7800, where the software directory could be different than MAME... I've just decided to assume it's set up that way
	# I truck an idea that might work! If we rewrite all this to take a MAME executable, and everything related to MameDriver is like that… maybe we can make everything take an option to use default_mame_executable or something else, and that may all work out


def mednafen_module_launch(module: str, exe_path: PurePath) -> LaunchCommand:
	return LaunchCommand(exe_path, ['-video.fs', '1', '-force_module', module, rom_path_argument])


def mame_driver_base(
	game: 'ROMGame',
	emulator: 'BaseMAMEDriver',
	driver: str,
	slot: str | None = None,
	slot_options: Mapping[str, str] | None = None,
	*,
	has_keyboard: bool = False,
	autoboot_script: str | None = None,
) -> LaunchCommand:
	# Hmm I might need to refactor this and mame_system when I figure out what I'm doing
	software: Software | None = game.info.specific_info.get('MAME Software')
	if software and emulator.config.software_compatibility_threshold is not None:
		# We assume something without software Just Works, well unless skip_unknown_stuff is enabled down below
		game_compatibility = software.emulation_status
		if (
			game_compatibility
			and game_compatibility < emulator.config.software_compatibility_threshold
		):
			raise EmulationNotSupportedError(f'{software.name} is {game_compatibility.name}')

	if emulator.config.skip_unknown and not software:
		raise EmulationNotSupportedError('Does not match anything in software list')

	args = MAME.launch_args(
		driver, slot, slot_options, has_keyboard=has_keyboard, autoboot_script=autoboot_script
	)
	return LaunchCommand(emulator.exe_path, args)


def first_available_romset(*driver_list: 'Collection[str]', mame: 'MAME') -> str | None:
	if not mame.is_available:
		return None
	return next(
		(driver for driver in chain.from_iterable(driver_list) if mame.verifyroms(driver)), None
	)
