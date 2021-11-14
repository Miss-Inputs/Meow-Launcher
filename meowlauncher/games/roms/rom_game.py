import os
import tempfile
from typing import Optional, cast

from meowlauncher.config.platform_config import PlatformConfig
from meowlauncher.config.runner_config import EmulatorConfig
from meowlauncher.emulated_game import EmulatedGame, EmulatorLauncher
from meowlauncher.emulated_platform import EmulatedPlatform
from meowlauncher.emulator import StandardEmulator
from meowlauncher.games.mame_common.software_list import SoftwareList
from meowlauncher.launcher import LaunchCommand
from meowlauncher.util.io_utils import make_filename

from .rom import ROM, CompressedROM, FileROM


class ROMGame(EmulatedGame):
	def __init__(self, rom: ROM, platform_name: str, platform: EmulatedPlatform):
		super().__init__()
		self.rom = rom
		self.platform_name = self.metadata.platform = platform_name
		self.platform = platform
		self.metadata.categories = []
		self.filename_tags: list[str] = []

		self.subroms: list[FileROM] = []
		self.software_lists: list[SoftwareList] = []
		self.exception_reason: Optional[BaseException] = None
	
	@property
	def name(self) -> str:
		name = self.rom.name
		if self.rom.ignore_name and self.metadata.names:
			name = self.metadata.names.get('Name', list(self.metadata.names.values())[0])
			
		return name

class ROMLauncher(EmulatorLauncher):
	def __init__(self, game: ROMGame, emulator: StandardEmulator, platform_config: PlatformConfig, emulator_config: EmulatorConfig) -> None:
		self.game: ROMGame = game
		self.runner: StandardEmulator = emulator
		super().__init__(game, emulator)
		self.platform_config = platform_config
		self.emulator_config = emulator_config

	@property
	def game_type(self) -> str:
		return 'ROM'
	
	@property
	def game_id(self) -> str:
		return str(self.game.rom.path)

	def get_launch_command(self) -> LaunchCommand:
		#TODO: Ideally EmulatorLauncher would do something useful with self.runner and then we call super() but that also needs refactoring
		params = self.runner.get_launch_params(self.game, self.platform_config.options, self.emulator_config)
		if self.game.rom.is_compressed:
			rom = cast(CompressedROM, self.game.rom)
			if rom.extension not in self.runner.supported_compression:
				temp_extraction_folder = os.path.join(tempfile.gettempdir(), 'meow-launcher-' + make_filename(self.game.name))

				extracted_path = os.path.join(temp_extraction_folder, rom.inner_filename)
				params = params.replace_path_argument(extracted_path)
				params = params.prepend_command(LaunchCommand('7z', ['x', '-o' + temp_extraction_folder, str(self.game.rom.path)]))
				params = params.append_command(LaunchCommand('rm', ['-rf', temp_extraction_folder]))
		else:
			params = params.replace_path_argument(str(self.game.rom.path))
		return params
