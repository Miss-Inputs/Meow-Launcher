from info.region_info import TVSystem
from common import convert_alphanumeric, NotAlphanumericException

def add_vectrex_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'
	
	try:
		game.metadata.year = convert_alphanumeric(game.rom.read(seek_to=6, amount=4))
	except NotAlphanumericException:
		pass
