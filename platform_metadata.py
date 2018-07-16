import sys
import os
import xml.etree.ElementTree as ElementTree
import binascii

from region_info import TVSystem
from metadata import SaveType

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

def add_atari7800_metadata(game):
	header = game.rom.read(amount=128)
	if header[1:10] != b'ATARI7800':
		game.metadata.specific_info['Headerless'] = True
		return

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

	#Only other thing worth noting is save type at header[58]: 0 = none, 1 = High Score Cartridge, 2 = SaveKey

def add_psp_metadata(game):
	game.metadata.main_cpu = 'Allegrex'

	if game.rom.extension == 'pbp':
		#These are basically always named EBOOT.PBP (due to how PSPs work I guess), so that's not a very good launcher name, and use the folder it's stored in instead
		game.rom.name = os.path.basename(game.folder)

def add_wii_metadata(game):
	game.metadata.main_cpu = 'IBM PowerPC 603'

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
		#TODO: Get author from licensee code at header[15]
		
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
	
	#TODO: Get author from licensee code
	game.metadata.specific_info['SGB-Enhanced'] = header[0x46] == 3
	if header[0x47] in game_boy_mappers:
		mapper = game_boy_mappers[header[0x47]]
		game.metadata.specific_info['Mapper'] = mapper
		game.metadata.save_type = SaveType.Cart if mapper.has_battery else SaveType.Nothing
		game.metadata.specific_info['Force-Feedback'] = mapper.has_rumble
		game.metadata.input_method = 'Motion Controls' if mapper.has_accelerometer else 'Normal'

	#TODO: Calculate header checksum, add system specific info if invalid

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
		#TODO: Maybe get region from product_code[3]?
	except UnicodeDecodeError:
		#Well, shit. If the product code's invalid for whatever reason, then we can't derive much info from it anyway. Anything officially licensed should be alphanumeric.
		pass
	#TODO: Get author from licensee code
	
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

def add_ds_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.main_cpu = 'ARM946E-S'

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
	game.metadata.tv_type = TVSystem.Agnostic4

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

def nothing_interesting(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'


helpers = {
	'3DS': add_3ds_metadata,
	'Atari 7800': add_atari7800_metadata,
	'Atari 8-bit': add_atari_8bit_metadata,
	'C64': add_commodore_64_metadata,
	'DS': add_ds_metadata,
	'Epoch Game Pocket Computer': nothing_interesting,
	'Gamate': nothing_interesting,
	'Game Boy': add_gameboy_metadata,
	'GBA': add_gba_metadata,
	'Mega Duck': nothing_interesting,
	'Neo Geo Pocket': add_ngp_metadata,
	'NES': add_nes_metadata,
	'Pokemon Mini': nothing_interesting,
	'PSP': add_psp_metadata,
	'Vectrex': nothing_interesting,
	'Virtual Boy': add_virtual_boy_metadata,
	'Watara Supervision': nothing_interesting,
	'Wii': add_wii_metadata,
	'WonderSwan': add_wonderswan_metadata,
}
