from abc import ABC
from typing import TYPE_CHECKING

from .game import Game

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig

class EmulatedGame(Game, ABC):
	#This class doesn't actually make the most sense, it just has a PlatformConfig, which we want to get rid of
	def __init__(self, platform_config: 'PlatformConfig') -> None:
		self.platform_config = platform_config
		super().__init__()
