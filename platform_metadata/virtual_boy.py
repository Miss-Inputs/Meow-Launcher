from common import convert_alphanumeric, NotAlphanumericException
from metadata import SaveType
from info.region_info import TVSystem
from platform_metadata.nintendo_common import nintendo_licensee_codes

def add_virtual_boy_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	
	rom_size = game.rom.get_size()
	header_start_position = rom_size - 544 #Yeah I dunno
	header = game.rom.read(seek_to=header_start_position, amount=32)
	try:
		licensee_code = convert_alphanumeric(header[25:27])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	try:
		game.metadata.specific_info['Product-Code'] = convert_alphanumeric(header[27:31])
	except NotAlphanumericException:
		pass
	#Can get country from product_code[3] if needed
