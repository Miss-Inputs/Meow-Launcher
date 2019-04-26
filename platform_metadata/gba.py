from zlib import crc32

import input_metadata
from common import convert_alphanumeric, NotAlphanumericException
from common_types import SaveType
from info.region_info import TVSystem
from software_list_info import find_in_software_lists, get_crc32_for_software_list, matcher_args_for_bytes
from data.nintendo_licensee_codes import nintendo_licensee_codes

nintendo_gba_logo_crc32 = 0xD0BEB55E
def parse_gba_header(game, header):
	nintendo_logo = header[4:0xa0]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_gba_logo_crc32
	game.metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid

	product_code = None
	try:
		product_code = convert_alphanumeric(header[0xac:0xb0])
		if len(product_code) == 4:
			game_type = product_code[0]
			if game_type in ('K', 'R'):
				game.metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls())
			game.metadata.specific_info['Force-Feedback'] = game_type in ('R', 'V')

			game.metadata.product_code = product_code
	except NotAlphanumericException:
		pass

	licensee_code = None
	try:
		licensee_code = convert_alphanumeric(header[0xb0:0xb2])

		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	game.metadata.revision = header[0xbc]

def add_gba_metadata(game):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 2 #L R
	game.metadata.input_info.add_option(builtin_gamepad)

	game.metadata.tv_type = TVSystem.Agnostic

	entire_cart = game.rom.read()
	if len(entire_cart) >= 0xc0:
		header = entire_cart[0:0xc0]
		parse_gba_header(game, header)

	has_save = False
	save_strings = [b'EEPROM_V', b'SRAM_V', b'SRAM_F_V', b'FLASH_V', b'FLASH512_V', b'FLASH1M_V']
	for string in save_strings:
		if string in entire_cart:
			has_save = True
			break
	game.metadata.specific_info['Has-RTC'] = b'SIIRTC_V' in entire_cart
	game.metadata.save_type = SaveType.Cart if has_save else SaveType.Nothing

	if b'AUDIO ERROR, too many notes on channel 0.increase polyphony RAM' in entire_cart:
		#Look for Rare sound driver because I can
		game.metadata.developer = 'Rare'

	software = find_in_software_lists(game.software_lists, matcher_args_for_bytes(entire_cart))
	if software:
		software.add_generic_info(game)
