#!/usr/bin/env python3

import datetime
import sys
import time

import meowlauncher.main
from meowlauncher.config.main_config import main_config
from meowlauncher.games.mame.mame_helpers import have_mame

overall_time_started = time.perf_counter()

def print_callback(data, _):
	if data:
		print(data)

if __name__ == '__main__':
	mame_enabled = '--no-arcade' not in sys.argv and have_mame()
	meowlauncher.main.main(print_callback, mame_enabled=mame_enabled)

	if main_config.print_times:
		overall_time_ended = time.perf_counter()
		print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
