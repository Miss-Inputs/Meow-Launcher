import sys
import os
import xml.etree.ElementTree as ElementTree
import binascii
import subprocess
import hashlib
import re

from region_info import TVSystem
from metadata import SaveType
from region_detect import get_region_by_name

debug = '--debug' in sys.argv

#For roms.py, gets metadata in ways specific to certain platforms
#I guess this is duplicating a lot of ROMniscience code, huh? Well, it's my project, and I'll use it for reference for my other project if I want. But I guess there is duplication there. I mean, it's C# and Python, so I can't really combine them directly, but it makes me think... it makes me overthink. That's the best kind of think.

#Metadata used in arcade: main_input, emulation_status, genre, subgenre, nsfw, language, year, author
#Gamecube, 3DS, Wii can sorta find the languages (or at least the title/banner stuff) by examining the ROM itself...
#though as you have .gcz files for the former, that gets a bit involved, actually yeah any of what I'm thinking would
#be difficult without a solid generic file handling thing, but still
#Can get these from the ROM/disc/etc itself:
#	main_input: Megadrive family, Atari 7800 (all through lookup table)
#	year: Megadrive family (usually; via copyright), FDS, GameCube, Satellaview, homebrew SMS/Game Gear, Atari 5200
#	(sometimes), Vectrex, ColecoVersion (sometimes), homebrew Wii
#	author: Homebrew SMS/Game Gear, ColecoVision (in uppercase, sometimes)
#		With a giant lookup table: GBA, Game Boy, SNES, Satellaview, Megadrive family, commercial SMS/Game Gear, Virtual
#		Boy, FDS, Wonderswan, GameCube, 3DS, Wii, DS
#		Neo Geo Pocket can say if SNK, but nothing specific if not SNK
#	language: 3DS, DS, GameCube somewhat (can see title languages, though this isn't a complete indication)
#	nsfw: Sort of; Wii/3DS can do this but only to show that a game is 18+ in a given country etc, but not why it's that
#	rating and of course different countries can have odd reasons
#Maybe MAME software list could say something?  If nothing else, it could give us emulation_status (supported=partial,
#supported=no) where we use MAME for that platform

