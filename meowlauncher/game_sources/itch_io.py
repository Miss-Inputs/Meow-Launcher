#!/usr/bin/env python3

import logging
from collections.abc import Sequence
from pathlib import Path

from meowlauncher.config.config import Config, configoption, main_config
from meowlauncher.games.itch import ItchGame
from meowlauncher.util.desktop_files import has_been_done

logger = logging.getLogger(__name__)

class ItchioConfig(Config):
	@classmethod
	def section(cls) -> str:
		return 'itch.io'

	@classmethod
	def prefix(cls) -> str | None:
		return 'itch-io'
		
	@configoption(readable_name='itch.io folders') #itch.io
	def itch_io_folders(self) -> Sequence[Path]:
		"""Folders where itch.io games are installed"""
		return ()

	@configoption(readable_name='Use itch.io as platform') #itch.io
	def use_itch_io_as_platform(self) -> bool:
		"""Set platform in game info to itch.io instead of underlying platform"""
		return False


def scan_itch_dir(path: Path) -> ItchGame | None:
	if not path.joinpath('.itch').is_dir():
		return None

	game = ItchGame(path, ItchioConfig())
	return game

def do_itch_io_games() -> None:
	for itch_io_folder in ItchioConfig().itch_io_folders:
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
