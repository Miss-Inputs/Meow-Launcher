import contextlib
import logging
from typing import TYPE_CHECKING, Any

from meowlauncher.common_types import ByteAmount
from meowlauncher.games.mame_common.mame_utils import consistentify_manufacturer
from meowlauncher.info import Date, GameInfo
from meowlauncher.platform_types import AppleIIHardware
from meowlauncher.util.region_info import get_language_by_english_name

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom import FileROM

logger = logging.getLogger(__name__)


def _parse_woz_info_chunk(game_info: GameInfo, chunk_data: bytes) -> None:
	info_version = chunk_data[0]
	# 1: Disk type = 5.25" if 1 else 3.25 if 2
	# 2: 1 if write protected
	if info_version == 2:
		compatible_hardware = int.from_bytes(chunk_data[40:42], 'little')
		if compatible_hardware:
			machines = set()
			if compatible_hardware & 1:
				machines.add(AppleIIHardware.AppleII)
			if compatible_hardware & 2:
				machines.add(AppleIIHardware.AppleIIPlus)
			if compatible_hardware & 4:
				machines.add(AppleIIHardware.AppleIIE)
			if compatible_hardware & 8:
				machines.add(AppleIIHardware.AppleIIC)
			if compatible_hardware & 16:
				machines.add(AppleIIHardware.AppleIIEEnhanced)
			if compatible_hardware & 32:
				machines.add(AppleIIHardware.AppleIIgs)
			if compatible_hardware & 64:
				machines.add(AppleIIHardware.AppleIICPlus)
			if compatible_hardware & 128:
				machines.add(AppleIIHardware.AppleIII)
			if compatible_hardware & 256:
				machines.add(AppleIIHardware.AppleIIIPlus)
			game_info.specific_info['Machine'] = machines
		minimum_ram = int.from_bytes(chunk_data[42:44], 'little')
		if minimum_ram:
			game_info.specific_info['Minimum RAM'] = ByteAmount(minimum_ram * 1024)


woz_meta_machines = {
	'2': AppleIIHardware.AppleII,
	'2+': AppleIIHardware.AppleIIPlus,
	'2e': AppleIIHardware.AppleIIE,
	'2c': AppleIIHardware.AppleIIC,
	'2e+': AppleIIHardware.AppleIIEEnhanced,
	'2gs': AppleIIHardware.AppleIIgs,
	'2c+': AppleIIHardware.AppleIICPlus,
	'3': AppleIIHardware.AppleIII,
	'3+': AppleIIHardware.AppleIIIPlus,
}


def _parse_woz_kv(
	game_info: GameInfo, key: str, value: str, object_for_warning: Any = None
) -> None:
	""" "Parses key/values from WOZ META chunk
	@param object_for_warning: Just here to format any logging messages with, suggest you use a ROM object
	"""
	if key in {'side', 'side_name', 'contributor', 'image_date', 'collection', 'requires_platform'}:
		# No use for these
		# "collection" is not part of the spec but it shows up and it just says where the image came from
		# requires_platform is not either, it just seems to be "apple2" so far and I don't get it
		return

	if key == 'version':
		# Note that this is free text
		if not value.startswith('v'):
			value = 'v' + value
		game_info.specific_info['Version'] = value
	elif key == 'title':
		game_info.add_alternate_name(value, 'Header Title')
	elif key == 'subtitle':
		game_info.specific_info['Subtitle'] = value
	elif key == 'requires_machine':
		if game_info.specific_info.get('Machine'):
			# Trust the info from the INFO chunk more if it exists
			return
		machines = set()
		for machine in value.split('|'):
			if machine in woz_meta_machines:
				machines.add(woz_meta_machines[machine])
			else:
				logger.info(
					'Unknown compatible machine %s in Woz META chunk in %s',
					machine,
					object_for_warning,
				)
		game_info.specific_info['Machine'] = machines
	elif key == 'requires_ram':
		# Should be in INFO chunk, but sometimes isn't
		if value[-1].lower() == 'k':
			value = value[:-1]
		with contextlib.suppress(ValueError):
			game_info.specific_info['Minimum RAM'] = ByteAmount(int(value) * 1024)
	elif key == 'publisher':
		game_info.publisher = consistentify_manufacturer(value)
	elif key == 'developer':
		game_info.developer = consistentify_manufacturer(value)
	elif key == 'copyright':
		game_info.specific_info['Copyright'] = value
		with contextlib.suppress(ValueError):
			game_info.release_date = Date(value)
	elif key == 'language':
		game_info.languages = {
			lang
			for lang in (get_language_by_english_name(lang_name) for lang_name in value.split('|'))
			if lang
		}
	elif key == 'genre':
		# This isn't part of the specification, but I've seen it
		if value == 'rpg':
			game_info.genre = 'RPG'
		else:
			game_info.genre = value.capitalize() if value.islower() else value
	elif key == 'notes':
		# This isn't part of the specification, but I've seen it
		game_info.add_notes(value)
	else:
		logger.info('Unknown Woz META key %s with value %s in %s', key, value, object_for_warning)