#Sorry about this taking up a lot of space in the module. Not sure how I'd organize everything in future.
nintendo_licensee_codes = {
	'01': 'Nintendo',
	'08': 'Capcom',
	'09': 'Hot-B',
	'0A': 'Jaleco',
	'0B': 'Coconuts',
	'0C': 'Elite Systems',
	'13': 'EA Japan',
	'18': 'Hudson Soft',
	'19': 'Bandai (B-AI)',
	'1A': 'Yanoman',
	'1D': 'Clary',
	'1M': 'Micro Cabin',
	'1Q': 'TDK (Japan)',
	'20': 'Zoo',
	'24': 'PCM Complete',
	'29': 'Seta',
	'2L': 'Tamsoft',
	'2N': 'Smilesoft',
	'2P': 'The Pokémon Company',
	'35': 'Hector',
	'36': 'Codemasters',
	'3E': 'Gremlin',
	'41': 'Ubisoft',
	'44': 'Malibu',
	'47': 'Bullet-Proof Software/Spectrum Holobyte',
	'49': 'Irem',
	'4A': 'Gakken',
	'4B': 'Raya Systems',
	'4F': 'Eidos',
	'4Q': 'Disney',
	'4S': 'Black Pearl Software',
	'4Y': 'Rare',
	'4Z': 'Crave Entertainment',
	'50': 'Absolute',
	'51': 'Acclaim',
	'52': 'Activision',
	'53': 'Sammy (America)',
	'54': 'Take-Two Interactive',
	'55': 'Hi-Tech Expressions',
	'56': 'LJN',
	'57': 'Matchbox',
	'58': 'Mattel',
	'59': 'Milton Bradley',
	'5A': 'Mindscape',
	'5B': 'Romstar',
	'5D': 'Midway/Tradewest/Williams',
	'5F': 'American Softworks',
	'5G': 'Majesco',
	'5H': 'The 3DO Company',
	'5K': 'Hasbro',
	'5L': 'NewKidsCo',
	'5Q': 'Lego',
	'5T': 'Cyro Interactive',
	'5X': 'Microids',
	'5Z': 'Classified Games',
	'60': 'Titus',
	'61': 'Virgin',
	'64': 'LucasArts',
	'67': 'Ocean',
	'69': 'Electronic Arts',
	'6B': 'Beam Software/Melbourne House',
	'6F': 'Electro Brain',
	'6H': 'BBC Multimedia',
	'6J': 'Software 2000',
	'6L': 'BAM! Entertainment',
	'6S': 'TDK',
	'6V': 'JoWooD Entertainment',
	'70': 'Infogrames/Atari, SA',
	'71': 'Interplay',
	'72': 'JVC',
	'78': 'THQ',
	'79': 'Accolade',
	'7A': 'Triffix Entertainment',
	'7C': 'Microprose',
	'7D': 'Vivendi',
	'7F': 'Kemco',
	'7G': 'Rage Software',
	'7L': 'Simon & Schuster',
	'80': 'Misawa Entertainment',
	'82': 'Namcot',
	'83': 'LOZC',
	'86': 'Tokuma Shoten',
	'87': 'Tsukuda Ori',
	'8B': 'Bullet-Proof Software',
	'8C': 'Vic Tokai',
	'8E': 'Character Soft',
	'8F': "I'Max",
	'8N': 'Success',
	'8P': 'Sega',
	'91': 'Chunsoft',
	'92': 'Video System',
	'95': 'Varie',
	'97': 'Kaneko',
	'99': 'Pack-in Video/Victor Interactive/Marvelous Interactive',
	'9A': 'Nihon Bussan (Nichibutsu)',
	'9B': 'Tecmo',
	'9C': 'Imagineer',
	'9F': 'Nova',
	'9H': 'Bottom Up',
	'9M': 'Jaguar',
	'9N': 'Marvelous',
	'A0': 'Telenet',
	'A1': 'Hori Electric',
	'A2': 'Scorpion Soft',
	'A4': 'Konami',
	'A5': 'K Amusement Leasing',
	'A6': 'Kawada',
	'A7': 'Takara',
	'A8': 'Royal Industries',
	'A9': 'Technos Japan',
	'AA': 'Broderbund',
	'AC': 'Toei Animation',
	'AD': 'Toho',
	'AF': '[Bandai] Namco',
	'AH': 'J-Wing',
	'AL': 'Media Factory',
	'B1': 'ASCII/Nexoft',
	'B2': 'Bandai',
	'B3': 'Soft Pro',
	'B4': 'Enix',
	'B6': 'HAL',
	'B7': 'SNK',
	'B9': 'Pony Canyon',
	'BA': 'Culture Brain',
	'BB': 'Sunsoft',
	'BC': 'Toshiba EMI',
	'BD': 'Sony Imagesoft',
	'BF': 'Sammy',
	'BJ': 'Compile',
	'BL': 'MTO',
	'C0': 'Taito',
	'C1': 'Sunsoft (Chinou Game Series)',
	'C3': 'Squaresoft',
	'C5': 'Data East',
	'C6': 'Tokyo Shoseki (Tonkin House)',
	'C8': 'Koei',
	'C9': 'UFL',
	'CA': 'Konami (Ultra Games)',
	'CB': 'Vap',
	'CC': 'Use',
	'CD': 'Meldac',
	'CE': 'Pony Canyon',
	'CP': 'Enterbrain',
	'CF': 'Angel',
	'D1': 'SOFEL',
	'D2': 'Bothtec / Quest',
	'D3': 'Sigma Enterprises',
	'D4': 'Ask Kodansha',
	'D6': 'Naxat Soft',
	'D7': 'Copya Systems',
	'D9': 'Banpresto',
	'DA': 'Tomy',
	'DB': 'Hiro',
	'DD': 'Masaka',
	'DE': 'Human',
	'DF': 'Altron',
	'E1': 'Towachiki',
	'E2': 'Yuutaka',
	'E4': 'T&E Soft',
	'E5': 'Epoch',
	'E7': 'Athena',
	'E8': 'Asmik',
	'E9': 'Natsume',
	'EA': 'King Records',
	'EB': 'Atlus',
	'EC': 'Epic/Sony Records',
	'EE': 'Information Global Services',
	'F0': 'A Wave',
	'F3': 'Extreme Entertainment',
	'FJ': 'Virtual Toys',
	'FQ': 'iQue',
	'FR': 'Digital Tainment Pool',
	'FT': 'Daiwon C&A Holdings',
	'GD': 'Square Enix',
	'GL': 'Gameloft',
	'HF': 'Level5',
	'JS': 'Digital Leisure',
	'KM': 'Deep Silver',
	'KR': 'Krea Medie',
	'RW': 'RealNetworks',
	'TL': 'Telltale',
	'WY': 'WayForward',
}


