#!/usr/bin/env python3

import locale
import logging

import meowlauncher
from meowlauncher.frontend.main import main
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

locale.setlocale(locale.LC_ALL, '') #TODO: What do we need this for?

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(
	NotLaunchableExceptionFormatter(
		fmt='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s'
	)
)

logger = logging.getLogger(__package__)
logger.addHandler(stream_handler)
logger.setLevel(meowlauncher.config.main_config.logging_level)

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
