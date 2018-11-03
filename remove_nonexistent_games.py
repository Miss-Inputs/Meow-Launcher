#!/usr/bin/env python

import os

from config import main_config
from launchers import convert_desktop, get_field

import mame_machines

def remove_nonexistent_games():
	#If not doing a full rescan, we want to remove games that are no longer there
	output_folder = main_config.output_folder
	for name in os.listdir(output_folder):
		path = os.path.join(output_folder, name)

		launcher = convert_desktop(path)
		game_type = get_field(launcher, 'X-Type')
		game_id = get_field(launcher, 'X-Unique-ID')

		should_remove = False
		if game_type == 'MAME machine':
			should_remove = mame_machines.no_longer_exists(game_id)
		#TODO: Implement this for the rest of the game types: DOS, Mac = dos_mac_common (may be tricky), 'ROM': roms, 'Engine game': roms, 'ScummVM': scummvm.py

		if should_remove:
			os.remove(path)

if __name__ == '__main__':
	remove_nonexistent_games()
