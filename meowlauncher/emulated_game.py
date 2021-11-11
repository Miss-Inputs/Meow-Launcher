from meowlauncher.game import Game
from meowlauncher.launcher import Launcher
from meowlauncher.emulator import Emulator

class EmulatedGame(Game):
	pass

class EmulatorLauncher(Launcher):
	def __init__(self, game: EmulatedGame, runner: Emulator) -> None:
		super().__init__(game, runner)