def add_atari7800_metadata(game):
	header = game.rom.read(amount=128)
	if header[1:10] != b'ATARI7800':
		game.metadata.specific_info['Headered'] = False
		return

	game.metadata.specific_info['Headered'] = True

	input_type = header[55] #I guess we only care about player 1. They should be the same anyway
	#Although... would that help us know the number of players? Is controller 2 set to none for singleplayer games?
	if input_type == 0:
		game.metadata.input_method = 'Nothing'
	elif input_type == 1:
		game.metadata.input_method = 'Normal'
	elif input_type == 2:
		game.metadata.input_method = 'Light Gun'
	elif input_type == 3:
		game.metadata.input_method = 'Paddle'
	elif input_type == 4:
		game.metadata.input_method = 'Trackball'
	
	tv_type = header[57]

	if tv_type == 1:
		game.metadata.tv_type = TVSystem.PAL
	elif tv_type == 0:
		game.metadata.tv_type = TVSystem.NTSC
	else:
		if debug:
			print('Something is wrong with', game.rom.path, ', has TV type byte of', tv_type)
		game.metadata.specific_info['Invalid-TV-Type'] = True

	save_type = header[58]
	if save_type == 0:
		game.metadata.save_type = SaveType.Nothing
	elif save_type == 1:
		#High Score Cart, an unreleased device that ends up being supported by some games (apparently). Just saves high scores so don't get too excited. It doesn't seem to be supported by MAME which is the only 7800 emulator we use anyway.
		#You plug the High Score Cart into the 7800 and then the game into the High Score Cart, so I guess this is the easiest thing to call it.
		game.metadata.save_type = SaveType.Internal
	elif save_type == 2:
		#AtariVox/SaveKey. Both are third party products which plug into the controller port, so what else can you call them except memory cards?
		game.metadata.save_type = SaveType.MemoryCard

def add_psp_metadata(game):
	game.metadata.main_cpu = 'Allegrex'

	if game.rom.extension == 'pbp':
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		game.rom.name = os.path.basename(game.folder)

def add_gamecube_wii_disc_metadata(game):
	header = game.rom.read(amount=32)
	#Actually, the header is quite a bit bigger than that. We don't really need the disc name or filesystem offset or anything like that, though.
	try:
		game.metadata.specific_info['Product-Code'] = header[:4].decode('ascii')
	except UnicodeDecodeError:
		pass	

	try:
		licensee_code = header[4:6].decode('ascii')
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except UnicodeDecodeError:
		pass
	
def add_gamecube_metadata(game):
	game.metadata.main_cpu = 'IBM PowerPC 603'
	game.metadata.clock_speed = '485 MHz'

	if game.rom.extension == 'gcz' or game.rom.extension == 'tgc':
		#Nuh uh. Not touching weird formats. Not today.
		return
	
	if game.rom.extension == 'iso':
		add_gamecube_wii_disc_metadata(game)

def add_wii_metadata(game):
	game.metadata.main_cpu = 'IBM PowerPC 603'

	if game.rom.extension == 'iso':
		add_gamecube_wii_disc_metadata(game)

	#TODO WiiWare wad
	
	#TODO: Only do this if ext = dol or elf, not that you'd expect to see meta.xml anywhere else but who knows
	xml_path = os.path.join(game.folder, 'meta.xml')
	if os.path.isfile(xml_path):
		#boot is not a helpful launcher name
		try:
			meta_xml = ElementTree.parse(xml_path)
			game.rom.name = meta_xml.findtext('name')
			coder = meta_xml.findtext('coder')
			if not coder:
				coder = meta_xml.findtext('author')
			game.metadata.author = coder
		except ElementTree.ParseError as etree_error:
			if debug:
				print('Ah bugger', game.rom.path, etree_error)
			game.rom.name = os.path.basename(game.folder)

