#!/usr/bin/env python3

import os
import sys
import shlex
import time
import datetime
import pathlib

import common
import archives
import launchers
import metadata
import io_utils

from config import system_configs, main_config
from info import system_info, emulator_info
from common_types import EmulationNotSupportedException, NotARomException
from roms_metadata import add_engine_metadata, add_metadata

class EngineFile():
	def __init__(self, path):
		self.path = path
		original_name = os.path.basename(path)
		self.name, self.extension = os.path.splitext(original_name)

		if self.extension.startswith('.'):
			self.extension = self.extension[1:]
		self.extension = self.extension.lower()

	def read(self, seek_to=0, amount=-1):
		return io_utils.read_file(self.path, seek_to=seek_to, amount=amount)

	def contains_subfolder(self, name):
		if not os.path.isdir(self.path):
			return False

		return os.path.isdir(os.path.join(self.path, name))

class EngineGame():
	def __init__(self, file, engine, folder):
		self.file = file
		self.engine = engine
		self.metadata = metadata.Metadata()
		self.metadata.categories = []
		self.folder = folder
		self.icon = None

	def get_command_line(self, system_config):
		return self.engine.get_command_line(self, system_config.specific_config)

	def make_launcher(self, system_config):
		exe_name, exe_args = self.get_command_line(system_config)
		exe_args = [arg.replace('$<path>', self.file.path) for arg in exe_args]
		launchers.make_launcher(exe_name, exe_args, self.file.name, self.metadata, 'Engine game', self.file.path, self.icon)

def try_engine(system_config, engine, base_dir, root, name):
	path = os.path.join(root, name)

	file = EngineFile(path)
	game = EngineGame(file, engine, root)

	game.metadata.categories = [i for i in root.replace(base_dir, '').split('/') if i]

	if not engine.is_game_data(file):
		return None

	add_engine_metadata(game)

	if not game.get_command_line(system_config):
		return None

	return game

def process_engine_file(system_config, file_dir, root, name):
	game = None

	engine_name = None
	potential_engines = system_config.chosen_emulators
	for potential_engine in potential_engines:
		if potential_engine not in emulator_info.engines:
			continue
		engine_name = potential_engine
		game = try_engine(system_config, emulator_info.engines[potential_engine], file_dir, root, name)
		if game:
			break

	if not game:
		return

	game.metadata.emulator_name = engine_name

	game.make_launcher(system_config)

class Rom():
	def __init__(self, path):
		self.path = path
		self.warn_about_multiple_files = False

		original_name = os.path.basename(path)
		name_without_extension, self.original_extension = os.path.splitext(original_name)

		if self.original_extension.startswith('.'):
			self.original_extension = self.original_extension[1:]
		self.original_extension = self.original_extension.lower()

		if self.original_extension in archives.compressed_exts:
			self.is_compressed = True

			found_file_already = False
			for entry in archives.compressed_list(self.path):
				if found_file_already:
					self.warn_about_multiple_files = True
					continue
				found_file_already = True

				self.name, self.extension = os.path.splitext(entry)
				self.compressed_entry = entry
		else:
			self.is_compressed = False
			self.compressed_entry = None
			self.name = name_without_extension
			self.extension = self.original_extension

		if self.extension.startswith('.'):
			self.extension = self.extension[1:]
		self.extension = self.extension.lower()

	def read(self, seek_to=0, amount=-1):
		return io_utils.read_file(self.path, self.compressed_entry, seek_to, amount)

	def get_size(self):
		return io_utils.get_real_size(self.path, self.compressed_entry)

def make_linux_multiple_command_line(command_list, quote=True):
	#FIXME hack hack hack hack hack hack heck move this to launchers base_make_desktop somehow
	shell_commands = [' '.join(shlex.quote(arg) if quote else arg for arg in command) for command in command_list]
	exe_name = 'sh'
	exe_args = ['-c', ' && '.join(shell_commands)]
	return exe_name, exe_args

