#!/usr/bin/env python3

import datetime
import os
import pathlib
import sys
import tempfile
import time
import traceback
from zlib import crc32

import archives
import cd_read
import common
import io_utils
import launchers
import metadata
from common_types import (EmulationNotSupportedException,
                          ExtensionNotSupportedException, NotARomException)
from config.emulator_config import emulator_configs
from config.main_config import main_config
from config.system_config import system_configs
from info import emulator_info, system_info
from roms_metadata import add_metadata

class RomFile():
	def __init__(self, path):
		self.path = path
		self.warn_about_multiple_files = False
		self.ignore_name = False

		original_name = os.path.basename(path)
		self.original_extension = None
		if os.extsep in original_name:
			name_without_extension, self.original_extension = original_name.rsplit(os.extsep, 1)
			self.original_extension = self.original_extension.lower()
		else:
			name_without_extension = original_name

		self.extension = self.original_extension

		if self.original_extension in archives.compressed_exts:
			self.is_compressed = True

			found_file_already = False
			for entry in archives.compressed_list(self.path):
				if found_file_already:
					self.warn_about_multiple_files = True
					continue
				found_file_already = True

				if os.extsep in entry:
					self.name, self.extension = entry.rsplit(os.extsep, 1)
					self.extension = self.extension.lower()
				else:
					self.name = entry
				self.compressed_entry = entry
		else:
			self.is_compressed = False
			self.compressed_entry = None
			self.name = name_without_extension
			
		self.store_entire_file = False
		self.entire_file = b''
		if self._get_size() < main_config.max_size_for_storing_in_memory:
			self.store_entire_file = True
			self.entire_file = self._read()

		self.crc_for_database = None
		self.header_length_for_crc_calculation = 0

	def _read(self, seek_to=0, amount=-1):
		return io_utils.read_file(self.path, self.compressed_entry, seek_to, amount)

	def read(self, seek_to=0, amount=-1):
		if self.store_entire_file:
			if amount == -1:
				return self.entire_file[seek_to:]
			return self.entire_file[seek_to: seek_to + amount]
		return self._read(seek_to, amount)

	def _get_size(self):
		return io_utils.get_real_size(self.path, self.compressed_entry)

	def get_size(self):
		if self.store_entire_file:
			return len(self.entire_file)
		return self._get_size()

	def _get_crc32(self):
		return io_utils.get_crc32(self.path, self.compressed_entry)

	def get_crc32(self):
		if self.crc_for_database:
			return self.crc_for_database
		
		if self.header_length_for_crc_calculation > 0:
			crc = crc32(self.read(seek_to=self.header_length_for_crc_calculation)) & 0xffffffff
			self.crc_for_database = crc
			return crc

		if self.store_entire_file:
			crc = crc32(self.entire_file) & 0xffffffff
		else:
			crc = self._get_crc32()
		self.crc_for_database = crc
		return crc

class GCZRomFile(RomFile):
	def read(self, seek_to=0, amount=-1):
		return cd_read.read_gcz(self.path, seek_to, amount)

def rom_file(path):
	ext = path.rsplit(os.extsep, 1)[-1]
	if ext.lower() == 'gcz':
		return GCZRomFile(path)
	return RomFile(path)

class RomGame():
	def __init__(self, rom, system_name, system, folder):
		self.rom = rom
		self.metadata = metadata.Metadata()
		self.system_name = self.metadata.platform = system_name
		self.system = system
		self.metadata.categories = []
		self.folder = folder
		self.filename_tags = []

		self.emulator = None
		self.launch_params = None

		self.subroms = None
		self.software_lists = None
		self.exception_reason = None

	def make_launcher(self):
		params = self.launch_params

		if self.rom.is_compressed and (self.rom.original_extension not in self.emulator.supported_compression):
			temp_extraction_folder = os.path.join(tempfile.gettempdir(), 'meow-launcher-' + launchers.make_filename(self.rom.name))

			extracted_path = os.path.join(temp_extraction_folder, self.rom.compressed_entry)
			params = params.replace_path_argument(extracted_path)
			params = params.prepend_command(launchers.LaunchParams('7z', ['x', '-o' + temp_extraction_folder, self.rom.path]))
			params = params.append_command(launchers.LaunchParams('rm', ['-rf', temp_extraction_folder]))
		else:
			params = params.replace_path_argument(self.rom.path)

		name = self.rom.name
		if self.rom.ignore_name and self.metadata.names:
			name = list(self.metadata.names.values())[0]
		launchers.make_launcher(params, name, self.metadata, 'ROM', self.rom.path)

