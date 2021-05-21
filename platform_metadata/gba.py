from zlib import crc32

import input_metadata
from common import NotAlphanumericException, convert_alphanumeric, load_dict
from common_types import SaveType
from software_list_info import get_software_list_entry

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

nintendo_gba_logo_crc32 = 0xD0BEB55E
def parse_gba_header(metadata, header):
	#Entry point: 0-4
	nintendo_logo = header[4:0xa0]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_gba_logo_crc32
	metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid
	
	internal_title = header[0xa0:0xac].decode('ascii', errors='backslashreplace').rstrip('\0')
	metadata.specific_info['Internal-Title'] = internal_title
	if internal_title == 'mb2gba':
		return
	
	product_code = None
	try:
		product_code = convert_alphanumeric(header[0xac:0xb0])
		if len(product_code) == 4:
			game_type = product_code[0]
			if game_type in ('K', 'R'):
				metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls())
			metadata.specific_info['Force-Feedback'] = game_type in ('R', 'V')

			metadata.product_code = product_code
	except NotAlphanumericException:
		pass

	licensee_code = None
	try:
		licensee_code = convert_alphanumeric(header[0xb0:0xb2])

		if licensee_code in nintendo_licensee_codes:
			metadata.publisher = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	#"Fixed value": 0xb2, apparently should be 0x96
	#Main unit code: 0xb3, apparently should be 0
	#Device type: 0xb4, apparently normally should be 0
	#Reserved: 0xb5 - 0xbc

	metadata.specific_info['Revision'] = header[0xbc]

	#Checksum (see ROMniscience for how to calculate it, because I don't feel like describing it all in a single line of comment): 0xbd
	#Reserved: 0xbe - 0xc0

def look_for_strings_in_cart(entire_cart, metadata):
	has_save = False
	save_strings = [b'EEPROM_V', b'SRAM_V', b'SRAM_F_V', b'FLASH_V', b'FLASH512_V', b'FLASH1M_V']
	for string in save_strings:
		if string in entire_cart:
			has_save = True
			break
	if b'SIIRTC_V' in entire_cart:
		metadata.specific_info['Has-RTC'] = True
	if b'RFU_V10' in entire_cart:
		metadata.specific_info['Uses-Wireless-Adapter'] = True
	metadata.save_type = SaveType.Cart if has_save else SaveType.Nothing

	#Look for sound drivers because I can
	mp2k_selectsong = b'\x00\xb5\x00\x04\x07J\x08I@\x0b@\x18\x83\x88Y\x00\xc9\x18\x89\x00\x89\x18\nh\x01h\x10\x1c\x00\xf0'
	mp2k_new_selectsong = b'\x00\xb5\x00\x04\x07K\x08I@\x0b@\x18\x82\x88Q\x00\x89\x18\x89\x00\xc9\x18\nh\x01h\x10\x1c\x00\xf0'
	krawall_mixcenter = bytes((
			#Converted from lib/mixer_func.s from Github source, I don't know what I'm doing (this is from some old thing elsewhere) but this seems to work
			0xf0, 0x0f, 0x2d, 0xe9, #stmdb	sp! {r4-r11}
			0x08, 0x50, 0x90, 0xe5, #ldr	r5, [r0, #8]
			0x14, 0x60, 0x90, 0xe5, #ldr	r6, [r0, #20]
			0xbc, 0x71, 0xd0, 0xe1, #ldrh	r7, [r0, #28]
			0x1e, 0x30, 0xd0, 0xe5, #ldrb	r3, [r0, #30]
			0x22, 0x21, 0xa0, 0xe1  #mov r2, r2, lsr #2
	))

	if mp2k_selectsong in entire_cart:
		metadata.specific_info['Sound-Driver'] = 'MP2000'
	elif mp2k_new_selectsong in entire_cart:
		metadata.specific_info['Sound-Driver'] = 'MP2000 (newer)'
	elif krawall_mixcenter in entire_cart:
		metadata.specific_info['Sound-Driver'] = 'Krawall'
	elif b'GAX2_INIT' in entire_cart:
		metadata.specific_info['Sound-Driver'] = 'GAX'
	elif b'GBAModPlay (C) Logik State ' in entire_cart:
		metadata.specific_info['Sound-Driver'] = 'GBAModPlay'
	elif b'LS_Play (C) Logik State ' in entire_cart:
		#Is this actually the same thing as GBAModPlay?
		metadata.specific_info['Sound-Driver'] = 'LS_Play'
	elif b'AUDIO ERROR, too many notes on channel 0.increase polyphony RAM' in entire_cart:
		metadata.specific_info['Sound-Driver'] = 'Rare'
		metadata.developer = 'Rare'

def add_gba_metadata(game):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 2 #L R
	game.metadata.input_info.add_option(builtin_gamepad)

	entire_cart = game.rom.read()
	if len(entire_cart) >= 0xc0:
		header = entire_cart[0:0xc0]
		parse_gba_header(game.metadata, header)

	look_for_strings_in_cart(entire_cart, game.metadata)

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
