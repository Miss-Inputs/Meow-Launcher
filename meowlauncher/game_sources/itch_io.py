#!/usr/bin/env python3

import logging
from pathlib import Path

from meowlauncher.config.main_config import main_config
from meowlauncher.games.itch import ItchGame
from meowlauncher.util.desktop_files import has_been_done

logger = logging.getLogger(__name__)

def scan_itch_dir(path: Path) -> ItchGame | None:
	if not path.joinpath('.itch').is_dir():
		return None

	game = ItchGame(path)
	return game

def do_itch_io_games() -> None:
	for itch_io_folder_str in main_config.itch_io_folders:
		itch_io_folder = Path(itch_io_folder_str)
		if not itch_io_folder.is_dir():
			logger.warning('%s does not exist/is not a directory', itch_io_folder)
			continue
	
		for subfolder in itch_io_folder.iterdir():
			if not main_config.full_rescan:
				if has_been_done('itch.io', str(subfolder)):
					continue
			if not subfolder.is_dir():
				continue
			if subfolder.name == 'downloads':
				continue
			if not (game := scan_itch_dir(subfolder)):
				logger.info('itch.io subfolder does not have an itch.io game (detection may have failed): %s', subfolder)
				continue

			#TODO: Somehow, we need to add all the documentation etc to other folders with matching game IDs (they won't be launchable themselves)
			#Well I guess technically they would be, by launching the file with xdg-open, but we don't want to do it that way and also haven't set that up

			game.add_info()
			game.make_launcher()
