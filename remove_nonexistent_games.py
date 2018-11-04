#!/usr/bin/env python

import os
import datetime
import time

from config import main_config, command_line_flags
from launchers import convert_desktop, get_field

import mame_machines
import scummvm

def remove_nonexistent_games():
	#If not doing a full rescan, we want to remove games that are no longer there

	time_started = time.perf_counter()

	output_folder = main_config.output_folder
	for name in os.listdir(output_folder):
		path = os.path.join(output_folder, name)

		launcher = convert_desktop(path)
		game_type = get_field(launcher, 'X-Type')
		game_id = get_field(launcher, 'X-Unique-ID')

		should_remove = False
		if game_type == 'MAME machine':
			should_remove = mame_machines.no_longer_exists(game_id)
		elif game_type in ('ROM', 'Engine game'):
			#Note that in the case of engine games this may be a folder, so isfile will not do
			should_remove = not os.path.exists(game_id)
		elif game_type == 'ScummVM':
			should_remove = scummvm.no_longer_exists(game_id)
		#TODO: Implement this for the rest of the game types: DOS, Mac = dos_mac_common (may be tricky)

		if should_remove:
			if command_line_flags['debug']:
				print(game_type, game_id, 'no longer exists, removing')
			os.remove(path)

	if command_line_flags['print_times']:
		time_ended = time.perf_counter()
		print('Removal of non-existent items finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	remove_nonexistent_games()
