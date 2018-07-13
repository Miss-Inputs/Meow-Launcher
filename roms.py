import re
import os
import xml.etree.ElementTree as ElementTree
import sys

import config
import archives
import launchers
import common
import emulator_info

debug = '--debug' in sys.argv

year_regex = re.compile(r'\(([x\d]{4})\)')
def get_metadata_from_filename_tags(tags):
	metadata = {}
	#TODO: Make case insensitive
	#TODO: Refactor mercilessly, could probably use some kind of dict here
	if len(tags) == 1:
		#TODO: Refactor this so that it works if there is more than one tags, but not if there are more than one specifying
		#the region (to avoid confuzzlion)
		#TODO: Multiple languages
		#Not associated with any particular language necessarily:
		#(World) (although that's usually English); (Asia); (Brazil) is just as much English as it is Portugese it seems;
		#(Brazil, Korea); (Japan, Europe); (Japan, Korea) might be Japanese; (Japan, Korea, Asia); (Japan, USA), etc
		
		if tags[0] in ('(USA)', '(Australia)', '(UK)', '(Europe)', '(USA, Europe)', '(USA, Australia)', '(Europe, Australia)'):
			#Europe in theory could be any number of languages, but by itself it's assumed to be in English
			metadata['Languages'] = 'English'
		elif tags[0] == '(Japan)':
			metadata['Languages'] = 'Japanese'
		elif tags[0] == '(Italy)':
			metadata['Languages'] = 'Italian'
		elif tags[0] == '(France)': 
			#Canada sometimes is French, sometimes it is not, that's not consistent across all naming standards which one is
			#implied and which one should be specified
			metadata['Languages'] = 'French'
		elif tags[0] == '(Russia)':
			metadata['Languages'] = 'Russian'
		elif tags[0] == '(Germany)':
			metadata['Languages'] = 'German'
		elif tags[0] == '(China)':
			metadata['Languages'] = 'Chinese'
		elif tags[0] == '(Sweden)':
			metadata['Languages'] = 'Swedish'
		elif tags[0] == '(Spain)':
			metadata['Languages'] = 'Spanish'
		elif tags[0] == '(Netherlands)':
			metadata['Languages'] = 'Dutch'
		elif tags[0] == '(Denmark)':
			metadata['Languages'] = 'Danish'
		elif tags[0] == '(Poland)':
			metadata['Languages'] = 'Polish'
		elif tags[0] == '(Finland)':
			metadata['Languages'] = 'Finnish'
		elif tags[0] == '(Norway)':
			metadata['Languages'] = 'Norwegian'
		elif tags[0] in ('(Brazil)', '(Portugal)'):
			metadata['Languages'] = 'Portugese'
	else:
		if '(En)' in tags or '(en)' in tags:
			metadata['Languages'] = 'English'
		elif '(en-ja)' in tags or '(En,Ja)' in tags:
			metadata['Languages'] = 'English;Japanese'
		elif '(En,Es)' in tags:
			metadata['Languages'] = 'English;Spanish'
		elif '(En,Es,It)' in tags:
			metadata['Languages'] = 'English;Spanish;Italian'
		elif '(En,Es,Pt)' in tags:
			metadata['Languages'] = 'English;Spanish;Portugese'
		elif '(En,Fr)' in tags:
			metadata['Languages'] = 'English;French'
		elif '(En,Fr,De)' in tags:
			metadata['Languages'] = 'English;French;German'
		elif '(En,Fr,De,Es)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish'
		elif '(En,Fr,De,Es,It)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian'
		elif '(En,Fr,De,Es,It,Da)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Danish'
		elif '(En,Fr,De,Es,It,Nl)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch'
		elif '(En,Fr,De,Es,It,Nl,Pl,Ru)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Polish;Russian'
		elif '(En,Fr,De,Es,It,Nl,Pt)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch;Portugese'
		elif '(En,Fr,De,Es,It,Nl,Pt,No,Da,Fi,Ru)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch;Portugese;Norwegian;Danish;Finnish;Russian'
		elif '(En,Fr,De,Es,It,Nl,Pt,Ru)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch;Portugese;Russian'
		elif '(En,Fr,De,Es,It,Nl,Pt,Sv,Da)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch;Portugese;Swedish;Danish'
		elif '(En,Fr,De,Es,It,Nl,Pt,Sv,No,Da)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch;Portugese;Swedish;Norwegian;Danish'
		elif '(En,Fr,De,Es,It,Nl,Pt,Sv,No,Da,Fi)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Dutch;Portugese;Swedish;Norwegian;Danish;Finnish'
		elif '(En,Fr,De,Es,It,Pt)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Portugese'
		elif '(En,Fr,De,Es,It,Sv)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Italian;Swedish'
		elif '(En,Fr,De,Es,Sv)' in tags:
			metadata['Languages'] = 'English;French;German;Spanish;Swedish'
		elif '(En,Fr,De,It)' in tags:
			metadata['Languages'] = 'English;French;German;Italian'
		elif '(En,Fr,De,It,Nl,Sv)' in tags:
			metadata['Languages'] = 'English;French;German;Italian;Dutch;Swedish'
		elif '(En,Fr,De,Nl)' in tags:
			metadata['Languages'] = 'English;French;German;Dutch'
		elif '(En,Fr,Es)' in tags:
			metadata['Languages'] = 'English;French;Spanish'
		elif '(En,Fr,Es,It)' in tags:
			metadata['Languages'] = 'English;French;Spanish;Italian'
		elif '(En,Fr,Es,Nl,Pt)' in tags:
			metadata['Languages'] = 'English;French;Spanish;Dutch;Portugese'
		elif '(En,Fr,Es,Pt)' in tags:
			metadata['Languages'] = 'English;French;Spanish;Portugese'
		elif '(En,Fr,It)' in tags:
			metadata['Languages'] = 'English;French;Italian'
		elif '(En,It)' in tags:
			metadata['Languages'] = 'English;Italian'
		elif '(En,Ja,Fr)' in tags:
			metadata['Languages'] = 'English;Japanese;French'
		elif '(En,Ja,Fr,De)' in tags:
			metadata['Languages'] = 'English;Japanese;French;German'
		elif '(En,Ja,Fr,De,Es)' in tags:
			metadata['Languages'] = 'English;Japanese;French;German;Spanish'
		elif '(En,Ja,Fr,De,Es,It)' in tags:
			metadata['Languages'] = 'English;Japanese;French;German;Spanish;Italian'
		elif '(En,Ja,Fr,De,Es,It,Ko)' in tags:
			metadata['Languages'] = 'English;Japanese;French;German;Spanish;Italian;Korean'
		elif '(En,Ja,Fr,De,Es,It,Zh,Ko)' in tags:
			metadata['Languages'] = 'English;Japanese;French;German;Spanish;Italian;Chinese;Korean'
		elif '(En,Ja,Fr,De,Es,Zh)' in tags:
			metadata['Languages'] = 'English;Japanese;French;German;Spanish;Chinese'
		elif '(En,Nl)' in tags:
			metadata['Languages'] = 'English;Dutch'
		elif '(En,No,Da,Fi)' in tags:
			metadata['Languages'] = 'English;Norwegian;Danish;Finnish'
		elif '(En,Pt)' in tags or '(en-pt)' in tags:
			metadata['Languages'] = 'English;Portugese'
		elif '(En,Sv)' in tags:
			metadata['Languages'] = 'English;Swedish'
		elif '(En,Sv,No,Da,Fi)' in tags:
			metadata['Languages'] = 'English;Swedish;Norwegian;Danish;Finnish'
		elif '(Fr,De)' in tags:
			metadata['Languages'] = 'French;German'
		elif '(Fr,De,Es)' in tags:
			metadata['Languages'] = 'French;German;Spanish'
		elif '(Fr,De,Es,It)' in tags:
			metadata['Languages'] = 'French;German;Spanish;Italian'
		elif '(Fr,De,Nl)' in tags:
			metadata['Languages'] = 'French;German;Dutch'
		elif '(It,Sv)' in tags:
			metadata['Languages'] = 'Italian;Swedish'
		elif '(ja)' in tags or '(Ja)' in tags:
			metadata['Languages'] = 'French;German;Dutch'
			
		for tag in tags:
			if tag.startswith('[tr en') and tag.endswith(']'):
				metadata['Languages'] = 'English'
			if (tag.startswith('[T+En') or tag.startswith('[T-En')) or tag.endswith(']'):
				metadata['Languages'] = 'English'
	
	for tag in tags:
		if year_regex.match(tag):
			#TODO Ensure only one tag matches
			metadata['Year'] = year_regex.match(tag).group(1)
	
	return metadata
	
