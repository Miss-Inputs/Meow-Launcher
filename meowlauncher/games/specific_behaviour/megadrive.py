import logging
import re
from collections.abc import Collection
from datetime import datetime
from functools import lru_cache
from itertools import chain
from typing import TYPE_CHECKING, Any

from meowlauncher import input_info
from meowlauncher.common_types import SaveType
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.mame_common.machine import (
	Machine,
	does_machine_match_name,
	iter_machines_from_source_file,
)
from meowlauncher.games.mame_common.mame import MAME
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.info import Date, GameInfo
from meowlauncher.platform_types import MegadriveRegionCodes
from meowlauncher.util import cd_read
from meowlauncher.util.utils import load_dict

from .common.atari_controllers import megadrive_pad as standard_gamepad

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom_game import ROMGame

logger = logging.getLogger(__name__)

_licensee_codes = load_dict(None, 'sega_licensee_codes')

_copyright_regex = re.compile(r'\(C\)(\S{4}.)(\d{4})\.(.{3})')
_t_with_zero = re.compile(r'^T-0')
_t_not_followed_by_dash = re.compile(r'^T(?!-)')


def _parse_peripherals(
	game_info: GameInfo, peripherals: Collection[int], object_for_logging: Any = None
) -> None:
	for peripheral_char_code in peripherals:
		peripheral_char = chr(peripheral_char_code)
		if peripheral_char == 'M':
			# 3 buttons if I'm not mistaken
			mouse = input_info.Mouse()
			mouse.buttons = 3
			game_info.input_info.add_option(mouse)
		elif peripheral_char == 'V':
			# Is this just the SMS paddle?
			game_info.input_info.add_option(input_info.Paddle())
		elif peripheral_char == 'A':
			xe_1_ap = input_info.NormalController()
			xe_1_ap.face_buttons = 10
			xe_1_ap.shoulder_buttons = 4
			xe_1_ap.analog_sticks = 2  # The second one only has one axis, though
			game_info.input_info.add_option(xe_1_ap)
		elif peripheral_char == 'G':
			menacer = input_info.LightGun()
			menacer.buttons = 2  # Also pause button
			game_info.input_info.add_option(menacer)
		elif peripheral_char == 'K':
			xband_keyboard = input_info.Keyboard()
			xband_keyboard.keys = (
				68  # I think I counted that right... I was just looking at the picture
			)
			game_info.input_info.add_option(xband_keyboard)
		elif peripheral_char == 'J':
			game_info.input_info.add_option(standard_gamepad)
		elif peripheral_char == '6':
			six_button_gamepad = input_info.NormalController()
			six_button_gamepad.face_buttons = 6
			six_button_gamepad.dpads = 1
			game_info.input_info.add_option(six_button_gamepad)
			game_info.specific_info['Uses 6-Button Controller?'] = True
		elif peripheral_char == '0':
			sms_gamepad = input_info.NormalController()
			sms_gamepad.face_buttons = 2
			sms_gamepad.dpads = 1
			game_info.input_info.add_option(sms_gamepad)
		elif peripheral_char == 'L':
			# Activator
			game_info.input_info.add_option(input_info.MotionControls())
		elif peripheral_char in '4O':
			# Team Play and J-Cart respectively
			# num_players = 4
			pass
		elif peripheral_char == 'C':
			game_info.specific_info['Uses CD?'] = True
		elif peripheral_char_code not in {0, 32}:
			logger.debug('%s has unknown peripheral: %s', object_for_logging, peripheral_char)
		# Apparently these also exist with dubious/unclear definitions:
		# P: "Printer"
		# B: "Control Ball"
		# F: "Floppy Drive"
		# R: "RS232C Serial"
		# T: "Tablet"


def _add_info_from_copyright_string(game_info: GameInfo, copyright_string: str) -> None:
	game_info.specific_info['Copyright'] = copyright_string
	copyright_match = _copyright_regex.match(copyright_string)
	if copyright_match:
		maker = copyright_match[1].strip().rstrip(',')
		maker = _t_with_zero.sub('T-', maker)
		maker = _t_not_followed_by_dash.sub('T-', maker)
		if maker in _licensee_codes:
			game_info.publisher = _licensee_codes[maker]
		year = copyright_match[2]
		month: str | int
		try:
			month = datetime.strptime(copyright_match[3], '%b').month
		except ValueError:
			# There are other spellings such as JUR, JLY out there, but oh well
			month = '??'
		game_info.specific_info['Copyright Date'] = Date(year, month)
		if not game_info.release_date:
			game_info.release_date = Date(year, month, is_guessed=True)


