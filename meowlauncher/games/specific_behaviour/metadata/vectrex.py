from typing import TYPE_CHECKING, cast

from meowlauncher import input_metadata
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.metadata import Date
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric)

from meowlauncher.games.common.generic_info import add_generic_software_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame

def add_vectrex_metadata(game: 'ROMGame'):
	gamepad = input_metadata.NormalController()
	gamepad.face_buttons = 4 #All arranged in a row, not rectangle
	gamepad.analog_sticks = 1
	game.metadata.input_info.add_option(gamepad)
	#There's also a light pen but I dunno stuff about it or how to detect it so there's not a lot that can be done about it

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

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
