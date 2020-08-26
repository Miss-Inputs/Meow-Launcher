#!/usr/bin/env python

import os
import datetime
import time

import config.main_config
from launchers import get_desktop, get_field, id_section_name

import mame_machines
import scummvm
import mac
import steam

conf = config.main_config.main_config 

def remove_nonexistent_games():
	#If not doing a full rescan, we want to remove games that are no longer there

	time_started = time.perf_counter()

	output_folder = conf.output_folder
	for name in os.listdir(output_folder):
		path = os.path.join(output_folder, name)

		launcher = get_desktop(path)
		game_type = get_field(launcher, 'Type', id_section_name)
		game_id = get_field(launcher, 'Unique-ID', id_section_name)

		should_remove = False
		if game_type == 'MAME machine':
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
		#Hmm, not sure what I should do if game_type is unrecognized. I guess ignore it, it might be from somewhere else and therefore not my business

		if should_remove:
			if conf.debug:
				print(game_type, game_id, 'no longer exists, removing')
			os.remove(path)

	if conf.print_times:
		time_ended = time.perf_counter()
		print('Removal of non-existent items finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	remove_nonexistent_games()