def get_metadata(emulator_name, rom):
	#TODO: Link this back to process_file in other ways: Could be useful to read a ROM and change the command line (to use
	#a different emulator that supports something not supported in the usual one, etc), for example
	#Metadata used in arcade: main_input, emulation_status, genre, subgenre, nsfw, language, year, author
	#If we can get these from somewhere for non-arcade things: Great!!
	#main_cpu, source_file and family aren't really relevant
	#Gamecube, 3DS, Wii can sorta find the languages (or at least the title/banner stuff) by examining the ROM itself...
	#though as you have .gcz files for the former, that gets a bit involved, actually yeah any of what I'm thinking would
	#be difficult without a solid generic file handling thing, but still
	#Can get these from the ROM/disc/etc itself:
	#	main_input: Megadrive family, Atari 7800 (all through lookup table)
	#		Somewhat Game Boy, GBA (if type from product code = K or R, uses motion controls)
	#	year: Megadrive family (usually; via copyright), FDS, GameCube, Satellaview, homebrew SMS/Game Gear, Atari 5200
	#	(sometimes), Vectrex, ColecoVersion (sometimes), homebrew Wii
	#	author: Homebrew SMS/Game Gear, ColecoVision (in uppercase, sometimes), homebrew Wii
	#		With a giant lookup table: GBA, Game Boy, SNES, Satellaview, Megadrive family, commercial SMS/Game Gear, Virtual
	#		Boy, FDS, Wonderswan, GameCube, 3DS, Wii, DS
	#		Neo Geo Pocket can say if SNK, but nothing specific if not SNK
	#	language: 3DS, DS, GameCube somewhat (can see title languages, though this isn't a complete indication)
	#	nsfw: Sort of; Wii/3DS can do this but only to show that a game is 18+ in a given country etc, but not why it's that
	#	rating and of course different countries can have odd reasons
	#Maybe MAME software list could say something?  If nothing else, it could give us emulation_status (supported=partial,
	#supported=no) where we use MAME for that platform

	metadata = {}
	
	if emulator_name in ('Gamate', 'Epoch Game Pocket Computer', 'Mega Duck', 'Watara Supervision'):
		#Well, you sure won't be seeing anything weird out of these
		metadata['Main-Input'] = 'Normal'
	elif emulator_name == 'Virtual Boy':
		metadata['Main-Input'] = 'Twin Joystick'
	
	tags = common.find_filename_tags.findall(rom.display_name)
	for k, v in get_metadata_from_filename_tags(tags).items():
		if k not in metadata:
			metadata[k] = v
	
	return metadata