def _parse_region_codes(
	regions: bytes, object_for_logging: Any = None
) -> Collection[MegadriveRegionCodes]:
	region_codes = set()
	for region in regions:
		try:
			region_code = MegadriveRegionCodes(chr(region))
		except ValueError:
			if region not in {0, 32, 255}:
				logger.debug('%s has unknown region code: %s', object_for_logging, chr(region))
		else:
			region_codes.add(region_code)
	# Seen in some betas and might just be invalid:
	# D - Brazil?
	return region_codes


def add_megadrive_info(game_info: GameInfo, header: bytes, object_for_logging: Any = None) -> None:
	try:
		console_name = header[:16].decode('ascii')
	except UnicodeDecodeError:
		game_info.specific_info['Bad TMSS?'] = True
		return

	game_info.specific_info['Console Name'] = console_name
	if not console_name.startswith(('SEGA', ' SEGA')) and console_name not in {
		'IMA IKUNOUJYUKU ',
		'IMA IKUNOJYUKU  ',
		'SAMSUNG PICO    ',
	}:
		game_info.specific_info['Bad TMSS?'] = True
		return

	if game_info.platform == 'Mega CD' and console_name.startswith('SEGA 32X'):
		# Could also set platform to something like "Mega CD 32X" I guess
		game_info.specific_info['32X Only?'] = True

	try:
		copyright_string = header[16:32].decode('ascii')
		_add_info_from_copyright_string(game_info, copyright_string)
	except UnicodeDecodeError:
		pass

	domestic_title = header[32:80].rstrip(b'\0 ').decode('shift_jis', 'backslashreplace')
	overseas_title = header[80:128].rstrip(b'\0 ').decode('shift_jis', 'backslashreplace')
	if domestic_title:
		game_info.specific_info['Internal Title'] = domestic_title
	if overseas_title:
		# Often the same as domestic title, but for games that get their names changed yet work on multiple regions, domestic is the title in Japan and and overseas is in USA (and maybe Europe). I don't know what happens if a game is originally in USA then gets its name changed when it goes to Japan, but it might just be "Japan is domestic and everwhere else is overseas"
		game_info.specific_info['Internal Overseas Title'] = overseas_title
	# Product type: 128:130, it's usually GM for game but then some other values appear too (especially in Sega Pico)
	# Space for padding: 130

	try:
		serial = header[131:142].decode('ascii')
		game_info.product_code = serial[:8].rstrip('\0 ')
		# - in between
		version = serial[9:10]
		if version.isdigit():
			game_info.specific_info['Revision'] = int(version)
	except ValueError:
		pass
	# Checksum: header[142:144]

	_parse_peripherals(game_info, set(header[144:160]), object_for_logging)

	if game_info.platform == 'Mega Drive':
		save_id = header[0xB0:0xB4]
		# Apparently... what the heck
		# This seems to be different on Mega CD, and also 32X
		game_info.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing

	modem_info = header[0xBC:0xC8]
	memo_bytes = header[0xC8:0xF0]
	modem_string = None
	if modem_info[:2] == b'MO':
		game_info.specific_info['Supports Modem?'] = True
	elif modem_info[:11] == b'No modem...':
		game_info.specific_info['Supports Modem?'] = False
	else:
		modem_string = modem_info.rstrip(b'\0 ').decode('ascii', 'backslashreplace')

	try:
		memo = memo_bytes.rstrip(b'\0 ').decode('ascii')
		if modem_string:
			# Not really correct, but a few homebrews use the modem part to put in a longer message (and sometimes, varying amounts of it - the first 2 or 4 bytes might be filled with garbage data…)
			memo = modem_string + memo

		if memo:
			if memo == 'SV':
				game_info.specific_info['Expansion Chip'] = 'SVP'
			else:
				# This only seems to really be used for homebrews bootlegs etc
				game_info.descriptions['Memo'] = memo
	except UnicodeDecodeError:
		pass

	regions = header[0xF0:0xF3]
	region_codes = _parse_region_codes(regions, object_for_logging)
	game_info.specific_info['Region Code'] = region_codes
	if console_name[:12] == 'SEGA GENESIS' and not region_codes:
		# Make a cheeky guess (if it wasn't USA it would be SEGA MEGADRIVE etc presumably)
		game_info.specific_info['Region Code'] = [MegadriveRegionCodes.USA]


