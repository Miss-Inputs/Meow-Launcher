import sys

from metadata import SaveType
from info.region_info import TVSystem

debug = '--debug' in sys.argv

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