def try_emulator(game, emulator, system_config, emulator_config):
	if game.rom.extension not in emulator.supported_extensions:
		raise ExtensionNotSupportedException('Unsupported extension: ' + game.rom.extension)

	return emulator.get_launch_params(game, system_config.options, emulator_config)

def process_file(system_config, rom_dir, root, rom):
	game = RomGame(rom, system_config.name, system_info.systems[system_config.name], root)

	if game.rom.extension == 'm3u':
		lines = game.rom.read().decode('utf-8').splitlines()
		filenames = [line if line.startswith('/') else os.path.join(game.folder, line) for line in lines if not line.startswith("#")]
		if any([not os.path.isfile(filename) for filename in filenames]):
			if main_config.debug:
				print('M3U file', game.rom.path, 'has broken references!!!!', filenames)
			return
		game.subroms = [rom_file(referenced_file) for referenced_file in filenames]

	potential_emulators = system_config.chosen_emulators
	if not potential_emulators:
		return

	game.metadata.categories = [cat for cat in list(pathlib.Path(root).relative_to(rom_dir).parts) if cat != rom.name]
	game.filename_tags = common.find_filename_tags_at_end(game.rom.name)
	add_metadata(game)
	if not game.metadata.categories:
		game.metadata.categories = [game.metadata.platform]

	exception_reason = None

	if rom.warn_about_multiple_files and main_config.debug:
		print('Warning!', rom.path, 'has more than one file and that may cause unexpected behaviour, as I only look at the first file')

	emulator = None
	emulator_name = None
	launch_params = None

	for potential_emulator_name in potential_emulators:
		if potential_emulator_name not in emulator_info.emulators:
			continue
		try:
			potential_emulator = emulator_info.emulators[potential_emulator_name]
			potential_emulator_config = emulator_configs[potential_emulator_name]
			params = try_emulator(game, potential_emulator, system_config, potential_emulator_config)
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
		return

	game.emulator = emulator
	game.launch_params = launch_params
	if isinstance(game.emulator, emulator_info.MameDriver):
		game.metadata.emulator_name = 'MAME'
	elif isinstance(game.emulator, emulator_info.MednafenModule):
		game.metadata.emulator_name = 'Mednafen'
	elif isinstance(game.emulator, emulator_info.ViceEmulator):
		game.metadata.emulator_name = 'VICE'
	else:
		game.metadata.emulator_name = emulator_name
	game.make_launcher()

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
	time_started = time.perf_counter()

	for emulator_name in system_config.chosen_emulators:
		if emulator_name not in emulator_info.emulators:
			print('Config warning:', emulator_name, 'is not a valid emulator')
		elif emulator_name not in system_info.systems[system_config.name].emulators:
			print('Config warning:', emulator_name, 'is not a valid emulator for', system_config.name)

	for rom_dir in system_config.paths:
		if not os.path.isdir(rom_dir):
			print('Oh no', system_config.name, 'has invalid ROM dir', rom_dir)
			continue
		for root, _, files in os.walk(rom_dir):
			if common.starts_with_any(root + os.sep, main_config.ignored_directories):
				continue
			subfolders = list(pathlib.Path(root).relative_to(rom_dir).parts)
			if subfolders:
				if subfolders[0] in main_config.skipped_subfolder_names:
					continue

			for name in sorted(files, key=sort_m3u_first()):
				path = os.path.join(root, name)

				rom = rom_file(path)

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

				try:
					process_file(system_config, rom_dir, root, rom)
				#pylint: disable=broad-except
				except Exception as ex:
					#It would be annoying to have the whole program crash because there's an error with just one ROM… maybe. This isn't really expected to happen, but I guess there's always the possibility of "oh no the user's hard drive exploded" or some other error that doesn't really mean I need to fix something, either, but then I really do need the traceback for when this does happen
					print('FUCK!!!!', path, ex, type(ex), traceback.extract_tb(ex.__traceback__)[1:])

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(system_config.name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def process_system(system_config):
	if system_config.name in system_info.systems:
		process_emulated_system(system_config)
	else:
		#Let DOS and Mac fall through, as those are in systems.ini but not handled here
		return

def process_systems():
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

def main():
	if len(sys.argv) >= 2 and '--rom' in sys.argv:
		arg_index = sys.argv.index('--rom')
		if len(sys.argv) < 4:
			print("BZZZT that's not how you use that")
			return

		rom = sys.argv[arg_index + 1]
		system = sys.argv[arg_index + 2]
		process_file(system_configs[system], os.path.dirname(rom), os.path.dirname(rom), rom_file(rom))
		return

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


if __name__ == '__main__':
	main()
