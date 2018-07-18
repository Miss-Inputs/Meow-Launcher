from common import convert_alphanumeric, NotAlphanumericException
from info.region_info import TVSystem

def add_pokemini_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'
	
	#There really isn't much else here, other than maybe the title. I don't think I can do anything with all those IRQs.
	product_code_bytes = game.rom.read(seek_to=0x21ac, amount=4)
	try:
		product_code = convert_alphanumeric(product_code_bytes)
		game.metadata.specific_info['Product-Code'] = product_code
	except NotAlphanumericException:
		pass