def decode_bcd(i):
	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def add_nes_metadata(game):
	if game.rom.extension == 'fds':
		game.metadata.platform = 'FDS'
		header = game.rom.read(amount=56)
		licensee_code = '{:02X}'.format(header[15])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
		
		#Uses Showa years (hence 1925), in theory... but then some disks (notably Zelda) seem to use 19xx years, as it has an actual value of 0x86 which results in it being Showa 86 = 2011, but it should be [Feb 21] 1986, so... hmm. I guess I could say anything after the Showa perioud (1989) is just plain years? Who's out there developing homebrew in the new millenium anyway
		game.metadata.year = 1925 + decode_bcd(header[31])
	else:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'NES\x00' or magic == b'NES\x1a':
			game.metadata.specific_info['Headered'] = False
			#Some emulators are okay with not having a header if they have something like an internal database, others are not.
			#Note that \x00 at the end instead of \x1a indicates this is actually Wii U VC, but it's still the same header format
			flags = header[7]
			has_battery = (flags & 2) > 0
			game.metadata.save_type = SaveType.Cart if has_battery else SaveType.Nothing
			
			#Could get the mapper here, I suppose, but then it gets tricky when you involve NES 2.0 (which has the same header format for the first few bytes)
			#TV type apparently isn't used much despite it being part of the iNES specification, and looking at a lot of headered ROMs it does seem that they are all NTSC other than a few that say PAL that shouldn't be, so yeah, I wouldn't rely on it. Might as well just use the filename.
		else:
			game.metadata.specific_info['Headered'] = False

class GameBoyMapper():
	def __init__(self, name, has_ram=False, has_battery=False, has_rtc=False, has_rumble=False, has_accelerometer=False):
		self.name = name
		self.has_ram = has_ram
		self.has_battery = has_battery
		self.has_rtc = has_rtc
		self.has_rumble = has_rumble
		self.has_accelerometer = has_accelerometer

	def __str__(self):
		return self.name

game_boy_mappers = {
	0: GameBoyMapper("ROM only"),
	8: GameBoyMapper("ROM only", has_ram=True),
	9: GameBoyMapper("ROM only", has_ram=True, has_battery=True),
	
	1: GameBoyMapper('MBC1'),
	2: GameBoyMapper('MBC1', has_ram=True),
	3: GameBoyMapper('MBC1', has_ram=True, has_battery=True),
	
	5: GameBoyMapper('MBC2'),
	6: GameBoyMapper('MBC2', has_ram=True, has_battery=True),
	
	11: GameBoyMapper('MMM01'),
	12: GameBoyMapper('MMM01', has_ram=True),
	13: GameBoyMapper('MMM01', has_ram=True, has_battery=True),

	15: GameBoyMapper('MBC3', has_battery=True, has_rtc=True),
	16: GameBoyMapper('MBC3', has_ram=True, has_battery=True, has_rtc=True),
	17: GameBoyMapper('MBC3'),
	18: GameBoyMapper('MBC3', has_ram=True),
	19: GameBoyMapper('MBC3', has_battery=True),

	#MBC4 might not exist. Hmm...

	25: GameBoyMapper('MBC5'),
	26: GameBoyMapper('MBC5', has_ram=True),
	27: GameBoyMapper('MBC5', has_ram=True, has_battery=True),
	28: GameBoyMapper('MBC5', has_rumble=True),
	29: GameBoyMapper('MBC5', has_rumble=True, has_ram=True),
	30: GameBoyMapper('MBC5', has_rumble=True, has_ram=True, has_battery=True),

	32: GameBoyMapper('MBC6', has_ram=True, has_battery=True),
	34: GameBoyMapper('MBC7', has_ram=True, has_battery=True, has_accelerometer=True), #Might have rumble? Don't think it does
	252: GameBoyMapper('Pocket Camera', has_ram=True, has_battery=True),
	253: GameBoyMapper('Bandai TAMA5'),
	254: GameBoyMapper('HuC3'),
	255: GameBoyMapper('HuC1', has_ram=True, has_battery=True),
}
		

