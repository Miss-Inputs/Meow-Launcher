#!/usr/bin/env python3

import re
import os
import sys
import shlex
import calendar

import config
import archives
import launchers
import common
import region_detect
import platform_metadata
import metadata

from info import system_info, emulator_info
from mame_helpers import lookup_system_cpu, lookup_system_displays

debug = '--debug' in sys.argv

date_regex = re.compile(r'\((?P<year>[x\d]{4})\)|\((?P<year2>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\)|\((?P<day2>\d{2})\.(?P<month2>\d{2})\.(?P<year3>\d{4})\)')
revision_regex = re.compile(r'\(Rev ([A-Z\d]+?)\)')

cpu_overrides = {
	#Usually just look up system_info.systems, but this is here where they aren't in systems or there isn't a MAME driver so we can't get the CPU from there or where MAME gets it wrong because the CPU we want to return isn't considered the main CPU
	"32X": lookup_system_cpu('sega_32x_ntsc'),
	"FDS": lookup_system_cpu('fds'),
	"Game Boy Color": lookup_system_cpu('gbcolor'),
	"Mega CD": lookup_system_cpu('segacd_us'),
	"C64GS": lookup_system_cpu('c64gs'),
	'Satellaview': lookup_system_cpu('snes'),
	'Sufami Turbo': lookup_system_cpu('snes'),
	#TODO: Figure out Benesse Pocket Challenge V2. No MAME driver, would it just be the same CPU and display as Wonderswan?
}

display_overrides = {
	'FDS': lookup_system_displays('fds'),
	'Game Boy Color': lookup_system_displays('gbcolor'),
	'C64GS': lookup_system_displays('c64gs'),	
	'Satellaview': lookup_system_displays('snes'),
	'Sufami Turbo': lookup_system_displays('snes'),
}

def get_year_revision_from_filename_tags(game, tags):
	found_date = False
	found_revision = True
	if not game.metadata.revision:
		found_revision = False
	for tag in tags:
		date_match = date_regex.match(tag)
		revision_match = revision_regex.match(tag)
		if date_match:
			game.metadata.ignored_filename_tags.append(tag)
			if not found_date:
				#Fuck you and your stupid bullshit. If you hate reading this code direct your anger at Python devs and not me
				groupdict = date_match.groupdict()
				if not game.metadata.year:
					if groupdict['year']:
						game.metadata.year = date_match['year']
					elif groupdict['year2']:
						game.metadata.year = date_match['year2']
					elif groupdict['year3']:
						game.metadata.year = date_match['year3']

				if not game.metadata.month:				
					if groupdict['month']:
						try:
							game.metadata.month = calendar.month_name[int(date_match['month'])]
						except (ValueError, IndexError):
							game.metadata.month = date_match['month']
					elif groupdict['month2']:
						try:
							game.metadata.month = calendar.month_name[int(date_match['month2'])]
						except (ValueError, IndexError):
							game.metadata.month = date_match['month2']

				if not game.metadata.day:
					if groupdict['day']:
						game.metadata.day = date_match['day']
					elif groupdict['day2']:
						game.metadata.day = date_match['day2']

				found_date = True
		if revision_match:
			game.metadata.ignored_filename_tags.append(tag)
			if not found_revision:
				game.metadata.revision = revision_match[1]
				found_revision = True

def get_metadata_from_tags(game):
	#Only fall back on filename-based detection of stuff if we weren't able to get it any other way. platform_metadata handlers take priority.
	tags = common.find_filename_tags.findall(game.rom.name)

	get_year_revision_from_filename_tags(game, tags)
	
	if not game.metadata.regions:
		regions = region_detect.get_regions_from_filename_tags(tags, game.metadata.ignored_filename_tags)
		if regions:
			game.metadata.regions = regions

	if not game.metadata.languages:
		languages = region_detect.get_languages_from_filename_tags(tags, game.metadata.ignored_filename_tags)
		if languages:
			game.metadata.languages = languages
		elif game.metadata.regions:
			languages = region_detect.get_languages_from_regions(game.metadata.regions)
			if languages:
				game.metadata.languages = languages
		

	if not game.metadata.tv_type:
		if game.metadata.regions:
			game.metadata.tv_type = region_detect.get_tv_system_from_regions(game.metadata.regions)
		else:
			tv_type = region_detect.get_tv_system_from_filename_tags(tags, game.metadata.ignored_filename_tags)
			if tv_type:
				game.metadata.tv_type = tv_type

