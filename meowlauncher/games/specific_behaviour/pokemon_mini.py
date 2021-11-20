from typing import TYPE_CHECKING

from meowlauncher import input_metadata
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.metadata import Metadata

def _add_info_from_header(header: bytes, metadata: 'Metadata'):
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

def add_pokemini_rom_file_info(rom: 'FileROM', metadata: 'Metadata'):
	header = rom.read(seek_to=0x21ac, amount=16)
	_add_info_from_header(header, metadata)

def add_pokemini_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()

	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 1 #C
	metadata.input_info.add_option(builtin_gamepad)
	#Technically you could say Motion Controls because of the shake detection, but not all games use it, and you can't really tell which do and which don't programmatically
