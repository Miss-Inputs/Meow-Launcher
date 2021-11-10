#!/usr/bin/env python3

import datetime
import os
import pathlib
import sys
import time
import traceback
from collections.abc import Iterable, Sequence
from typing import Union

from meowlauncher import launchers
from meowlauncher.common_types import (EmulationNotSupportedException,
                                       ExtensionNotSupportedException,
                                       NotARomException)
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.system_config import SystemConfig, system_configs
from meowlauncher.data.emulators import emulators, libretro_frontends
from meowlauncher.games.emulator import (LibretroCore,
                                         LibretroCoreWithFrontend, MameDriver,
                                         MednafenModule, ViceEmulator)
from meowlauncher.games.roms.platform_specific.roms_folders import \
    folder_checks
from meowlauncher.games.roms.rom import FileROM, FolderROM, rom_file
from meowlauncher.games.roms.rom_game import RomGame
from meowlauncher.games.roms.roms_metadata import add_metadata
from meowlauncher.info import system_info
from meowlauncher.util import archives
from meowlauncher.util.utils import find_filename_tags_at_end, starts_with_any


def process_file(system_config: SystemConfig, potential_emulators: Iterable[str], rom: Union[FileROM, FolderROM], subfolders: Sequence[str]):
	game = RomGame(rom, system_config.name, system_info.systems[system_config.name])

	if game.rom.extension == 'm3u':
		lines = game.rom.read().decode('utf-8').splitlines()
		filenames = [line if line.startswith('/') else os.path.join(os.path.dirname(game.rom.path), line) for line in lines if not line.startswith("#")]
		if any(not os.path.isfile(filename) for filename in filenames):
			if main_config.debug:
				print('M3U file', game.rom.path, 'has broken references!!!!', filenames)
			return False
		game.subroms = [rom_file(referenced_file) for referenced_file in filenames]

	have_emulator_that_supports_extension = False
	for potential_emulator_name in potential_emulators:
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
		return False
			
	game.filename_tags = find_filename_tags_at_end(game.rom.name)
	if subfolders and subfolders[-1] == game.rom.name:
		game.metadata.categories = subfolders[:-1]
	else:
		game.metadata.categories = subfolders
		
	add_metadata(game)

	if not game.metadata.categories:
		game.metadata.categories = [game.metadata.platform]

	exception_reason = None

	emulator = None
	emulator_name = None
	launch_params = None

	for potential_emulator_name in potential_emulators:
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

			params = potential_emulator.get_launch_params(game, system_config.options, potential_emulator_config)
			if params:
				emulator = potential_emulator
				emulator_name = potential_emulator_name
				launch_params = params
				break
		except (EmulationNotSupportedException, NotARomException) as ex:
			exception_reason = ex

	if not emulator:
		if main_config.debug:
			if isinstance(exception_reason, EmulationNotSupportedException) and not isinstance(exception_reason, ExtensionNotSupportedException):
				print(rom.path, 'could not be launched by', potential_emulators, 'because', exception_reason)
		return False

	game.emulator = emulator
	game.launch_params = launch_params
	if isinstance(game.emulator, MameDriver):
		game.metadata.emulator_name = 'MAME'
	elif isinstance(game.emulator, MednafenModule):
		game.metadata.emulator_name = 'Mednafen'
	elif isinstance(game.emulator, ViceEmulator):
		game.metadata.emulator_name = 'VICE'
	else:
		game.metadata.emulator_name = emulator_name
	game.make_launcher()
	return True

def parse_m3u(path: str):
	with open(path, 'rt') as f:
		return [line.rstrip('\n') for line in f]

def sort_m3u_first():
	class Sorter:
		def __init__(self, obj, *_):
			self.o = obj
		def __lt__(self, other):
			return self.o.lower().endswith('.m3u')
		def __le__(self, other):
			return self.o.lower().endswith('.m3u')
		def __gt__(self, other):
			return other.lower().endswith('.m3u')
		def __ge__(self, other):
			return other.lower().endswith('.m3u')

	return Sorter

