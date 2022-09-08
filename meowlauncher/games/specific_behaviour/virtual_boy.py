from typing import TYPE_CHECKING

from meowlauncher.games.roms.rom import FileROM
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

if TYPE_CHECKING:
	from meowlauncher.metadata import Metadata

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

unofficial_vb_publishers = {
	#From https://planetvb.com/modules/dokuwiki/doku.php?id=info_at_the_end_of_the_rom
	#The PlanetVB people have started using their own publisher codes for individual users / their names... that's kind of annoying and not how this is supposed to work, but I can't really stop them, and homebrew software has already been made like that
	'AB': 'Amos Bieler', #aka RunnerPack
	'AE': 'Aegis Games', #aka VirtualChris
	'CR': 'Christian Radke', #aka KR155E
	'DA': 'Dan Bergman', #aka DanB
	'DB': 'David Tucker',
	'DP': 'Pat Daderko', #aka DogP
	'DW': 'David Williamson', #aka lameboyadvance
	'GP': 'Guy Perfect',
	'JA': 'Jorge Andres Eremiev',
	'MH': 'Matej Horvat', #aka HorvatM
	'MK': 'Martin Kujaczynski',
	'SP': 'Sploopby!', #aka Fwirt
	'TS': 'Thunderstruck',
	'VE': 'Alberto Covarrubias', #aka Virtual-E
}

def add_virtual_boy_rom_info(rom: FileROM, metadata: 'Metadata') -> None:
	rom_size = rom.size
	header_start_position = rom_size - 544 #Wait wouldn't that make it a footer sorta
	header = rom.read(seek_to=header_start_position, amount=32)
	title = header[0:20].rstrip(b'\0 ').decode('shift_jis', errors='backslashreplace')
	if title:
		metadata.specific_info['Internal Title'] = title
	
	try:
		licensee_code = convert_alphanumeric(header[25:27])
		if licensee_code in nintendo_licensee_codes:
			metadata.publisher = nintendo_licensee_codes[licensee_code]
		elif licensee_code in unofficial_vb_publishers:
			metadata.publisher = unofficial_vb_publishers[licensee_code]
	except NotAlphanumericException:
		pass

	try:
		metadata.product_code = convert_alphanumeric(header[27:31])
	except NotAlphanumericException:
		pass
	#Can get country from product_code[3] if needed

	metadata.specific_info['Revision'] = header[31]
