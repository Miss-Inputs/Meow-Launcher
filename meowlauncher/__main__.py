#!/usr/bin/env python3

import datetime
import logging
import time

from meowlauncher.frontend.main import main
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

from .config.main_config import main_config

overall_time_started = time.perf_counter()

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(NotLaunchableExceptionFormatter(fmt='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s'))
stream_handler.setLevel(main_config.logging_level)
logging.basicConfig(handlers={stream_handler})
main(print)

if main_config.print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
