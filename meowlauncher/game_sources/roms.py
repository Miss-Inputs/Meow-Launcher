#!/usr/bin/env python3

import logging
import os
from collections.abc import Collection, Iterator, Sequence
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Union

from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import ignored_directories, main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.config_types import (EmulatorConfig, PlatformConfig,
                                       TypeOfConfigValue)
from meowlauncher.configured_emulator import (ConfiguredStandardEmulator,
                                              LibretroCoreWithFrontend)
from meowlauncher.data.emulated_platforms import platforms
from meowlauncher.data.emulators import (emulators, libretro_cores,
                                         libretro_frontends)
from meowlauncher.emulator import (LibretroCore, MAMEDriver, MednafenModule,
                                   StandardEmulator, ViceEmulator)
from meowlauncher.exceptions import (EmulationNotSupportedException,
                                     ExtensionNotSupportedException,
                                     NotActuallyLaunchableGameException)
from meowlauncher.game_source import (ChooseableEmulatorGameSource,
                                      CompoundGameSource)
from meowlauncher.games.roms.rom import ROM, FolderROM, get_rom
from meowlauncher.games.roms.rom_game import ROMGame, ROMLauncher
from meowlauncher.games.roms.rom_info import add_info
from meowlauncher.util import archives
from meowlauncher.util.desktop_files import has_been_done

if TYPE_CHECKING:
	from meowlauncher.emulated_platform import StandardEmulatedPlatform

logger = logging.getLogger(__name__)

def _get_emulator_config(emulator: Union[StandardEmulator, LibretroCore]) -> EmulatorConfig:
	"""TODO: Eventually, once we have per-game overrides, we should give this a ROMGame parameter too, and that should work out"""
	if isinstance(emulator, (MednafenModule, ViceEmulator, MAMEDriver)):
		specific = emulator_configs[emulator.config_name]
		global_config = emulator_configs[emulator.name]
		combined: dict[str, TypeOfConfigValue] = {}
		combined.update(global_config.options)
		combined.update(specific.options)
		if isinstance(emulator, ViceEmulator):
			exe_path = specific.exe_path #It does not make sense to specify path for VICE globally
		else:
			#By default, use global Mednafen/MAME path (if it is set), but if it is set to something specific, use that
			exe_path = specific.exe_path if specific.exe_path != emulator.default_exe_name else global_config.exe_path
		return EmulatorConfig(exe_path, combined)
	return emulator_configs[emulator.config_name]

