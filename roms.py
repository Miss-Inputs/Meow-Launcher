import re
import os
import xml.etree.ElementTree as ElementTree
import sys
import shlex

import config
import archives
import launchers
import common
import emulator_info
import region_detect
import platform_metadata

debug = '--debug' in sys.argv

year_regex = re.compile(r'\(([x\d]{4})\)')

def get_metadata_from_filename_tags(tags):
	metadata = {}

	languages = region_detect.get_languages_from_filename_tags(tags)
	if languages:
		#TODO: Should this use native_name instead?
		metadata['Languages'] = [language.english_name for language in languages]
	
	for tag in tags:
		if year_regex.match(tag):
			#TODO Ensure only one tag matches
			metadata['Year'] = year_regex.match(tag).group(1)
	
	return metadata
	
def add_metadata(game):
	game.metadata['Extension'] = game.rom.extension
	
	if game.platform in ('Gamate', 'Epoch Game Pocket Computer', 'Mega Duck', 'Watara Supervision'):
		#Well, you sure won't be seeing anything weird out of these
		game.metadata['Main-Input'] = 'Normal'
	elif game.platform == 'Virtual Boy':
		game.metadata['Main-Input'] = 'Twin Joystick'

	if game.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.platform](game)

	tags = common.find_filename_tags.findall(game.rom.name)
	for k, v in get_metadata_from_filename_tags(tags).items():
		if k not in game.metadata:
			game.metadata[k] = v

	if not game.regions:
		game.regions = region_detect.get_regions_from_filename_tags(tags)	
	if not game.tv_type:
		if game.regions:
			game.tv_type = region_detect.get_tv_system_from_regions(game.regions)
	
	if game.regions:
		game.metadata['Regions'] = [region.name if region else 'None!' for region in game.regions]
	if game.tv_type:
		game.metadata['TV-Type'] = str(game.tv_type)

class Rom():
	def __init__(self, path):
		self.path = path
		self.warn_about_multiple_files = False
		self.original_name = os.path.basename(path)
		name_without_extension, self.original_extension = os.path.splitext(self.original_name)
		if self.original_extension.startswith('.'):
			self.original_extension = self.original_extension[1:]
		self.original_extension = self.original_extension.lower()

		if self.original_extension in archives.COMPRESSED_EXTS:
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

	def read(self):
		return common.read_file(self.path, self.compressed_entry)

	def get_size(self):
		return common.get_real_size(self.path, self.compressed_entry)

class Game():
	def __init__(self, rom, emulator, platform):
		self.rom = rom
		self.platform = platform
		self.emulator = emulator
		self.categories = []
		self.metadata = {}
		self.regions = []
		self.tv_type = None
		self.unrunnable = False

	def get_command_line(self, system_config):
		return self.emulator.get_command_line(self, system_config.other_config)

	def make_launcher(self, system_config):
		base_command_line = self.get_command_line(system_config)

		is_unsupported_compression = self.rom.is_compressed and (self.rom.original_extension not in self.emulator.supported_compression)

		if is_unsupported_compression:
			temp_folder = '/tmp/temporary_rom_extract'
			#TODO: Use mktemp inside shell_command to ensure we always have a nice unique directory
			extracted_path = os.path.join(temp_folder, self.rom.compressed_entry)
			inner_cmd = base_command_line.replace('$<path>', shlex.quote(extracted_path))
			shell_command = shlex.quote('7z x -o{2} {0}; {1}; rm -rf {2}'.format(shlex.quote(self.rom.path), inner_cmd, temp_folder))
			command_line = 'sh -c {0}'.format(shell_command)
		else:
			command_line = base_command_line.replace('$<path>', shlex.quote(self.rom.path))

		launchers.make_launcher(self.platform, command_line, self.rom.name, self.categories, self.metadata)

def process_file(system_config, root, name):
	path = os.path.join(root, name)
	
	emulator_name = system_config.chosen_emulator
	if emulator_name not in emulator_info.emulators:
		#TODO: Only warn about this once!
		print(system_config.name, 'is trying to use emulator', emulator_name, 'which does not exist!')
		return
	
	rom = Rom(path)
	game = Game(rom, emulator_info.emulators[emulator_name], system_config.name)

	#TODO This looks weird, but is there a better way to do this? (Get subfolders we're in from rom_dir)
	game.categories = [i for i in root.replace(system_config.rom_dir, '').split('/') if i]
	if not game.categories:
		game.categories = [system_config.name]
	if rom.extension == 'pbp':
		#EBOOT is not a helpful launcher name
		#TODO: This should be in somewhere like system_info or emulator_info or perhaps get_metadata, ideally
		rom.name = game.categories[-1]
	if system_config.name == 'Wii' and os.path.isfile(os.path.join(root, 'meta.xml')):
		#boot is not a helpful launcher name
		try:
			meta_xml = ElementTree.parse(os.path.join(root, 'meta.xml'))
			rom.name = meta_xml.findtext('name')
		except ElementTree.ParseError as etree_error:
			if debug:
				print('Ah bugger', path, etree_error)
			rom.name = game.categories[-1]
		
	if rom.extension not in game.emulator.supported_extensions:
		return

	if rom.warn_about_multiple_files and debug:
		print('Warning!', rom.path, 'has more than one file and that may cause unexpected behaviour, as I only look at the first file')

	add_metadata(game)

	if game.unrunnable:
		return
			
	if not game.get_command_line(system_config):
		return

	#TODO: Stuff like this should go into somewhere like get_metadata
	if game.platform == 'NES' and rom.extension == 'fds':
		game.platform = 'FDS'
			
	if game.platform == 'Game Boy' and rom.extension == 'gbc':
		game.platform = 'Game Boy Color'
			
	if isinstance(game.emulator, emulator_info.MameSystem):
		game.metadata['Emulator'] = 'MAME'
	elif isinstance(game.emulator, emulator_info.MednafenModule):
		game.metadata['Emulator'] = 'Mednafen'
	else:
		game.metadata['Emulator'] = emulator_name 
			
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
