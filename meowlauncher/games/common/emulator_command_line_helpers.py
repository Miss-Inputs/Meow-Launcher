import os
from collections.abc import Iterable, Mapping
from typing import Optional

from meowlauncher.common_types import (EmulationNotSupportedException,
                                       EmulationStatus, EmulatorStatus)
from meowlauncher.emulator import LaunchCommandFunc, MednafenModule
from meowlauncher.games.mame_common.mame_helpers import (have_mame,
                                                         verify_romset)
from meowlauncher.games.mame_common.software_list_info import \
    get_software_list_by_name
from meowlauncher.launch_command import LaunchCommand, rom_path_argument


def _get_autoboot_script_by_name(name: str) -> str:
	#Hmm I'm not sure I like this one but whaddya do otherwise… where's otherwise a good place to store shit
	this_package = os.path.dirname(__file__)
	root_package = os.path.dirname(this_package)
	root_dir = os.path.dirname(root_package)
	return os.path.join(root_dir, 'mame_autoboot', name + '.lua')

def _verify_supported_gb_mappers(game, supported_mappers: Iterable[str], detected_mappers: Iterable[str]) -> None:
	mapper = game.metadata.specific_info.get('Mapper', None)

	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		raise EmulationNotSupportedException('Mapper is not detected at all')
	
	if mapper == 'ROM only':
		#Literally everything will work with this
		return

	if game.metadata.specific_info.get('Override-Mapper', False) and mapper not in detected_mappers:
		#If the mapper in the ROM header is different than what the mapper actually is, it won't work, since we can't override it from the command line or anything
		#But it'll be okay if the mapper is something that gets autodetected outside of the header anyway
		raise EmulationNotSupportedException('Overriding the mapper to {0} is not supported'.format(mapper))

	if mapper not in supported_mappers and mapper not in detected_mappers:
		raise EmulationNotSupportedException('Mapper ' + mapper + ' not supported')

def verify_mgba_mapper(game) -> None:
	supported_mappers = ['MBC1', 'MBC2', 'MBC3', 'HuC1', 'MBC5', 'HuC3', 'MBC6', 'MBC7', 'Pocket Camera', 'Bandai TAMA5']
	detected_mappers = ['MBC1 Multicart', 'MMM01', 'Wisdom Tree', 'Pokemon Jade/Diamond bootleg', 'BBD', 'Hitek']

	_verify_supported_gb_mappers(game, supported_mappers, detected_mappers)

def _is_software_available(software_list_name: str, software_name: str) -> bool:
	if not have_mame():
		return False

	software_list = get_software_list_by_name(software_list_name)
	if not software_list:
		return False
	available_software = software_list.get_available_software()
	for software in available_software:
		if software.name == software_name:
			return True
	return False

def is_highscore_cart_available() -> bool:
	return _is_software_available('a7800', 'hiscore')
	#FIXME: This is potentially wrong for A7800, where the software directory could be different than MAME... I've just decided to assume it's set up that way
	#I truck an idea that might work! If we rewrite all this to take a MAME executable, and everything related to MameDriver is like that… maybe we can make everything take an option to use default_mame_executable or something else, and that may all work out


def mednafen_module(module: str, exe_path: str='mednafen') -> LaunchCommand:
	return LaunchCommand(exe_path, ['-video.fs', '1', '-force_module', module, rom_path_argument])

def mame_base(driver: str, slot: Optional[str]=None, slot_options: Optional[Mapping[str, str]]=None, has_keyboard: bool=False, autoboot_script: Optional[str]=None, software: Optional[str]=None, bios: Optional[str]=None) -> list[str]:
	args = ['-skip_gameinfo']
	if has_keyboard:
		args.append('-ui_active')

	if bios:
		args.append('-bios')
		args.append(bios)

	args.append(driver)
	if software:
		args.append(software)

	if slot_options:
		for name, value in slot_options.items():
			if not value:
				value = ''
			args.append('-' + name)
			args.append(value)

	if slot:
		args.append('-' + slot)
		args.append(rom_path_argument)

	if autoboot_script:
		args.append('-autoboot_script')
		args.append(_get_autoboot_script_by_name(autoboot_script))

	return args

def mame_driver(game, emulator_config, driver: str, slot=None, slot_options: Optional[Mapping[str, str]]=None, has_keyboard=False, autoboot_script=None) -> LaunchCommand:
	#Hmm I might need to refactor this and mame_system when I figure out what I'm doing
	compat_threshold = emulator_config.options.get('software_compatibility_threshold', 1)
	if compat_threshold > -1:
		game_compatibility = game.metadata.specific_info.get('MAME-Emulation-Status', EmulationStatus.Good)
		if game_compatibility < compat_threshold:
			raise EmulationNotSupportedException('{0} is {1}'.format(game.metadata.specific_info.get('MAME-Software-Name'), game_compatibility.name))

	skip_unknown = emulator_config.options.get('skip_unknown_stuff', False)
	if skip_unknown:
		if not game.metadata.specific_info.get('MAME-Software-Name'):
			raise EmulationNotSupportedException('Does not match anything in software list')

	args = mame_base(driver, slot, slot_options, has_keyboard, autoboot_script)
	return LaunchCommand(emulator_config.exe_path, args)

def first_available_romset(driver_list: Iterable[str]) -> Optional[str]:
	for driver in driver_list:
		if verify_romset(driver):
			return driver
	return None

#This is here to make things simpler, instead of putting a whole new function in emulator_command_lines we can return the appropriate function from here
def simple_emulator(args: Optional[list[str]]=None) -> LaunchCommandFunc:
	def inner(_, __, emulator_config):
		return LaunchCommand(emulator_config.exe_path, args if args else [rom_path_argument])
	return inner

def simple_gb_emulator(args, mappers: Iterable[str], autodetected_mappers: Iterable[str]):
	def inner(game, _, emulator_config):
		_verify_supported_gb_mappers(game, mappers, autodetected_mappers)
		return LaunchCommand(emulator_config.exe_path, args)
	return inner

def simple_md_emulator(args: list[str], unsupported_mappers: Iterable[str]) -> LaunchCommandFunc:
	def inner(game, _, emulator_config):
		mapper = game.metadata.specific_info.get('Mapper')
		if mapper in unsupported_mappers:
			raise EmulationNotSupportedException(mapper + ' not supported')
		return LaunchCommand(emulator_config.exe_path, args)
	return inner

def simple_mame_driver(driver: str, slot: Optional[str]=None, slot_options: Optional[Mapping[str, str]]=None, has_keyboard=False, autoboot_script=None) -> LaunchCommandFunc:
	def inner(game, _, emulator_config):
		return mame_driver(game, emulator_config, driver, slot, slot_options, has_keyboard, autoboot_script)
	return inner

def simple_mednafen_module_args(module: str) -> LaunchCommandFunc:
	def inner(_, __, emulator_config):
		return mednafen_module(module, exe_path=emulator_config.exe_path)
	return inner

class SimpleMednafenModule(MednafenModule):
	def __init__(self, name: str, status: EmulatorStatus, module: str, supported_extensions: list[str], configs=None):
		super().__init__(name, status, supported_extensions, params_func=simple_mednafen_module_args(module), configs=configs)
