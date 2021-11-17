from typing import cast

from meowlauncher import input_metadata
from meowlauncher.games.mame_common.software_list_info import \
    get_software_list_entry
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Metadata

def add_info_from_lynx_header(header: bytes, metadata: Metadata):
	#UBYTE   magic[4];
	#UWORD   page_size_bank0;
	#UWORD   page_size_bank1;
	#UWORD   version; #That'd be the header version by the looks of it, not the revision of the cart
	#UBYTE   cartname[32];
	#UBYTE   manufname[16];
	#UBYTE   rotation;
	#UBYTE   spare[5];
	try:
		metadata.publisher = header[0x2a:0x3a].decode('ascii').strip('\0')
	except UnicodeDecodeError:
		pass
	rotation = header[0x3a]
	if rotation == 0:
		metadata.specific_info['Screen Rotation'] = 'None'
	elif rotation == 1:
		metadata.specific_info['Screen Rotation'] = 'Left'
	elif rotation == 2:
		metadata.specific_info['Screen Rotation'] = 'Right'

def add_lynx_metadata(game: ROMGame):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.add_option(builtin_gamepad)

	rom = cast(FileROM, game.rom)
	magic = rom.read(amount=4)
	is_headered = magic == b'LYNX'
	game.metadata.specific_info['Headered?'] = is_headered
	if is_headered:
		header = rom.read(amount=64)
		add_info_from_lynx_header(header, game.metadata)
		rom.header_length_for_crc_calculation = 64	

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
