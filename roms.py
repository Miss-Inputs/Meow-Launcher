import re
import os
import xml.etree.ElementTree as ElementTree
import sys

import config
import archives
import launchers
import common

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
		elif tags[0] == '(France)': #Canada sometimes is French, sometimes it is not, that's not consistent across all naming standards which one is
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
	
def get_metadata(emulator_name, path, name, compressed_entry=None):
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
	
	tags = common.find_filename_tags.findall(name)
	for k, v in get_metadata_from_filename_tags(tags).items():
		if k not in metadata:
			metadata[k] = v
	
	return metadata
	
def detect_region_from_filename(name):
	#TODO Make this more robust, and maybe consolidate with get_metadata_from_filename_tags
	tags = ''.join(common.find_filename_tags.findall(name)).lower()
	
	if 'world' in tags or ('ntsc' in tags and 'pal' in tags):
		return 'world'
	elif 'ntsc' in tags or 'usa' in tags or '(us)' in tags or 'japan' in tags:
		return 'ntsc'
	elif 'pal' in tags or 'europe' in tags or 'netherlands' in tags or 'spain' in tags or 'germany' in tags or 'australia' in tags: #Shit, I'm gonna have to put every single European/otherwise PAL country in there.  That's all that I need to put in here so far, though
		return 'pal'
	else:
		return None
		
def get_real_size(path, compressed_entry=None):
	if compressed_entry is None:
		return os.path.getsize(path)
		
	return archives.compressed_getsize(path, compressed_entry)
	
def read_file(path, compressed_entry=None):
	#TODO: Do a thing where we can just read a small part of the file instead of slurping the whole thing (impossible if
	#it's compressed, though)
	if compressed_entry is None:
		with open(path, 'rb') as f:
			return f.read() 
	else:
		return archives.compressed_get(path, compressed_entry)
	
def build_atari7800_command_line(path, compressed_entry=None):
	base_command_line = 'mame -skip_gameinfo %s -cart {0}' 
	rom_data = read_file(path, compressed_entry)
	if rom_data[1:10] != b'ATARI7800':
		if debug:
			print(path, 'has no header and is therefore unsupported')
		return None
	
	region_byte = rom_data[57]
		
	if region_byte == 1:
		return base_command_line % 'a7800p'
	elif region_byte == 0:
		return base_command_line % 'a7800'
	else:
		if debug:
			print('Something is wrong with', path, ', has region byte of', region_byte)
		return None #MAME can't do anything with unheadered ROMs (or stuff with invalid region byte), so these won't be any good to us

def build_vic20_command_line(path, name, compressed_entry=None):
	size = get_real_size(path, compressed_entry)
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		if debug:
			print('Bugger!', path, 'is too big for MAME at the moment, it is', size)
		return None
	
	base_command_line = 'mame %s -skip_gameinfo -ui_active -cart {0}'
	region = detect_region_from_filename(name)
	if region == 'pal':
		return base_command_line % 'vic20p'
	else:
		return base_command_line % 'vic20'
		
def build_a800_command_line(path, name, compressed_entry=None):
	is_left = True
	rom_data = read_file(path, compressed_entry)
	if rom_data[:4] == b'CART':
		cart_type = int.from_bytes(rom_data[4:8], 'big')
		#See also: https://github.com/dmlloyd/atari800/blob/master/DOC/cart.txt,
		#https://github.com/mamedev/mame/blob/master/src/devices/bus/a800/a800_slot.cpp
		if cart_type in (13, 14, 23, 24, 25) or (cart_type >= 33 and cart_type <= 38):
			if debug:
				print(path, 'is actually a XEGS ROM which is not supported by MAME yet, cart type is', cart_type)
			return None
			
		#You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become
		#supported (even if I have to use some other emulator or something to do it)
		if cart_type in (5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61) or (cart_type >= 26 and cart_type <= 32) or (cart_type >= 54 and cart_type <= 56):
			if debug:
				print(path, "won't work as cart type is", cart_type)
			return None

		if cart_type in (4, 6, 7, 16, 19, 20):
			if debug:
				print(path, "is an Atari 5200 ROM ya goose!! It won't work as an Atari 800 ROM as the type is", cart_type)
			return None
			
		if cart_type == 21: #59 goes in the right slot as well, but that's not supported
			if debug:
				print(path, 'goes in right slot')
			is_left = False
	else:
		size = get_real_size(path, compressed_entry)
		#Treat 8KB files as type 1, 16KB as type 2, everything else is unsupported for now
		if size > ((16 * 1024) + 16):
			if debug:
				print(path, 'may actually be a XL/XE/XEGS cartridge, please check it as it has no header and a size of', size)
			return None
	
	if is_left:
		base_command_line = 'mame %s -skip_gameinfo -ui_active -cart1 {0}'
	else:
		base_command_line = 'mame %s -skip_gameinfo -ui_active -cart2 {0}'

	region = detect_region_from_filename(name) #Why do these CCS64 and CART and whatever else thingies never frickin' store the TV type?
	if region == 'pal':
		#Atari 800 should be fine for everything, and I don't feel like the XL/XE series to see in which ways they don't work
		return base_command_line % 'a800p'
	else:
		return base_command_line % 'a800'
	
