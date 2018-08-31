from info.region_info import TVSystem
from common import convert_alphanumeric, NotAlphanumericException
from metadata import PlayerInput, InputType
from software_list_info import get_software_list_entry

def add_vectrex_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.buttons = 4
	player.inputs = [InputType.Analog]
	#TODO: There's also a light pen
	game.metadata.input_info.players += [player] * 2

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

	if not game.metadata.year:
		#Only do things the wrong way if we can't find year by software list
		try:
			year = convert_alphanumeric(game.rom.read(seek_to=6, amount=4))
			try:
				year = int(year)
				if year > 1982:
					game.metadata.year = year
			except ValueError:
				pass
		except NotAlphanumericException:
			pass

