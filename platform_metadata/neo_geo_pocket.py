from info.region_info import TVSystem

def add_ngp_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	
	copyright_string = game.rom.read(amount=28).decode('ascii', errors='ignore')
	if copyright_string == 'COPYRIGHT BY SNK CORPORATION':
		game.metadata.author = 'SNK'
	#Otherwise it'd say " LICENSED BY SNK CORPORATION" and that could be any dang third party which isn't terribly useful
	#There's really not much here, so I didn't even bother reading the whole header
	#At offset 35, you could get the colour flag, and if equal to 0x10 set platform to "Neo Geo Pocket Color" if you really wanted
	#TODO: Get product code at offset 32