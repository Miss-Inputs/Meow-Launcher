from abc import ABC, abstractmethod
from typing import Any

from .game import Game
from .launch_command import LaunchCommand
from .configured_runner import ConfiguredRunner


class Launcher(ABC):
	def __init__(self, game: Game, runner: ConfiguredRunner) -> None:
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

	@property
	def info_fields(self) -> dict[str, dict[str, Any]]:
		return self.game.metadata.to_launcher_fields()

	@abstractmethod
	def get_launch_command(self) -> LaunchCommand:
		pass