class Rom():
	def __init__(self, rom_file):
		self.file = rom_file
		self.categories = []
		self.path = rom_file.path
		self.warn_about_multiple_files = False
		self.extension = rom_file.extension

		if self.extension in archives.COMPRESSED_EXTS:
			self.is_compressed = True

			found_file_already = False
			for entry in archives.compressed_list(self.file.path):
				if found_file_already:
					self.warn_about_multiple_files = True
					continue
				found_file_already = True
				
				self.display_name, self.extension = os.path.splitext(entry)
				if self.extension.startswith('.'):
					self.extension = self.extension[1:]
				self.extension = self.extension.lower()
				self.compressed_entry = entry
		else:
			self.is_compressed = False
			self.compressed_entry = None
			self.display_name = rom_file.name_without_extension



class RomFile():
#TODO: Do I need this class? It's just initialized and then passed straight off to Rom(), could just use original_extension field there
	def __init__(self, path):
		self.path = path
		self.name = os.path.basename(path)
		self.name_without_extension, self.extension = os.path.splitext(self.name)
		if self.extension.startswith('.'):
			self.extension = self.extension[1:]
		self.extension = self.extension.lower()
		
def process_file(system_config, root, name):
	path = os.path.join(root, name)
	
	emulator_name = system_config.chosen_emulator
	if emulator_name not in emulator_info.emulators:
		#TODO: Only warn about this once!
		print(system_config.name, 'is trying to use emulator', emulator_name, 'which does not exist!')
		return

	emulator = emulator_info.emulators[emulator_name]

	rom_file = RomFile(path)
	rom = Rom(rom_file)

	#TODO This looks weird, but is there a better way to do this? (Get subfolders we're in from rom_dir)
	rom.categories = [i for i in root.replace(system_config.rom_dir, '').split('/') if i]
	if not rom.categories:
		rom.categories = [system_config.name]
	if rom.extension == 'pbp':
		#EBOOT is not a helpful launcher name
		#TODO: This should be in somewhere like system_info or emulator_info or perhaps get_metadata, ideally
		rom.display_name = rom.categories[-1]
	if system_config.name == 'Wii' and os.path.isfile(os.path.join(root, 'meta.xml')):
		#boot is not a helpful launcher name
		try:
			meta_xml = ElementTree.parse(os.path.join(root, 'meta.xml'))
			rom.display_name = meta_xml.findtext('name')
		except ElementTree.ParseError as etree_error:
			if debug:
				print('Ah bugger', path, etree_error)
			rom.display_name = rom.categories[-1]
		
	if rom.extension not in emulator.supported_extensions:
		return

	if rom.warn_about_multiple_files and debug:
		print('Warning!', rom.path, 'has more than one file and that may cause unexpected behaviour, as I only look at the first file')

	command_line = emulator.get_command_line(rom, system_config.other_config)
	if command_line is None:
		return
			
	#TODO: Stuff like this should go into somewhere like get_metadata
	platform = system_config.name
	if platform == 'NES' and rom.extension == 'fds':
		platform = 'FDS'
			
	if rom.extension == 'gbc':
		platform = 'Game Boy Color'
			
	metadata = get_metadata(system_config.name, rom)
			
	is_unsupported_compression = rom.is_compressed and (rom.file.extension in emulator.supported_compression)

	if is_unsupported_compression:
		#TODO: Mmmmm don't like this should be refactored
		launchers.make_desktop(platform, command_line, rom.path, rom.display_name, rom.categories, metadata, rom.extension, rom.compressed_entry)
	else:
		launchers.make_desktop(platform, command_line, rom.path, rom.display_name, rom.categories, metadata, rom.extension)

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
