from abc import ABC
from typing import TYPE_CHECKING

from .game import Game

if TYPE_CHECKING:
	from meowlauncher.config.platform_config import PlatformConfig

class EmulatedGame(Game, ABC):
	def __init__(self, platform_config: 'PlatformConfig') -> None:
		self.platform_config = platform_config
		super().__init__()
