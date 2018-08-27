from info.region_info import TVSystem
from metadata import PlayerInput, InputType
from software_list_info import get_software_list_entry

def add_ngp_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 3 #A B Option (Option is just Start really but they have to be special and unique and not like the other girls)
	game.metadata.input_info.players.append(player)
	
	header = game.rom.read(amount=64)
	copyright_string = header[:28].decode('ascii', errors='ignore')
	if copyright_string == 'COPYRIGHT BY SNK CORPORATION':
		game.metadata.publisher = 'SNK'
	#Otherwise it'd say " LICENSED BY SNK CORPORATION" and that could be any dang third party which isn't terribly useful
	#There's really not much here, so I didn't even bother reading the whole header
	#At offset 35, you could get the colour flag, and if equal to 0x10 set platform to "Neo Geo Pocket Color" if you really wanted
	game.metadata.product_code = int.from_bytes(header[32:34], 'little')
	game.metadata.revision = header[34]
	game.metadata.specific_info['Is-Colour'] = header[35] == 0x10

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
