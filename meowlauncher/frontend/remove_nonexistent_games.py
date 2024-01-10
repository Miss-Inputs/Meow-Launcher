#!/usr/bin/env python

import logging
from pathlib import Path

from meowlauncher.config import main_config
from meowlauncher.game_sources.all_sources import game_sources
from meowlauncher.output.desktop_files import id_section_name
from meowlauncher.util.desktop_files import get_desktop, get_field

logger = logging.getLogger(__name__)


def remove_nonexistent_games() -> None:
	"If not doing a full rescan, we want to remove games that are no longer there"

	game_types = {source.game_type(): source() for source in game_sources}

	for path in main_config.output_folder.iterdir():
		launcher = get_desktop(path)
		game_type = get_field(launcher, 'Type', id_section_name)
		game_id = get_field(launcher, 'Unique-ID', id_section_name)
		if not game_type or not game_id:
			logger.debug('Interesting, %s has no type or no ID', path)
			continue

		should_remove = False
		if game_type in {'GOG', 'itch.io'}:
			should_remove = not Path(game_id).exists()
		else:
			game_source = game_types.get(game_type)
			if game_source:
				should_remove = game_source.no_longer_exists(game_id)
		# Hmm, not sure what I should do if game_type is unrecognized. I guess ignore it, it might be from somewhere else and therefore not my business

		if should_remove:
			logger.debug('%s %s no longer exists, removing', game_type, game_id)
			path.unlink()


__doc__ = remove_nonexistent_games.__doc__ or 'Shut up mypy'
