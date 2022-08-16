from typing import TYPE_CHECKING

from meowlauncher.common_types import SaveType

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.metadata import Metadata

publishers = {
	1: 'Bandai',
	2: 'Taito',
	3: 'Tomy',
	4: 'Koei',
	5: 'Data East',
	6: 'Asmik Ace',
	7: 'Media Entertainment',
	8: 'Nichibutsu',
	10: 'Coconuts Japan',
	11: 'Sammy',
	12: 'Sunsoft',
	13: 'Mebius',
	14: 'Banpresto',
	16: 'Jaleco',
	17: 'Imagineer',
	18: 'Konami',
	22: 'Kobunsha',
	23: 'Bottom Up',
	25: 'Sunrise',
	26: 'Cyber Front',
	27: 'Mega House',
	28: 'Interbec',
	30: 'Ninhon Application',
	32: 'Athena',
	33: 'KID',
	34: 'HAL',
	35: 'Yuki Enterprise',
	36: 'Omega Micott',
	38: 'Kadokawa Shoten',
	40: 'Squaresoft',
	42: 'NTT DoCoMo',
	43: 'Tom Create',
	45: 'Namco',
	46: 'Movic',
	49: 'Vanguard',
	50: 'Megatron',
	51: 'Wiz',
	54: 'Capcom',
	#24: Kaga Tech, Naxat, Mechanic Arms, or Media Entertainment
	#31: Bandai Visual or Emotion
	#37: Layup or Upstar
	#39: Shall Luck or Cocktail Soft
	#47: E3 Staff or Gust
}

def add_wonderswan_header_info(rom: 'FileROM', metadata: 'Metadata') -> None:
	rom_size = rom.size
	header_start_position = rom_size - 10
	header = rom.read(seek_to=header_start_position, amount=10)

	publisher_code = header[0]
	if publisher_code in publishers:
		metadata.publisher = publishers[publisher_code]
	metadata.specific_info['Is Colour?'] = header[1] == 1

	metadata.product_code = str(header[2])

	metadata.specific_info['Revision'] = header[3]

	save_info = header[5]
	#If >= 10, contains EEPROM, if >0 and < 10, contains SRAM; number determines size by arbitrary lookup table but that's not that important for our purposes I guess
	metadata.save_type = SaveType.Cart if save_info > 0 else SaveType.Nothing

	metadata.specific_info['Has RTC?'] = header[7] == 1
	flags = header[6]
	metadata.specific_info['Display Orientation'] = 'Vertical' if flags & 1 else 'Horizontal'
	#Checksum schmecksum
	