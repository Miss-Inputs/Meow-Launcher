from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from meowlauncher.exceptions import GameNotSupportedError

if TYPE_CHECKING:
	from .game import Game
	from .launch_command import LaunchCommand
	from .runner import Runner


class Launcher(ABC):
	"""Base class for Launcher - the actual output of Meow Launcher, which is generally something that launches a game, but may also include sub-games or variations"""

	def __init__(self, game: 'Game', runner: 'Runner[Game] | None') -> None:
		""":param runner: May be None if this game is able to run itself"""
		self.game = game
		self.runner = runner

	@property
	def name(self) -> str:
		"""Display name of this launcher. By default, the game's name, override if your GameSource has some other way of getting a name"""
		return self.game.name

	@property
	@abstractmethod
	def game_id(self) -> str:
		"""This is written to the ID section of the launcher, and is used to uniquely identify a game"""
		# Hmm does that mean it should be on Game instead? Or GameSource as a method taking Game?

	@property
	def command(self) -> 'LaunchCommand':
		"""The actual command that this launcher executes"""
		if not self.runner:
			raise GameNotSupportedError('Game has nothing to run it with')
		return self.runner.get_wrapped_command(self.runner.get_game_command(self.game))

	def __hash__(self) -> int:
		return hash((type(self.game).__name__, self.game_id))


__doc__ = Launcher.__doc__ or Launcher.__name__
