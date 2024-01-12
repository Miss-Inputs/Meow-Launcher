from abc import ABC
from typing import TYPE_CHECKING

from .launcher import Launcher

if TYPE_CHECKING:
	from collections.abc import Mapping

	from meowlauncher.config_types import TypeOfConfigValue

	from .emulator import Emulator
	from .game import Game

class EmulatorLauncher(Launcher, ABC):
	def __init__(self, game: 'Game', emulator: 'Emulator', platform_config: 'Mapping[str, TypeOfConfigValue] | None'=None) -> None:
		self.game: 'Game' = game
		self.runner: 'Emulator' = emulator
		self.platform_config = platform_config if platform_config else {}
		super().__init__(game, emulator)

