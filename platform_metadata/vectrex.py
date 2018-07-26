from info.region_info import TVSystem
from common import convert_alphanumeric, NotAlphanumericException
from metadata import PlayerInput, InputType


def add_vectrex_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.buttons = 4
	player.inputs = [InputType.Analog]
	#TODO: There's also a light pen
	game.metadata.input_info.players += [player] * 2
	
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
