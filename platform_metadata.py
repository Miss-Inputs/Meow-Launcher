import sys
import os
import xml.etree.ElementTree as ElementTree

from region_info import TVSystem
from metadata import SystemSpecificInfo

debug = '--debug' in sys.argv

#For roms.py, gets metadata in ways specific to certain platforms

#Metadata used in arcade: main_input, emulation_status, genre, subgenre, nsfw, language, year, author
#If we can get these from somewhere for non-arcade things: Great!!
#main_cpu, source_file and family aren't really relevant
#Gamecube, 3DS, Wii can sorta find the languages (or at least the title/banner stuff) by examining the ROM itself...
#though as you have .gcz files for the former, that gets a bit involved, actually yeah any of what I'm thinking would
#be difficult without a solid generic file handling thing, but still
#Can get these from the ROM/disc/etc itself:
#	main_input: Megadrive family, Atari 7800 (all through lookup table)
#		Somewhat Game Boy, GBA (if type from product code = K or R, uses motion controls)
#	year: Megadrive family (usually; via copyright), FDS, GameCube, Satellaview, homebrew SMS/Game Gear, Atari 5200
#	(sometimes), Vectrex, ColecoVersion (sometimes), homebrew Wii
#	author: Homebrew SMS/Game Gear, ColecoVision (in uppercase, sometimes), homebrew Wii
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
		game.metadata.system_specific_info.append(SystemSpecificInfo('Headerless', True, False))
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
		game.metadata.system_specific_info.append(SystemSpecificInfo('Invalid-TV-Type', True, False))

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

def add_nes_metadata(game):
	if game.rom.extension == 'fds':
		game.metadata.platform = 'FDS'

def add_gameboy_metadata(game):
	if game.rom.extension == 'gbc':
		game.metadata.platform = 'Game Boy Color'

def add_3ds_metadata(game):
	game.metadata.main_cpu = 'ARM11'

def add_ds_metadata(game):
	game.metadata.main_cpu = 'ARM946E-S'

def nothing_interesting(game):
	game.metadata.input_method = 'Normal'


helpers = {
	'Atari 7800': add_atari7800_metadata,
	'PSP': add_psp_metadata,
	'Wii': add_wii_metadata,
	'NES': add_nes_metadata,
	'Game Boy': add_gameboy_metadata,
	'Gamate': nothing_interesting,
	'Watara Supervision': nothing_interesting,
	'Epoch Game Pocket Computer': nothing_interesting,
	'Mega Duck': nothing_interesting,
	'DS': add_ds_metadata,
	'3DS': add_3ds_metadata,
}
