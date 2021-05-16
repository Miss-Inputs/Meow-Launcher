import input_metadata
from common import load_dict
from common_types import SaveType
from config.system_config import system_configs
from info.region_info import TVSystem
from mame_helpers import MAMENotInstalledException
from mame_machine import does_machine_match_game, get_machines_from_source_file
from metadata import Date
from platform_types import NESPeripheral
from software_list_info import (find_in_software_lists_with_custom_matcher,
                                get_crc32_for_software_list,
                                get_software_list_entry)

nes_config = system_configs.get('NES')
nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

ines_mappers = {
	#6, 8, 17 are some kind of copier thing
	#29 is for homebrew but doesn't really have a name
	#31 is for homebrew musicdisks specifically
	#51, 53, 55, 126, 162, 197, 204, 213, 214, 217, 236, 244, 251 are unknown/undocumented pirate mappers
	#63, 103, 108, 117, 120, 170, 179, 216 are even more unknown
	#160 is unknown (well, undocumented) Sachen mapper; 56, 142, 175 are undocumented Kaiser mappers; 198, 223, 249 are undocumented Waixing mappers
	#98, 102, 109, 110, 122, 124, 127, 128, 129, 130, 131, 161, 239, 247 are unassigned supposedly (I bet someone's assigned them by now)
	#12, 14, 45, 74, 106, 114, 115, 116, 165, 182, 191, 192, 194, 195, 196, 205, 238, 245 are pirate MMC3 clones (interestingly 196 seems to be used for hacks where the protagonist is now Mario)
	#150 is some invalid Sachen thing apparently
	#151 is invalid, but used for VRC1 on VS System
	#87, 92, 152 are used by misc official games but don't seem to have a particular name
	#15, 84, 91, 112, 164, 173, 176, 177, 178, 189, 199, 200, 201, 202, 203, 209, 211, 220, 222, 225, 226, 227, 230, 231, 233, 240, 242, 246, 250, 252, 253 are used for misc unlicensed carts but don't seem to have a particular name
	#100, 101, 181, 241. 248 are basically junk

	0: 'NROM',
	1: 'MMC1',
	2: 'UxROM',
	3: 'CNROM',
	4: 'MMC3',
	5: 'MMC5',
	7: 'AxROM',
	9: 'MMC2',
	10: 'MMC4',
	11: 'Color Dreams', #Unlicensed
	13: 'CPROM',
	16: 'Bandai FCG-1, FCG-2, FCG-4',
	18: 'Jaleco SS88006',
	19: 'Namco 129, 163',
	20: 'FDS', #Not really used in dumps, just for internal use by emulators
	21: 'VRC4a, VRC4c',
	22: 'VRC2a',
	23: 'VRC2b, VRC4e',
	24: 'VRC6a',
	25: 'VRC4b, VRC4d',
	26: 'VRC6b',
	27: 'VRC4 pirate',
	28: 'Action 53',
	30: 'UNROM 512', #Mostly for homebrew
	32: 'Irem G-101',
	33: 'Taito TC0190',
	34: 'BNROM, NINA-001',
	35: 'JY Company with WRAM',
	36: 'TXC 01-22000-400',
	37: 'Super Mario Bros + Tetris + Nintendo World Cup',
	38: 'Crime Busters',
	39: 'Study & Game 35-in-1',
	40: 'Whirlwind Manu SMB2J cartridge hack',
	41: 'Caltron 6-in-1',
	42: 'FDS to cartridge hacks',
	43: 'SMB2J cartridge hack (43)', #Mr. Mary 2
	44: 'Super Big 7-in-1',
	46: 'Game Station',
	47: "Super Spike V'Ball + Nintendo World Cup",
	48: 'Taito TC0690',
	49: 'Super HIK 4-in-1',
	50: 'SMB2J cartridge hack (50)',
	52: 'Mario Party 7-in-1',
	54: 'Novel Diamond 9999999-in-1',
	57: 'GK 47-in-1',
	58: 'Game Star 68-in-1',
	59: 'BMC-T3H53', #Apparently FCEUX and others assign this to 60
	60: 'Reset Based 4-in-1',
	61: '20-in-1',
	62: 'Super 700-in-1',
	64: 'Tengen RAMBO-1',
	65: 'Irem H3001',
	66: 'GxROM',
	67: 'Sunsoft-3',
	68: 'Sunsoft-4',
	69: 'Sunsoft FME-7',
	70: 'Family Trainer',
	71: 'Camerica',
	72: 'Jaleco JF-17',
	73: 'Konami VRC3',
	75: 'Konami VRC1',
	76: 'NAMCOT-3446',
	77: 'Napoleon Senki',
	78: 'Irem 74HC161',
	79: 'American Video Entertainment NINA-03, NINA-06',
	80: 'Taito X1-005',
	81: 'NTDEC Super Gun',
	82: 'Taito X1-017',
	83: 'Cony',
	85: 'Konami VRC7',
	86: 'Jaleco JF-13',
	88: 'Namco 118',
	89: 'Sunsoft-2 IC on Sunsoft-3 board',
	90: 'JY Company',
	93: 'Sunsoft-2 IC on Sunsoft-3R board',
	94: 'UN1ROM', #Used only in Senjou no Ookami
	95: 'NAMCOT-3425',
	96: 'Oeka Kids',
	97: 'Irem TAM-S1',
	99: 'VS System CNROM',
	104: 'Pegasus 5 in 1',
	105: 'NES-EVENT',
	107: 'Magic Dragon',
	111: 'GTROM', #Homebrew board
	112: 'Asder',
	113: 'MB-91',
	118: 'MMC3 (TKSROM, TLSROM)',
	119: 'TQROM',
	121: '卡聖 A9711, A9713',
	123: '卡聖 H2288',
	125: 'Whirlwind Manu Monty on the Run cartridge hack',
	132: 'TXC UNL-22211',
	133: 'Sachen 3009',
	134: 'Sachen 74LS374N',
	135: 'Sachen 8259A',
	136: 'Sachen 3011',
	137: 'Sachen 8259D',
	138: 'Sachen 8259B',
	139: 'Sachen 8259C',
	140: 'Jaleco JF-11, JF-14',
	141: 'Sachen 8259A',
	143: 'NROM with Sachen copy protection',
	144: 'AGCI 50282',
	145: 'Sachen SA-72007',
	146: 'Sachen Galactic Crusader',
	147: 'Sachen 3018',
	148: 'Tengen 800008',
	149: 'Sachen SA-0036',
	153: 'Bandai BA-JUMP2',
	154: 'NAMCOT-3453',
	155: 'MMC1A',
	156: 'DIS23C01 DAOU ROM CONTROLLER',
	157: 'Datach Joint ROM System',
	158: 'Tengen 800037',
	159: 'LZ93D50 with 24C01',
	163: 'Nanjing',
	166: 'Subor 166',
	167: 'Subor 167',
	168: 'Racermate Challenge 2',
	169: 'Yuxing',
	171: 'Kaiser KS-7058',
	172: 'Super Mega P-4070',
	174: 'NTDec 5-in-1',
	180: 'UNROM (Crazy Climber)',
	183: 'Suikan Pipe',
	184: 'Sunsoft-1',
	185: 'CNROM with copy protection',
	186: 'StudyBox',
	187: '卡聖 A98402',
	188: 'Karaoke Studio',
	190: 'Magic Kid GooGoo',
	193: 'NTDEC TC-112',
	206: 'Namcot 108, Tengen MIMIC-1',
	207: 'Fudou Myouou Den',
	208: '快打傳説 Street Fighter IV',
	210: 'Namco 175, 340',
	212: 'BMC Super HiK 300-in-1',
	215: 'Sugar Softec',
	218: 'Magic Floor', #Homebrew
	219: '卡聖 A9461',
	221: 'N625092 multicart',
	224: '晶科泰 KT-008',
	228: 'Action 52',
	229: 'BMC 31-IN-1',
	232: 'Quattro',
	234: 'Maxi 15',
	235: 'Golden Game 150 in 1',
	237: 'Teletubbies 420-in-1',
	243: 'Sachen 74LS374N',
	254: 'Pikachu Y2K',
	255: '110-in-1 multicart',
}