nintendo_logo_crc32 = 0x46195417
def add_gameboy_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

	header = game.rom.read(seek_to=0x100, amount=0x50)
	nintendo_logo = header[4:0x34]
	nintendo_logo_valid = binascii.crc32(nintendo_logo) == nintendo_logo_crc32
	game.metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid
	
	game.metadata.specific_info['SGB-Enhanced'] = header[0x46] == 3
	if header[0x47] in game_boy_mappers:
		mapper = game_boy_mappers[header[0x47]]
		game.metadata.specific_info['Mapper'] = mapper
		game.metadata.save_type = SaveType.Cart if mapper.has_battery else SaveType.Nothing
		game.metadata.specific_info['Force-Feedback'] = mapper.has_rumble
		game.metadata.input_method = 'Motion Controls' if mapper.has_accelerometer else 'Normal'
	
	#Can get product code from header[0x3f:0x43] if and only if it exists. It might not, it's only for newer games. Has to exist for GBC only games, but then homebrew doesn't follow your rules of course.
	#Can also get destination code from header[0x4a]. 0 means Japan and 1 means not Japan. Not sure how reliable that is.
	#TODO: Calculate header checksum, add system specific info if invalid
	licensee_code = header[0x4b]
	if licensee_code == 0x33:
		try:
			licensee_code = header[0x44:0x46].decode('ascii')
			if licensee_code in nintendo_licensee_codes:
				game.metadata.author = nintendo_licensee_codes[licensee_code]
		except UnicodeDecodeError:
			pass
	else:
		licensee_code = '{:02X}'.format(licensee_code)
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	
	if game.rom.extension == 'gbc':
		game.metadata.platform = 'Game Boy Color'

nintendo_gba_logo_crc32 = 0xD0BEB55E
def add_gba_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

	entire_cart = game.rom.read()
	header = entire_cart[0:0xc0]

	nintendo_logo = header[4:0xa0]
	nintendo_logo_valid = binascii.crc32(nintendo_logo) == nintendo_gba_logo_crc32
	game.metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid

	try:
		product_code = header[0xac:0xb0].decode('ascii')
		game_type = product_code[0]
		if game_type[0] == 'K' or game_type == 'R':
			game.metadata.input_method = 'Motion Controls'
		else:
			game.metadata.input_method = 'Normal'
		game.metadata.specific_info['Force-Feedback'] = game_type in ('R', 'V')
		
		game.metadata.specific_info['Product-Code'] = product_code
		#TODO: Maybe get region from product_code[3]?
	except UnicodeDecodeError:
		#Well, shit. If the product code's invalid for whatever reason, then we can't derive much info from it anyway. Anything officially licensed should be alphanumeric.
		pass
	
	try:
		licensee_code = header[0xb0:0xb2].decode('ascii')
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except UnicodeDecodeError:
		pass
	
	has_save = False
	save_strings = [b'EEPROM_V', b'SRAM_V', b'SRAM_F_V', b'FLASH_V', b'FLASH512_V', b'FLASH1M_V']
	for string in save_strings:
		if string in entire_cart:
			has_save = True
			break
	#Can also look for SIIRTC_V in entire_cart to detect RTC if desired
	game.metadata.save_type = SaveType.Cart if has_save else SaveType.Nothing

def add_3ds_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.main_cpu = 'ARM11'
	game.metadata.clock_speed = '268 MHz' #New 3DS is 804 MHz