def build_c64_command_line(path, name, compressed_entry=None):
	#While we're here building a command line, should mention that you have to manually put a joystick in the first
	#joystick port, because by default there's only a joystick in the second port.  Why the fuck is that the default?
	#Most games use the first port (although, just to be annoying, some do indeed use the second...  why????)
	#Anyway, might as well use this "Boostergrip" thingy, or really it's like using the C64GS joystick, because it just
	#gives us two extra buttons for any software that uses it (probably nothing), and the normal fire button works as
	#normal.  _Should_ be fine
	#(Super cool pro tip: Bind F1 to Start)
	base_command_line = 'mame %s -joy1 joybstr -joy2 joybstr -skip_gameinfo -ui_active -cart {0}'
	
	#with open(path, 'rb') as f:
	rom_data = read_file(path, compressed_entry)
	if rom_data[:16] == b'C64 CARTRIDGE   ':
		#Just gonna make sure we're actually dealing with the CCS64 header format thingy first (see:
		#http://unusedino.de/ec64/technical/formats/crt.html)
		#It's okay if it doesn't, though; just means we won't be able to be clever here
		cart_type = int.from_bytes(rom_data[22:24], 'big')
		
		if cart_type == 15: #Commodore C64GS System 3 cart
			#For some reason, these carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
			return base_command_line % 'c64gs'
	
	region = detect_region_from_filename(name)
	#Don't think we really need c64c unless we really want the different SID chip
	if region == 'pal':
		return base_command_line % 'c64p'
	else:
		return base_command_line % 'c64'

def process_file(emulator, root, name):
	path = os.path.join(root, name)
	try:
		name_we, ext = os.path.splitext(name)
		ext = ext[1:].lower()
		categories = [i for i in root.replace(emulator['rom_dir'], '').split('/') if i]
		if not categories:
			categories = [emulator['name']]
		if ext == 'pbp':
			#EBOOT is not a helpful launcher name
			name_we = categories[-1]
		if emulator['name'] == 'Wii' and os.path.isfile(os.path.join(root, 'meta.xml')):
			#boot is not a helpful launcher name
			meta_xml = ElementTree.parse(os.path.join(root, 'meta.xml'))
			name_we = meta_xml.findtext('name')
		
		#TODO: Make these variable names make more sense
		entry = None
		the_entry = None
		if ext in emulator['supported_extensions']:
			is_unsupported_compression = False
			is_compressed = False
			extension = ext
			the_name = name_we
		elif ext in archives.COMPRESSED_EXTS:
			found_file_already = False
			for entry in archives.compressed_list(path):
				if debug:
					if found_file_already:
						print('Warning!', path, 'has more than one file and that may cause problems')
					found_file_already = True
				
				entry_we, entry_ext = os.path.splitext(entry)
				entry_ext = entry_ext[1:]
				if entry_ext in emulator['supported_extensions']:
					if ext in emulator['supported_compression']: 
						is_unsupported_compression = False
						is_compressed = True
						extension = entry_ext
						the_name = entry_we
						the_entry = entry
					else:
						is_unsupported_compression = True
						is_compressed = True
						extension = entry_ext
						the_name = entry_we
						the_entry = entry
				else:
					return
		else:
			return
			
		if emulator['name'] == 'Atari 7800':
			command_line = build_atari7800_command_line(path, the_entry)
		elif emulator['name'] == 'C64':
			command_line = build_c64_command_line(path, the_name, the_entry)
		elif emulator['name'] == 'VIC-20':
			command_line = build_vic20_command_line(path, the_name, the_entry)
		elif emulator['name'] == 'Atari 8-bit':
			command_line = build_a800_command_line(path, the_name, the_entry)
		else:
			command_line = emulator['command_line']
		
		if command_line is None:
			return
			
		platform = emulator['name']
		if platform == 'NES' and extension == 'fds':
			platform = 'FDS'
			
		if extension == 'gbc':
			platform = 'Game Boy Color'
			
		metadata = get_metadata(emulator['name'], path, the_name, the_entry)
			
		if is_unsupported_compression:
			launchers.make_desktop(platform, command_line, path, the_name, categories, metadata, extension, entry)
		else:
			launchers.make_desktop(platform, command_line, path, the_name, categories, metadata, extension)

	except Exception as e:
		print('Fuck stupid bullshit', path, 'fucking', e)

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
def process_emulator(emulator):
	for root, dirs, files in os.walk(emulator['rom_dir']):
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
				#This is why we have to make sure m3u files are added first, though...  not really a nice way around this
				if name in used_m3u_filenames or path in used_m3u_filenames:
					continue
			
			process_file(emulator, root, name)
			
