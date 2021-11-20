from typing import TYPE_CHECKING, cast

from meowlauncher import input_metadata
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric)

from meowlauncher.games.common.generic_info import add_generic_software_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

def add_info_from_header(header: bytes, metadata: 'Metadata'):
	#https://github.com/pokemon-mini/pm-dev-docs/wiki/PM_Cartridge - we are only bothering to read a small part of the thing for the time being
	product_code_bytes = header[0:4]
	try:
		product_code = convert_alphanumeric(product_code_bytes)
		metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	title = header[4:16].decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	if title:
		metadata.specific_info['Internal Title'] = title

def add_pokemini_metadata(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()

	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 1 #C
	game.metadata.input_info.add_option(builtin_gamepad)
	#Technically you could say Motion Controls because of the shake detection, but not all games use it, and you can't really tell which do and which don't programmatically

	rom = cast(FileROM, game.rom)
	header = rom.read(seek_to=0x21ac, amount=16)
	add_info_from_header(header, game.metadata)
	
	software = game.get_software_list_entry()
	if software:
		add_generic_software_info(software, game.metadata)
