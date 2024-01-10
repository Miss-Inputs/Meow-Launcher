#!/usr/bin/env python3

from typing import TYPE_CHECKING

from meowlauncher import global_runners
from meowlauncher.config import main_config
from meowlauncher.game_source import GameSource
from meowlauncher.games.scummvm.scummvm_config import ScummVMConfig, scummvm_config
from meowlauncher.games.scummvm.scummvm_game import ScummVMGame, ScummVMLauncher
from meowlauncher.settings.settings import Settings
from meowlauncher.util.desktop_files import has_been_done

if TYPE_CHECKING:
	from collections.abc import Iterator


class ScummVM(GameSource):
	"""Games defined in scummvm.ini
	This used to have ResidualVM as well, but I guess I decided that if you don't update to the new version of stuff that's on you"""
	@property
	def is_available(self) -> bool:
		return scummvm_config.have_scummvm

	def no_longer_exists(self, game_id: str) -> bool:
		return game_id not in scummvm_config.scummvm_ini.sections() if scummvm_config.have_scummvm else True

	def iter_launchers(self) -> 'Iterator[ScummVMLauncher]':
		for section in scummvm_config.scummvm_ini.sections():
			if section == 'scummvm':
				#Skip the top section
				continue
			if section == 'cloud':
				#This is not a game either
				continue
			if not main_config.full_rescan and has_been_done('ScummVM', section):
				continue

			game = ScummVMGame(section)
			yield ScummVMLauncher(game, global_runners.scummvm)

	@classmethod
	def config_class(cls) -> type[Settings] | None:
		return ScummVMConfig

__doc__ = ScummVM.__doc__ or ScummVM.__name__