def add_ds_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.main_cpu = 'ARM946ES'
	game.metadata.clock_speed = '67 MHz'

	header = game.rom.read(amount=0x200)
	
	try:
		product_code = header[12:16].decode('ascii')
		game.metadata.specific_info['Product-Code'] = product_code
	except UnicodeDecodeError:
		pass

	try:
		licensee_code = header[16:18].decode('ascii')
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except UnicodeDecodeError:
		pass

	is_dsi = False
	unit_code = header[18]
	if unit_code == 0:
		game.metadata.specific_info['DSi-Enhanced'] = False
	elif unit_code == 2:
		is_dsi = True
		game.metadata.specific_info['DSi-Enhanced'] = True
	elif unit_code == 3:
		is_dsi = True
		game.metadata.platform = "DSi"
		#We won't set this upgraded clock speed for DSi-enhanced DS games for now, since nothing emulates them in that mode
		game.metadata.clock_speed = '133 MHz'

	if is_dsi:
		region_flags = int.from_bytes(header[0x1b0:0x1b4], 'little')
		if region_flags < 0xffff0000:
			#If they're set any higher than this, it's region free
			#GBATEK says region free is 0xffffffff specifically but Pokemon gen 5 is 0xffffffef so who knows
			regions = []
			if region_flags & 1:
				regions.append(get_region_by_name('Japan'))
			elif region_flags & 2:
				regions.append(get_region_by_name('USA'))
			elif region_flags & 4:
				regions.append(get_region_by_name('Europe'))
			elif region_flags & 8:
				regions.append(get_region_by_name('Australia'))
			elif region_flags & 16:
				regions.append(get_region_by_name('China'))
			elif region_flags & 32:
				regions.append(get_region_by_name('Korea'))
			game.metadata.regions = regions
	else:
		region = header[29]
		if region == 0x40:
			game.metadata.regions = [get_region_by_name('Korea')]
		elif region == 0x80:
			game.metadata.regions = [get_region_by_name('China')]
		#If 0, could be anywhere else

def add_ngp_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	
	copyright_string = game.rom.read(amount=28).decode('ascii', errors='ignore')
	if copyright_string == 'COPYRIGHT BY SNK CORPORATION':
		game.metadata.author = 'SNK'
	#Otherwise it'd say " LICENSED BY SNK CORPORATION" and that could be any dang third party which isn't terribly useful
	#There's really not much here, so I didn't even bother reading the whole header
	#At offset 36, you could get the colour flag, and if equal to 0x10 set platform to "Neo Geo Pocket Color" if you really wanted

def add_wonderswan_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

def add_virtual_boy_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	
	rom_size = game.rom.get_size()
	header_start_position = rom_size - 544 #Yeah I dunno
	header = game.rom.read(seek_to=header_start_position, amount=32)
	try:
		licensee_code = header[25:27].decode('ascii')
		if licensee_code in nintendo_licensee_codes:
			game.metadata.author = nintendo_licensee_codes[licensee_code]
	except UnicodeDecodeError:
		pass
	product_code = header[27:32]
	
	try:
		game.metadata.specific_info['Product-Code'] = product_code.decode('ascii')
	except UnicodeDecodeError:
		pass
	#Can get country from product_code[3] if needed

def add_atari_8bit_metadata(game):
	if game.rom.extension in ['bin', 'rom', 'car']:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'CART':
			game.metadata.specific_info['Headered'] = True
			cart_type = int.from_bytes(header[4:8], 'big')
			#TODO: Have nice table of cart types like with Game Boy mappers; also set platform to XEGS/XL/XE/etc accordingly
			game.metadata.specific_info['Cart-Type'] = cart_type
			game.metadata.specific_info['Slot'] = 'Right' if cart_type in [21, 59] else 'Left'
		else:
			game.metadata.specific_info['Headered'] = False

def add_commodore_64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:16]
	if magic == b'C64 CARTRIDGE   ':
		game.metadata.specific_info['Headered'] = True
		cart_type = int.from_bytes(header[22:24], 'big')
		game.metadata.specific_info['Cart-Type'] = cart_type
		if cart_type == 15:
			game.metadata.platform = 'C64GS'
	else:
		game.metadata.specific_info['Headered'] = False		

def add_vectrex_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'

	game.metadata.year = game.rom.read(seek_to=6, amount=4).decode('ascii', errors='ignore')

def add_megadrive_metadata(game):
	header = game.rom.read(0x100, 0x100)
	#TODO: Parse copyright at header[16:32] to get author (from giant lookup table) and year if possible
	peripherals = [c for c in header[144:160].decode('ascii', errors='ignore') if c != '\x00' and c != ' ']
	#TODO Definitely needs a hecking rewrite to have multiple input methods
	if 'M' in peripherals:
		game.metadata.input_method = 'Mouse'
	elif 'V' in peripherals:
		game.metadata.input_method = 'Paddle'
	elif 'A' in peripherals:
		game.metadata.input_method = 'Stick'
	elif 'G' in peripherals:
		game.metadata.input_method = 'Light Gun'
	elif 'K' in peripherals:
		game.metadata.input_method = 'Keyboard'
	else:
		if 'J' in peripherals:
			game.metadata.input_method = 'Normal'
		elif '6' in peripherals:
			game.metadata_input_method = 'Normal'
			game.metadata.specific_info['Uses-6-Button-Controller'] = True
	#Other peripheral characters of interest:
	#0 = SMS gamepad
	#4 = Team Play
	#B = "Control Ball" (trackball?)
	#C = CD-ROM
	#F = Floppy drive
	#L = Activator
	#O = J-Cart
	#P = Printer
	#R = Serial
	#T = Tablet

	save_id = header[0xb0:0xb4]
	#Apparently... what the heck
	game.metadata.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing
	

	#Hmm... get regions from [0xfd:0xff] or nah

