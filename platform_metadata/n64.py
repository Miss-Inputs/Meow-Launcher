import hashlib
import configparser
import os

import input_metadata
from common_types import SaveType
from common import convert_alphanumeric, NotAlphanumericException
from software_list_info import find_in_software_lists, matcher_args_for_bytes, get_crc32_for_software_list

def _byteswap(b):
	byte_array = bytearray(b)
	for i in range(0, len(byte_array), 2):
		temp = byte_array[i]
		byte_array[i] = byte_array[i + 1]
		byte_array[i + 1] = temp
	return bytes(byte_array)

_mupen64plus_database = None
def get_mupen64plus_database():
	global _mupen64plus_database
	if _mupen64plus_database:
		return _mupen64plus_database

	locations = ['/usr/share/mupen64plus/mupen64plus.ini', '/usr/local/share/mupen64plus/mupen64plus.ini']
	location = None
	for possible_location in locations:
		if os.path.isfile(possible_location):
			location = possible_location
			break

	if not location:
		return None

	parser = configparser.ConfigParser(interpolation=None)
	parser.optionxform = str
	parser.read(location)

	database = {section: {k: v for k, v in parser.items(section)} for section in parser.sections()}
	for game, keypairs in database.items():
		if 'RefMD5' in keypairs:
			parent_md5 = keypairs['RefMD5']
			if parent_md5 in database:
				parent = database[parent_md5]
				for parent_key, parent_value in parent.items():
					if parent_key in database[game]:
						continue
					database[game][parent_key] = parent_value

	_mupen64plus_database = database
	return database

def parse_n64_header(game, header):
	try:
		product_code = convert_alphanumeric(header[59:63])
		game.metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	game.metadata.revision = header[63]

def add_info_from_database_entry(game, database_entry):
	#Keys: {'SaveType', 'Biopak', 'GoodName', 'SiDmaDuration', 'Players', 'DisableExtraMem', 'Mempak', 'Cheat0', 'Transferpak', 'CRC', 'Status', 'Rumble', 'CountPerOp'}
	#CRC is just the N64 checksum from the ROM header so I dunno if that's any use
	#Stuff like SiDmaDuration and CountPerOp and DisableExtraMem should be applied automatically by Mupen64Plus I would think (and be irrelevant for other emulators)
	#Likewise Cheat0 is just a quick patch to workaround emulator issues, so it doesn't need to be worried about here
	#Status seems... out of date

	#This is just here for debugging etc
	game.metadata.specific_info['GoodName'] = database_entry.get('GoodName')

	if 'Players' in database_entry:
		game.metadata.specific_info['Number-of-Players'] = database_entry['Players']

	if database_entry.get('SaveType', 'None') != 'None':
		game.metadata.save_type = SaveType.Cart
	elif database_entry.get('Mempak', 'No') == 'Yes':
		#Apparently it is possible to have both cart and memory card saving, so that is strange
		#I would think though that if the cartridge could save everything it needed to, it wouldn't bother with a memory card, so if it does use the controller pak then that's probably the main form of saving
		game.metadata.specific_info['Uses-Controller-Pak'] = True
		game.metadata.save_type = SaveType.MemoryCard
	else:
		#TODO: iQue would be SaveType.Internal, could maybe detect that based on CIC but that might be silly (the saving wouldn't be emulated by anything at this point anyway)
		game.metadata.save_type = SaveType.Nothing

	if database_entry.get('Rumble', 'No') == 'Yes':
		game.metadata.specific_info['Force-Feedback'] = True
	if database_entry.get('Biopak', 'No') == 'Yes':
		game.metadata.input_info.input_options[0].inputs.append(input_metadata.Biological())
	if database_entry.get('Transferpak', 'No') == 'Yes':
		game.metadata.specific_info['Uses-Transfer-Pak'] = True
	#Unfortunately nothing in here which specifies to use VRU, or any other weird fancy controllers which may or may not exist

def add_n64_metadata(game):
	entire_rom = game.rom.read()

	magic = entire_rom[:4]

	byte_swap = False
	if magic == b'\x80\x37\x12\x40':
		game.metadata.specific_info['ROM-Format'] = 'Z64'
	elif magic == b'\x37\x80\x40\x12':
		byte_swap = True
		game.metadata.specific_info['ROM-Format'] = 'V64'
	else:
		#TODO: Detect other formats (there are a few homebrews that start with 0x80 0x37 but not 0x12 0x40 after that, which may be launchable on some emulators but not on others)
		game.metadata.specific_info['ROM-Format'] = 'Unknown'
		return

	header = entire_rom[:64]
	if byte_swap:
		header = _byteswap(header)

	parse_n64_header(game, header)

	rom_md5 = hashlib.md5(entire_rom).hexdigest().upper()

	normal_controller = input_metadata.NormalController()
	normal_controller.face_buttons = 6 #A, B, 4 * C
	normal_controller.shoulder_buttons = 3 #L, R, and I guess Z will have to be counted as a shoulder button
	normal_controller.analog_sticks = 1
	normal_controller.dpads = 1
	game.metadata.input_info.add_option(normal_controller)

	database = get_mupen64plus_database()
	if database:
		database_entry = database.get(rom_md5)
		if database_entry:
			add_info_from_database_entry(game, database_entry)

	if not byte_swap:
		entire_rom = _byteswap(entire_rom)
		#For some reason, MAME uses little endian dumps in its software list at the moment, hence "not byte_swap" which would be wrong otherwise
	software = find_in_software_lists(game.software_lists, matcher_args_for_bytes(entire_rom))
	if software:
		software.add_generic_info(game)
