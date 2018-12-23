import input_metadata
from common import convert_alphanumeric, NotAlphanumericException
from info.region_info import TVSystem
from software_list_info import get_software_list_entry

def add_pokemini_metadata(game):
	builtin_gamepad = input_metadata.NormalController()

	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 1 #C
	game.metadata.input_info.add_option(builtin_gamepad)
	#Technically you could say Motion Controls because of the shake detection, but not all games use it, and you can't really tell which do and which don't programmatically
	game.metadata.tv_type = TVSystem.Agnostic

	#There really isn't much else here, other than maybe the title. I don't think I can do anything with all those IRQs.
	product_code_bytes = game.rom.read(seek_to=0x21ac, amount=4)
	try:
		product_code = convert_alphanumeric(product_code_bytes)
		game.metadata.product_code = product_code
	except NotAlphanumericException:
		pass

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
