from typing import TYPE_CHECKING
from meowlauncher.common_types import SaveType

from meowlauncher.info import Date
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.info import GameInfo

def add_ngp_header_info(rom: 'FileROM', metadata: 'GameInfo') -> None:
	header = rom.read(amount=64)
	copyright_string = header[:28]
	metadata.specific_info['Copyright'] = copyright_string.decode('ascii', 'backslashreplace')
	if copyright_string == b'COPYRIGHT BY SNK CORPORATION':
		metadata.publisher = 'SNK'
	#Otherwise it'd say " LICENSED BY SNK CORPORATION" and that could be any dang third party which isn't terribly useful
	#There's really not much here, so I didn't even bother reading the whole header
	metadata.product_code = str(int.from_bytes(header[32:34], 'little'))
	metadata.specific_info['Revision'] = header[34]
	metadata.specific_info['Is Colour?'] = header[35] == 0x10
	internal_title = header[36:48].rstrip(b'\0').decode('ascii', 'backslashreplace')
	if internal_title:
		metadata.specific_info['Internal Title'] = internal_title

def add_vectrex_header_info(rom: 'FileROM', metadata: 'GameInfo') -> None:
	try:
		year = convert_alphanumeric(rom.read(seek_to=6, amount=4))
		try:
			if int(year) > 1982: #If it's any less than that, we know it was invalid (or maybe it was a prototype, but then I especially don't trust the header)
				year_date = Date(year, is_guessed=True)
				if year_date.is_better_than(metadata.release_date):
					metadata.release_date = metadata.release_date
		except ValueError:
			pass
	except NotAlphanumericException:
		pass

def add_doom_rom_file_info(rom: 'FileROM', metadata: 'GameInfo') -> None:
	magic = rom.read(amount=4)
	if magic == b'PWAD':
		metadata.specific_info['Is PWAD?'] = True
	
	metadata.save_type = SaveType.Internal #Hmm this would be more of a static system info thing, oh well

def add_pokemini_rom_file_info(rom: 'FileROM', metadata: 'GameInfo') -> None:
	header = rom.read(seek_to=0x21ac, amount=16)
	#https://github.com/pokemon-mini/pm-dev-docs/wiki/PM_Cartridge - we are only bothering to read a small part of the thing, which is really all that's there
	product_code_bytes = header[0:4]
	try:
		product_code = convert_alphanumeric(product_code_bytes)
		metadata.product_code = product_code
	except NotAlphanumericException:
		pass
	title = header[4:16].rstrip(b'\0 ').decode('shift_jis', errors='backslashreplace')
	if title:
		metadata.specific_info['Internal Title'] = title
