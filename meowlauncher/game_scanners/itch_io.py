#!/usr/bin/env python3

import datetime
import os
import time

from meowlauncher import launchers
from meowlauncher.config.main_config import main_config
from meowlauncher.games.itch import ItchGame

def scan_itch_dir(path):
	if not os.path.isdir(os.path.join(path, '.itch')):
		return None

	game = ItchGame(path)
	return game

def do_itch_io_games():
	time_started = time.perf_counter()

	for itch_io_folder in main_config.itch_io_folders:
		if not os.path.isdir(itch_io_folder):
			if main_config.debug:
				print(itch_io_folder, 'does not exist/is not a directory')
			continue
	
		for subfolder in os.scandir(itch_io_folder):
			if not main_config.full_rescan:
				if launchers.has_been_done('itch.io', subfolder.path):
					continue
			if not subfolder.is_dir():
				continue
			if subfolder.name == 'downloads':
				continue
			game = scan_itch_dir(subfolder.path)
			if not game:
				if main_config.debug:
					print('itch.io subfolder does not have an itch.io game (detection may have failed)', subfolder.path)
					continue

			#TODO: Somehow, we need to add all the documentation etc to other folders with matching game IDs (they won't be launchable themselves)

			game.add_metadata()
			game.make_launcher()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('itch.io finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

if __name__ == '__main__':
	do_itch_io_games()
