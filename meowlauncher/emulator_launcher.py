from abc import ABC
from typing import TYPE_CHECKING

from .launcher import Launcher

if TYPE_CHECKING:
	from collections.abc import Mapping

	from meowlauncher.config_types import TypeOfConfigValue

	from .configured_emulator import ConfiguredEmulator
	from .emulated_game import EmulatedGame
	from .launch_command import LaunchCommand

class EmulatorLauncher(Launcher, ABC):
	def __init__(self, game: 'EmulatedGame', emulator: 'ConfiguredEmulator', platform_config: 'Mapping[str, TypeOfConfigValue] | None'=None) -> None:
		self.game: 'EmulatedGame' = game
		self.runner: 'ConfiguredEmulator' = emulator
		self.platform_config = platform_config if platform_config else {}
		super().__init__(game, emulator)

	@property
	def command(self) -> 'LaunchCommand':
		return self.runner.get_launch_command_for_game(self.game, self.platform_config)