class Game():
	def __init__(self, rom, platform, folder):
		self.rom = rom
		self.metadata = metadata.Metadata()
		self.metadata.platform = platform
		self.metadata.categories = []
		self.folder = folder
		self.icon = None
		self.filename_tags = []

		self.emulator = None
		self.exe_name = None
		self.exe_args = None

		self.subroms = None
		self.software_lists = None
		self.exception_reason = None

	def get_exe_name_and_args(self, emulator, system_config):
		return emulator.get_command_line(self, system_config.specific_config)

	def make_launcher(self, system_config):
		is_unsupported_compression = self.rom.is_compressed and (self.rom.original_extension not in self.emulator.supported_compression)

		exe_name = self.exe_name
		exe_args = self.exe_args

		if is_unsupported_compression:
			#Hmm, I hope this works. This should be moved into launchers base_make_desktop too honestly
			set_temp_folder_cmd = ['temp_extract_folder=$(mktemp -d)']
			extract_cmd = ['7z', 'x', '-o"$temp_extract_folder"', shlex.quote(self.rom.path)]
			remove_dir_command = ['rm', '-rf', "$temp_extract_folder"]

			extracted_path = os.path.join('$temp_extract_folder/' + shlex.quote(self.rom.compressed_entry))
			inner_command = [exe_name] + [arg.replace('$<path>', extracted_path) for arg in exe_args]
			all_commands = [set_temp_folder_cmd, extract_cmd, inner_command, remove_dir_command]
			exe_name, exe_args = make_linux_multiple_command_line(all_commands, False)
		elif self.emulator.wrap_in_shell: #Should be if exe_args is a list of lists
			#What happens if this is the case, but compression is also unsupported? I think that doesn't work
			inner_commands = []
			for inner_command in exe_args:
				inner_command = [arg.replace('$<path>', self.rom.path) for arg in inner_command]
				inner_command = [arg.replace('$<exe>', exe_name) for arg in inner_command]
				inner_commands.append(inner_command)
			exe_name, exe_args = make_linux_multiple_command_line(inner_commands)
		else:
			exe_args = [arg.replace('$<path>', self.rom.path) for arg in exe_args]

		launchers.make_launcher(exe_name, exe_args, self.rom.name, self.metadata, 'ROM', self.rom.path, self.icon)

def try_emulator(game, emulator, system_config):
	if game.rom.extension not in emulator.supported_extensions:
		raise NotARomException('Unsupported extension: ' + game.rom.extension)

	return game.get_exe_name_and_args(emulator, system_config)

def process_file(system_config, rom_dir, root, rom):
	game = Game(rom, system_config.name, root)

	if game.rom.extension == 'm3u':
		lines = game.rom.read().decode('utf-8').splitlines()
		filenames = [line if line.startswith('/') else os.path.join(game.folder, line) for line in lines if not line.startswith("#")]
		game.subroms = [Rom(referenced_file) for referenced_file in filenames]

	game.metadata.categories = list(pathlib.Path(root).relative_to(rom_dir).parts)
	if not game.metadata.categories:
		game.metadata.categories = [game.metadata.platform]
	game.filename_tags = common.find_filename_tags.findall(game.rom.name)
	add_metadata(game)

	potential_emulators = system_config.chosen_emulators
	if not potential_emulators:
		return
	exception_reason = None

	if rom.warn_about_multiple_files and main_config.debug:
		print('Warning!', rom.path, 'has more than one file and that may cause unexpected behaviour, as I only look at the first file')

	emulator = None
	emulator_name = None
	exe_name = None
	exe_args = None

	for potential_emulator_name in potential_emulators:
		if potential_emulator_name not in emulator_info.emulators:
			#Should I warn about this? hmm
			continue

		try:
			potential_emulator = emulator_info.emulators[potential_emulator_name]
			exe_and_args = try_emulator(game, potential_emulator, system_config)
			if exe_and_args:
				if main_config.skip_mame_non_working_software and isinstance(potential_emulator, emulator_info.MameSystem):
					if game.metadata.specific_info.get('MAME-Emulation-Status', metadata.EmulationStatus.Unknown) == metadata.EmulationStatus.Broken:
						reason = '{0} not supported'.format(game.metadata.specific_info.get('MAME-Software-Name', ''))
						#game = None #Guess I have to explicitly do that if I want to do things that way
						raise EmulationNotSupportedException(reason)
				emulator = potential_emulator
				emulator_name = potential_emulator_name
				exe_name, exe_args = exe_and_args
				break
		except (EmulationNotSupportedException, NotARomException) as ex:
			exception_reason = ex


	if not emulator:
		if main_config.debug:
			print(rom.path, 'could not be launched by', potential_emulators, 'because', exception_reason)
		return

	game.emulator = emulator
	game.exe_name = exe_name
	game.exe_args = exe_args
	if isinstance(game.emulator, emulator_info.MameSystem):
		game.metadata.emulator_name = 'MAME'
	elif isinstance(game.emulator, emulator_info.MednafenModule):
		game.metadata.emulator_name = 'Mednafen'
	elif isinstance(game.emulator, emulator_info.ViceEmulator):
		game.metadata.emulator_name = 'VICE'
	else:
		game.metadata.emulator_name = emulator_name

	game.make_launcher(system_config)