def add_device_hardware_metadata(game):
	if not game.metadata.cpu_info:
		cpu = None
		if game.metadata.platform in cpu_overrides:
			cpu = cpu_overrides[game.metadata.platform]			
		else:
			mame_driver = system_info.get_mame_driver_by_system_name(game.metadata.platform)
			if mame_driver:
				cpu = lookup_system_cpu(mame_driver)

		if cpu:
			game.metadata.cpu_info = cpu

	if not game.metadata.screen_info:
		displays = None
		if game.metadata.platform in display_overrides:
			displays = display_overrides[game.metadata.platform]
		else:	
			mame_driver = system_info.get_mame_driver_by_system_name(game.metadata.platform)
			if mame_driver:
				displays = lookup_system_displays(mame_driver)
		if displays:
			game.metadata.screen_info = displays

def add_metadata(game):
	game.metadata.extension = game.rom.extension
	
	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)

	add_device_hardware_metadata(game)
	
	get_metadata_from_tags(game)


def add_engine_metadata(game):
	game.metadata.extension = game.file.extension
	
	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)

class EngineFile():
	def __init__(self, path):
		self.path = path
		self.original_name = os.path.basename(path)
		self.name, self.extension = os.path.splitext(self.original_name)

		if self.extension.startswith('.'):
			self.extension = self.extension[1:]
		self.extension = self.extension.lower()

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
		return self.engine.get_command_line(self, system_config.other_config)

	def make_launcher(self, system_config):
		base_command_line = self.get_command_line(system_config)
		command_line = base_command_line.replace('$<path>', shlex.quote(self.file.path))

		launchers.make_launcher(command_line, self.file.name, self.metadata, {'Full-Path': self.file.path}, self.icon)

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
		self.original_name = os.path.basename(path)
		name_without_extension, self.original_extension = os.path.splitext(self.original_name)
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
		return common.read_file(self.path, self.compressed_entry, seek_to, amount)

	def get_size(self):
		return common.get_real_size(self.path, self.compressed_entry)

class Game():
	def __init__(self, rom, emulator, platform, folder):
		self.rom = rom
		self.emulator = emulator
		self.metadata = metadata.Metadata()
		self.metadata.platform = platform
		self.metadata.categories = []
		self.folder = folder
		self.icon = None

	def get_command_line(self, system_config):
		return self.emulator.get_command_line(self, system_config.other_config)

	def make_launcher(self, system_config):
		base_command_line = self.get_command_line(system_config)

		is_unsupported_compression = self.rom.is_compressed and (self.rom.original_extension not in self.emulator.supported_compression)

		if is_unsupported_compression:
			extracted_path = os.path.join('$temp_extract_folder/' + shlex.quote(self.rom.compressed_entry))
			inner_cmd = base_command_line.replace('$<path>', extracted_path)
			
			set_temp_folder_cmd = 'temp_extract_folder=$(mktemp -d)'
			extract_cmd = '7z x -o"$temp_extract_folder" {0}'.format(shlex.quote(self.rom.path))
			remove_dir_cmd = 'rm -rf "$temp_extract_folder"'
			all_commands = [set_temp_folder_cmd, extract_cmd, inner_cmd, remove_dir_cmd]
			shell_command = shlex.quote(';'.join(all_commands))
			command_line = 'sh -c {0}'.format(shell_command)
		else:
			command_line = base_command_line.replace('$<path>', shlex.quote(self.rom.path))

		if self.emulator.wrap_in_shell and not is_unsupported_compression:
			#Don't need to wrap in sh -c if we've already done that
			command_line = 'sh -c {0}'.format(shlex.quote(command_line))

		launchers.make_launcher(command_line, self.rom.name, self.metadata, {'Full-Path': self.rom.path}, self.icon)

