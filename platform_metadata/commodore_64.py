from software_list_info import get_software_list_entry, find_in_software_lists, matcher_args_for_bytes

ccs64_cart_types = {
	#From https://github.com/mamedev/mame/blob/master/src/lib/formats/cbm_crt.cpp
	0: 'Normal',
	1: 'Action Replay',
	2: 'KCS Power Cartridge',
	3: 'Final Cartridge III',
	4: 'Simon\'s Basic',
	5: 'Ocean type 1',
	6: 'Expert Cartridge',
	7: 'Fun Play/Power Play',
	8: 'Super Games',
	9: 'Atomic Power',
	10: 'Epyx Fastload',
	11: 'Westermann Learning',
	12: 'Rex Utility',
	13: 'Final Cartridge I',
	14: 'Magic Formel',
	15: 'C64GS/System 3',
	16: 'WarpSpeed',
	17: 'Dinamic',
	18: 'Sega Zaxxon',
	19: 'Magic Desk/Domark/HES',
	20: 'Super Snapshot V5',
	21: 'Comal-80',
	22: 'Structured BASIC',
	23: 'Ross',
	24: 'Dela EP64',
	25: 'Dela EP7x8',
	26: 'Dela EP256',
	27: 'Rex EP256',
	28: 'Mikro Assembler',
	29: 'Final Cartridge Plus',
	30: 'Action Replay 4',
	31: 'Stardos',
	32: 'EasyFlash',
	33: 'EasyFlash Xbank',
	34: 'Capture',
	35: 'Action Replay 3',
	36: 'Retro Replay',
	37: 'MMC64',
	38: 'MMC Replay',
	39: 'IDE64',
	40: 'Super Snapshot V4',
	41: 'IEEE-488',
	42: 'Game Killer',
	43: 'Prophet64',
	44: 'EXOS',
	45: 'Freeze Frame',
	46: 'Freeze Machine',
	47: 'Snapshot64',
	48: 'Super Explode V5.0',
	49: 'Magic Voice',
	50: 'Action Replay 2',
	51: 'MACH 5',
	52: 'Diashow-Maker',
	53: 'Pagefox',
	#54 is question mark, apparently
	55: 'Silverrock',
}

def get_commodore_64_software(game, headered):
	if headered:
		#Skip CRT header
		data = game.rom.read(seek_to=64)

		total_data = b''
		i = 0
		while i < len(data):
			chip_header = data[i:i+16]
			total_size = int.from_bytes(chip_header[4:8], 'big')
			chip_size = int.from_bytes(chip_header[14:16], 'big')
			total_data += data[i+16:i+16+chip_size]
			i += total_size

		return find_in_software_lists(game.software_lists, matcher_args_for_bytes(total_data))

	return get_software_list_entry(game)

def add_commodore_64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:16]
	if magic == b'C64 CARTRIDGE   ':
		headered = True
		game.metadata.specific_info['Header-Format'] = 'CCS64'
		cart_type = int.from_bytes(header[22:24], 'big')
		#I'm just gonna call it a mapper for consistency, even though that could be argued to be the wrong terminology, but... eh
		game.metadata.specific_info['Mapper-Number'] = cart_type
		game.metadata.specific_info['Mapper'] = ccs64_cart_types.get(cart_type, 'CCS64 type %d' % cart_type)

		try:
			cartridge_name = header[0x20:0x3f].decode('ascii').strip('\0')
			if cartridge_name:
				game.metadata.specific_info['Internal-Title'] = cartridge_name
		except UnicodeDecodeError:
			pass
	else:
		headered = False

	game.metadata.specific_info['Headered'] = headered

	software = get_commodore_64_software(game, headered)
	if software:
		software.add_generic_info(game.metadata)
		game.metadata.notes = software.get_info('usage')
		#Enter 'SYS 32768' to run
		#Commodore: Load "JINGLE",8,1 / Apple IIc and e: Self boots

		#Also see 'requirement' info field... may be useful at some point
		#There's dataarea nvram, but those are two carts which are more accurately described as device BIOSes, so I won't bother
