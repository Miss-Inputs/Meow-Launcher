#!/usr/bin/env python

import datetime
import logging
import os
import time

from meowlauncher.config.main_config import main_config
from meowlauncher.game_sources import game_types
from meowlauncher.output.desktop_files import id_section_name
from meowlauncher.util.desktop_files import get_desktop, get_field

logger = logging.getLogger(__name__)

def remove_nonexistent_games() -> None:
	'If not doing a full rescan, we want to remove games that are no longer there'

	time_started = time.perf_counter()

	for path in main_config.output_folder.iterdir():
		launcher = get_desktop(path)
		game_type = get_field(launcher, 'Type', id_section_name)
		game_id = get_field(launcher, 'Unique-ID', id_section_name)
		if not game_type or not game_id:
			logger.debug('Interesting, %s has no type or no ID', path)
			continue

		should_remove = False
		game_source = game_types.get(game_type)
		if game_source:
			should_remove = game_source().no_longer_exists(game_id)
		elif game_type == 'GOG':
			should_remove = not os.path.exists(game_id)
		elif game_type == 'itch.io':
			should_remove = not os.path.exists(game_id)
		#Hmm, not sure what I should do if game_type is unrecognized. I guess ignore it, it might be from somewhere else and therefore not my business

		if should_remove:
			logger.debug('%s %s no longer exists, removing', game_type, game_id)
			os.remove(path)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Removal of non-existent items finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

__doc__ = remove_nonexistent_games.__doc__ or "Shut up mypy"
