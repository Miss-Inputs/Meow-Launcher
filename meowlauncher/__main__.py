#!/usr/bin/env python3

import locale
import logging
from argparse import ArgumentParser

from meowlauncher.frontend.main import main
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

from meowlauncher.config.config import Config, ConfigProperty, MainConfig, main_config
from meowlauncher import __version__
from meowlauncher.game_sources import game_sources

locale.setlocale(locale.LC_ALL, '')

game_source_config_classes = {game_source.config_class() for game_source in game_sources if game_source.config_class()}
#Hmm mypy still says game_source could be None if I use game_source.config_class()() so I dunno, maybe I'm doing this wrong/am tired and missing something
game_source_configs = {config_class() for config_class in game_source_config_classes if config_class}
config_classes: set[type[Config]] = {MainConfig}.union(config_class for config_class in game_source_config_classes if config_class)

option_to_config: dict[str, type[Config]] = {}
for config_class in config_classes:
	options = {k: v for k, v in vars(config_class).items() if isinstance(v, ConfigProperty)}
	for k, v in options.items():
		option_to_config[k] = config_class
parser = ArgumentParser(add_help=True, parents=[config().parser for config in config_classes], prog=f'python -m {__package__}')
parser.add_argument('--version', action='version', version=__version__)
for k, v in vars(parser.parse_intermixed_args()).items():
	option_to_config[k]().values[k] = v

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
