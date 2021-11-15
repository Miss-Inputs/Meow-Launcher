from abc import ABC
from collections.abc import Mapping
from typing import Any

from .configured_emulator import ConfiguredEmulator
from .emulated_game import EmulatedGame
from .launch_command import LaunchCommand
from .launcher import Launcher


class EmulatorLauncher(Launcher, ABC):
	def __init__(self, game: EmulatedGame, emulator: ConfiguredEmulator, platform_config: Mapping[str, Any]=None) -> None:
		self.game: EmulatedGame = game
		self.runner: ConfiguredEmulator = emulator
		self.platform_config = platform_config if platform_config else {}
		super().__init__(game, emulator)

	def get_launch_command(self) -> LaunchCommand:
		return self.runner.get_launch_command_for_game(self.game, self.platform_config)
