#!/usr/bin/env python3

import datetime
import time
import sys

from mame_helpers import have_mame
from config import main_config
import main

if '--refresh-config' in sys.argv:
	#TODO: Do this on first run... or is that a bad idea
	exit()

overall_time_started = time.perf_counter()

mame_enabled = '--no-arcade' not in sys.argv and have_mame()
main.main(mame_enabled, True, True, True, True, True)

if main_config.print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
