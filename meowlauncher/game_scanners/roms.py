#!/usr/bin/env python3

import datetime
import os
import pathlib
import sys
import time
import traceback
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Optional, Type, cast

from meowlauncher.common_types import (EmulationNotSupportedException,
                                       ExtensionNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import PlatformConfig, platform_configs
from meowlauncher.data.emulated_platforms import platforms
from meowlauncher.data.emulators import emulators, libretro_frontends
from meowlauncher.desktop_launchers import (has_been_done,
                                            make_linux_desktop_for_launcher)
from meowlauncher.emulator import LibretroCore, LibretroCoreWithFrontend
from meowlauncher.games.roms.platform_specific.roms_folders import \
    folder_checks
from meowlauncher.games.roms.rom import ROM, FileROM, FolderROM, rom_file
from meowlauncher.games.roms.rom_game import ROMGame, ROMLauncher
from meowlauncher.games.roms.roms_metadata import add_metadata
from meowlauncher.util import archives
from meowlauncher.util.utils import find_filename_tags_at_end, starts_with_any


def process_file(platform_config: PlatformConfig, potential_emulator_names: Iterable[str], rom: ROM, subfolders: Sequence[str]) -> Optional[ROMLauncher]:
	game = ROMGame(rom, platform_config.name, platforms[platform_config.name])

	if game.rom.extension == 'm3u':
		file_rom = cast(FileROM, game.rom)
		lines = file_rom.read().decode('utf-8').splitlines()
		filenames = [Path(line) if line.startswith('/') else game.rom.path.with_name(line) for line in lines if not line.startswith("#")]
		if any(not filename.is_file() for filename in filenames):
			if main_config.debug:
				print('M3U file', game.rom.path, 'has broken references!!!!', filenames)
			return None
		game.subroms = [rom_file(str(referenced_file)) for referenced_file in filenames]

	have_emulator_that_supports_extension = False
	for potential_emulator_name in potential_emulator_names:
		potential_emulator = emulators[potential_emulator_name]
		potential_emulator_config = emulator_configs[potential_emulator_name]
		if rom.is_folder:
			if potential_emulator.supports_folders:
				have_emulator_that_supports_extension = True
				break
		else:
			if rom.extension in potential_emulator.supported_extensions:
				have_emulator_that_supports_extension = True
	if not have_emulator_that_supports_extension:
		return None
			
	game.filename_tags = find_filename_tags_at_end(game.rom.name)
	if subfolders and subfolders[-1] == game.rom.name:
		game.metadata.categories = subfolders[:-1]
	else:
		game.metadata.categories = subfolders
		
	add_metadata(game)

	if not game.metadata.categories:
		game.metadata.categories = [game.metadata.platform]

	exception_reason = None
	launcher = None

	for potential_emulator_name in potential_emulator_names:
		try:
			potential_emulator = emulators[potential_emulator_name]
			potential_emulator_config = emulator_configs[potential_emulator_name]
			if isinstance(potential_emulator, LibretroCore):
				if not main_config.libretro_frontend:
					raise EmulationNotSupportedException('Must choose a frontend to run libretro cores')
				frontend_config = emulator_configs[main_config.libretro_frontend]
				frontend = libretro_frontends[main_config.libretro_frontend]
				potential_emulator = LibretroCoreWithFrontend(potential_emulator, frontend, frontend_config)

			if rom.is_folder and not potential_emulator.supports_folders:
				raise ExtensionNotSupportedException('{0} does not support folders'.format(potential_emulator))
			if not rom.is_folder and rom.extension not in potential_emulator.supported_extensions:
				raise ExtensionNotSupportedException('{0} does not support {1} extension'.format(potential_emulator, rom.extension))

			potential_launcher = ROMLauncher(game, potential_emulator, platform_config, potential_emulator_config)
			params = potential_launcher.get_launch_command() #We need to test each one for EmulationNotSupportedException… what's the maybe better way to do this, since we call get_launch_command again and that sucks
			if params:
				launcher = potential_launcher
				break
		except (EmulationNotSupportedException, NotARomException) as ex:
			exception_reason = ex

	if not launcher:
		if main_config.debug:
			if isinstance(exception_reason, EmulationNotSupportedException) and not isinstance(exception_reason, ExtensionNotSupportedException):
				print(rom.path, 'could not be launched by', potential_emulator_names, 'because', exception_reason)
		return None
	
	return launcher

def parse_m3u(path: str):
	with open(path, 'rt') as f:
		return [line.rstrip('\n') for line in f]

def sort_m3u_first() -> Type:
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

def process_emulated_platform(platform_config: PlatformConfig):
	time_started = time.perf_counter()

	potential_emulators = []
	for emulator_name in platform_config.chosen_emulators:
		if emulator_name not in emulators:
			if emulator_name + ' (libretro)' in emulators:
				potential_emulators.append(emulator_name + ' (libretro)')
			else:
				print('Config warning:', emulator_name, 'is not a valid emulator')
		elif emulator_name not in platforms[platform_config.name].emulators:
			print('Config warning:', emulator_name, 'is not a valid emulator for', platform_config.name)
		else:
			potential_emulators.append(emulator_name)

	file_list = []

	for rom_dir in platform_config.paths:
		rom_dir = os.path.expanduser(rom_dir)
		if not os.path.isdir(rom_dir):
			print('Oh no', platform_config.name, 'has invalid ROM dir', rom_dir)
			continue

		#used_m3u_filenames = []
		for root, dirs, files in os.walk(rom_dir):
			if starts_with_any(root + os.sep, main_config.ignored_directories):
				continue
			subfolders = list(pathlib.Path(root).relative_to(rom_dir).parts)
			if subfolders:
				if any(subfolder in main_config.skipped_subfolder_names for subfolder in subfolders):
					continue

			if platform_config.name in folder_checks:
				remaining_subdirs = [] #The subdirectories of rom_dir that aren't folder ROMs
				for d in dirs:
					folder_path = os.path.join(root, d)
					folder_rom = FolderROM(folder_path)
					media_type = folder_checks[platform_config.name](folder_rom)
					if media_type:
						folder_rom.media_type = media_type
						#if process_file(platform_config, rom_dir, root, folder_rom):
						#Theoretically we might want to continue descending if we couldn't make a launcher for this folder, because maybe we also have another emulator which doesn't work with folders, but does support a file inside it. That results in weird stuff where we try to launch a file inside the folder using the same emulator we just failed to launch the folder with though, meaning we actually don't want it but now it just lacks metadata, so I'm gonna just do this for now
						#I think I need to be more awake to re-read that comment
						launcher = process_file(platform_config, potential_emulators, folder_rom, subfolders)
						if launcher:
							make_linux_desktop_for_launcher(launcher)
						continue
					remaining_subdirs.append(d)
				dirs[:] = remaining_subdirs
			dirs.sort()

			for name in sorted(files, key=sort_m3u_first()):
				path = os.path.join(root, name)

				#categories = [cat for cat in list(pathlib.Path(os.path.).relative_to(rom_dir).parts) if cat != rom.name]
				file_list.append((path, subfolders))


	for path, categories in file_list:
		try:
			rom = rom_file(path)
		except archives.BadArchiveError as badarchiveerror:
			print('Uh oh fucky wucky!', path, 'is an archive file that we tried to open to list its contents, but it was invalid:', badarchiveerror.__cause__, traceback.extract_tb(badarchiveerror.__traceback__)[1:])
			continue

		# if rom.extension == 'm3u':
		# 	used_m3u_filenames.extend(parse_m3u(path))
		# else:
		# 	#Avoid adding part of a multi-disc game if we've already added the whole thing via m3u
		# 	#This is why we have to make sure m3u files are added first, though...  not really a nice way around this, unless we scan the whole directory for files first and then rule out stuff?
		# 	if name in used_m3u_filenames or path in used_m3u_filenames:
		# 		continue

		platform = platforms[platform_config.name]
		if not platform.is_valid_file_type(rom.extension):
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
			launcher = process_file(platform_config, potential_emulators, rom, categories)
			if launcher:
				make_linux_desktop_for_launcher(launcher)
		#pylint: disable=broad-except
		except Exception as ex:
			#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
			print('FUCK!!!!', path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])
		

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(platform_config.name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def process_platform(platform_config: PlatformConfig):
	if platform_config.name in platforms:
		process_emulated_platform(platform_config)
	else:
		#Let DOS and Mac fall through, as those are in systems.ini but not handled here
		return

def process_platforms() -> None:
	time_started = time.perf_counter()

	excluded_platforms = []
	for arg in sys.argv:
		if arg.startswith('--exclude='):
			excluded_platforms.append(arg.partition('=')[2])

	for platform_name, platform in platform_configs.items():
		if platform_name in excluded_platforms:
			continue
		if not platform.is_available:
			continue
		process_platform(platform)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('All standard emulated platforms finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main() -> None:
	if len(sys.argv) >= 2 and '--platforms' in sys.argv:
		arg_index = sys.argv.index('--platforms')
		if len(sys.argv) == 2:
			print('--platforms requires an argument')
			return

		platform_list = sys.argv[arg_index + 1].split(',')
		for platform_name in platform_list:
			process_platform(platform_configs[platform_name])
		return

	process_platforms()

