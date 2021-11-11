from abc import ABC
from meowlauncher.game import Game
from meowlauncher.launcher import Launcher
from meowlauncher.emulator import Emulator

class EmulatedGame(Game, ABC):
	pass

class EmulatorLauncher(Launcher, ABC):
	def __init__(self, game: EmulatedGame, emulator: Emulator) -> None:
		self.game: EmulatedGame = game
		self.runner: Emulator = emulator
		super().__init__(game, emulator)

	#TODO: Ideally get_launch_command should be implemented with self.runner.get_launch_params but that needs refactoring
