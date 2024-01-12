#!/usr/bin/env python3

from collections.abc import Iterator
from typing import TYPE_CHECKING

from meowlauncher import global_runners
from meowlauncher.config import main_config
from meowlauncher.game_source import GameSource
from meowlauncher.games.scummvm.scummvm_game import ScummVMGame, ScummVMLauncher
from meowlauncher.util.desktop_files import has_been_done
from meowlauncher.util.utils import NoNonsenseConfigParser

if TYPE_CHECKING:
	from meowlauncher.settings.settings import Settings


class ScummVM(GameSource):
	"""Games defined in scummvm.ini
	This used to have ResidualVM as well, but I guess I decided that if you don't update to the new version of stuff that's on you"""

	def __init__(self) -> None:
		super().__init__()
		self.config: global_runners.ScummVMConfig
		self.scummvm = global_runners.ScummVM()
		self.ini = NoNonsenseConfigParser()
		self.ini.read(self.config.scummvm_config_path)

	@property
	def is_available(self) -> bool:
		return self.ini.has_section('scummvm') and self.scummvm.is_path_valid

	def no_longer_exists(self, game_id: str) -> bool:
		return game_id not in self.ini.sections() if self.is_available else True

	def iter_games(self) -> Iterator[ScummVMGame]:
		for section in self.ini.sections():
			if section == 'scummvm':
				# Skip the top section
				continue
			if section == 'cloud':
				# This is not a game either
				continue
			if not main_config.full_rescan and has_been_done('ScummVM', section):
				continue

			section_items = dict(self.ini.items(section))
			yield ScummVMGame(section, self.scummvm, section_items)

	def iter_all_launchers(self) -> 'Iterator[ScummVMLauncher]':
		for game in self.iter_games():
			yield ScummVMLauncher(game, self.scummvm)

	@classmethod
	def config_class(cls) -> type['Settings'] | None:
		return global_runners.ScummVMConfig


__doc__ = ScummVM.__doc__ or ScummVM.__name__
