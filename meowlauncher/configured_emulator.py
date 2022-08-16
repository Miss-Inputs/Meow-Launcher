from collections.abc import Mapping
from typing import TYPE_CHECKING

from meowlauncher.config_types import EmulatorConfig, TypeOfConfigValue

from .configured_runner import ConfiguredRunner
from .emulator import (Emulator, LibretroCore, LibretroFrontend,
                       StandardEmulator)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import ROM

	from .emulated_game import EmulatedGame
	from .launch_command import LaunchCommand

class ConfiguredEmulator(ConfiguredRunner):
	def __init__(self, emulator: Emulator['EmulatedGame'], config: EmulatorConfig):
		self.runner: Emulator['EmulatedGame'] = emulator
		self.config: EmulatorConfig = config
		super().__init__(emulator, config)

	def get_launch_command_for_game(self, game: 'EmulatedGame', platform_config_options: Mapping[str, TypeOfConfigValue]) -> 'LaunchCommand':
		assert self.runner.launch_command_func, 'launch_command_func should never have been left as None'
		command = self.runner.launch_command_func(game, platform_config_options, self.config)
		return self.set_wrapper_options(command)

class ConfiguredStandardEmulator(ConfiguredEmulator):
	def __init__(self, emulator: StandardEmulator, config: EmulatorConfig):
		self.runner: StandardEmulator = emulator
		super().__init__(emulator, config)

	def supports_extension(self, extension: str) -> bool:
		return extension in self.runner.supported_extensions

	def supports_compressed_extension(self, extension: str) -> bool:
		return extension in self.runner.supported_compression

	@property
	def supports_folders(self) -> bool:
		return '/' in self.runner.supported_extensions

	def supports_rom(self, rom: 'ROM') -> bool:
		if rom.is_folder:
			return self.supports_folders
		return self.supports_extension(rom.extension)

class LibretroCoreWithFrontend(ConfiguredStandardEmulator):
	def __init__(self, core: LibretroCore, core_config: EmulatorConfig, frontend: LibretroFrontend, frontend_config: EmulatorConfig):
		self.core = core
		self.frontend = frontend
		self.core_config = core_config
		self.frontend_config = frontend_config
		combined_options: dict[str, TypeOfConfigValue] = {}
		combined_options.update(core_config.options)
		combined_options.update(frontend_config.options)
		combined_config = EmulatorConfig(frontend_config.exe_path, frontend_config.options)

		display_name = f'{self.frontend.name} ({self.core.name} core)'
		#.status doesn't do anything here, otherwise I would be trying to get min(core.status, frontend.status)
		#default_exe_name is irrelevant as it is already configured
		core_as_emulator = StandardEmulator(display_name, core.status, '', core.launch_command_func, core.supported_extensions, frontend.supported_compression, host_platform=frontend.host_platform)
		super().__init__(core_as_emulator, combined_config)

	def get_launch_command_for_game(self, game: 'EmulatedGame', platform_config_options: Mapping[str, TypeOfConfigValue]) -> 'LaunchCommand':
		if self.core.launch_command_func:
			#A libretro core having a launch_command_func is only useful to raise EmulationNotSupportedException therefore we ignore the return value, then we can reuse the same launch command func for a libretro core and the standalone emulator and that should probably work in most cases, and if it doesn't, we can just do command_lines.blah_libretro
			self.core.launch_command_func(game, platform_config_options, self.core_config)
		return self.frontend.launch_command_func(game, platform_config_options, self.core_config, self.frontend_config)
