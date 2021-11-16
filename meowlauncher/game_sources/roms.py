#!/usr/bin/env python3

import os
import pathlib
import traceback
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Optional, Union, cast

from meowlauncher.common_types import (EmulationNotSupportedException,
                                       ExtensionNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import (PlatformConfig,
                                                 platform_configs)
from meowlauncher.configured_emulator import (ConfiguredStandardEmulator,
                                              LibretroCoreWithFrontend)
from meowlauncher.data.emulated_platforms import platforms
from meowlauncher.data.emulators import (emulators, libretro_cores,
                                         libretro_frontends)
from meowlauncher.desktop_launchers import has_been_done
from meowlauncher.emulated_platform import EmulatedPlatform
from meowlauncher.emulator import LibretroCore, StandardEmulator
from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.games.roms.platform_specific.roms_folders import \
    folder_checks
from meowlauncher.games.roms.rom import ROM, FileROM, FolderROM, rom_file
from meowlauncher.games.roms.rom_game import ROMGame, ROMLauncher
from meowlauncher.games.roms.roms_metadata import add_metadata
from meowlauncher.util import archives
from meowlauncher.util.utils import find_filename_tags_at_end, starts_with_any

def parse_m3u(path: Path):
	with open(path, 'rt', encoding='utf-8') as f:
		return [line.rstrip('\n') for line in f]

def sort_m3u_first() -> type:
	class Sorter:
		def __init__(self, obj, *_):
			self.o = obj
		def __lt__(self, _):
			return self.o.lower().endswith('.m3u')
		def __le__(self, _):
			return self.o.lower().endswith('.m3u')
		def __gt__(self, other):
			return other.lower().endswith('.m3u')
		def __ge__(self, other):
			return other.lower().endswith('.m3u')

	return Sorter

class ROMPlatform(GameSource):
	def __init__(self, platform_config: PlatformConfig, platform: EmulatedPlatform) -> None:
		self.platform_config = platform_config
		self.platform = platform
		self.chosen_emulators: list[Union[StandardEmulator, LibretroCore]] = []

		for emulator_name in self.platform_config.chosen_emulators:
			if emulator_name not in emulators:
				if emulator_name + ' (libretro)' in libretro_cores:
					self.chosen_emulators.append(libretro_cores[emulator_name + ' (libretro)'])
				elif emulator_name in libretro_cores:
					self.chosen_emulators.append(libretro_cores[emulator_name])
				else:
					print('Config warning:', emulator_name, 'is not a valid emulator, specified in', self.name)
			elif emulator_name not in self.platform.emulators:
				print('Config warning:', emulator_name, 'is not a valid emulator for', self.name)
			else:
				self.chosen_emulators.append(emulators[emulator_name])

	@property
	def name(self) -> str:
		return self.platform.name

	@property
	def is_available(self) -> bool:
		return self.platform_config.is_available


	def _process_file(self, rom: ROM, subfolders: Sequence[str]) -> Optional[ROMLauncher]:
		game = ROMGame(rom, self.platform, self.platform_config)

		if game.rom.extension == 'm3u':
			file_rom = cast(FileROM, game.rom)
			lines = file_rom.read().decode('utf-8').splitlines()
			filenames = [Path(line) if line.startswith('/') else game.rom.path.with_name(line) for line in lines if not line.startswith("#")]
			if any(not filename.is_file() for filename in filenames):
				if main_config.debug:
					print('M3U file', game.rom.path, 'has broken references!!!!', filenames)
				return None
			game.subroms = [rom_file(str(referenced_file)) for referenced_file in filenames]

		#TODO: We used to have a check here that we actually have anything in potential_emulator_names that supported the game before we added metadata, to save performance, but it got confusing in refactoring and had duplicated code… maybe we should do something like that again
				
		game.filename_tags = find_filename_tags_at_end(game.rom.name)
		if subfolders and subfolders[-1] == game.rom.name:
			game.metadata.categories = list(subfolders[:-1])
		else:
			game.metadata.categories = list(subfolders)
			
		add_metadata(game)

		if not game.metadata.categories and game.metadata.platform:
			game.metadata.categories = [game.metadata.platform]

		exception_reason = None
		launcher = None

		for chosen_emulator in self.chosen_emulators:
			try:
				potential_emulator: ConfiguredStandardEmulator
				if isinstance(chosen_emulator, LibretroCore):
					potential_core_config = emulator_configs[chosen_emulator.name + ' (libretro)']
					if not main_config.libretro_frontend: #TODO: This should be in the config of LibretroCore actually, see secret evil plan
						raise EmulationNotSupportedException('Must choose a frontend to run libretro cores')
					frontend_config = emulator_configs[main_config.libretro_frontend]
					frontend = libretro_frontends[main_config.libretro_frontend]
					potential_emulator = LibretroCoreWithFrontend(chosen_emulator, potential_core_config, frontend, frontend_config)
				else:
					potential_emulator_config = emulator_configs[chosen_emulator.name]
					potential_emulator = ConfiguredStandardEmulator(chosen_emulator, potential_emulator_config)

				if rom.is_folder and not potential_emulator.supports_folders:
					raise ExtensionNotSupportedException('{0} does not support folders'.format(potential_emulator))
				if not rom.is_folder and not potential_emulator.supports_extension(rom.extension):
					raise ExtensionNotSupportedException('{0} does not support {1} extension'.format(potential_emulator, rom.extension))

				potential_launcher = ROMLauncher(game, potential_emulator, self.platform_config)
				params = potential_launcher.get_launch_command() #We need to test each one for EmulationNotSupportedException… what's the maybe better way to do this, since we call get_launch_command again and that sucks
				if params:
					launcher = potential_launcher
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not launcher:
			if main_config.debug:
				if isinstance(exception_reason, EmulationNotSupportedException) and not isinstance(exception_reason, ExtensionNotSupportedException):
					print(rom.path, 'could not be launched by', [emu.name for emu in self.chosen_emulators], 'because', exception_reason)
			return None
		
		return launcher

	def _process_file_list(self, file_list: Iterable[tuple[str, Sequence[str]]]) -> Iterable[ROMLauncher]:
		for path, categories in file_list:
			try:
				rom = rom_file(path)
			except archives.BadArchiveError as badarchiveerror:
				print('Uh oh fucky wucky!', path, 'is an archive file that we tried to open to list its contents, but it was invalid:', badarchiveerror.__cause__, traceback.extract_tb(badarchiveerror.__traceback__)[1:])
				continue
			except IOError as ioerror:
				print('Uh oh fucky wucky!', path, 'is an archive file that has nothing in it or something else weird:', ioerror.__cause__, traceback.extract_tb(ioerror.__traceback__)[1:])
				continue

			# if rom.extension == 'm3u':
			# 	used_m3u_filenames.extend(parse_m3u(path))
			# else:
			# 	#Avoid adding part of a multi-disc game if we've already added the whole thing via m3u
			# 	#This is why we have to make sure m3u files are added first, though...  not really a nice way around this, unless we scan the whole directory for files first and then rule out stuff?
			# 	if name in used_m3u_filenames or path in used_m3u_filenames:
			# 		continue

			if not self.platform.is_valid_file_type(rom.extension):
				continue

			if not main_config.full_rescan:
				if has_been_done('ROM', path):
					continue
			
			try:
				rom.maybe_read_whole_thing()
			#pylint: disable=broad-except
			except Exception as ex:
				print('Bother!!! Reading the ROM produced an error', path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])
				continue

			try:
				launcher = self._process_file(rom, categories)
				if launcher:
					yield launcher
			#pylint: disable=broad-except
			except Exception as ex:
				#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
				print('FUCK!!!!', path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])

	def get_launchers(self) -> Iterable[ROMLauncher]:
		file_list = []

		for rom_dir in self.platform_config.paths:
			rom_dir = os.path.expanduser(rom_dir)
			if not os.path.isdir(rom_dir):
				print('Oh no', self.name, 'has invalid ROM dir', rom_dir)
				continue

			#used_m3u_filenames = []
			for root, dirs, files in os.walk(rom_dir):
				if starts_with_any(root + os.sep, main_config.ignored_directories):
					continue
				subfolders = list(pathlib.Path(root).relative_to(rom_dir).parts)
				if subfolders:
					if any(subfolder in main_config.skipped_subfolder_names for subfolder in subfolders):
						continue

				if self.platform_config.name in folder_checks:
					remaining_subdirs = [] #The subdirectories of rom_dir that aren't folder ROMs
					for d in dirs:
						folder_path = os.path.join(root, d)
						folder_rom = FolderROM(folder_path)
						media_type = folder_checks[self.platform_config.name](folder_rom)
						if media_type:
							folder_rom.media_type = media_type
							#if process_file(platform_config, rom_dir, root, folder_rom):
							#Theoretically we might want to continue descending if we couldn't make a launcher for this folder, because maybe we also have another emulator which doesn't work with folders, but does support a file inside it. That results in weird stuff where we try to launch a file inside the folder using the same emulator we just failed to launch the folder with though, meaning we actually don't want it but now it just lacks metadata, so I'm gonna just do this for now
							#I think I need to be more awake to re-read that comment
							#TODO: Yeah nah - process_file_list should contain files and folders, and if it encounters a folder where emulator 1 doesn't support folders but supports a file inside it, descends into it first, and then if that doesn't work, go to emulator 2 which does, etc
							launcher = self._process_file(folder_rom, subfolders)
							if launcher:
								yield launcher
							continue
						remaining_subdirs.append(d)
					dirs[:] = remaining_subdirs
				dirs.sort()

				for name in sorted(files, key=sort_m3u_first()):
					path = os.path.join(root, name)

					#categories = [cat for cat in list(pathlib.Path(os.path.).relative_to(rom_dir).parts) if cat != rom.name]
					file_list.append((path, subfolders))
		yield from self._process_file_list(file_list)

	def no_longer_exists(self, game_id: str) -> bool:
		return not os.path.exists(game_id)

class ROMs(CompoundGameSource):
	def __init__(self, only_platforms: Sequence[str]=None, excluded_platforms: Iterable[str]=None) -> None:
		if only_platforms:
			super().__init__([ROMPlatform(platform_configs[only_platform], platforms[only_platform]) for only_platform in only_platforms])
		else:
			platform_sources = []
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
				platform_sources.append(platform_source)
			super().__init__(platform_sources)

	@property
	def name(self) -> str:
		return 'ROMs'

	@property
	def description(self) -> str:
		return 'ROMs'

	def no_longer_exists(self, game_id: str) -> bool:
		return not os.path.exists(game_id)
