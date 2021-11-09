from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.software_list_info import get_software_list_entry
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

unofficial_vb_publishers = {
	#From https://planetvb.com/modules/dokuwiki/doku.php?id=info_at_the_end_of_the_rom
	#The PlanetVB people have started using their own publisher codes for individual users / their names... that's kind of annoying and not how this is supposed to work, but I can't really stop them, and homebrew software has already been made like that
	'AB': 'Amos Bieler', #aka RunnerPack
	'AE': 'Aegis Games', #aka VirtualChris
	'CR': 'Christian Radke', #aka KR155E
	'DA': 'Dan Bergman', #aka DanB
	'DB': 'David Tucker',
	'DP': 'Pat Daderko', #aka DogP
	'DW': 'David Williamson', #aka lameboyadvance
	'GP': 'Guy Perfect',
	'JA': 'Jorge Andres Eremiev',
	'MH': 'Matej Horvat', #aka HorvatM
	'MK': 'Martin Kujaczynski',
	'SP': 'Sploopby!', #aka Fwirt
	'TS': 'Thunderstruck',
	'VE': 'Alberto Covarrubias', #aka Virtual-E
}

def add_virtual_boy_metadata(game):
	rom_size = game.rom.get_size()
	header_start_position = rom_size - 544 #Yeah I dunno
	header = game.rom.read(seek_to=header_start_position, amount=32)

	title = header[0:20].decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	if title:
		game.metadata.specific_info['Internal-Title'] = title
	
	try:
		licensee_code = convert_alphanumeric(header[25:27])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
		elif licensee_code in unofficial_vb_publishers:
			game.metadata.publisher = unofficial_vb_publishers[licensee_code]
	except NotAlphanumericException:
		pass

	try:
		game.metadata.product_code = convert_alphanumeric(header[27:31])
	except NotAlphanumericException:
		pass
	#Can get country from product_code[3] if needed

	game.metadata.specific_info['Revision'] = header[31]

	gamepad = input_metadata.NormalController()
	gamepad.face_buttons = 2
	gamepad.shoulder_buttons = 2
	gamepad.dpads = 2
	game.metadata.input_info.add_option(gamepad)

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		#We won't need to get serial here I guess
		game.metadata.save_type = SaveType.Nothing
		if software.has_data_area('eeprom') or software.has_data_area('sram') or software.get_part_feature('battery'):
			#I am making assumptions about how saving works and I could be wrong
			game.metadata.save_type = SaveType.Cart
