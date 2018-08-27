from common import convert_alphanumeric, NotAlphanumericException
from info.region_info import TVSystem
from software_list_info import get_software_list_entry
from metadata import SaveType
from .nintendo_common import nintendo_licensee_codes

def add_virtual_boy_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	
	rom_size = game.rom.get_size()
	header_start_position = rom_size - 544 #Yeah I dunno
	header = game.rom.read(seek_to=header_start_position, amount=32)
	try:
		licensee_code = convert_alphanumeric(header[25:27])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
		elif licensee_code != '00':
			game.metadata.publisher = '<unknown Nintendo licensee {0}>'.format(licensee_code)
	except NotAlphanumericException:
		pass

	try:
		game.metadata.product_code = convert_alphanumeric(header[27:31])
	except NotAlphanumericException:
		pass
	#Can get country from product_code[3] if needed
	
	game.metadata.revision = header[31]

	#TODO: Input info, should always be the same

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#We won't need to get serial here I guess
		game.metadata.save_type = SaveType.Cart if software.has_data_area('eeprom') else SaveType.Nothing