def _get_smd_header(rom: FileROM) -> bytes:
	"""Just get the first block which is all that's needed for the header, otherwise this would be a lot more complicated (just something to keep in mind if you ever need to convert a whole-ass .smd ROM)"""
	block = rom.read(seek_to=512, amount=16384)

	buf = bytearray(16386)
	midpoint = 8192
	even = 1  # Hmm, maybe I have these the wrong way around
	odd = 2

	for i, b in enumerate(block):
		if i <= midpoint:
			buf[even] = b
			even += 2
		else:
			buf[odd] = b
			odd += 2

	return bytes(buf[0x100:0x200])


@lru_cache(maxsize=1)
def _get_megaplay_games() -> Collection[Machine]:
	mame = MAME()
	if not mame.is_available:
		return []
	return frozenset(iter_machines_from_source_file('megaplay', mame))


@lru_cache(maxsize=1)
def _get_megatech_games() -> Collection[Machine]:
	mame = MAME()
	if not mame.is_available:
		return []
	return frozenset(iter_machines_from_source_file('megatech', mame))


@lru_cache(maxsize=1)
def _get_megadrive_arcade_bootlegs() -> Collection[Machine]:
	mame = MAME()
	if not mame.is_available:
		return []
	return set(iter_machines_from_source_file('megadriv_acbl', mame))


def find_equivalent_mega_drive_arcade(game_name: str) -> Machine | None:
	# TODO: Maybe StandardEmulatedPlatform can just hold some field called "potentially_equivalent_machines" or is that stupid? Yeah maybe just have a function yielding them
	for machine in chain(
		_get_megatech_games(), _get_megaplay_games(), _get_megadrive_arcade_bootlegs()
	):
		if does_machine_match_name(game_name, machine):
			return machine

	return None


def add_megadrive_software_list_metadata(software: 'Software', game_info: GameInfo) -> None:
	add_generic_software_info(software, game_info)
	if software.get_shared_feature('addon') == 'SVP':
		game_info.specific_info['Expansion Chip'] = 'SVP'
	if software.get_shared_feature('incompatibility') == 'TMSS':
		game_info.specific_info['Bad TMSS?'] = True

	slot = software.get_part_feature('slot')
	if slot == 'rom_eeprom' or software.has_data_area('sram'):
		game_info.save_type = SaveType.Cart
	elif game_info.platform == 'Mega Drive':
		game_info.save_type = SaveType.Nothing

	if software.name == 'aqlian':
		# This isn't a different slot, but we special case it as though it was a different mapper, to choose the proper emulator for it that supports it
		game_info.specific_info['Mapper'] = 'aqlian'
	elif slot:
		if slot not in {'rom_sram', 'rom_fram'}:
			mapper = slot.removeprefix('rom_')
			if mapper in {
				'eeprom',
				'nbajam_alt',
				'nbajamte',
				'nflqb96',
				'cslam',
				'nhlpa',
				'blara',
				'eeprom_mode1',
			}:
				game_info.specific_info['Mapper'] = 'EEPROM'
			elif mapper == 'jcart':
				game_info.specific_info['Mapper'] = 'J-Cart'
			elif mapper in {'codemast', 'mm96'}:
				game_info.specific_info['Mapper'] = 'J-Cart + EEPROM'
			else:
				# https://github.com/mamedev/mame/blob/master/src/devices/bus/megadrive/md_carts.cpp
				game_info.specific_info['Mapper'] = mapper
		if software.name == 'pokemon' and software.software_list_name == 'megadriv':
			# This is also a bit naughty, but Pocket Monsters has different compatibility compared to other games with rom_kof99
			game_info.specific_info['Mapper'] = slot[4:] + '_pokemon'


def add_megadrive_custom_info(game: 'ROMGame') -> None:
	header = None
	if game.rom.extension == 'cue':
		first_track_and_sector_size = cd_read.get_first_data_cue_track(game.rom.path)
		if not first_track_and_sector_size:
			logger.info('%s has invalid cuesheet', game.rom)
			return
		first_track, sector_size = first_track_and_sector_size
		if not first_track.is_file():
			logger.warning('%s has cuesheet with track %s not found', game.rom, first_track)
			return
		try:
			header = cd_read.read_mode_1_cd(first_track, sector_size, 0x100, 0x100)
		except NotImplementedError:
			logger.info('%s has weird sector size %s', game.rom, sector_size)
			return
	elif isinstance(game.rom, FileROM):
		header = (
			_get_smd_header(game.rom)
			if game.rom.extension == 'smd'
			else game.rom.read(0x100, 0x100)
		)

	if header:
		add_megadrive_info(game.info, header, game.rom)

	software = game.get_software_list_entry()
	if software:
		add_megadrive_software_list_metadata(software, game.info)
