#!/usr/bin/env python3

import datetime
import io
import os
from enum import Enum

from meowlauncher.config.main_config import main_config
from meowlauncher.config.system_config import system_configs
from meowlauncher.games import pc
from meowlauncher.metadata import Date
from meowlauncher.util.utils import format_byte_size

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
	from PIL import Image, UnidentifiedImageError
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
	FrenchCanada = 11
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
	YugoslaviaCroatia = 25
	HindiIndia = 33
	UrduPakistan = 34
	Lithuania = 41
	Poland = 42
	Hungary = 43
	Estonia = 44
	Latvia = 45
	Lapland = 46
	FaroeIslands = 47
	Iran = 48
	Russia = 49
	Ireland = 50
	Korea = 51
	China = 52
	Taiwan = 53
	Thailand = 54
	Brazil = 71
	#I know there are more than these, ResEdit says so… must have been in a later version though because Inside Macintosh only lists these

mac_epoch = datetime.datetime(1904, 1, 1)

def get_path(volume, path):
	#Skip the first part since that's the volume name and the tuple indexing for machfs.Volume doesn't work that way
	return volume[tuple(path.split(':')[1:])]

def _machfs_read_file(path):
	#Try to avoid having to slurp really big files for each app by keeping it in memory if it's the same disk image
	if _machfs_read_file.current_file_path == path:
		return _machfs_read_file.current_file

	with open(path, 'rb') as f:
		#Hmm, this could be slurping very large (maybe gigabyte(s)) files all at once
		v = machfs.Volume()
		v.read(f.read())
		_machfs_read_file.current_file = v
		_machfs_read_file.current_file_path = path
		return v
_machfs_read_file.current_file = None
_machfs_read_file.current_file_path = None

def does_exist(hfv_path, path):
	if not have_machfs:
		#I guess it might just be safer to assume it's still there
		return True
	try:
		try:
			v = _machfs_read_file(hfv_path)
			get_path(v, path)
			return True
		except KeyError:
			return False
	except FileNotFoundError:
		return False

