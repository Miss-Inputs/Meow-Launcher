#!/usr/bin/env python3

import datetime
import locale
import logging
import time
from argparse import ArgumentParser

from meowlauncher.frontend.main import main
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

from meowlauncher.config.main_config import main_config
from meowlauncher import __version__

overall_time_started = time.perf_counter()
locale.setlocale(locale.LC_ALL, '')

parser = ArgumentParser(add_help=True, parents=[main_config.parser], prog=f'python -m {__package__}')
parser.add_argument('--version', action='version', version=__version__)
main_config.values.update(vars(parser.parse_known_intermixed_args()[0]))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(NotLaunchableExceptionFormatter(fmt='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s'))

logger = logging.getLogger(__package__)
logger.addHandler(stream_handler)
logger.setLevel(main_config.logging_level)
main()

if main_config.print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