def decode_bcd(i):
	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def add_fds_metadata(rom, metadata):
	if nes_config and nes_config.options.get('set_fds_as_different_platform'):
		metadata.platform = 'FDS'

	header = rom.read(amount=56)
	if header[:4] == b'FDS\x1a':
		metadata.specific_info['Headered'] = True
		metadata.specific_info['Header-Format'] = 'fwNES'
		rom.header_length_for_crc_calculation = 16
		header = rom.read(seek_to=16, amount=56)
	else:
		metadata.specific_info['Headered'] = False

	licensee_code = '{:02X}'.format(header[15])
	if licensee_code in nintendo_licensee_codes:
		metadata.publisher = nintendo_licensee_codes[licensee_code]

	metadata.specific_info['Revision'] = header[20]
	#Uses Showa years (hence 1925), in theory... but then some disks (notably Zelda) seem to use 19xx years, as it has an actual value of 0x86 which results in it being Showa 86 = 2011, but it should be [Feb 21] 1986, so... hmm
	year = decode_bcd(header[31])
	if 61 <= year <= 99:
		#Showa 61 = 1986 when the FDS was released. Year > 99 wouldn't be valid BCD, so... I'll check back in 2025 to see if anyone's written homebrew for the FDS in that year and then I'll figure out what I'm doing. But homebrew right now seems to leave the year as 00 anyway, though
		year = 1925 + year
	else:
		year = 1900 + year
	month = decode_bcd(header[32])
	day = decode_bcd(header[33])
	if not metadata.release_date:
		metadata.release_date = Date(year, month, day, True)
	

