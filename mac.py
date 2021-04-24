#!/usr/bin/env python3

from enum import Enum
import os

import pc
from config.main_config import main_config
from config.system_config import system_configs
from info.emulator_info import mac_emulators

try:
	import machfs
	have_machfs = True
except ImportError:
	have_machfs = False

try:
	import macresources
	have_macresources = True
except ImportError:
	have_macresources = False

try:
	from PIL import Image
	have_pillow = True
except ImportError:
	have_pillow = False

mac_config = system_configs.get('Mac')

def get_macos_256_palette():
	#This is stored in the ROM as a clut resource otherwise
	#Yoinked from http://belkadan.com/blog/2018/01/Color-Palette-8/ and converted to make sense for Python
	pal = []
	for i in range(0, 215):
		#Primary colours
		red = (5 - (i // 36)) * 51
		green = (5 - (i // 6 % 6)) * 51
		blue = (5 - (i % 6)) * 51
		pal += [red, green, blue]
	for i in range(215, 255):
		#Shades of red, green, blue, then grayscale
		shades = [s * 17 for s in range(15, -1, -1) if s % 3 != 0]
		shade = int((i - 215) % 10)
		shade_of = int((i - 215) / 10)
		if shade_of == 0:
			colours = [shades[shade], 0, 0]
		elif shade_of == 1:
			colours = [0, shades[shade], 0]
		elif shade_of == 2:
			colours = [0, 0, shades[shade]]
		elif shade_of == 3:
			colours = [shades[shade], shades[shade], shades[shade]]
		pal += colours
		
	#Black is always last
	pal += [0, 0, 0]
	return pal

mac_os_16_palette = [
	#White, yellow, orange, red, magenta, purple, blue, cyan, green, dark green, brown, tan, light gray, medium gray, dark gray, black
	#TODO: Make the colours actually accurate
	255, 255, 255,
	255, 255, 0,
	255, 128, 0,
	255, 0, 0,
	255, 0, 255,
	128, 0, 255,
	0, 0, 255,
	0, 128, 255, #The cyan used in Mac OS does seem to be a bit darker
	0, 255, 0,
	0, 128, 0,
	128, 64, 0,
	128, 64, 64,
	192, 192, 192,
	128, 128, 128,
	64, 64, 64,
	0, 0, 0,
]

class BuildStage(Enum):
	Final = 0x80
	Beta = 0x60
	Alpha = 0x40
	Development = 0x20

class CountryCode(Enum):
	USA = 0
	France = 1
	Britain = 2
	Germany = 3
	Italy = 4
	Netherlands = 5
	BelgiumLuxembourg = 6
	Sweden = 7
	Spain = 8
	Denmark = 9
	Portugal = 10
	Canada = 11
	Norway = 12
	Israel = 13
	Japan = 14
	Australia = 15
	Arabia = 16
	Finland = 17
	FrenchSwiss = 18
	GermanSwiss = 19
	Greece = 20
	Iceland = 21
	Malta = 22
	Cyprus = 23
	Turkey = 24
	Yugoslavia = 25
	#I know there are more than these, ResEdit says so… must have been in a later version though because Inside Macintosh only lists these

def get_path(volume, path):
	#Skip the first part since that's the volume name and the tuple indexing for machfs.Volume doesn't work that way
	return volume[tuple(path.split(':')[1:])]

def does_exist(hfv_path, path):
	if not have_machfs:
		#I guess it might just be safer to assume it's still there
		return True
	v = machfs.Volume()
	try:
		with open(hfv_path, 'rb') as f:
		#Hmm, this could be slurping very large (maybe gigabyte(s)) files all at once
			v.read(f.read())
			try:
				get_path(v, path)
				return True
			except KeyError:
				return False
	except FileNotFoundError:
		return False

class MacApp(pc.App):
	def __init__(self, info):
		super().__init__(info)
		self.hfv_path = info['hfv_path']
		self._file = None #Lazy load it
	
	@property
	def platform_name(self):
		return "Mac"

	def _real_get_file(self):
		v = machfs.Volume()
		try:
			with open(self.hfv_path, 'rb') as f:
			#Hmm, this could be slurping very large (maybe gigabyte(s)) files all at once
				v.read(f.read())
				return get_path(v, self.path)
		except (KeyError, FileNotFoundError):
			return None

	def _get_file(self):
		if not self._file:
			self._file = self._real_get_file()
		return self._file
		
	@property
	def is_valid(self):
		if have_machfs:
			if self._get_file():
				return True
		return does_exist(self.hfv_path, self.path)

	def get_fallback_name(self):
		return self.path.split(':')[-1]

	def _get_resources(self):
		res = {}
		f = self._get_file()
		if not f:
			return res
		for resource in macresources.parse_file(f.rsrc):
			if resource.type not in res: #bytes, should we decode to MacRoman?
				res[resource.type] = {}
			res[resource.type][resource.id] = resource
		return res

	def _get_icon(self):
		resources = self._get_resources()
		mask = None
		icon_bw = None
		icon_16 = None
		icon_256 = None
		
		if -16455 in resources.get(b'ICN#', {}):
			#Get custom icon if we have one
			resource_id = -16455
		else:
			resource_id = 128 #Usually the icon the Finder displays has ID 128, but we will check the BNDL to be sure if it has one
			bndls = resources.get(b'BNDL', {})
			if bndls:
				bndl = list(bndls.values())[0] #Probably has ID 128, and is supposed to, but sometimes doesn't
				for fref in resources.get(b'FREF', {}).values():
					if fref[0:4] == self._get_file().type:
						icon_local_id = int.from_bytes(fref[4:6], 'big')
						bndl_type_count = int.from_bytes(bndl[6:8], 'big') + 1 #Why does it minus 1??? wtf
						type_offset = 8
						for _ in range(0, bndl_type_count):
							type_header = bndl[type_offset: type_offset + 6]
							count_of_ids = int.from_bytes(type_header[4:6], 'big') + 1
							ids = bndl[type_offset + 6: type_offset + 6 + (count_of_ids * 4)] #Array of two integers (local ID, resource ID)
							type_offset += 6 + (count_of_ids * 4)
							if type_header[0:4] == b'ICN#':
								for i in range(0, count_of_ids):
									this_id = ids[i * 4: (i * 4) + 4]
									if int.from_bytes(this_id[0:2], 'big') == icon_local_id:
										resource_id = int.from_bytes(this_id[2:4], 'big')
										break
						break

		icn_resource = resources.get(b'ICN#', {}).get(resource_id)
		if icn_resource:
			if len(icn_resource) != 256:
				if main_config.debug:
					print('Baaa', self.path, 'has a bad ICN## with size', len(icn_resource), 'should be 256')
			else:
				#The icon has backwards colours? I don't know
				icon_bw = Image.frombytes('1', (32, 32), bytes(256 + ~b for b in icn_resource[:128])).convert('RGBA')
				mask = Image.frombytes('1', (32, 32), bytes(icn_resource[128:]))
				icon_bw.putalpha(mask)
		icl4 = resources.get(b'icl4', {}).get(resource_id)
		if icl4:
			if len(icl4) != 512:
				if main_config.debug:
					print('Baaa', self.path, 'has a bad icl8 with size', len(icl4), 'should be 512')
			else:
				#Since this is 4-bit colour we need to unpack 0b1111_1111 to 0b0000_1111 0b0000_1111
				
				image_bytes = bytes(b for bb in [(bbb >> 4, bbb & 16) for bbb in icl4] for b in bb)
				icon_16 = Image.frombytes('P', (32, 32), image_bytes)
				icon_16.putpalette(mac_os_16_palette, 'RGB')
				if mask:
					icon_16 = icon_16.convert('RGBA')
					icon_16.putalpha(mask)
		icl8 = resources.get(b'icl8', {}).get(resource_id)
		if icl8:
			if len(icl8) != 1024:
				if main_config.debug:
					print('Baaa', self.path, 'has a bad icl8 with size', len(icl8), 'should be 1024')
			else:
				icon_256 = Image.frombytes('P', (32, 32), bytes(icl8))
				icon_256.putpalette(get_macos_256_palette(), 'RGB')
				if mask:
					icon_256 = icon_256.convert('RGBA')
					icon_256.putalpha(mask)
		if icon_256:
			return icon_256
		elif icon_16:
			return icon_16
		elif icon_bw:
			return icon_bw
		return None

	def additional_metadata(self):
		self.metadata.specific_info['Executable-Name'] = self.path.split(':')[-1]
		if have_machfs:
			creator = self._get_file().creator.decode('mac-roman', errors='backslashreplace')
			self.metadata.specific_info['Creator-Code'] = creator
			#self.metadata.specific_info['File-Flags'] = self._get_file().flags
			if have_macresources:
				#If you have machfs you do have macresources too, but still
				if have_pillow:
					self.metadata.images['Icon'] = self._get_icon()
			
				verses = self._get_resources().get(b'vers', {})
				vers = verses.get(1, verses.get(128)) #There are other vers resources too but 1 is the main one (I think?), 128 is used in older apps? maybe?
				if vers:
					version, revision = vers[0:2]
					self.metadata.specific_info['Version'] = str(version) + '.' + '.'.join('{0:x}'.format(revision))
					if vers[2] != 0x80:
						try:
							self.metadata.specific_info['Build-Stage'] = BuildStage(vers[2])
						except ValueError:
							pass
						if not self.metadata.categories:
							self.metadata.categories = ['Betas']
					if vers[3]: #"Non-release" / build number
						self.metadata.specific_info['Revision'] = vers[3]
					language_code = int.from_bytes(vers[4:6], 'big') #Or is it a country? I don't know
					try:
						#TODO: Fill out region/language fields using this
						self.metadata.specific_info['Language-Code'] = CountryCode(language_code)
					except ValueError:
						self.metadata.specific_info['Language-Code'] = language_code
					try:
						short_version_length = vers[6] #Pascal style strings
						short_version = vers[7:7+short_version_length].decode('mac-roman')
						long_version_length = vers[7+short_version_length]
						long_version = vers[7+short_version_length + 1:7+short_version_length + 1 + long_version_length].decode('mac-roman')
						#These seem to be used for copyright strings more than actual versions
						self.metadata.descriptions['Short-Version'] = short_version
						self.metadata.descriptions['Long-Version'] = long_version
					except UnicodeDecodeError:
						pass
				
	def get_launcher_id(self):
		return self.hfv_path + '/' + self.path

def no_longer_exists(game_id):
	hfv_path, inner_path = game_id.split('/', 1)
	if not os.path.isfile(hfv_path):
		return True

	return not does_exist(hfv_path, inner_path)

def make_mac_launchers():
	if mac_config:
		if not mac_config.chosen_emulators:
			return
	pc.make_launchers('Mac', MacApp, mac_emulators, mac_config)

# def scan_app(hfv_path, app, game_list, unknown_games, found_games, ambiguous_games):
# 	overall_path = hfv_path + ':' + app['path']

# 	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['creator_code'] == app['creator']]
# 	if not possible_games:
# 		unknown_games.append(overall_path)
# 	elif len(possible_games) == 1:
# 		found_games[overall_path] = possible_games[0][0]
# 	else:
# 		possible_games = [(game_name, game_config) for game_name, game_config in possible_games if game_config['app_name'] == app['name']]
# 		if not possible_games:
# 			unknown_games.append(overall_path)
# 		elif len(possible_games) == 1:
# 			found_games[overall_path] = possible_games[0][0]
# 		else:
# 			ambiguous_games[overall_path] = [game_name for game_name, game_config in possible_games]

# def scan_mac_volume(path, game_list, unknown_games, found_games, ambiguous_games):
# 	for f in hfs.list_hfv(path):
# 		if f['file_type'] != 'APPL':
# 			continue
# 		scan_app(path, f, game_list, unknown_games, found_games, ambiguous_games)

# def scan_mac_volumes():
# 	pc.scan_folders('Mac', mac_ini_path, scan_mac_volume)

if __name__ == '__main__':
	# if '--scan' in sys.argv:
	# 	scan_mac_volumes()
	# else:
	# 	make_mac_launchers()
	make_mac_launchers()
