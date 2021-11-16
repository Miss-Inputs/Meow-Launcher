from abc import ABC

from meowlauncher.config.platform_config import PlatformConfig

from .game import Game

class EmulatedGame(Game, ABC):
	def __init__(self, platform_config: PlatformConfig) -> None:
		self.platform_config = platform_config
		super().__init__()
