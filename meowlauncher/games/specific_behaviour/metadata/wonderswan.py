from typing import cast

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame

from .generic import add_generic_info

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

def add_wonderswan_metadata(game: ROMGame):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	if game.metadata.platform == 'Benesse Pocket Challenge V2':
		builtin_gamepad.face_buttons = 3 #I don't know what they're called
	else:
		#Because of the rotation, it's hard to say which one of the sets of 4 buttons is the one used for directional control; but one of them will be
		builtin_gamepad.face_buttons = 6
	game.metadata.input_info.add_option(builtin_gamepad)

	rom = cast(FileROM, game.rom)
	rom_size = rom.get_size()
	header_start_position = rom_size - 10
	header = rom.read(seek_to=header_start_position, amount=10)

	publisher_code = header[0]
	if publisher_code in publishers:
		game.metadata.publisher = publishers[publisher_code]
	game.metadata.specific_info['Is Colour?'] = header[1] == 1

	game.metadata.product_code = str(header[2])

	game.metadata.specific_info['Revision'] = header[3]

	save_info = header[5]
	#If >= 10, contains EEPROM, if >0 and < 10, contains SRAM; number determines size by arbitrary lookup table but that's not that important for our purposes I guess
	game.metadata.save_type = SaveType.Cart if save_info > 0 else SaveType.Nothing

	game.metadata.specific_info['Has RTC?'] = header[7] == 1
	flags = header[6]
	game.metadata.specific_info['Screen Orientation'] = 'Vertical' if flags & 1 else 'Horizontal'
	#Checksum schmecksum

	add_generic_info(game)
	#software = get_software_list_entry(game)
	#if software:
	#	software.add_standard_metadata(game.metadata)
		#We could get save type from software.has_data_area('sram' or 'eeprom') but I think we can trust the header flags for now, even with BPCv2 carts
		#By the same token we can get screen orientation = vertical if feature rotated = 'yes'
