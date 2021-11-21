#!/usr/bin/env python3

import os
import traceback
from collections.abc import Collection, Iterator, Sequence
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Optional, Union

from meowlauncher.common_types import (EmulationNotSupportedException,
                                       ExtensionNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.config_types import EmulatorConfig, PlatformConfig
from meowlauncher.configured_emulator import (ConfiguredStandardEmulator,
                                              LibretroCoreWithFrontend)
from meowlauncher.data.emulated_platforms import platforms
from meowlauncher.data.emulators import (emulators, libretro_cores,
                                         libretro_frontends)
from meowlauncher.emulator import (LibretroCore, MAMEDriver, MednafenModule,
                                   StandardEmulator, ViceEmulator)
from meowlauncher.game_source import (ChooseableEmulatorGameSource,
                                      CompoundGameSource)
from meowlauncher.games.roms.rom import ROM, FolderROM, get_rom
from meowlauncher.games.roms.rom_game import ROMGame, ROMLauncher
from meowlauncher.games.roms.roms_metadata import add_metadata
from meowlauncher.util import archives
from meowlauncher.util.desktop_files import has_been_done

if TYPE_CHECKING:
	from meowlauncher.emulated_platform import StandardEmulatedPlatform

def _get_emulator_config(emulator: Union[StandardEmulator, LibretroCore]):
	#Eventually, once we have per-game overrides, we should give this a ROMGame parameter too, and that should work out
	if isinstance(emulator, (MednafenModule, ViceEmulator, MAMEDriver)):
		specific = emulator_configs[emulator.config_name]
		global_config = emulator_configs[emulator.name]
		combined = {}
		combined.update(global_config.options)
		combined.update(specific.options)
		if isinstance(emulator, ViceEmulator):
			exe_path = specific.exe_path #It does not make sense to specify path for VICE globally
		else:
			#By default, use global Mednafen/MAME path (if it is set), but if it is set to something specific, use that
			exe_path = specific.exe_path if (specific.exe_path and specific.exe_path != emulator.default_exe_name) else global_config.exe_path
		return EmulatorConfig(exe_path, combined)
	return emulator_configs[emulator.config_name]

class ROMPlatform(ChooseableEmulatorGameSource[StandardEmulator]):
	def __init__(self, platform_config: PlatformConfig, platform: 'StandardEmulatedPlatform') -> None:
		self.platform: 'StandardEmulatedPlatform' = platform
		super().__init__(platform_config, platform, emulators, libretro_cores)

	@property
	def name(self) -> str:
		return self.platform.name

	@property
	def is_available(self) -> bool:
		return self.platform_config.is_available

	def _process_rom(self, rom: ROM, subfolders: Sequence[str]) -> Optional[ROMLauncher]:
		game = ROMGame(rom, self.platform, self.platform_config)

		categories = subfolders[:-1] if subfolders and subfolders[-1] == game.rom.name else subfolders
		game.metadata.categories = categories
			
		add_metadata(game)

		if not game.metadata.categories and game.metadata.platform:
			game.metadata.categories = (game.metadata.platform, )

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
				command = potential_launcher.command #We need to test each one for EmulationNotSupportedException… what's the maybe better way to do this, since we call get_launch_command again and that sucks
				if command:
					launcher = potential_launcher
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not launcher:
			if main_config.debug:
				#TODO: We also need a warn_about_unemulated_extensions type thing
				if isinstance(exception_reason, EmulationNotSupportedException):
				#if isinstance(exception_reason, EmulationNotSupportedException) and not isinstance(exception_reason, ExtensionNotSupportedException):
					print(rom.path, 'could not be launched by', chosen_emulator_names, 'because', exception_reason)
			return None
		
		return launcher

	# def _process_rom_list(self, rom_list: Collection[tuple[ROM, Sequence[str]]]) -> Iterable[ROMLauncher]:
	# 	for rom, subfolders in rom_list:
	# 		if not rom.is_folder and not self.platform.is_valid_file_type(rom.extension):
	# 			#TODO: Probs want a warn_about_invalid_extension main_config (or platform_config)
	# 			print('Invalid extension', rom.path, rom.extension, type(rom), rom.path.suffix)
	# 			continue

	# 		try:
	# 			if rom.should_read_whole_thing:
	# 				rom.read_whole_thing()
	# 		#pylint: disable=broad-except
	# 		except Exception as ex:
	# 			print('Bother!!! Reading the ROM produced an error', rom.path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])
	# 			continue

	# 		launcher = None
	# 		try:
	# 			launcher = self._process_rom(rom, subfolders)
	# 		#pylint: disable=broad-except
	# 		except Exception as ex:
	# 			#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
	# 			print('FUCK!!!!', rom.path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])

	# 		if launcher:
	# 			yield launcher

	def _process_file_list(self, file_list: Collection[tuple[Path, Sequence[str]]]) -> Iterator[ROMLauncher]:
		for path, subfolders in file_list:
			try:
				rom = get_rom(path)
			except archives.BadArchiveError as badarchiveerror:
				print('Uh oh fucky wucky!', path, 'is an archive file that we tried to open to list its contents, but it was invalid:', badarchiveerror.__cause__, traceback.extract_tb(badarchiveerror.__traceback__)[1:])
				continue
			except IOError as ioerror:
				print('Uh oh fucky wucky!', path, 'is an archive file that has nothing in it or something else weird:', ioerror.__cause__, traceback.extract_tb(ioerror.__traceback__)[1:])
				continue

					
			if not rom.is_folder and not self.platform.is_valid_file_type(rom.extension):
				#TODO: Probs want a warn_about_invalid_extension main_config (or platform_config)
				print(f'Invalid extension for this platform in {type(rom).__name__} {rom.path}: {rom.extension}')
				continue

			try:
				if rom.should_read_whole_thing:
					rom.read_whole_thing()
			#pylint: disable=broad-except
			except Exception as ex:
				print('Bother!!! Reading the ROM produced an error', rom.path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])
				continue

			launcher = None
			try:
				launcher = self._process_rom(rom, subfolders)
			#pylint: disable=broad-except
			except Exception as ex:
				#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
				print('FUCK!!!!', rom.path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])

			if launcher:
				yield launcher

	def iter_launchers(self) -> Iterator[ROMLauncher]:
		file_list = []
		#rom_list: list[tuple[ROM, Sequence[str]]] = []
		for rom_dir in self.platform_config.paths:
			if not rom_dir.is_dir():
				print('Oh no', self.name, 'has invalid ROM dir', rom_dir)
				continue
			#used_m3u_filenames = []
			for root, dirs, files in os.walk(rom_dir):
				root_path = PurePath(root)
			
				if any(root_path.is_relative_to(ignored_directory) for ignored_directory in main_config.ignored_directories):
					continue

				subfolders = root_path.relative_to(rom_dir).parts
				if subfolders:
					if any(subfolder in main_config.skipped_subfolder_names for subfolder in subfolders):
						continue

				folder_check = self.platform.folder_check
				if folder_check:
					remaining_subdirs = [] #The subdirectories of rom_dir that aren't folder ROMs
					for d in dirs:
						folder_path = Path(root, d)
						if not main_config.full_rescan:
							if has_been_done('ROM', str(folder_path)):
								continue

						folder_rom = FolderROM(folder_path)
						media_type = folder_check(folder_rom)
						if media_type:
							folder_rom.media_type = media_type
							#rom_list.append((folder_rom, subfolders))
							launcher = self._process_rom(folder_rom, subfolders)
							if launcher:
								yield launcher
								#file_list.append((folder_path, subfolders))
								continue
						remaining_subdirs.append(d)
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

def _iter_platform_sources(excluded_platforms: Collection[str]=None) -> Iterator[ROMPlatform]:
	for platform_name, platform_config in platform_configs.items():
		platform = platforms.get(platform_name)
		if not platform:
			#As DOS, Mac, etc would be in platform_configs too
			continue
		if excluded_platforms and platform_name in excluded_platforms:
			continue
		platform_source = ROMPlatform(platform_config, platform)
		if not platform_source.is_available:
			continue
		yield platform_source

class ROMs(CompoundGameSource):
	def __init__(self, only_platforms: Sequence[str]=None, excluded_platforms: Collection[str]=None) -> None:
		if only_platforms:
			super().__init__(tuple(ROMPlatform(platform_configs[only_platform], platforms[only_platform]) for only_platform in only_platforms))
		else:
			super().__init__(tuple(_iter_platform_sources(excluded_platforms)))

	@property
	def name(self) -> str:
		return 'ROMs'

	@property
	def description(self) -> str:
		return 'ROMs'

	def no_longer_exists(self, game_id: str) -> bool:
		return not os.path.exists(game_id)