def parse_m3u(path):
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

used_m3u_filenames = []
def process_emulated_system(system_config):
	for rom_dir in system_config.paths:
		for root, _, files in os.walk(rom_dir):
			if common.starts_with_any(root + os.sep, main_config.ignored_directories):
				continue
			for name in sorted(files, key=sort_m3u_first()):
				path = os.path.join(root, name)

				rom = Rom(path)

				if rom.extension == 'm3u':
					used_m3u_filenames.extend(parse_m3u(path))
				else:
					#Avoid adding part of a multi-disc game if we've already added the whole thing via m3u
					#This is why we have to make sure m3u files are added first, though...  not really a nice way around this, unless we scan the whole directory for files first and then rule out stuff?
					if name in used_m3u_filenames or path in used_m3u_filenames:
						continue

					system = system_info.systems[system_config.name]
					if not system.is_valid_file_type(rom.extension):
						continue

				if not main_config.full_rescan:
					if launchers.has_been_done('ROM', path):
						continue

				process_file(system_config, rom_dir, root, rom)

def process_engine_system(system_config, game_info):
	#Can this be refactored? Looks duplicaty
	for file_dir in system_config.paths:
		if game_info.uses_folders:
			for root, dirs, _ in os.walk(file_dir):
				for d in dirs:
					if not main_config.full_rescan:
						if launchers.has_been_done('Engine game', os.path.join(root, d)):
							continue
					process_engine_file(system_config, file_dir, root, d)
		else:
			for root, _, files in os.walk(file_dir):
				for f in files:
					if not main_config.full_rescan:
						if launchers.has_been_done('Engine game', os.path.join(root, f)):
							continue
					process_engine_file(system_config, file_dir, root, f)

def validate_emulator_choices(system_config, system):
	for chosen_emulator in system_config.chosen_emulators:
		if chosen_emulator not in system.emulators:
			print(chosen_emulator, 'is not valid for', system_config.name)
			return False
	return True

def process_system(system_config):
	time_started = time.perf_counter()

	if system_config.name in system_info.systems:
		if not validate_emulator_choices(system_config, system_info.systems[system_config.name]):
			return
		process_emulated_system(system_config)
	elif system_config.name in system_info.games_with_engines:
		process_engine_system(system_config, system_info.games_with_engines[system_config.name])
	else:
		#Let DOS and Mac fall through, as those are in systems.ini but not handled here
		return

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(system_config.name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def process_systems():
	time_started = time.perf_counter()

	excluded_systems = []
	for arg in sys.argv:
		if arg.startswith('--exclude='):
			excluded_systems.append(arg.partition('=')[2])

	for system_name, system in system_configs.configs.items():
		if system_name in excluded_systems:
			continue
		if not system.is_available:
			continue
		process_system(system)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('All emulated/engined systems finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def main():
	if len(sys.argv) >= 2 and '--rom' in sys.argv:
		arg_index = sys.argv.index('--rom')
		if len(sys.argv) < 4:
			print("BZZZT that's not how you use that")
			return

		rom = sys.argv[arg_index + 1]
		system = sys.argv[arg_index + 2]
		process_file(system_configs.configs[system], os.path.basename(rom), os.path.basename(rom), Rom(rom))
		return

	if len(sys.argv) >= 2 and '--systems' in sys.argv:
		arg_index = sys.argv.index('--systems')
		if len(sys.argv) == 2:
			print('--systems requires an argument')
			return

		system_list = sys.argv[arg_index + 1].split(',')
		for system_name in system_list:
			process_system(system_configs.configs[system_name])
		return

	process_systems()


if __name__ == '__main__':
	main()
