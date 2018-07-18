from zlib import crc32

from common import convert_alphanumeric, NotAlphanumericException
from metadata import SaveType
from info.region_info import TVSystem
from platform_metadata.nintendo_common import nintendo_licensee_codes

nintendo_gba_logo_crc32 = 0xD0BEB55E
def add_gba_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

	entire_cart = game.rom.read()
	header = entire_cart[0:0xc0]

	nintendo_logo = header[4:0xa0]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_gba_logo_crc32
	game.metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid

	try:
		product_code = convert_alphanumeric(header[0xac:0xb0])
		game_type = product_code[0]
		if game_type[0] == 'K' or game_type == 'R':
			game.metadata.input_method = 'Motion Controls'
		else:
			game.metadata.input_method = 'Normal'
		game.metadata.specific_info['Force-Feedback'] = game_type in ('R', 'V')
		
		game.metadata.specific_info['Product-Code'] = product_code
		#TODO: Maybe get region from product_code[3]?
	except NotAlphanumericException:
		#Well, shit. If the product code's invalid for whatever reason, then we can't derive much info from it anyway. Anything officially licensed should be alphanumeric.
		pass
	
	try:
		licensee_code = convert_alphanumeric(header[0xb0:0xb2])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass
	
	has_save = False
	save_strings = [b'EEPROM_V', b'SRAM_V', b'SRAM_F_V', b'FLASH_V', b'FLASH512_V', b'FLASH1M_V']
	for string in save_strings:
		if string in entire_cart:
			has_save = True
			break
	#Can also look for SIIRTC_V in entire_cart to detect RTC if desired
	game.metadata.save_type = SaveType.Cart if has_save else SaveType.Nothing