def add_ines_metadata(rom, metadata, header):
	metadata.specific_info['Headered'] = True
	#Some emulators are okay with not having a header if they have something like an internal database, others are not.
	#Note that \x00 at the end instead of \x1a indicates this is actually Wii U VC, but it's still the same header format
	rom.header_length_for_crc_calculation = 16 #We use a custom software list matcher anyway, but we need to just chop the header off to find it in libretro-database
	prg_size = header[4]
	chr_size = header[5]

	flags = header[6]
	has_battery = (flags & 2) > 0
	metadata.save_type = SaveType.Cart if has_battery else SaveType.Nothing
	metadata.specific_info['Has-iNES-Trainer'] = (flags & 4) > 0
	mapper_lower_nibble = (flags & 0b1111_0000) >> 4

	more_flags = header[7]
	if (more_flags & 3) == 1:
		metadata.specific_info['Arcade-System'] = 'VS Unisystem'
	elif (more_flags & 3) == 2:
		metadata.specific_info['Arcade-System'] = 'PlayChoice-10'

	mapper_upper_nibble = more_flags & 0b1111_0000
	is_nes_2_0 = ((more_flags & 0b_00_00_11_00) >> 2) == 2
	if is_nes_2_0:
		metadata.specific_info['Header-Format'] = 'NES 2.0'
		mapper_upper_upper_nibble = header[8] & 0b1111
		mapper = mapper_lower_nibble | mapper_upper_nibble | (mapper_upper_upper_nibble << 8)
		metadata.specific_info['Mapper-Number'] = mapper
		if mapper in ines_mappers:
			metadata.specific_info['Mapper'] = ines_mappers[mapper]
		else:
			metadata.specific_info['Mapper'] = 'NES 2.0 Mapper %d' % mapper

		metadata.specific_info['Submapper'] = (header[8] & 0b1111_0000) >> 4
		
		metadata.specific_info['PRG-Size'] = ((header[9] & 0b1111) << 4) | prg_size
		metadata.specific_info['CHR-Size'] = (header[9] & 0b1111_0000) | chr_size

		#9/10: PRG/CHR RAM and NVRAM size

		cpu_ppu_timing = header[12] & 0b11
		if cpu_ppu_timing == 0:
			metadata.specific_info['TV-Type'] = TVSystem.NTSC
		elif cpu_ppu_timing == 1:
			metadata.specific_info['TV-Type'] = TVSystem.PAL
		elif cpu_ppu_timing == 2:
			metadata.specific_info['TV-Type'] = TVSystem.Agnostic
		elif cpu_ppu_timing == 3:
			metadata.specific_info['Is-Dendy'] = True

		if (header[7] & 3) == 3:
			metadata.specific_info['Extended-Console-Type'] = header[13] #TODO: Actually use this
		if header[15]:
			default_expansion_device = header[15] #TODO: Actually use this
			metadata.specific_info['Default-Expansion-Device'] = default_expansion_device
			if default_expansion_device == 1:
				metadata.specific_info['Peripheral'] = NESPeripheral.NormalController
			#42 = multicart also exists I guess but it doesn't mean much to us
	else:
		metadata.specific_info['Header-Format'] = 'iNES'
		mapper = mapper_lower_nibble | mapper_upper_nibble
		metadata.specific_info['Mapper-Number'] = mapper
		if mapper in ines_mappers:
			metadata.specific_info['Mapper'] = ines_mappers[mapper]
		else:
			metadata.specific_info['Mapper'] = 'iNES Mapper %d' % mapper

		metadata.specific_info['PRG-Size'] = prg_size * 16 * 1024
		metadata.specific_info['CHR-Size'] = chr_size * 8 * 1024
		#TV type apparently isn't used much despite it being part of the iNES specification, and looking at a lot of headered ROMs it does seem that they are all NTSC other than a few that say PAL that shouldn't be, so yeah, I wouldn't rely on it. Might as well just use the filename.

