import input_metadata
from common import NotAlphanumericException, convert_alphanumeric
from metadata import Date

from platform_metadata.minor_systems import add_generic_info


def add_vectrex_metadata(game):
	gamepad = input_metadata.NormalController()
	gamepad.face_buttons = 4 #All arranged in a row, not rectangle
	gamepad.analog_sticks = 1
	game.metadata.input_info.add_option(gamepad)
	#There's also a light pen but I dunno stuff about it or how to detect it so there's not a lot that can be done about it

	add_generic_info(game)

	#Only do things the wrong way if we can't find year by software list
	try:
		year = convert_alphanumeric(game.rom.read(seek_to=6, amount=4))
		try:
			if int(year) > 1982:
				year_date = Date(year, is_guessed=True)
				if year_date.is_better_than(game.metadata.release_date):
					game.metadata.release_date = game.metadata.release_date
		except ValueError:
			pass
	except NotAlphanumericException:
		pass
