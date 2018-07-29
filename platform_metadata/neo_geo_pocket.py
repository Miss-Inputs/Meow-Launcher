from info.region_info import TVSystem

def add_ngp_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	
	header = game.rom.read(amount=64)
	copyright_string = header[:28].decode('ascii', errors='ignore')
	if copyright_string == 'COPYRIGHT BY SNK CORPORATION':
		game.metadata.publisher = 'SNK'
	#Otherwise it'd say " LICENSED BY SNK CORPORATION" and that could be any dang third party which isn't terribly useful
	#There's really not much here, so I didn't even bother reading the whole header
	#At offset 35, you could get the colour flag, and if equal to 0x10 set platform to "Neo Geo Pocket Color" if you really wanted
	game.metadata.specific_info['Product-Code'] = int.from_bytes(header[32:34], 'little')
	game.metadata.revision = header[34]
