from typing import cast

from meowlauncher import input_metadata
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric)

from .minor_platforms import add_generic_info


def add_pokemini_metadata(game: ROMGame):
	builtin_gamepad = input_metadata.NormalController()

	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 1 #C
	game.metadata.input_info.add_option(builtin_gamepad)
	#Technically you could say Motion Controls because of the shake detection, but not all games use it, and you can't really tell which do and which don't programmatically

	rom = cast(FileROM, game.rom)
	product_code_bytes = rom.read(seek_to=0x21ac, amount=4)
	try:
		product_code = convert_alphanumeric(product_code_bytes)
		game.metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	title = rom.read(seek_to=0x21b0, amount=12).decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	if title:
		game.metadata.specific_info['Internal-Title'] = title

	add_generic_info(game)
