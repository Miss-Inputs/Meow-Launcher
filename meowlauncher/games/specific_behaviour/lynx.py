import contextlib
from typing import TYPE_CHECKING, cast

from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.roms.rom import FileROM

from .static_platform_info import add_lynx_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

def add_info_from_lynx_header(header: bytes, game_info: 'GameInfo') -> None:
	"""TODO: Where is this from?
	UBYTE   magic[4];
	UWORD   page_size_bank0;
	UWORD   page_size_bank1;
	UWORD   version; #That'd be the header version by the looks of it, not the revision of the cart
	UBYTE   cartname[32];
	UBYTE   manufname[16];
	UBYTE   rotation;
	UBYTE   spare[5];"""
	with contextlib.suppress(UnicodeDecodeError):
		game_info.add_alternate_name(header[0x0a:0x2a].rstrip(b'\0 ').decode('ascii', 'backslashreplace'), 'Header Title')
	with contextlib.suppress(UnicodeDecodeError):
		game_info.publisher = header[0x2a:0x3a].strip(b'\0').decode('ascii')
	rotation = header[0x3a]
	if rotation == 0:
		game_info.specific_info['Display Rotation'] = 'None'
	elif rotation == 1:
		game_info.specific_info['Display Rotation'] = 'Left'
	elif rotation == 2:
		game_info.specific_info['Display Rotation'] = 'Right'

def add_lynx_custom_info(game: 'ROMGame') -> None:
	add_lynx_info(game.info)

	rom = cast(FileROM, game.rom)
	magic = rom.read(amount=4)
	is_headered = magic == b'LYNX'
	game.info.specific_info['Headered?'] = is_headered
	if is_headered:
		header = rom.read(amount=64)
		add_info_from_lynx_header(header, game.info)
		rom.header_length_for_crc_calculation = 64	

	software = game.get_software_list_entry()
	if software:
		add_generic_software_info(software, game.info)
