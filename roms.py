#!/usr/bin/env python3

import re
import os
import sys
import shlex

import config
import archives
import launchers
import common
import emulator_info
import region_detect
import platform_metadata
import metadata
import system_info
from mame_machines import lookup_system_cpu

debug = '--debug' in sys.argv

year_regex = re.compile(r'\(([x\d]{4})\)')

cpu_overrides = {
	#Usually just look up system_info.systems, but this is here where they aren't in systems or there isn't a MAME driver so we can't get the CPU from there or where MAME gets it wrong because the CPU we want to return isn't considered the main CPU
	"32X": lookup_system_cpu('sega_32x_ntsc'),
	"FDS": lookup_system_cpu('fds'),
	"Game Boy Color": lookup_system_cpu('gbcolor'),
	"Mega CD": lookup_system_cpu('segacd_us'),
}

def add_metadata(game):
	game.metadata.extension = game.rom.extension
	
	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)

	if not game.metadata.main_cpu:
		if game.metadata.platform in cpu_overrides:
			game.metadata.main_cpu = cpu_overrides[game.metadata.platform]
		else:
			for system in system_info.systems:
				if game.metadata.platform == system.name:
					mame_driver = system.mame_driver
					if mame_driver:
						game.metadata.main_cpu = lookup_system_cpu(mame_driver)

	#Only fall back on filename-based detection of stuff if we weren't able to get it any other way. platform_metadata handlers take priority.
	tags = common.find_filename_tags.findall(game.rom.name)
	
	#TODO: Detect regions first, and then languages, and then infer languages from regions if still unspecified
	languages = region_detect.get_languages_from_filename_tags(tags)
	if languages:
		game.metadata.languages = [language.english_name for language in languages]

	for tag in tags:
		if year_regex.match(tag):
			#TODO Ensure only one tag matches
			game.metadata.year = year_regex.match(tag).group(1)

	if not game.metadata.regions:
		regions = region_detect.get_regions_from_filename_tags(tags)
		if regions:
			game.metadata.regions = regions
	if not game.metadata.tv_type:
		if game.metadata.regions:
			game.metadata.tv_type = region_detect.get_tv_system_from_regions(game.metadata.regions)
		else:
			tv_type = region_detect.get_tv_system_from_filename_tags(tags)
			if tv_type:
				game.metadata.tv_type = tv_type
	
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

		launchers.make_launcher(command_line, self.rom.name, self.metadata)

def process_file(system_config, root, name):
	path = os.path.join(root, name)
	
	emulator_name = system_config.chosen_emulator
	if emulator_name not in emulator_info.emulators:
		#TODO: Only warn about this once!
		print(system_config.name, 'is trying to use emulator', emulator_name, 'which does not exist!')
		return
	
	rom = Rom(path)
	game = Game(rom, emulator_info.emulators[emulator_name], system_config.name, root)


	#TODO This looks weird, but is there a better way to do this? (Get subfolders we're in from rom_dir)
	game.metadata.categories = [i for i in root.replace(system_config.rom_dir, '').split('/') if i]
	if not game.metadata.categories:
		game.metadata.categories = [game.metadata.platform]

	if rom.extension not in game.emulator.supported_extensions:
		return

	if rom.warn_about_multiple_files and debug:
		print('Warning!', rom.path, 'has more than one file and that may cause unexpected behaviour, as I only look at the first file')

	add_metadata(game)

	if not game.get_command_line(system_config):
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
		def __init__(self, obj, *args):
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
def process_system(system_config):
	for root, _, files in os.walk(system_config.rom_dir):
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
			
			process_file(system_config, root, name)

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