def process_emulated_system(system_config: SystemConfig):
	time_started = time.perf_counter()

	potential_emulators = []
	for emulator_name in system_config.chosen_emulators:
		if emulator_name not in emulators:
			if emulator_name + ' (libretro)' in emulators:
				potential_emulators.append(emulator_name + ' (libretro)')
			else:
				print('Config warning:', emulator_name, 'is not a valid emulator')
		elif emulator_name not in system_info.systems[system_config.name].emulators:
			print('Config warning:', emulator_name, 'is not a valid emulator for', system_config.name)
		else:
			potential_emulators.append(emulator_name)

	file_list = []

	for rom_dir in system_config.paths:
		rom_dir = os.path.expanduser(rom_dir)
		if not os.path.isdir(rom_dir):
			print('Oh no', system_config.name, 'has invalid ROM dir', rom_dir)
			continue

		#used_m3u_filenames = []
		for root, dirs, files in os.walk(rom_dir):
			if starts_with_any(root + os.sep, main_config.ignored_directories):
				continue
			subfolders = list(pathlib.Path(root).relative_to(rom_dir).parts)
			if subfolders:
				if any(subfolder in main_config.skipped_subfolder_names for subfolder in subfolders):
					continue

			if system_config.name in folder_checks:
				remaining_subdirs = [] #The subdirectories of rom_dir that aren't folder ROMs
				for d in dirs:
					folder_path = os.path.join(root, d)
					folder_rom = FolderROM(folder_path)
					media_type = folder_checks[system_config.name](folder_rom)
					if media_type:
						folder_rom.media_type = media_type
						#if process_file(system_config, rom_dir, root, folder_rom):
						#Theoretically we might want to continue descending if we couldn't make a launcher for this folder, because maybe we also have another emulator which doesn't work with folders, but does support a file inside it. That results in weird stuff where we try to launch a file inside the folder using the same emulator we just failed to launch the folder with though, meaning we actually don't want it but now it just lacks metadata, so I'm gonna just do this for now
						#I think I need to be more awake to re-read that comment
						process_file(system_config, potential_emulators, folder_rom, subfolders)
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

		system = system_info.systems[system_config.name]
		if not system.is_valid_file_type(rom.extension):
			continue

		if not main_config.full_rescan:
			if launchers.has_been_done('ROM', path):
				continue
		
		try:
			rom.maybe_read_whole_thing()
		#pylint: disable=broad-except
		except Exception as ex:
			print('Bother!!! Reading the ROM produced an error', path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])
			continue

		try:
			process_file(system_config, potential_emulators, rom, categories)
		#pylint: disable=broad-except
		except Exception as ex:
			#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
			print('FUCK!!!!', path, ex, type(ex), ex.__cause__, traceback.extract_tb(ex.__traceback__)[1:])
		

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(system_config.name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def process_system(system_config: SystemConfig):
	if system_config.name in system_info.systems:
		process_emulated_system(system_config)
	else:
		#Let DOS and Mac fall through, as those are in systems.ini but not handled here
		return

def process_systems() -> None:
	time_started = time.perf_counter()

	excluded_systems = []
	for arg in sys.argv:
		if arg.startswith('--exclude='):
			excluded_systems.append(arg.partition('=')[2])

	for system_name, system in system_configs.items():
		if system_name in excluded_systems:
			continue
		if not system.is_available:
			continue
		process_system(system)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('All emulated/engined systems finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main() -> None:
	if len(sys.argv) >= 2 and '--systems' in sys.argv:
		arg_index = sys.argv.index('--systems')
		if len(sys.argv) == 2:
			print('--systems requires an argument')
			return

		system_list = sys.argv[arg_index + 1].split(',')
		for system_name in system_list:
			process_system(system_configs[system_name])
		return

	process_systems()