def add_pokemini_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'
	
	#There really isn't much else here, other than maybe the title. I don't think I can do anything with all those IRQs.
	product_code_bytes = game.rom.read(seek_to=0x21a4, amount=4)
	try:
		product_code = product_code_bytes.decode('ascii')
		game.metadata.specific_info['Product-Code'] = product_code
	except UnicodeDecodeError:
		pass

def get_stella_database():
	proc = subprocess.run(['stella', '-listrominfo'], stdout=subprocess.PIPE, universal_newlines=True)
	proc.check_returncode()
	
	lines = proc.stdout.splitlines()
	first_line = lines[0]
	lines = lines[1:]

	columns = {}
	column_names = first_line.split('|')
	for i, column_name in enumerate(column_names):
		columns[i] = column_name
	
	games = {}
	for line in lines:
		game_columns = line.split('|')
		game = {}

		md5 = None
		for i, game_column in enumerate(game_columns):
			if i in columns:
				if columns[i] == 'Cartridge_MD5':
					md5 = game_column.lower()
				elif game_column:
					game[columns[i]] = game_column
	
		if md5:
			games[md5] = game

	return games

stella_input_methods = {
	'JOYSTICK': 'Normal',
	'PADDLES': 'Paddle',
	'PADDLES_IAXIS': 'Paddle',
	'PADDLES_IAXDR': 'Paddle',	
	'BOOSTERGRIP': 'Normal',
	'DRIVING': 'Steering Wheel',
	'KEYBOARD': 'Keyboard',
	'AMIGAMOUSE': 'Mouse',
	'ATARIMOUSE': 'Mouse',
	'TRAKBALL': 'Trackball',
	'GENESIS': 'Normal',
	'COMPUMATE': 'Keyboard', #Kinda, it's an entire goddamn computer
}	

stella_display_format_line_regex = re.compile(r'^\s*Display Format:\s*(PAL|NTSC)\*')
def autodetect_from_stella(game):
	proc = subprocess.run(['stella', '-rominfo', game.rom.path], stdout=subprocess.PIPE, universal_newlines=True)
	if proc.returncode != 0:
		return

	lines = proc.stdout.splitlines()
	for line in lines:
		display_format_match = stella_display_format_line_regex.match(line)
		if display_format_match:
			game.tv_type = TVSystem[display_format_match.group(1)]
		#Can also get bankswitch type from here if needed. Controller 0 and Controller 1 too, but then it's probably better to just get that from the database

