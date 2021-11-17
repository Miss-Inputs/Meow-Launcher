import tempfile
from pathlib import Path
from typing import Optional, cast

from meowlauncher.config.platform_config import PlatformConfig
from meowlauncher.configured_emulator import ConfiguredStandardEmulator
from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulated_platform import StandardEmulatedPlatform
from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.games.mame_common.software_list import SoftwareList
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.util.io_utils import make_filename
from meowlauncher.util.utils import find_filename_tags_at_end

from .rom import ROM, CompressedROM, FileROM


class ROMGame(EmulatedGame):
	def __init__(self, rom: ROM, platform: StandardEmulatedPlatform, platform_config: PlatformConfig):
		super().__init__(platform_config)
		self.rom = rom
		self.metadata.platform = platform.name
		self.platform = platform
		self.metadata.categories = []
		self.filename_tags = find_filename_tags_at_end(rom.path.name)

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
	def __init__(self, game: ROMGame, emulator: ConfiguredStandardEmulator, platform_config: PlatformConfig) -> None:
		self.game: ROMGame = game
		self.runner: ConfiguredStandardEmulator = emulator
		super().__init__(game, emulator, platform_config.options)

	@property
	def game_type(self) -> str:
		return 'ROM'
	
	@property
	def game_id(self) -> str:
		return str(self.game.rom.path)

	def get_launch_command(self) -> LaunchCommand:
		#TODO: Ideally EmulatorLauncher would do something useful with self.runner and then we call super() but that also needs refactoring
		command = super().get_launch_command()
		if self.game.rom.is_compressed:
			rom = cast(CompressedROM, self.game.rom)
			if not self.runner.supports_compressed_extension(rom.extension):
				temp_extraction_folder = Path(tempfile.gettempdir(), 'meow-launcher-' + make_filename(self.game.name))
				extracted_path = temp_extraction_folder.joinpath(rom.inner_filename)
				command = command.replace_path_argument(extracted_path)
				command = command.prepend_command(LaunchCommand('7z', ['x', '-o' + temp_extraction_folder.as_posix(), self.game.rom.path.as_posix()]))
				command = command.append_command(LaunchCommand('rm', ['-rf', temp_extraction_folder.as_posix()]))
		else:
			command = command.replace_path_argument(self.game.rom.path)
		return command