def _does_nes_rom_match(part, prg_crc, chr_crc):
	prg_area = part.data_areas.get('prg')
	#These two data area names seem to be used for alternate types of carts (Aladdin Deck Enhancer/Datach/etc)
	if not prg_area:
		prg_area = part.data_areas.get('rom')
	if not prg_area:
		prg_area = part.data_areas.get('cart')

	if prg_area:
		#(There is only one ROM, or at least I hope so, otherwise I'd look silly)
		prg_matches = prg_area.roms[0].matches(prg_crc, None)
	else:
		prg_matches = False #prg_crc is None?
	if not prg_matches:
		return False

	chr_area = part.data_areas.get('chr')
	if len(part.data_areas) == 2 and prg_area and not chr_area:
		#This doesn't happen often, but... hmm
		chr_area = part.data_areas.get('rom')
	
	if chr_area:
		chr_matches = chr_area.roms[0].matches(chr_crc, None)
	else:
		chr_matches = chr_crc is None
	if not chr_matches:
		return False

	return True

def _get_headered_nes_rom_software_list_entry(game):
	prg_crc32 = game.metadata.specific_info.get('PRG-CRC')
	chr_crc32 = game.metadata.specific_info.get('CHR-CRC')
	if not prg_crc32 and not chr_crc32:
		prg_size = game.metadata.specific_info.get('PRG-Size', 0)
		chr_size = game.metadata.specific_info.get('CHR-Size', 0)
		#Is it even possible for prg_size to be 0 on a valid ROM?
		prg_offset = 16 + 512 if game.metadata.specific_info.get('Has-iNES-Trainer', False) else 16
		chr_offset = prg_offset + prg_size

		prg_rom = game.rom.read(seek_to=prg_offset, amount=prg_size)
		chr_rom = game.rom.read(seek_to=chr_offset, amount=chr_size) if chr_size else None

		prg_crc32 = get_crc32_for_software_list(prg_rom)
		chr_crc32 = get_crc32_for_software_list(chr_rom) if chr_rom else None

	return find_in_software_lists_with_custom_matcher(game.software_lists, _does_nes_rom_match, [prg_crc32, chr_crc32])

