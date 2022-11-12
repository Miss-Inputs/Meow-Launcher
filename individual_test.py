#!/usr/bin/env python3

__doc__ = """
TODO: Eventually this wouldn't be needed - you would just have a --game-sources argument in meowlauncher/__main__.py and you can have one or many
Until then this will duplicate code from there so I am sorry
TODO: Just need to deal with itch.io/GOG/MAME software…"""

import locale
import logging
import sys

from meowlauncher.config.main_config import main_config
from meowlauncher.frontend import organize_folders, series_detect
from meowlauncher.frontend.add_games import add_game_source
from meowlauncher.frontend.disambiguate import disambiguate_names
from meowlauncher.frontend.remove_nonexistent_games import \
    remove_nonexistent_games
from meowlauncher.game_sources import game_sources, gog, itch_io, mame_software
from meowlauncher.util.utils import NotLaunchableExceptionFormatter

locale.setlocale(locale.LC_ALL, '')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(NotLaunchableExceptionFormatter(fmt='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s'))
stream_handler.setLevel(main_config.logging_level)
logging.basicConfig(handlers={stream_handler})
logger = logging.getLogger(__name__)

def main() -> None:
	if main_config.full_rescan:
		if main_config.output_folder.is_dir():
			for f in main_config.output_folder.iterdir():
				f.unlink()

	if sys.argv[1] == 'gog':
		gog.do_gog_games()
	elif sys.argv[1] == 'itchio':
		itch_io.do_itch_io_games()
	elif sys.argv[1] == 'mame_software':
		mame_software.add_mame_software()
	
	elif sys.argv[1] == 'series_detect':
		series_detect.detect_series_for_all_desktops()
	elif sys.argv[1] == 'remove_nonexistent_games':
		remove_nonexistent_games()
	elif sys.argv[1] == 'disambiguate':
		disambiguate_names()
	elif sys.argv[1] == 'organize_folders':
		#This one's a bit jank and I should clean it up I guess
		organize_folders.main()
	else:
		source = None
		for game_source in game_sources:
			if sys.argv[1] in {game_source.name, game_source.name.lower()}:
				source = game_source
				break

		if not source:
			logger.error('Unknown game source: %s', sys.argv[1])
			return
		if not source.is_available:
			logger.error('%s is not available', source)
			return
			
		add_game_source(source, print)

if __name__ == '__main__':
	main()