class ROMPlatform(ChooseableEmulatorGameSource[StandardEmulator]):
	"""An emulated game system, as an individual source. Use with ROMs to cycle through all of them"""

	def __init__(self, platform_config: PlatformConfig, platform: 'StandardEmulatedPlatform') -> None:
		#Bit naughty, because it has a different signature? Hmm maybe not
		self.platform: 'StandardEmulatedPlatform' = platform
		super().__init__(platform_config, platform, emulators, libretro_cores)

	@property
	def is_available(self) -> bool:
		return self.platform_config.is_available

	def _process_rom(self, rom: ROM, subfolders: Sequence[str]) -> ROMLauncher | None:
		game = ROMGame(rom, self.platform, self.platform_config)

		categories = subfolders[:-1] if subfolders and subfolders[-1] == game.rom.name else subfolders
		game.info.categories = categories
			
		add_info(game)

		if not game.info.categories and game.info.platform:
			game.info.categories = (game.info.platform, )

		exception_reason = None
		launcher = None

		chosen_emulator_names = [] #For warning message
		for chosen_emulator in self.iter_chosen_emulators():
			chosen_emulator_names.append(chosen_emulator.name)
			try:
				potential_emulator_config = _get_emulator_config(chosen_emulator)
				potential_emulator: ConfiguredStandardEmulator
				if isinstance(chosen_emulator, LibretroCore):
					if not main_config.libretro_frontend: #TODO: This should be in the config of LibretroCore actually, see secret evil plan
						raise EmulationNotSupportedException('Must choose a frontend to run libretro cores')
					frontend_config = emulator_configs[main_config.libretro_frontend]
					frontend = libretro_frontends[main_config.libretro_frontend]
					potential_emulator = LibretroCoreWithFrontend(chosen_emulator, potential_emulator_config, frontend, frontend_config)
				else:
					potential_emulator = ConfiguredStandardEmulator(chosen_emulator, potential_emulator_config)

				if not potential_emulator.supports_rom(rom):
					message = 'folders' if rom.is_folder else f'{rom.extension} extension'
					raise ExtensionNotSupportedException(f'{potential_emulator.name} does not support {message}')

				potential_launcher = ROMLauncher(game, potential_emulator, self.platform_config)
				potential_launcher.command #We need to test each one for EmulationNotSupportedException… what's the maybe better way to do this, since we call get_launch_command again and that sucks #pylint: disable=pointless-statement
				#TODO But is that really right?
				launcher = potential_launcher
				break
			except (EmulationNotSupportedException, NotActuallyLaunchableGameException) as ex:
				exception_reason = ex

		if not launcher:
			#TODO: We also need a warn_about_unemulated_extensions type thing
			#Actually is it better to use some kind of custom level or logging field for that?
			if isinstance(exception_reason, EmulationNotSupportedException):
				if isinstance(exception_reason, ExtensionNotSupportedException):
					logger.info('%s could not be launched by %s', rom, chosen_emulator_names, exc_info=exception_reason)
				else:
					logger.warning('%s could not be launched by %s', rom, chosen_emulator_names, exc_info=exception_reason)
			else:
				logger.debug('%s could not be launched by %s', rom, chosen_emulator_names, exc_info=exception_reason)
			return None
		
		return launcher

	def _process_file_list(self, file_list: Collection[tuple[Path, Sequence[str]]]) -> Iterator[ROMLauncher]:
		for path, subfolders in file_list:
			try:
				rom = get_rom(path)
			except archives.BadArchiveError:
				logger.exception('Uh oh fucky wucky! %s is an archive file that we tried to open to list its contents, but it was invalid', path)
				continue
			except OSError:
				logger.exception('Uh oh fucky wucky! %s is an archive file that has nothing in it or something else weird', path)
				continue

			if not rom.is_folder and not self.platform.is_valid_file_type(rom.extension):
				#TODO: Probs want a warn_about_invalid_extension main_config (or platform_config)
				logger.debug('Invalid extension for this platform in %s %s: %s', type(rom).__name__, rom, rom.extension)
				continue

			try:
				if rom.should_read_whole_thing:
					rom.read_whole_thing()			
			except Exception: #pylint: disable=broad-except
				logger.exception('Bother!!! Reading %s produced an error', rom)
				continue

			launcher = None
			try:
				launcher = self._process_rom(rom, subfolders)
			except Exception: #pylint: disable=broad-except
				#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
				logger.exception('FUCK!!!! %s', rom)

			if launcher:
				yield launcher

	def iter_launchers(self) -> Iterator[ROMLauncher]:
		file_list = []
		#rom_list: list[tuple[ROM, Sequence[str]]] = []
		for rom_dir in self.platform_config.paths:
			if not rom_dir.is_dir():
				logger.warning('Oh no %s has invalid ROM dir: %s', self.name, rom_dir)
				continue
			#used_m3u_filenames = []
			for root, dirs, files in os.walk(rom_dir):
				root_path = PurePath(root)
			
				if any(root_path.is_relative_to(ignored_directory) for ignored_directory in ignored_directories):
					continue

				subfolders = root_path.relative_to(rom_dir).parts
				if subfolders and any(subfolder in main_config.skipped_subfolder_names for subfolder in subfolders):
						continue

				folder_check = self.platform.folder_check
				if folder_check:
					remaining_subdirs = [] #The subdirectories of rom_dir that aren't folder ROMs
					for d in dirs:
						folder_path = Path(root, d)
						if not main_config.full_rescan and has_been_done('ROM', str(folder_path)):
							continue

						folder_rom = FolderROM(folder_path)
						media_type = folder_check(folder_rom)
						if not media_type:
							#This was not a folder we want, descend into it normally
							remaining_subdirs.append(d)
							continue
						folder_rom.media_type = media_type
						#rom_list.append((folder_rom, subfolders))
						launcher = self._process_rom(folder_rom, subfolders)
						if launcher:
							yield launcher
							#file_list.append((folder_path, subfolders))
						#Avoid descending further, even if we get a NotARomException
						#This will not work well if we have multiple emulators for these folder-having systems and one supports folders and one doesn't, but eh, worry about that later I think
					dirs[:] = remaining_subdirs
				dirs.sort()

				for name in sorted(files):
					path = Path(root, name)
					#TODO: We might actually want to do something with associated documents later, but for now, we know we aren't doing anything with them
					if (not self.platform.is_valid_file_type(path.suffix[1:].lower())) and path.suffix[1:].lower() in {'txt', 'md', 'jpg', 'nfo', 'gif', 'bmp'}:
						continue
					if not main_config.full_rescan:
						if has_been_done('ROM', str(path)):
							continue

					file_list.append((path, subfolders))
		yield from self._process_file_list(file_list)

	def no_longer_exists(self, game_id: str) -> bool:
		return not os.path.exists(game_id)

	@classmethod
	def game_type(cls) -> str:
		return 'ROMs'


def _rom_platform(platform: str) -> type[ROMPlatform]:
	"""Using this because otherwise I'm not sure how I get name to return the platform name since that requires construction
	This feels REALLY cursed"""
	class _ROMPlatform(ROMPlatform):
		@classmethod
		def name(cls) -> str:
			return platform
	return _ROMPlatform

class ROMs(CompoundGameSource):
	"""Source for emulated games that are "normal" and are mostly just one file for each game (if not a folder or a few files), and are simple conceptually"""

	@staticmethod
	def _iter_platform_sources() -> Iterator[ROMPlatform]:
		"""Returns an iterator for a ROMPlatform for every platform in platform_configs, excpet DOS/Mac/etc and anything in main_config.excluded_platforms"""
		for platform_name, platform_config in platform_configs.items():
			platform = platforms.get(platform_name)
			if not platform:
				#As DOS, Mac, etc would be in platform_configs too
				continue
			if platform_name in main_config.excluded_platforms:
				continue
			platform_source = _rom_platform(platform_name)(platform_config, platform)
			if not platform_source.is_available:
				continue
			yield platform_source

	def __init__(self) -> None:
		if main_config.platforms:
			super().__init__(tuple(_rom_platform(only_platform)(platform_configs[only_platform], platforms[only_platform]) for only_platform in main_config.platforms))
		else:
			super().__init__(tuple(self._iter_platform_sources()))

	@classmethod
	def description(cls) -> str:
		return 'ROMs'

	def no_longer_exists(self, game_id: str) -> bool:
		return not os.path.exists(game_id)
