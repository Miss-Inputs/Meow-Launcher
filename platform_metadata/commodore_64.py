from software_list_info import get_software_list_entry

def add_commodore_64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:16]
	if magic == b'C64 CARTRIDGE   ':
		headered = True
		cart_type = int.from_bytes(header[22:24], 'big')
		game.metadata.specific_info['Cart-Type'] = cart_type
		if cart_type == 15:
			game.metadata.platform = 'C64GS'
	else:
		headered = False	

	game.metadata.specific_info['Headered'] = headered

	#TODO: Make this work where there are multiple CHIP entries in a CCS64 file... hmm...
	software = get_software_list_entry(game, skip_header = 80 if headered else 0)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#There's dataarea nvram, but those are two carts which are more accurately described as device BIOSes, so I won't bother
