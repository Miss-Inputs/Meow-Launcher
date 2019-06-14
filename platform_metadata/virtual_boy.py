import input_metadata
from common import convert_alphanumeric, NotAlphanumericException
from info.region_info import TVSystem
from software_list_info import get_software_list_entry
from common_types import SaveType
from data.nintendo_licensee_codes import nintendo_licensee_codes

def add_virtual_boy_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

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
		software.add_generic_info(game.metadata)
		#We won't need to get serial here I guess
		game.metadata.save_type = SaveType.Cart if software.has_data_area('eeprom') else SaveType.Nothing