def try_emulator(system_config, emulator, rom_dir, root, name):
	path = os.path.join(root, name)

	rom = Rom(path)
	game = Game(rom, emulator, system_config.name, root)

	#TODO This looks weird, but is there a better way to do this? (Get subfolders we're in from rom_dir)
	game.metadata.categories = [i for i in root.replace(rom_dir, '').split('/') if i]
	if not game.metadata.categories:
		game.metadata.categories = [game.metadata.platform]

	if rom.extension not in game.emulator.supported_extensions:
		return None

	if rom.warn_about_multiple_files and debug:
		print('Warning!', rom.path, 'has more than one file and that may cause unexpected behaviour, as I only look at the first file')

	add_metadata(game)

	if not game.get_command_line(system_config):
		return None

	return game

def process_file(system_config, rom_dir, root, name):
	game = None
	
	emulator_name = None
	potential_emulators = system_config.chosen_emulators
	for potential_emulator in potential_emulators:
		if potential_emulator not in emulator_info.emulators:
			continue
		emulator_name = potential_emulator
		game = try_emulator(system_config, emulator_info.emulators[potential_emulator], rom_dir, root, name)
		if game:
			break

	if not game:
		return

	if isinstance(game.emulator, emulator_info.MameSystem):
		game.metadata.emulator_name = 'MAME'
	elif isinstance(game.emulator, emulator_info.MednafenModule):
		game.metadata.emulator_name = 'Mednafen'
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
			if common.starts_with_any(root + os.sep, config.ignored_directories):
				continue
			for name in sorted(files, key=sort_m3u_first()):
				path = os.path.join(root, name)
				if name.startswith('[BIOS]'):
					continue			
				
				if name.lower().endswith('.m3u'):
					used_m3u_filenames.extend(parse_m3u(path))
				else:
					#Avoid adding part of a multi-disc game if we've already added the whole thing via m3u
					#This is why we have to make sure m3u files are added first, though...  not really a nice way around this, unless we scan the whole directory for files first and then rule out stuff?
					if name in used_m3u_filenames or path in used_m3u_filenames:
						continue
			
				process_file(system_config, rom_dir, root, name)

def process_engine_system(system_config, game_info):
	for file_dir in system_config.paths:
		if game_info.uses_folders:
			for root, dirs, _ in os.walk(file_dir):
				for d in dirs:
					process_engine_file(system_config, file_dir, root, d)
		else:
			for root, _, files in os.walk(file_dir):
				for f in files:
					process_engine_file(system_config, file_dir, root, f)

def process_system(system_config):
	if system_config.name in [system.name for system in system_info.systems]:
		process_emulated_system(system_config)
	elif system_config.name in system_info.games_with_engines:
		process_engine_system(system_config, system_info.games_with_engines[system_config.name])	
	#TODO: Perhaps warn user if system_config.name is not one of these, but also not arcade/DOS/Mac/etc

def process_systems():
	excluded_systems = []
	for arg in sys.argv:
		if arg.startswith('--exclude='):
			excluded_systems.append(arg.partition('=')[2])
	
	for system in config.system_configs:
		if system.name not in excluded_systems:
			process_system(system)

def get_system_config_by_name(name):
	for system in config.system_configs:
		if system.name == name:
			return system
	raise ValueError(name + ' not found')

def main():
	os.makedirs(config.output_folder, exist_ok=True)
	individual_systems = []
	for arg in sys.argv:
		#TODO: May want to use some kind of proper argument handling library. Hmm...
		if arg.startswith('--system='):
			individual_systems.append(arg.partition('=')[2])
		
	if individual_systems:
		for system_name in individual_systems:
			process_system(get_system_config_by_name(system_name))
	else:
		process_systems()


if __name__ == '__main__':
	main()	
