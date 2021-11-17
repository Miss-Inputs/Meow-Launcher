from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .launch_command import LaunchCommand
	from .game import Game
	from .configured_runner import ConfiguredRunner

class Launcher(ABC):
	def __init__(self, game: 'Game', runner: 'ConfiguredRunner') -> None:
		self.game = game
		self.runner = runner

	@property
	def name(self) -> str:
		return self.game.name

	@property
	@abstractmethod
	def game_type(self) -> str:
		pass
	
	@property
	@abstractmethod
	def game_id(self) -> str:
		pass

	@abstractmethod
	def get_launch_command(self) -> 'LaunchCommand':
		pass
