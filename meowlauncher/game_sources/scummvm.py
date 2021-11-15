#!/usr/bin/env python3

import datetime
import time

from meowlauncher import global_runners
from meowlauncher.config.main_config import main_config
from meowlauncher.desktop_launchers import (has_been_done,
                                            make_linux_desktop_for_launcher)
from meowlauncher.games.scummvm.scummvm_config import scummvm_config
from meowlauncher.games.scummvm.scummvm_game import (ScummVMGame,
                                                     ScummVMLauncher)


def no_longer_exists(game_id: str):
	return game_id not in scummvm_config.scummvm_ini.sections() if scummvm_config.have_scummvm else True

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
			launcher = ScummVMLauncher(game, global_runners.scummvm)
			make_linux_desktop_for_launcher(launcher)

		if main_config.print_times:
			time_ended = time.perf_counter()
			print('ScummVM finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
