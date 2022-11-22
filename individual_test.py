#!/usr/bin/env python3

__doc__ = """
TODO: Eventually this wouldn't be needed - you would just have a --game-sources argument in meowlauncher/__main__.py and you can have one or many
Until then this will duplicate code from there so I am sorry
TODO: Just need to deal with itch.io/GOG/MAME software…"""

import locale
import logging
import sys
from argparse import ArgumentParser

from meowlauncher.config.main_config import main_config
from meowlauncher.frontend import organize_folders, series_detect
from meowlauncher.frontend.add_games import add_game_source
from meowlauncher.frontend.disambiguate import disambiguate_names
from meowlauncher.frontend.remove_nonexistent_games import \
    remove_nonexistent_games
from meowlauncher.game_sources import game_sources, gog, itch_io, mame_software
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

first_arg = sys.argv.pop(1)
locale.setlocale(locale.LC_ALL, '')

parser = ArgumentParser(add_help=True, parents=[main_config.parser])
main_config.values.update(vars(parser.parse_known_intermixed_args()[0]))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(NotLaunchableExceptionFormatter(fmt='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s'))
logging.basicConfig(handlers={stream_handler}, level=main_config.logging_level)
logger = logging.getLogger(__name__)

def main() -> None:
	if main_config.full_rescan:
		if main_config.output_folder.is_dir():
			for f in main_config.output_folder.iterdir():
				f.unlink()

	if first_arg == 'gog':
		gog.do_gog_games()
	elif first_arg == 'itchio':
		itch_io.do_itch_io_games()
	elif first_arg == 'mame_software':
		mame_software.add_mame_software()
	
	elif first_arg == 'series_detect':
		series_detect.detect_series_for_all_desktops()
	elif first_arg == 'remove_nonexistent_games':
		remove_nonexistent_games()
	elif first_arg == 'disambiguate':
		disambiguate_names()
	elif first_arg == 'organize_folders':
		#This one's a bit jank and I should clean it up I guess
		organize_folders.main()
	else:
		game_source_type = next((source for source in game_sources if first_arg in {source.name(), source.name().lower()}), None)
		if not game_source_type:
			logger.error('Unknown game source: %s', first_arg)
			return
		
		game_source = game_source_type()
		if not game_source.is_available:
			logger.error('%s is not available', game_source)
			return
			
		add_game_source(game_source, print)

if __name__ == '__main__':
	main()