def parse_unif_chunk(metadata, chunk_type, chunk_data):
	if chunk_type == 'PRG0':
		metadata.specific_info['PRG-CRC'] = get_crc32_for_software_list(chunk_data)
	elif chunk_type.startswith('CHR'):
		metadata.specific_info['CHR-CRC'] = get_crc32_for_software_list(chunk_data)
	elif chunk_type == 'MAPR':
		metadata.specific_info['Mapper'] = chunk_data.decode('utf-8', errors='ignore').rstrip('\0')
	elif chunk_type == 'TVCI':
		tv_type = chunk_data[0]
		if tv_type == 0:
			metadata.specific_info['TV-Type'] = TVSystem.NTSC
		elif tv_type == 1:
			metadata.specific_info['TV-Type'] = TVSystem.PAL
		elif tv_type == 2:
			metadata.specific_info['TV-Type'] = TVSystem.Agnostic
	elif chunk_type == 'BATR':
		metadata.save_type = SaveType.Cart if chunk_data[0] else SaveType.Nothing
	elif chunk_type == 'CTRL':
		controller_info = chunk_data[0]
		#This is a bitfield, so actually one could have multiple peripherals
		if controller_info & 16:
			metadata.specific_info['Peripheral'] = NESPeripheral.PowerPad
		if controller_info & 8:
			metadata.specific_info['Peripheral'] = NESPeripheral.ArkanoidPaddle
		if controller_info & 4:
			metadata.specific_info['Peripheral'] = NESPeripheral.ROB
		if controller_info & 2:
			metadata.specific_info['Peripheral'] = NESPeripheral.Zapper
		if controller_info & 1:
			metadata.specific_info['Peripheral'] = NESPeripheral.NormalController
	elif chunk_type == 'READ':
		metadata.notes = chunk_data.decode('utf-8', errors='ignore').rstrip('\0')
	#NAME: Not needed, basically just something similar to the filename
	#MIRR: Probably not needed
	#PCK0, CCK0: CRC32 of PRG/CHR, would be nice except since this chunk isn't always there, we have to calculate it manually anyway
	#WRTR/DINF: Dumping info, who cares
	#VROR: Something to do with considering CHR-ROM as RAM, don't need to worry about this

def add_unif_metadata(rom, metadata):
	metadata.specific_info['Headered'] = True
	metadata.specific_info['Header-Format'] = 'UNIF'

	pos = 32
	size = rom.get_size()
	while pos < size:
		chunk = rom.read(amount=8, seek_to=pos)
		chunk_type = chunk[0:4].decode('ascii', errors='ignore')
		chunk_length = int.from_bytes(chunk[4:8], 'little')	
		
		chunk_data = rom.read(amount=chunk_length, seek_to=pos+8)
		parse_unif_chunk(metadata, chunk_type, chunk_data)

		pos += 8 + chunk_length

def try_get_equivalent_arcade(rom, metadata):
	if not hasattr(try_get_equivalent_arcade, 'playchoice10_games'):
		try:
			try_get_equivalent_arcade.playchoice10_games = list(get_machines_from_source_file('playch10'))
		except MAMENotInstalledException:
			try_get_equivalent_arcade.playchoice10_games = []
	if not hasattr(try_get_equivalent_arcade, 'vsnes_games'):
		try:
			try_get_equivalent_arcade.vsnes_games = list(get_machines_from_source_file('vsnes'))
		except MAMENotInstalledException:
			try_get_equivalent_arcade.vsnes_games = []

	for vsnes_machine in try_get_equivalent_arcade.vsnes_games:
		if does_machine_match_game(rom.name, metadata, vsnes_machine, match_vs_system=True):
			return vsnes_machine

	for playchoice10_machine in try_get_equivalent_arcade.playchoice10_games:
		if does_machine_match_game(rom.name, metadata, playchoice10_machine):
			return playchoice10_machine
	
	return None

standard_controller = input_metadata.NormalController()
standard_controller.dpads = 1
standard_controller.face_buttons = 2 #A B