class MacApp(pc.App):
	def __init__(self, info):
		super().__init__(info)
		self.hfv_path = self.cd_path if self.is_on_cd else info['hfv_path']
		self._file = None #Lazy load it
		
	@property
	def _carbon_path(self):
		if not self.path.endswith('.app'):
			return None
		try:
			v = _machfs_read_file(self.hfv_path)
			if isinstance(get_path(v, self.path), machfs.Folder):
				basename = self.path.split(':')[-1].removesuffix('.app')
				contents = get_path(v, self.path)['Contents']
				if 'MacOSClassic' in contents:
					return self.path + ':Contents:MacOSClassic:' + basename
				if 'MacOS' in contents:
					return self.path + ':Contents:MacOS:' + basename
		except (KeyError, FileNotFoundError):
			pass
		return None

	def _real_get_file(self):
		try:
			v = _machfs_read_file(self.hfv_path)
			carbon_path = self._carbon_path
			if carbon_path:
				return get_path(v, carbon_path)
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

	@property
	def base_folder(self):
		return None

	def get_fallback_name(self):
		if have_machfs:
			if self.path.endswith('.app'):
				return self.path.split(':')[-1].removesuffix('.app')
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
		
		has_custom_icn = -16455 in resources.get(b'ICN#', {})
		has_custom_icns = -16455 in resources.get(b'icns', {})
		not_custom_resource_id = 128
		if (self._get_file().flags & 1024 > 0) and (has_custom_icn or has_custom_icns):
			#"Use custom icon" flag in HFS, but sometimes it lies
			resource_id = -16455
		else:
			resource_id = 128 #Usually the icon the Finder displays has ID 128, but we will check the BNDL to be sure if it has one
			#I think this is controlled by the "Has bundle" HFS flag but I don't know what that is or if it's real and this seems a lot easier and sensibler
			bndls = resources.get(b'BNDL', {})
			if bndls:
				try:
					#Supposed to be BNDL 128, but not always
					bndl = [b for b in bndls.values() if b[0:4] == self._get_file().creator][0]
				except IndexError:
					bndl = list(bndls.values())[0]

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
										not_custom_resource_id = resource_id = int.from_bytes(this_id[2:4], 'big')
										break
						break
		try:
			if resource_id in resources.get(b'icns', {}):
				return Image.open(io.BytesIO(resources[b'icns'][resource_id]))
		except UnidentifiedImageError:
			#I guess sometimes it's janky and not loadable by us, which is strange
			if resource_id == -16455 and not has_custom_icn:
				resource_id = not_custom_resource_id

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
					print('Baaa', self.path, 'has a bad icl4 with size', len(icl4), 'should be 512')
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
		if icon_16:
			return icon_16
		if icon_bw:
			return icon_bw
		return None

	def additional_metadata(self):
		self.metadata.specific_info['Executable-Name'] = self.path.split(':')[-1]
		if have_machfs:
			carbon_path = self._carbon_path
			if carbon_path:
				self.metadata.specific_info['Is-Carbon'] = True
				self.metadata.specific_info['Carbon-Path'] = carbon_path
				self.metadata.specific_info['Architecture'] = 'PPC' #This has to be manually specified because some pretend to be fat binaries?
			creator = self._get_file().creator.decode('mac-roman', errors='backslashreplace')
			self.metadata.specific_info['Creator-Code'] = creator

			#Can also get mddate if wanted
			creation_datetime = mac_epoch + datetime.timedelta(seconds=self._get_file().crdate)
			creation_date = Date(creation_datetime.year, creation_datetime.month, creation_datetime.day, True)
			if creation_date.is_better_than(self.metadata.release_date):
				self.metadata.release_date = creation_date

			#self.metadata.specific_info['File-Flags'] = self._get_file().flags
			if have_macresources:
				#If you have machfs you do have macresources too, but still
				if have_pillow:
					self.metadata.images['Icon'] = self._get_icon()

				sizes = self._get_resources().get(b'SIZE')
				if sizes:
					#Supposed to be -1, 0 and 1 are created when user manually changes preferred/minimum RAM?
					size = sizes.get(-1, sizes.get(0, sizes.get(1)))
					if size:
						#Bit 0: Save screen (obsolete)
						#Bit 1: Accept suspend/resume events
						#Bit 2: Disable option (obsolete)
						#Bit 3: Can background
						#Bit 4: Does activate on FG switch
						#Bit 5: Only background (has no user interface)
						#Bit 6: Get front clicks
						#Bit 7: Accept app died events (debuggers) (the good book says "app launchers use this" and apparently applications use ignoreAppDiedEvents)
						#Bit 9 (bit 1 of second byte): High level event aware
						#Bit 10: Local and remote high level events
						#Bit 11: Stationery aware
						#Bit 12: Use text edit services ("inline services"?)
						if size[0] or size[1]: #If all flags are 0 then this is probably lies
							if size[1] & (1 << 7) == 0: #I guess the bits go that way around I dunno
								self.metadata.specific_info['Not-32-Bit-Clean'] = True
						self.metadata.specific_info['Minimum-RAM'] = format_byte_size(int.from_bytes(size[6:10], 'big'))

				if self._get_file().type == b'APPL' and 'Architecture' not in self.metadata.specific_info:
					#According to https://support.apple.com/kb/TA21606?locale=en_AU this should work
					has_ppc = b'cfrg' in self._get_resources() #Code fragment, ID always 0
					has_68k = b'CODE' in self._get_resources()
					if has_ppc:
						if has_68k:
							self.metadata.specific_info['Architecture'] = 'Fat'
						else:
							self.metadata.specific_info['Architecture'] = 'PPC'
					elif has_68k:
						self.metadata.specific_info['Architecture'] = '68k'
					else:
						self.metadata.specific_info['Architecture'] = 'Unknown' #Maybe this will happen for really old stuff
			
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
						long_version_length = vers[7+short_version_length]
						actual_short_version = None
						actual_long_version = None
						if short_version_length:
							short_version = vers[7:7+short_version_length].decode('mac-roman')
							if short_version.startswith('©'):
								self.metadata.specific_info['Short-Copyright'] = short_version
							else:
								actual_short_version = short_version
						if long_version_length:
							long_version = vers[7+short_version_length + 1:7+short_version_length + 1 + long_version_length].decode('mac-roman')
							copyright_string = None
							if ', ©' in long_version:
								actual_long_version, copyright_string = long_version.split(', ©')
							elif ' ©' in long_version:
								actual_long_version, copyright_string = long_version.split(' ©')
							elif '©' in long_version:
								actual_long_version, copyright_string = long_version.split('©')
							else:
								actual_long_version = long_version
							if copyright_string:
								if copyright_string[:4].isdigit() and (len(copyright_string) == 4 or copyright_string[5] in (',', ' ')):
									copyright_year = Date(year=copyright_string[:4], is_guessed=True)
									if copyright_year.is_better_than(self.metadata.release_date):
										self.metadata.release_date = copyright_year
								self.metadata.specific_info['Copyright'] = '©' + copyright_string
						if actual_short_version:
							self.metadata.specific_info['Version'] = actual_short_version
						if actual_long_version and actual_long_version != actual_short_version:
							self.metadata.specific_info['Long-Version'] = actual_long_version
					except UnicodeDecodeError:
						pass
		
		if 'arch' in self.info:
			#Allow manual override (sometimes apps are jerks and have 68K code just for the sole purpose of showing you a dialog box saying you can't run it on a 68K processor)
			self.metadata.specific_info['Architecture'] = self.info['arch']
				
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
		pc.make_launchers('Mac', MacApp, mac_config)

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
