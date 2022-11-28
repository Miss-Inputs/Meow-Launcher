#!/usr/bin/env python3

import locale
import logging
from argparse import ArgumentParser

from meowlauncher.frontend.main import main
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

from meowlauncher.config.main_config import main_config
from meowlauncher import __version__

locale.setlocale(locale.LC_ALL, '')

parser = ArgumentParser(add_help=True, parents=[main_config.parser], prog=f'python -m {__package__}')
parser.add_argument('--version', action='version', version=__version__)
main_config.values.update(vars(parser.parse_known_intermixed_args()[0]))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(NotLaunchableExceptionFormatter(fmt='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s'))

logger = logging.getLogger(__package__)
logger.addHandler(stream_handler)
logger.setLevel(main_config.logging_level)

progress_logger = logging.getLogger('meowlauncher.frontend.progress')
progress_logger.propagate = False
progress_logger.handlers.clear()
progress_logger.addHandler(logging.StreamHandler())
progress_logger.setLevel(logging.INFO)
time_logger = logging.getLogger('meowlauncher.frontend.time')
time_logger.propagate = False
time_logger.handlers.clear()
time_logger.addHandler(logging.StreamHandler())
time_logger.setLevel(logging.INFO)

main()