def _parse_woz_meta_chunk(
	game_info: GameInfo, chunk_data: bytes, object_for_warning: Any = None
) -> None:
	rows = chunk_data.split(b'\x0a')
	for row in rows:
		try:
			key, value = row.decode('utf-8').split('\t', maxsplit=1)
		except ValueError:  # Oh I guess this includes UnicodeDecodeError
			continue

		_parse_woz_kv(game_info, key, value, object_for_warning)


def _parse_woz_chunk(rom: 'FileROM', game_info: GameInfo, position: int) -> int:
	chunk_header = rom.read(seek_to=position, amount=8)
	chunk_id = chunk_header[0:4]
	chunk_data_size = int.from_bytes(chunk_header[4:8], 'little')

	if chunk_id == b'INFO':
		chunk_data = rom.read(seek_to=position + 8, amount=chunk_data_size)
		_parse_woz_info_chunk(game_info, chunk_data)
	elif chunk_id == b'META':
		chunk_data = rom.read(seek_to=position + 8, amount=chunk_data_size)
		_parse_woz_meta_chunk(game_info, chunk_data, rom)
	# TMAP, TRKS, FLUX, WRIT have nothing interesting for us

	return position + chunk_data_size + 8


def add_woz_metadata(rom: 'FileROM', game_info: GameInfo) -> None:
	"""https://applesaucefdc.com/woz/reference1/
	https://applesaucefdc.com/woz/reference2/"""
	magic = rom.read(amount=8)
	if magic == b'WOZ1\xff\n\r\n':
		game_info.specific_info['ROM Format'] = 'WOZ v1'
	elif magic == b'WOZ2\xff\n\r\n':
		game_info.specific_info['ROM Format'] = 'WOZ v2'
	else:
		logger.info('Weird .woz magic %s in %s', magic, rom)
		return

	position = 12
	size = rom.size
	while position:
		position = _parse_woz_chunk(rom, game_info, position)
		if position >= size:
			break
	if 'Header-Title' in game_info.names and 'Subtitle' in game_info.specific_info:
		game_info.add_alternate_name(
			game_info.names['Header Title'] + ': ' + game_info.specific_info['Subtitle'],
			'Header Title with Subtitle',
		)


def add_apple_ii_software_info(software: 'Software', game_info: 'GameInfo') -> None:
	software.add_standard_info(game_info)
	usage = software.get_info('usage')
	if usage == 'Works with Apple II Mouse Card in slot 4: -sl4 mouse':
		# Not setting up input_info just yet because I don't know if it uses joystick/keyboard as well. I guess I probably never will, but like... well.... dang
		game_info.specific_info['Uses Mouse?'] = True
	elif usage:
		game_info.add_notes(usage)

	if software.software_list.name == 'apple2_flop_orig' and software.name == 'arkanoid':
		game_info.specific_info['Uses Mouse?'] = True

	if not game_info.specific_info.get('Machine'):
		compat = software.compatibility
		if compat:
			machines = set()
			for machine in compat:
				if machine == 'A2':
					machines.add(AppleIIHardware.AppleII)
				if machine == 'A2P':
					machines.add(AppleIIHardware.AppleIIPlus)
				if machine == 'A2E':
					machines.add(AppleIIHardware.AppleIIE)
				if machine == 'A2EE':
					machines.add(AppleIIHardware.AppleIIEEnhanced)
				if machine == 'A2C':
					machines.add(AppleIIHardware.AppleIIC)
				if machine == 'A2GS':
					machines.add(AppleIIHardware.AppleIIgs)
				# Apple IIc+ doesn't show up in this list so far
			game_info.specific_info['Machine'] = machines


def add_apple_ii_rom_file_info(rom: 'FileROM', game_info: 'GameInfo') -> None:
	if rom.extension == 'woz':
		add_woz_metadata(rom, game_info)
