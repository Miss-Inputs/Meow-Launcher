import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.util.utils import (NoNonsenseConfigParser,
                                     NotAlphanumericException, byteswap,
                                     convert_alphanumeric)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

def _get_mupen64plus_database_location() -> Optional[Path]:
	config_location = Path('~/.config/mupen64plus/mupen64plus.cfg').expanduser()
	try:
		with config_location.open('rt', encoding='utf-8') as config_file:
			for line in config_file:
				if line.startswith('SharedDataPath = '):
					data_folder = line.rstrip()[len('SharedDataPath = '):].strip('"')
					possible_location = Path(data_folder, 'mupen64plus.ini')
					if possible_location.is_file():
						return possible_location
	except OSError:
		pass

	possible_locations = ('/usr/share/mupen64plus/mupen64plus.ini', '/usr/local/share/mupen64plus/mupen64plus.ini')
	for possible_location_str in possible_locations:
		possible_location = Path(possible_location_str)
		if possible_location.is_file():
			return possible_location
	#TODO: Add option to force the database to a certain location, although I guess if it's anywhere weird it'd probably be set in SharedDataPath anyway

	return None

def _get_mupen64plus_database() -> Optional[Mapping[str, Mapping[str, str]]]:
	if hasattr(_get_mupen64plus_database, 'mupen64plus_database'):
		return _get_mupen64plus_database.mupen64plus_database #type: ignore[attr-defined]

	location = _get_mupen64plus_database_location()
	if not location:
		return None

	parser = NoNonsenseConfigParser()
	parser.read(location)

	database = dict(parser) #I guess it doesn't work if we just hold onto it directly, well for starters the .items method is different
	for keypairs in database.values():
		if 'RefMD5' in keypairs:
			parent_md5 = keypairs['RefMD5']
			if parent_md5 in database:
				parent = database[parent_md5]
				for parent_key, parent_value in parent.items():
					if parent_key in keypairs:
						continue
					keypairs[parent_key] = parent_value

	_get_mupen64plus_database.mupen64plus_database = database #type: ignore[attr-defined]
	return database

def parse_n64_header(metadata: 'Metadata', header: bytes) -> None:
	#Clock rate, apparently? 0:4
	#Program counter: 4-8
	#Release address: 8-12
	#Checksum: 12-16
	#Checksum 2: 16-20
	#Zero filled: 20-28
	internal_title = header[28:52].decode('shift_jis', errors='backslashreplace').rstrip('\0')
	if internal_title:
		metadata.specific_info['Internal Title'] = internal_title
	#Unknown: 52-59
	try:
		product_code = convert_alphanumeric(header[59:63])
		metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	metadata.specific_info['Revision'] = header[63]

def add_info_from_database_entry(metadata: 'Metadata', database_entry: Mapping[str, str]) -> None:
	#Keys: {'SaveType', 'Biopak', 'GoodName', 'SiDmaDuration', 'Players', 'DisableExtraMem', 'Mempak', 'Cheat0', 'Transferpak', 'CRC', 'Status', 'Rumble', 'CountPerOp'}
	#CRC is just the N64 checksum from the ROM header so I dunno if that's any use
	#Stuff like SiDmaDuration and CountPerOp and DisableExtraMem should be applied automatically by Mupen64Plus I would think (and be irrelevant for other emulators)
	#Likewise Cheat0 is just a quick patch to workaround emulator issues, so it doesn't need to be worried about here
	#Status seems... out of date

	#This is just here for debugging etc
	goodname = database_entry.get('GoodName')
	if goodname:
		metadata.add_alternate_name(goodname, 'GoodName')

	if 'Players' in database_entry:
		metadata.specific_info['Number of Players'] = database_entry['Players']

	if database_entry.get('Mempak', 'No') == 'Yes':
		#Apparently it is possible to have both cart and memory card saving, so that is strange
		#I would think though that if the cartridge could save everything it needed to, it wouldn't bother with a memory card, so if it does use the controller pak then that's probably the main form of saving
		metadata.specific_info['Uses Controller Pak?'] = True
		metadata.save_type = SaveType.MemoryCard
	else:
		save_type = database_entry.get('SaveType')
		#TODO: iQue would be SaveType.Internal, could maybe detect that based on CIC but that might be silly (the saving wouldn't be emulated by anything at this point anyway)
		if save_type == 'None':
			metadata.save_type = SaveType.Nothing
		elif save_type: #If specified but not "None"
			metadata.save_type = SaveType.Cart

	if database_entry.get('Rumble', 'No') == 'Yes':
		metadata.specific_info['Force Feedback?'] = True
	if database_entry.get('Biopak', 'No') == 'Yes':
		metadata.input_info.input_options[0].inputs.append(input_metadata.Biological())
	if database_entry.get('Transferpak', 'No') == 'Yes':
		metadata.specific_info['Uses Transfer Pak?'] = True
	#Unfortunately nothing in here which specifies to use VRU, or any other weird fancy controllers which may or may not exist

def add_n64_custom_info(game: 'ROMGame') -> None:
	entire_rom = cast(FileROM, game.rom).read()

	magic = entire_rom[:4]

	is_byteswapped = False
	if magic == b'\x80\x37\x12\x40':
		game.metadata.specific_info['ROM Format'] = 'Z64'
	elif magic == b'\x37\x80\x40\x12':
		is_byteswapped = True
		game.metadata.specific_info['ROM Format'] = 'V64'
	else:
		game.metadata.specific_info['ROM Format'] = 'Unknown'
		return

	header = entire_rom[:64]
	if is_byteswapped:
		header = byteswap(header)

	parse_n64_header(game.metadata, header)

	normal_controller = input_metadata.NormalController()
	normal_controller.face_buttons = 6 #A, B, 4 * C
	normal_controller.shoulder_buttons = 3 #L, R, and I guess Z will have to be counted as a shoulder button
	normal_controller.analog_sticks = 1
	normal_controller.dpads = 1
	game.metadata.input_info.add_option(normal_controller)

	database = _get_mupen64plus_database()
	if database:
		rom_md5 = hashlib.md5(entire_rom).hexdigest().upper()
		database_entry = database.get(rom_md5)
		if database_entry:
			add_info_from_database_entry(game.metadata, database_entry)

	software = game.get_software_list_entry()
	if software:
		add_generic_software_info(software, game.metadata)
