from info.region_info import TVSystem

def add_vectrex_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'

	game.metadata.year = game.rom.read(seek_to=6, amount=4).decode('ascii', errors='ignore')