_stella_db = None
def add_atari_2600_metadata(game):
	global _stella_db 
	#Python, you're officially a fucking dumbarse. Of course that's a fucking global variable. It is right there. Two lines above here. In the global fucking scope.
	if _stella_db is None:
		try:
			_stella_db = get_stella_database()
		except subprocess.CalledProcessError:
			pass
	
	entire_rom = game.rom.read()
	md5 = hashlib.md5(entire_rom).hexdigest().lower()
	if md5 in _stella_db:
		game_info = _stella_db[md5]
	
		#TODO: Get year out of name	
		if 'Cartridge_Manufacturer' in game_info:
			#TODO: Includes the programmer as well, which is nice, but inconsistent with how X-Author is used elsewhere, maybe split by ', '?
			game.metadata.author = game_info['Cartridge_Manufacturer']
		if 'Cartridge_ModelNo' in game_info:
			game.metadata.specific_info['Product-Code'] = game_info['Cartridge_ModelNo']
		if 'Cartridge_Note' in game_info:
			#TODO: Ignore things like "Uses the Paddle Controllers" and "Console ports are swapped" that are already specified by other fields
			#TODO: Do something with "AKA blah blah blah" (X-Alternate-Name?) or ignore that
			game.metadata.specific_info['Notes'] = game_info['Cartridge_Note']
		if 'Controller_Left' in game_info:
			#TODO: Take note of Controller_SwapPorts or Controller_SwapPaddles and also the right controller
			#TODO: Use some attribute to note if PADDLES_IAXIS or PADDLES_IAXDR, whatever those do exactly that's different from just PADDLES
			#There's also things like the Track & Field controller that Stella just calls JOYSTICK so meh
			left_controller = game_info['Controller_Left']
			if left_controller in stella_input_methods:
				game.metadata.input_method = stella_input_methods[left_controller]
			else:
				#Includes MindLink because I dunno what to call that
				game.metadata.input_method = 'Custom'

			if left_controller == 'GENESIS':
				game.metadata.specific_info['Uses-Genesis-Controller'] = True
			elif left_controller == 'BOOSTERGRIP':
				game.metadata.specific_info['Uses-Boostergrip'] = True
			#TODO: Should differentiate between AMIGAMOUSE and ATARIMOUSE? Maybe that's needed for something	
	
		if 'Controller_Right' in game_info:
			right_controller = game_info['Controller_Right']
			#Really should be detecting this the same way as the left controller, but for now that's confusing and I'll figure it out later, so this just detects the presence of various peripherals.
			if right_controller in ('ATARIVOX', 'SAVEKEY'):
				game.metadata.save_type = SaveType.MemoryCard
			else:
				game.metadata.save_type = SaveType.Nothing

			if right_controller == 'KIDVID':
				game.metadata.specific_info['Uses-Kid-Vid'] = True
		
		if 'Display_Format' in game_info:
			display_format = game_info['Display_Format']
			if display_format == 'NTSC':
				game.metadata.tv_type = TVSystem.NTSC
			elif display_format == 'PAL':
				game.metadata_tv_type = TVSystem.PAL
			elif display_format == 'AUTO':
				#Yeah, I guess we're just reading the whole ROM again after already reading it once to get the MD5. Oh well. They aren't too big.
				#TODO: Actually... what if we run -rominfo first, get MD5 from there, and then if it's in stella_db add more values?
				autodetect_from_stella(game)
			#TODO: Can also be SECAM, NTSC50, PAL60, or SECAM60
	else:
		autodetect_from_stella(game)
	
def add_n64_metadata(game):
	header = game.rom.read(amount=64)
	magic = header[:4]
	if magic == b'\x80\x37\x12\x40':
		#Z64
		#TODO: Detect format and add as metadata. This'll be useful because some emulators won't even try and launch the thing if the first four bytes don't match something expected, even if it is a raw non-swapped dump that just happens to have weird values there
		try:
			product_code = header[59:63].decode('ascii')
			game.metadata.specific_info['Product-Code'] = product_code
		except UnicodeDecodeError:
			pass
		

def nothing_interesting(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'


helpers = {
	'32X': add_megadrive_metadata,
	'3DS': add_3ds_metadata,
	'Atari 2600': add_atari_2600_metadata,
	'Atari 7800': add_atari7800_metadata,
	'Atari 8-bit': add_atari_8bit_metadata,
	'C64': add_commodore_64_metadata,
	'DS': add_ds_metadata,
	'Epoch Game Pocket Computer': nothing_interesting,
	'Gamate': nothing_interesting,
	'Game Boy': add_gameboy_metadata,
	'GameCube': add_gamecube_metadata,
	'GBA': add_gba_metadata,
	'Mega Drive': add_megadrive_metadata,
	'Mega Duck': nothing_interesting,
	'N64': add_n64_metadata,
	'Neo Geo Pocket': add_ngp_metadata,
	'NES': add_nes_metadata,
	'Pokemon Mini': add_pokemini_metadata,
	'PSP': add_psp_metadata,
	'Vectrex': add_vectrex_metadata,
	'Virtual Boy': add_virtual_boy_metadata,
	'Watara Supervision': nothing_interesting,
	'Wii': add_wii_metadata,
	'WonderSwan': add_wonderswan_metadata,
}
