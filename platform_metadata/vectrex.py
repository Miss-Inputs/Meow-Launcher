import input_metadata
from common import NotAlphanumericException, convert_alphanumeric
from info.region_info import TVSystem
from platform_metadata.minor_systems import add_generic_info


def add_vectrex_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

	gamepad = input_metadata.NormalController()
	gamepad.face_buttons = 4 #All arranged in a row, not rectangle
	gamepad.analog_sticks = 1
	game.metadata.input_info.add_option(gamepad)
	#There's also a light pen but I dunno stuff about it or how to detect it so there's not a lot that can be done about it

	add_generic_info(game)

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