def add_nes_software_list_metadata(software, metadata):
	software.add_standard_metadata(metadata)

	nes_peripheral = None

	#FIXME: Acktually, you can have multiple feature = peripherals
	#See also: SMB / Duck Hunt / World Class Track Meet multicart, with both zapper and powerpad
	#Actually, how does that even work in real life? Are the controllers hotplugged? Different ports?
	peripheral = software.get_part_feature('peripheral')
	if peripheral == 'zapper':
		nes_peripheral = NESPeripheral.Zapper
		zapper = input_metadata.LightGun()
		zapper.buttons = 1
		metadata.input_info.add_option(zapper)
	elif peripheral == 'vaus':
		nes_peripheral = NESPeripheral.ArkanoidPaddle
		vaus = input_metadata.Paddle()
		vaus.buttons = 1
		metadata.input_info.add_option(vaus)
		#Can still use standard controller
		metadata.input_info.add_option(standard_controller)
	elif peripheral in ('powerpad', 'ftrainer', 'fffitness'):
		nes_peripheral = NESPeripheral.PowerPad

		power_pad = input_metadata.NormalController()
		power_pad.face_buttons = 12 #"face"
		metadata.input_info.add_option(power_pad)
	elif peripheral == 'powerglove':
		nes_peripheral = NESPeripheral.PowerGlove
		#Hmm... apparently it functions as a standard NES controller, but there are 2 games specifically designed for glove usage? So it must do something extra I guess

		power_glove = input_metadata.MotionControls()
		#game.metadata.input_info.buttons = 11 #Standard A + B + 9 program buttons
		metadata.input_info.add_option(power_glove)
	elif peripheral == 'rob':
		nes_peripheral = NESPeripheral.ROB
		#I'll leave input info alone, because I'm not sure how I would classify ROB
		metadata.input_info.add_option(standard_controller)
	elif peripheral == 'fc_keyboard':
		nes_peripheral = NESPeripheral.FamicomKeyboard

		famicom_keyboard = input_metadata.Keyboard()
		famicom_keyboard.keys = 72
		metadata.input_info.add_option(famicom_keyboard)
	elif peripheral == 'subor_keyboard':
		nes_peripheral = NESPeripheral.SuborKeyboard

		subor_keyboard = input_metadata.Keyboard()
		subor_keyboard.keys = 96
		metadata.input_info.add_option(subor_keyboard)
	elif peripheral == 'mpiano':
		nes_peripheral = NESPeripheral.Piano
		#Apparently, it's actually just a MIDI keyboard, hence the MAME driver adds MIDI in/out ports

		miracle_piano = input_metadata.Custom('88-key piano')
		#game.metadata.input_info.buttons = 88
		metadata.input_info.add_option(miracle_piano)
	else:
		metadata.input_info.add_option(standard_controller)

	#Well, it wouldn't be a controller... not sure how this one works exactly
	metadata.specific_info['Uses-3D-Glasses'] = peripheral == '3dglasses'
	if peripheral == 'turbofile':
		#Thing that goes into Famicom controller expansion port and saves stuff
		metadata.save_type = SaveType.MemoryCard
	#There's a "battlebox" which Armadillo (Japan) uses?
	#Barcode World (Japan) uses "barcode"
	#Peripheral = 4p_adapter: 4 players
	#Gimmi a Break stuff: "partytap"?
	#Hyper Olympic (Japan): "hypershot"
	#Ide Yousuke Meijin no Jissen Mahjong (Jpn, Rev. A): "mjcontroller" (mahjong controller?)
	#RacerMate Challenge 2: "racermate"
	#Top Rider (Japan): "toprider"

	metadata.notes = software.infos.get('usage')
	#This only works on a Famicom with Mahjong Controller attached
	#This only is only supported by Famicom [sic?]

	if nes_peripheral:
		metadata.specific_info['Peripheral'] = nes_peripheral

def add_nes_metadata(game):
	equivalent_arcade = try_get_equivalent_arcade(game.rom, game.metadata)
	if equivalent_arcade:
		game.metadata.specific_info['Equivalent-Arcade'] = equivalent_arcade

	if game.rom.extension == 'fds':
		add_fds_metadata(game.rom, game.metadata)
	else:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic in (b'NES\x00', b'NES\x1a'):
			add_ines_metadata(game.rom, game.metadata, header)
		elif magic == b'UNIF':
			add_unif_metadata(game.rom, game.metadata)
		else:
			game.metadata.specific_info['Headered'] = False

	software = None
	if not game.metadata.specific_info.get('Headered', False) or game.metadata.specific_info.get('Header-Format') == 'fwNES':
		software = get_software_list_entry(game)
	elif game.metadata.specific_info.get('Header-Format') in ('iNES', 'NES 2.0', 'UNIF'):
		software = _get_headered_nes_rom_software_list_entry(game)

	game.metadata.specific_info['Peripheral'] = NESPeripheral.NormalController

	if software:
		add_nes_software_list_metadata(software, game.metadata)
