import sys

from region_info import TVSystem

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
	rom_data = game.rom.read()
	if rom_data[1:10] != b'ATARI7800':
		if debug:
			print(game.rom.path, 'has no header and is therefore unsupported')
			game.unrunnable = True
			return

	tv_type = rom_data[57]

	if tv_type == 1:
		game.tv_type = TVSystem.PAL
	elif tv_type == 0:
		game.tv_type = TVSystem.NTSC
	else:
		if debug:
			print('Something is wrong with', game.rom.path, ', has region byte of', region_byte)
		game.unrunnable = True

helpers = {
	'Atari 7800': add_atari7800_metadata,
}