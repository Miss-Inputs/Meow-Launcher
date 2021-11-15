#!/usr/bin/env python3

#TODO: Eventually this wouldn't be needed - you would just have a --game-sources argument in cli_main.py and you can have one or many
#Until then this will duplicate code from there so I am sorry

import datetime
import sys
import time

from meowlauncher.desktop_launchers import make_linux_desktop_for_launcher
from meowlauncher.frontend import organize_folders, series_detect
from meowlauncher.frontend.disambiguate import disambiguate_names
from meowlauncher.frontend.remove_nonexistent_games import \
    remove_nonexistent_games
from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.game_sources import (game_sources, gog, itch_io,
                                       mame_software, steam)


def add_games(source: GameSource) -> int:
	time_started = time.perf_counter()
	count = 0
	
	print('Adding ' + source.description)
	if isinstance(source, CompoundGameSource):
		for subsource in source.sources:
			count += add_games(subsource)
	else:
		for launcher in source.get_launchers():
			count += 1
			make_linux_desktop_for_launcher(launcher)
	time_ended = time.perf_counter()
	print(f'Added {count} {source.description} in {str(datetime.timedelta(seconds=time_ended - time_started))}')
	return count

def main() -> None:
	#if sys.argv[1] == 'mame':
	#	process_mame_args()
	if sys.argv[1] == 'gog':
		gog.do_gog_games()
	elif sys.argv[1] == 'itchio':
		itch_io.do_itch_io_games()
	elif sys.argv[1] == 'mame_software':
		mame_software.add_mame_software()
	elif sys.argv[1] == 'steam':
		steam.process_steam()
	
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
			print('Unknown game source', sys.argv[1])
			return
		if not source.is_available:
			return
			
		add_games(source)

if __name__ == '__main__':
	main()
