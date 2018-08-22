import calendar

from metadata import SaveType
from .nintendo_common import nintendo_licensee_codes

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

def add_fds_metadata(game):
	game.metadata.platform = 'FDS'
	header = game.rom.read(amount=56)
	if header[:4] == b'FDS\x1a':
		header = game.rom.read(seek_to=16, amount=56)

	licensee_code = '{:02X}'.format(header[15])
	if licensee_code in nintendo_licensee_codes:
		game.metadata.publisher = nintendo_licensee_codes[licensee_code]
		
	game.metadata.revision = header[20]
	#Uses Showa years (hence 1925), in theory... but then some disks (notably Zelda) seem to use 19xx years, as it has an actual value of 0x86 which results in it being Showa 86 = 2011, but it should be [Feb 21] 1986, so... hmm
	year = decode_bcd(header[31])
	if year >= 61 and year <= 99: #Showa 61 = 1986 when the FDS was released. Year > 99 wouldn't be valid BCD, so... I'll check back in 2025 to see if anyone's written homebrew for the FDS in that year and then I'll figure out what I'm doing. But homebrew right now seems to leave the year as 00 anyway, though
		year = 1925 + year
		game.metadata.year = year
	month = decode_bcd(header[32])
	if month >= 1 and month <= 12:
		game.metadata.month = calendar.month_name[month]
	day = decode_bcd(header[33])
	if day >= 1 and day <= 28:
		game.metadata.day = day

def add_ines_metadata(game, header):
	game.metadata.specific_info['Headered'] = True
	#Some emulators are okay with not having a header if they have something like an internal database, others are not.
	#Note that \x00 at the end instead of \x1a indicates this is actually Wii U VC, but it's still the same header format
	flags = header[6]
	has_battery = (flags & 2) > 0
	game.metadata.save_type = SaveType.Cart if has_battery else SaveType.Nothing
	mapper_lower_nibble = (flags & 0b1111_0000) >> 4

	more_flags = header[7]
	if more_flags & 1:
		game.metadata.platform = 'VS Unisystem'
	elif more_flags & 2:
		game.metadata.platform = 'PlayChoice-10'
			
	mapper_upper_nibble = more_flags & 0b1111_0000
	is_nes_2_0 = ((more_flags & 0b_00_00_11_00) >> 2) == 2
	if is_nes_2_0:
		game.metadata.specific_info['Header-Format'] = 'NES 2.0'
		#Heck
	else:
		game.metadata.specific_info['Header-Format'] = 'iNES'
		mapper = mapper_lower_nibble | mapper_upper_nibble
		game.metadata.specific_info['Mapper-Number'] = mapper
		if mapper in ines_mappers:
			game.metadata.specific_info['Mapper'] = ines_mappers[mapper]
		else:
			game.metadata.specific_info['Mapper'] = 'iNES Mapper %d' % mapper
	#TV type apparently isn't used much despite it being part of the iNES specification, and looking at a lot of headered ROMs it does seem that they are all NTSC other than a few that say PAL that shouldn't be, so yeah, I wouldn't rely on it. Might as well just use the filename.

def add_nes_metadata(game):
	if game.rom.extension == 'fds':
		add_fds_metadata(game)
	else:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'NES\x00' or magic == b'NES\x1a':
			add_ines_metadata(game, header)
		else:
			game.metadata.specific_info['Headered'] = False
