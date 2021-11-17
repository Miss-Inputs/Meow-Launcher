#!/usr/bin/env python

import datetime
import os
from pathlib import Path
import time

from meowlauncher.config.main_config import main_config
from meowlauncher.desktop_launchers import (get_desktop, get_field,
                                            id_section_name)
from meowlauncher.game_sources import game_types, steam


def remove_nonexistent_games() -> None:
	#If not doing a full rescan, we want to remove games that are no longer there

	time_started = time.perf_counter()

	output_folder: Path = main_config.output_folder
	for path in output_folder.iterdir():
		launcher = get_desktop(path)
		game_type = get_field(launcher, 'Type', id_section_name)
		game_id = get_field(launcher, 'Unique-ID', id_section_name)
		if not game_type or not game_id:
			if main_config.debug:
				print('Interesting', path, 'has no type or no ID')
			continue

		should_remove = False
		game_source = game_types.get(game_type)
		if game_source:
			should_remove = game_source.no_longer_exists(game_id)
		elif game_type == 'Steam':
			should_remove = steam.no_longer_exists(game_id)
		elif game_type == 'GOG':
			should_remove = not os.path.exists(game_id)
		elif game_type == 'itch.io':
			should_remove = not os.path.exists(game_id)
		#Hmm, not sure what I should do if game_type is unrecognized. I guess ignore it, it might be from somewhere else and therefore not my business

		if should_remove:
			if main_config.debug:
				print(game_type, game_id, 'no longer exists, removing')
			os.remove(path)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Removal of non-existent items finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
