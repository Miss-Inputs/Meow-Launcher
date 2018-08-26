from common import convert_alphanumeric, NotAlphanumericException
from info.region_info import TVSystem
from metadata import PlayerInput, InputType
from .software_list_info import add_generic_software_list_info, get_software_list_entry


def add_pokemini_metadata(game):
	player = PlayerInput()
	player.buttons = 5 #A + B + C + start + select
	player.inputs = [InputType.Digital]
	#Technically you could say Motion Controls because of the shake detection, but not all games use it, and you can't really tell which do and which don't programmatically
	game.metadata.input_info.players.append(player)
	game.metadata.tv_type = TVSystem.Agnostic

	game.metadata.specific_info['Force-Feedback'] = True
	
	#There really isn't much else here, other than maybe the title. I don't think I can do anything with all those IRQs.
	product_code_bytes = game.rom.read(seek_to=0x21ac, amount=4)
	try:
		product_code = convert_alphanumeric(product_code_bytes)
		game.metadata.specific_info['Product-Code'] = product_code
	except NotAlphanumericException:
		pass

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		