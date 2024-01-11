from typing import TYPE_CHECKING

from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.games.common.emulator_command_line_helpers import mame_base
from meowlauncher.launch_command import LaunchCommand

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.data.machines_with_inbuilt_games import InbuiltGame

	from .mame import ConfiguredMAME

class MAMEInbuiltGame(EmulatedGame):
	def __init__(self, machine_name: str, inbuilt_game: 'InbuiltGame', platform_config: 'PlatformConfig', bios_name: str | None=None) -> None:
		super().__init__(platform_config)
		self.machine_name = machine_name
		self.inbuilt_game = inbuilt_game #Yeahhh this should be a dataclass/named tuple
		self.bios_name = bios_name

		self.info.platform = inbuilt_game.platform
		self.info.categories = [inbuilt_game.category]
		self.info.genre = None #We don't actually know these and it's probably not accurate to call a game "Home Videogame Console" etc
		self.info.subgenre = None #Could possibly add it ourselves to the inbuilt games list but that requires me knowing what I'm talking about when it comes to genres
		self.info.developer = None #We also don't know this necessarily, and I guess we could add it to InbuiltGame
	
	@property
	def name(self) -> str:
		return self.inbuilt_game.name
		
class MAMEInbuiltLauncher(EmulatorLauncher):
	def __init__(self, game: MAMEInbuiltGame, emulator: 'ConfiguredMAME') -> None:
		self.game: MAMEInbuiltGame = game
		super().__init__(game, emulator)

	@property
	def game_id(self) -> str:
		game_id = self.game.machine_name
		if self.game.bios_name:
			game_id += ':' + self.game.bios_name
		return game_id

	@property
	def command(self) -> LaunchCommand:
		return LaunchCommand(self.runner.config.exe_path, mame_base(self.game.machine_name, bios=self.game.bios_name))
