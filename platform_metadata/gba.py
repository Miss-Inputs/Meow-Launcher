from zlib import crc32

from common import convert_alphanumeric, NotAlphanumericException
from metadata import SaveType, PlayerInput, InputType
from info.region_info import TVSystem
from software_list_info import find_in_software_lists
from .nintendo_common import nintendo_licensee_codes

nintendo_gba_logo_crc32 = 0xD0BEB55E
def add_gba_metadata(game):
	player = PlayerInput()
	player.buttons = 6 #A + B + L + R + Select + Start
	player.inputs = [InputType.Digital]
	game.metadata.input_info.players.append(player)
	game.metadata.tv_type = TVSystem.Agnostic

	entire_cart = game.rom.read()
	header = entire_cart[0:0xc0]

	nintendo_logo = header[4:0xa0]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_gba_logo_crc32
	game.metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid

	product_code = None
	can_trust_header_data = nintendo_logo_valid
	try:
		product_code = convert_alphanumeric(header[0xac:0xb0])
		#TODO: Maybe get region from product_code[3]?
	except NotAlphanumericException:
		#Well, shit. If the product code's invalid for whatever reason, then we can't derive much info from it anyway. Anything officially licensed should be alphanumeric.
		can_trust_header_data = False

	licensee_code = None
	try:
		licensee_code = convert_alphanumeric(header[0xb0:0xb2])
	except NotAlphanumericException:
		can_trust_header_data = False
	if licensee_code == '00':
		can_trust_header_data = False

	if can_trust_header_data:
		game_type = product_code[0]
		if game_type[0] == 'K' or game_type == 'R':
			player.inputs.append(InputType.MotionControls)

		game.metadata.product_code = product_code
		game.metadata.specific_info['Force-Feedback'] = game_type in ('R', 'V')
		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
		else:
			game.metadata.publisher = '<unknown Nintendo licensee {0}>'.format(licensee_code)

		game.metadata.revision = header[0xbc]

	has_save = False
	save_strings = [b'EEPROM_V', b'SRAM_V', b'SRAM_F_V', b'FLASH_V', b'FLASH512_V', b'FLASH1M_V']
	for string in save_strings:
		if string in entire_cart:
			has_save = True
			break
	game.metadata.specific_info['Has-RTC'] = b'SIIRTC_V' in entire_cart
	game.metadata.save_type = SaveType.Cart if has_save else SaveType.Nothing

	if b'AUDIO ERROR, too many notes on channel 0.increase polyphony RAM' in entire_cart:
		game.metadata.specific_info['Sound-Driver'] = 'Rare'
		#I mean it's not wrong
		game.metadata.developer = 'Rare'
		#TODO: Detect the other sound drivers, should I feel inclined

	cart_crc32 = '{:08x}'.format(crc32(entire_cart))
	software = find_in_software_lists(game.software_lists, crc=cart_crc32)
	if software:
		software.add_generic_info(game)
		if not game.metadata.product_code:
			game.metadata.product_code = software.get_info('serial')
