from typing import cast

from meowlauncher import input_metadata
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Date
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric)

from .minor_platforms import add_generic_info


def add_vectrex_metadata(game: ROMGame):
	gamepad = input_metadata.NormalController()
	gamepad.face_buttons = 4 #All arranged in a row, not rectangle
	gamepad.analog_sticks = 1
	game.metadata.input_info.add_option(gamepad)
	#There's also a light pen but I dunno stuff about it or how to detect it so there's not a lot that can be done about it

	add_generic_info(game)

	#Only do things the wrong way if we can't find year by software list
	try:
		year = convert_alphanumeric(cast(FileROM, game.rom).read(seek_to=6, amount=4))
		try:
			if int(year) > 1982:
				year_date = Date(year, is_guessed=True)
				if year_date.is_better_than(game.metadata.release_date):
					game.metadata.release_date = game.metadata.release_date
		except ValueError:
			pass
	except NotAlphanumericException:
		pass
