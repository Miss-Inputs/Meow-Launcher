#!/usr/bin/env python3

from collections.abc import Iterable

from meowlauncher import global_runners
from meowlauncher.config.main_config import main_config
from meowlauncher.game_source import GameSource
from meowlauncher.games.scummvm.scummvm_config import scummvm_config
from meowlauncher.games.scummvm.scummvm_game import (ScummVMGame,
                                                     ScummVMLauncher)
from meowlauncher.util.desktop_files import has_been_done


class ScummVM(GameSource):
	@property
	def name(self) -> str:
		return 'ScummVM'

	@property
	def is_available(self) -> bool:
		return scummvm_config.have_scummvm

	def no_longer_exists(self, game_id: str) -> bool:
		return game_id not in scummvm_config.scummvm_ini.sections() if scummvm_config.have_scummvm else True

	def get_launchers(self) -> Iterable[ScummVMLauncher]:
		for section in scummvm_config.scummvm_ini.sections():
			if section == 'scummvm':
				#Skip the top section
				continue
			if section == 'cloud':
				#This is not a game either
				continue
			if not main_config.full_rescan:
				if has_been_done('ScummVM', section):
					continue

			game = ScummVMGame(section)
			yield ScummVMLauncher(game, global_runners.scummvm)
