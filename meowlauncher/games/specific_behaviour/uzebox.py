from typing import TYPE_CHECKING, cast

from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.metadata import Date, Metadata

from .common import snes_controllers

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame

def add_info_from_uze_header(header: bytes, metadata: Metadata) -> None:
	#Header version: 6
	#Target: 7 (0 = ATmega644, 1 = reserved for ATmega1284)
	#Program size: 8-0xc (LE)
	metadata.release_date = Date(int.from_bytes(header[0xc:0xe], 'little'))
	metadata.add_alternate_name(header[0xe:0x2e].decode('ascii', errors='backslashreplace').rstrip('\0'), 'Banner Title')
	metadata.developer = metadata.publisher = header[0x2e:0x4e].decode('ascii', errors='backslashreplace').rstrip('\0')
	#Icon (sadly unused) (16 x 16, BBGGGRRR): 0x4e:0x14e
	#CRC32: 0x14e:0x152
	uses_mouse = header[0x152] == 1
	metadata.specific_info['Uses Mouse?'] = uses_mouse
	#Potentially it could use other weird SNES peripherals but this should do
	metadata.input_info.add_option(snes_controllers.mouse if uses_mouse else snes_controllers.controller)

	description = header[0x153:0x193].decode('ascii', errors='backslashreplace').rstrip('\0')
	if description:
		#Official documentation claims this is unused, but it seems that it is used after all (although often identical to title)
		metadata.descriptions['Banner Description'] = description

def add_uzebox_custom_info(game: 'ROMGame') -> None:
	#Save type: ????

	header = cast(FileROM, game.rom).read(amount=512)
	magic = header[0:6]
	if magic != b'UZEBOX':
		has_header = False
	else:
		has_header = True
		add_info_from_uze_header(header, game.metadata)
		
	game.metadata.specific_info['Headered?'] = has_header

	software = game.get_software_list_entry(512 if has_header else 0)
	if software:
		add_generic_software_info(software, game.metadata)
		if game.metadata.publisher == 'Belogic':
			#Belogic just make the console itself, but don't actually make games necessarily
			game.metadata.publisher = game.metadata.developer
