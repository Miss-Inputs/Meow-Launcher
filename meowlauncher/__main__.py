#!/usr/bin/env python3

import datetime
import time

from meowlauncher.frontend.main import main

from .config.main_config import main_config

overall_time_started = time.perf_counter()

main(print)

if main_config.print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
