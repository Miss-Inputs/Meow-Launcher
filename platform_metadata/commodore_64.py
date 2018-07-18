def add_commodore_64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:16]
	if magic == b'C64 CARTRIDGE   ':
		game.metadata.specific_info['Headered'] = True
		cart_type = int.from_bytes(header[22:24], 'big')
		game.metadata.specific_info['Cart-Type'] = cart_type
		if cart_type == 15:
			game.metadata.platform = 'C64GS'
	else:
		game.metadata.specific_info['Headered'] = False		
