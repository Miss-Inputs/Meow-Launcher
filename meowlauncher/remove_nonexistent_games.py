#!/usr/bin/env python

import datetime
import os
import time

from meowlauncher.game_scanners import mac, mame_machines, scummvm, steam
from meowlauncher.config.main_config import main_config
from meowlauncher.launchers import get_desktop, get_field, id_section_name

def remove_nonexistent_games():
	#If not doing a full rescan, we want to remove games that are no longer there

	time_started = time.perf_counter()

	output_folder = main_config.output_folder
	for name in os.listdir(output_folder):
		path = os.path.join(output_folder, name)

		launcher = get_desktop(path)
		game_type = get_field(launcher, 'Type', id_section_name)
		game_id = get_field(launcher, 'Unique-ID', id_section_name)

		should_remove = False
		if game_type in ('MAME', 'Arcade', 'Inbuilt game'):
			should_remove = mame_machines.no_longer_exists(game_id)
		elif game_type in 'ROM':
			should_remove = not os.path.exists(game_id)
		elif game_type == 'DOS':
			should_remove = not os.path.exists(game_id)
		elif game_type == 'Mac':
			should_remove = mac.no_longer_exists(game_id)
		elif game_type == 'ScummVM':
			should_remove = scummvm.no_longer_exists(game_id)
		elif game_type == 'Steam':
			should_remove = steam.no_longer_exists(game_id)
		elif game_type == 'GOG':
			should_remove = not os.path.exists(game_id)
		elif game_type == 'itch.io':
			should_remove = not os.path.exists(game_id)
		#Hmm, not sure what I should do if game_type is unrecognized. I guess ignore it, it might be from somewhere else and therefore not my business

		if should_remove:
			if main_config.debug:
				print(game_type, game_id, 'no longer exists, removing')
			os.remove(path)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Removal of non-existent items finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	remove_nonexistent_games()
