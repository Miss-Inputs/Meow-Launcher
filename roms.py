#!/usr/bin/env python3

import datetime
import os
import pathlib
import sys
import tempfile
import time
from zlib import crc32

import archives
import cd_read
import common
import io_utils
import launchers
import metadata
from common_types import (EmulationNotSupportedException,
                          ExtensionNotSupportedException, NotARomException)
from config import main_config, system_configs
from info import emulator_info, system_info
from roms_metadata import add_metadata

#TODO: Should make this configuragble? Maybe
max_size_for_storing_in_memory = 32 * 1024 * 1024

class RomFile():
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

		self.store_entire_file = False
		self.entire_file = b''
		if self._get_size() < max_size_for_storing_in_memory:
			self.store_entire_file = True
			self.entire_file = self._read()

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
		if self.store_entire_file:
			return crc32(self.entire_file) & 0xffffffff
		return self._get_crc32()

class GCZRomFile(RomFile):
	def read(self, seek_to=0, amount=-1):
		return cd_read.read_gcz(self.path, seek_to, amount)

def rom_file(path):
	_, ext = os.path.splitext(path)
	if ext.lower() == '.gcz':
		return GCZRomFile(path)
	return RomFile(path)

class RomGame():
	def __init__(self, rom, platform, folder):
		self.rom = rom
		self.metadata = metadata.Metadata()
		#Should arguably check is_virtual but oh well
		self.metadata.platform = platform
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
		if self.metadata.override_name:
			#This is just a temporary workaround until I figure out what's the best way to do this
			name = self.metadata.override_name
		launchers.make_launcher(params, name, self.metadata, 'ROM', self.rom.path)

def try_emulator(game, emulator, system_config):
	if game.rom.extension not in emulator.supported_extensions:
		raise ExtensionNotSupportedException('Unsupported extension: ' + game.rom.extension)

	return emulator.get_launch_params(game, system_config.specific_config)

def process_file(system_config, rom_dir, root, rom):
	game = RomGame(rom, system_config.name, root)

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
	game.filename_tags = common.find_filename_tags.findall(game.rom.name)
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
			#Should I warn about this? hmm
			continue

		try:
			potential_emulator = emulator_info.emulators[potential_emulator_name]
			params = try_emulator(game, potential_emulator, system_config)
			if params:
				if main_config.skip_mame_non_working_software and isinstance(potential_emulator, emulator_info.MameDriver):
					if game.metadata.specific_info.get('MAME-Emulation-Status', metadata.EmulationStatus.Unknown) == metadata.EmulationStatus.Broken:
						reason = '{0} not supported'.format(game.metadata.specific_info.get('MAME-Software-Name', ''))
						raise EmulationNotSupportedException(reason)
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

	for rom_dir in system_config.paths:
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
					print('FUCK!!!!', path, type(ex), ex)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(system_config.name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def validate_emulator_choices(system_config, system):
	for chosen_emulator in system_config.chosen_emulators:
		if chosen_emulator not in system.emulators:
			print(chosen_emulator, 'is not valid for', system_config.name)
			return False
	return True

def process_system(system_config):
	if system_config.name in system_info.systems:
		if not validate_emulator_choices(system_config, system_info.systems[system_config.name]):
			return
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
		process_file(system_configs.configs[system], os.path.dirname(rom), os.path.dirname(rom), rom_file(rom))
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
