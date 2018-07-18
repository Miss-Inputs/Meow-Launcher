def add_atari_8bit_metadata(game):
	if game.rom.extension in ['bin', 'rom', 'car']:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'CART':
			game.metadata.specific_info['Headered'] = True
			cart_type = int.from_bytes(header[4:8], 'big')
			#TODO: Have nice table of cart types like with Game Boy mappers; also set platform to XEGS/XL/XE/etc accordingly
			game.metadata.specific_info['Cart-Type'] = cart_type
			game.metadata.specific_info['Slot'] = 'Right' if cart_type in [21, 59] else 'Left'
		else:
			game.metadata.specific_info['Headered'] = False
