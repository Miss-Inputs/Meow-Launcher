#!/usr/bin/env python3

import datetime
import time

from meowlauncher.desktop_launchers import has_been_done
from meowlauncher.config.main_config import main_config
from meowlauncher.games.scummvm.scummvm_config import scummvm_config
from meowlauncher.games.scummvm.scummvm_game import ScummVMGame


def no_longer_exists(game_id: str):
	if scummvm_config.have_scummvm:
		exists_in_scummvm = game_id in scummvm_config.scummvm_ini.sections()
	else:
		exists_in_scummvm = False

	return not exists_in_scummvm

def add_scummvm_games() -> None:
	if scummvm_config.have_scummvm:
		time_started = time.perf_counter()

		for section in scummvm_config.scummvm_ini.sections():
			if section == 'scummvm':
				#Skip the top section
				continue
			if section == 'cloud':
				#This is not a game either
				continue
			if not main_config.full_rescan:
				if has_been_done('ScummVM', section):
					continue

			game = ScummVMGame(section)
			game.make_launcher()

		if main_config.print_times:
			time_ended = time.perf_counter()
			print('ScummVM finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
