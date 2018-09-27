from software_list_info import get_software_list_entry
from info.system_info import MediaType

def add_atari_8bit_metadata(game):
	if game.metadata.media_type == MediaType.Cartridge:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'CART':
			headered = True
			cart_type = int.from_bytes(header[4:8], 'big')
			#TODO: Have nice table of cart types like with Game Boy mappers; also set platform to XEGS/XL/XE/etc accordingly
			game.metadata.specific_info['Cart-Type'] = cart_type
			game.metadata.specific_info['Slot'] = 'Right' if cart_type in [21, 59] else 'Left'
		else:
			headered = False

	game.metadata.specific_info['Headered'] = headered

	software = get_software_list_entry(game, skip_header=16 if headered else 0)
	if software:
		software.add_generic_info(game)
		compatibility = software.get_shared_feature('compatibility')
		if compatibility in ('XL', 'XL/XE'):
			game.metadata.specific_info['Requires-XL'] = True
		if compatibility == "OSb":
			game.metadata.specific_info['Requires-OS-B'] = True

		game.metadata.product_code = software.get_info('serial')

		peripheral = software.get_part_feature('peripheral')
		#TODO Setup input_info I guess:
		#cx77_touch = Touchscreen (tablet)
		#cx75_pen = Light Gun (light pen)
		#koala_pad,koala_pen = Tablet _and_ light pen
		#trackball = Trackball
		#lightgun = Light Gun (XEGS only)

		#trackfld = Track & Field controller but is that just a boneless joystick?
		#Otherwise do we assume joystick and keyboard? Hmm
		game.metadata.specific_info['Peripheral'] = peripheral
