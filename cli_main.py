#!/usr/bin/env python3

import datetime
import sys
import time

import meowlauncher.frontend.main
from meowlauncher.config.main_config import main_config

overall_time_started = time.perf_counter()

def print_callback(data, _):
	if data:
		print(data)

if __name__ == '__main__':
	meowlauncher.frontend.main.main(print_callback)

	if main_config.print_times:
		overall_time_ended = time.perf_counter()
		print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
