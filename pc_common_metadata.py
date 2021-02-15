import configparser
import datetime
import io
import json
import os
import re
import struct
import zipfile

from common import junk_suffixes, title_case
from config.main_config import main_config
from data.name_cleanup.capitalized_words_in_names import capitalized_words
from series_detect import chapter_matcher
from metadata import Date

try:
	import pefile
	have_pefile = True
except ModuleNotFoundError:
	have_pefile = False

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False


#Hmm, are other extensions going to work as icons in a file manager
icon_extensions = ('png', 'ico', 'xpm', 'svg')

def get_pe_file_info(pe):
	if not hasattr(pe, 'FileInfo'):
		return None
	for file_info in pe.FileInfo:
		for info in file_info:
			if hasattr(info, 'StringTable'):
				for string_table in info.StringTable:
					d = {k.decode('ascii', errors='ignore'): v.rstrip(b'\0').decode('ascii', errors='ignore') for k, v in string_table.entries.items()}
					if hasattr(pe, 'FILE_HEADER'):
						d['TimeDateStamp'] = datetime.datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp)
					return d
	return None

def get_exe_properties(path):
	if have_pefile:
		try:
			pe = pefile.PE(path, fast_load=True)
			pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])
			try:
				return get_pe_file_info(pe)
			#pylint: disable=broad-except
			except Exception as ex:
				if main_config.debug:
					print('Something weird happened in get_exe_properties', path, ex)
				return None
		except pefile.PEFormatError:
			pass
	return None

def add_metadata_for_raw_exe(path, metadata):
	props = get_exe_properties(path)
	if not props:
		return
	
	#Possible values to expect: https://docs.microsoft.com/en-us/windows/win32/api/winver/nf-winver-verqueryvaluea#remarks

	# if props.get('InternalName'):
	# 	if props.get('InternalName') != props.get('OriginalFilename'):
	# 		print(path, props.get('InternalName'), props.get('OriginalFilename'))

	if not metadata.publisher and not metadata.developer:
		company_name = props.get('CompanyName')
		if company_name:
			while junk_suffixes.search(company_name):
				company_name = junk_suffixes.sub('', company_name)
			metadata.publisher = company_name

	product_name = props.get('ProductName')
	if product_name:
		metadata.add_alternate_name(product_name, 'Name')
	copyright_string = props.get('LegalCopyright')
	if copyright_string:
		metadata.specific_info['Copyright'] = copyright_string
	description = props.get('FileDescription')
	if description and description != product_name:
		metadata.descriptions['File-Description'] = description
	comments = props.get('Comments')
	if comments and comments != product_name:
		metadata.specific_info['File-Comment'] = comments
	trademarks = props.get('LegalTrademarks')
	if trademarks and trademarks != copyright_string:
		metadata.specific_info['Trademarks'] = trademarks
	
	timedatestamp = props.get('TimeDateStamp')
	if timedatestamp:
		build_date = Date(timedatestamp.year, timedatestamp.month, timedatestamp.day)
		metadata.specific_info['BuildDate'] = build_date
		guessed_date = Date(build_date.year, build_date.month, build_date.day, True)
		if guessed_date.is_better_than(metadata.release_date):
			metadata.release_date = guessed_date

def pe_directory_to_dict(directory):
	d = {}
	for entry in directory.entries:
		if hasattr(entry, 'directory'):
			v = pe_directory_to_dict(entry.directory)
		else:
			v = entry
		d[entry.name if entry.name else entry.id] = v
	return d

def get_pe_resources(pe, resource_type):
	if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
		#weirdo has no resources
		return None
	for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
		if entry.id == resource_type:
			return pe_directory_to_dict(entry.directory)
	return None

def get_first_pe_resource(resource_dict):
	for k, v in resource_dict.items():
		if isinstance(v, dict):
			return get_first_pe_resource(v)
		return k, v

def parse_pe_group_icon_directory(data):
	struct_format = '<BBBBHHIH'
	_, _, count = struct.unpack('<HHH', data[:6]) #don't need type I think
	return {entry_id: {'width': width, 'height': height, 'colour_count': colour_count, 'planes': planes, 'bit_count': bit_count, 'bytes_in_res': bytes_in_res}
		for width, height, colour_count, _, planes, bit_count, bytes_in_res, entry_id in struct.iter_unpack(struct_format, data[6:6 + (struct.calcsize(struct_format) * count)])}

def get_icon_from_pe(pe):
	group_icons = get_pe_resources(pe, pefile.RESOURCE_TYPE['RT_GROUP_ICON'])
	if not group_icons:
		return None
	_, first_group_icon = get_first_pe_resource(group_icons)
	
	first_group_icon_data = pe.get_data(first_group_icon.data.struct.OffsetToData, first_group_icon.data.struct.Size)
	header = first_group_icon_data[:6]
	group_icon_entries = parse_pe_group_icon_directory(first_group_icon_data)
	icons_dir = get_pe_resources(pe, pefile.RESOURCE_TYPE['RT_ICON'])
	ico_entry_format = '<BBBBHHII'
	offset = 6 + (len(group_icon_entries) * struct.calcsize(ico_entry_format))
	data = b''
	for k, v in group_icon_entries.items():
		icon_resource = icons_dir.get(k)
		#if not icon_resource:
		#	#Odd, this should not happen
		#	continue
		if isinstance(icon_resource, dict):
			icon_resource = list(icon_resource.values())[0]
		icon_resource_data = pe.get_data(icon_resource.data.struct.OffsetToData, icon_resource.data.struct.Size)
		#This is the raw bytes so we need to make the .ico ourselves
		ico_entry = struct.pack(ico_entry_format, v['width'], v['height'], v['colour_count'], 0, v['planes'], v['bit_count'], v['bytes_in_res'], offset)
		offset += v['bytes_in_res']
		header += ico_entry
		data += icon_resource_data
	ico = header + data
	return Image.open(io.BytesIO(ico))

def get_icon_inside_exe(path):
	if have_pefile:
		try:
			pe = pefile.PE(path, fast_load=True)
			pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])
			try:
				icon = get_icon_from_pe(pe)
			#pylint: disable=broad-except
			except Exception as ex:
				if main_config.debug:
					print('Something weird happened in get_icon_from_pe', path, ex)
				return None
			if icon:
				return icon
		except pefile.PEFormatError:
			pass
	return None

def look_for_icon_next_to_file(path):
	exe_icon = get_icon_inside_exe(path)
	if exe_icon:
		return exe_icon

	parent_folder = os.path.dirname(path)
	for f in os.listdir(parent_folder):
		for ext in icon_extensions:
			if f.lower() == os.path.splitext(os.path.basename(path))[0].lower() + os.path.extsep + ext:
				return os.path.join(parent_folder, f)

	return look_for_icon_in_folder(parent_folder, False)

def look_for_icon_in_folder(folder, look_for_any_ico=True):
	for f in os.listdir(folder):
		for ext in icon_extensions:
			if f.lower() == 'icon' + os.path.extsep + ext:
				return os.path.join(folder, f)
			if f.startswith('goggame-') and f.endswith(icon_extensions):
				return os.path.join(folder, f)
			if f == 'gfw_high.ico':
				#Some kind of older GOG icon? Except not in actual GOG games, just stuff that was distributed elsewhere I guess
				return os.path.join(folder, f)

	if look_for_any_ico:
		#Just get the first ico if we didn't find anything specific
		for f in os.listdir(folder):
			if f.lower().endswith('.ico'):
				return os.path.join(folder, f)
	return None

def try_detect_unity(folder, metadata=None):
	if os.path.isfile(os.path.join(folder, 'Build', 'UnityLoader.js')):
		#Web version of Unity, there should be some .unityweb files here
		if metadata:
			for f in os.listdir(os.path.join(folder, 'Build')):
				if f.endswith('.json'):
					with open(os.path.join(folder, 'Build', f)) as json_file:
						info_json = json.load(json_file)
						if not metadata.publisher and not metadata.developer:
							company_name = info_json.get('companyName')
							if company_name:
								while junk_suffixes.search(company_name):
									company_name = junk_suffixes.sub('', company_name)
								metadata.developer = metadata.publisher = company_name
						metadata.add_alternate_name(info_json.get('productName'), 'Unity-Name')
		return True

	for f in os.scandir(folder):
		if not f.is_dir():
			continue

		if f.name.endswith('_Data'):
			#This folder "blah_Data" seems to always go with an executable named "blah", "blah.exe" (on Windows), "blah.x86", "blah.x86_64"
			#boot.config may be interesting? I dunno there's a vr-enabled in there
			if os.path.isfile(os.path.join(f.path, 'Managed', 'UnityEngine.dll')) or os.path.isfile(os.path.join(f.path, 'Resources', 'unity default resources')):
				if metadata:
					icon_path = os.path.join(f.path, 'Resources', 'UnityPlayer.png')
					if os.path.isfile(icon_path):
						metadata.images['Icon'] = icon_path
					screen_selector_path = os.path.join(f.path, 'ScreenSelector.png')
					if os.path.isfile(screen_selector_path):
						metadata.images['Banner'] = screen_selector_path #kinda?
					appinfo_path = os.path.join(f.path, 'app.info')
					try:
						with open(appinfo_path, 'rt') as appinfo:
							appinfo_lines = appinfo.readlines()
							if not metadata.publisher and not metadata.developer:
								company_name = appinfo_lines[0]
								if company_name:
									while junk_suffixes.search(company_name):
										company_name = junk_suffixes.sub('', company_name)
									metadata.developer = metadata.publisher = company_name
							if len(appinfo_lines) > 1:
								metadata.add_alternate_name(appinfo_lines[1], 'Unity-Name')
					except FileNotFoundError:
						pass

				return True
	return False

def try_detect_ue4(folder):
	if os.path.isfile(os.path.basename(folder) + '.uproject'):
		return True

	engine_folder = os.path.join(folder, 'Engine') #I guess this is always there… dunno if anything is _always_ in there though (Binaries + Content?)
	if not os.path.isdir(engine_folder):
		return False
	
	if os.path.isfile(os.path.join(engine_folder, 'Binaries', 'Linux', 'UE4Game-Linux-Shipping')):
		return True
	if os.path.isfile(os.path.join(engine_folder, 'Binaries', 'Win64', 'UE4Game-Win64-Shipping.exe')):
		return True

	redist_folder = os.path.join(engine_folder, 'Extras', 'Redist')
	if os.path.isdir(redist_folder):
		for subdir in os.scandir(redist_folder):
			if not subdir.is_dir():
				continue
			#subdir will probably be something like "en-us" but that's a language so maybe not
			if os.path.isfile(os.path.join(subdir.path, 'UE4PrereqSetup_x64.exe')) or os.path.isfile(os.path.join(subdir.path, 'UE4PrereqSetup_x86.exe')):
				return True

	#Hmm…
	#Something like Blah/Binaries/Linux/Blah-Linux-Shipping
	project_name = None
	binaries_folder = None
	for subdir in os.scandir(folder):
		if subdir.name == 'Engine':
			continue
		if not subdir.is_dir():
			continue
		maybe_binaries_path = os.path.join(subdir.path, 'Binaries')
		if os.path.isdir(maybe_binaries_path):
			project_name = subdir.name
			binaries_folder = maybe_binaries_path

	if not binaries_folder:
		#Gonna assume probably not then
		return False

	if not os.path.isdir(os.path.join(folder, project_name, 'Content', 'Paks')):
		return False
	
	if os.path.isfile(os.path.join(binaries_folder, 'Linux', project_name + '-Linux-Shipping')) or os.path.isfile(os.path.join(binaries_folder, 'Linux', project_name)):
		#HMMMMMMMMMmmmmmm
		return True
	if os.path.isfile(os.path.join(binaries_folder, 'Win64', project_name + '-Win64-Shipping.exe')):
		return True	
	
	return False

def try_detect_build(folder):
	files = [f.name.lower() for f in os.scandir(folder) if f.is_file()]
	if 'build.exe' in files and 'bsetup.exe' in files and 'editart.exe' in files:
		return True
	for f in os.scandir(folder):
		if f.name.lower() == 'build' and f.is_dir():
			if try_detect_build(os.path.join(folder, f)):
				return True
	return False

def try_detect_ue3(folder):
	for f in os.scandir(folder):
		if (f.name != 'Game' and f.name.endswith('Game')) or f.name == 'P13':
			if f.is_dir():
				if os.path.isfile(os.path.join(f.path, 'CookedPC', 'Engine.u')):
					return True
				if os.path.isdir(os.path.join(f.path, 'CookedPCConsole')) or os.path.isdir(os.path.join(f.path, 'CookedPCConsole_FR')) or os.path.isdir(os.path.join(f.path, 'CookedPCConsoleFinal')):
					return True
	return False

def try_detect_gamemaker(folder, metadata=None):
	if os.path.isfile(os.path.join(folder, 'audiogroup1.dat')) and os.path.isfile(os.path.join(folder, 'data.win')) and os.path.isfile(os.path.join(folder, 'options.ini')):
		#Hmmmmmmmmmmmmm probably
		#data.win generally has "FORM" magic? audiogroup1/2/3.dat and options.ini might not always be there but I wanna be more sure if I don't poke around in files
		return True
	
	#Linux ports are a bit different (assets folder seems to always be there? But game.unx is not always in there)
	assets_folder = os.path.join(folder, 'assets')
	if not os.path.isdir(assets_folder):
		return False
	#icon.png might be in here, usually seems to be

	#game.unx seems to also always have FORM magic
	options_ini_path = os.path.join(assets_folder, 'options.ini')
	if (os.path.isfile(os.path.join(folder, 'game.unx')) or os.path.isfile(os.path.join(assets_folder, 'game.unx'))) and os.path.isfile(options_ini_path):
		if metadata:
			icon_path = os.path.join(assets_folder, 'icon.png')
			if os.path.isfile(icon_path):
				metadata.images['Icon'] = icon_path
			parser = configparser.ConfigParser(interpolation=None)
			parser.optionxform = str
			parser.read(options_ini_path)
			if parser.has_section('Linux'):
				#There is also an Icon and Splash that seem to refer to images that don't exist…
				#What could AppId be for?
				metadata.add_alternate_name(parser['Linux']['DisplayName'], 'Display-Name')
		return True

	return False

def try_detect_source(folder):
	have_bin = os.path.isdir(os.path.join(folder, 'bin'))
	have_platform = os.path.isdir(os.path.join(folder, 'platform'))
	if not (have_bin or have_platform):
		return False

	game_folder = None
	for subdir in os.scandir(folder):
		if not subdir.is_dir():
			continue

		#Checking for 'hl2', 'ep1', etc
		if os.path.isfile(os.path.join(subdir.path, 'gameinfo.txt')):
			game_folder = subdir.path
		 	#gameinfo.txt contains metadata but then this would probably only appear on games that are from Steam and we get all the metadata from there anyway
		 	#Also there might be more than one gameinfo.txt inside multiple subdirs in folder (like the Half-Life 2 install dir having all the episodes)
	if have_bin and have_platform and game_folder:
		return True
	
	return False

def try_detect_adobe_air(folder):
	if os.path.isdir(os.path.join(folder, 'Adobe AIR')):
		return True
	if os.path.isdir(os.path.join(folder, 'runtimes', 'Adobe AIR')):
		return True
	
	if os.path.isfile(os.path.join(folder, 'AIR', 'arh')):
		#"Adobe Redistribution Helper" but I dunno how reliable this detection is, to be honest, but it seems to be used sometimes; games like this seem to instead check for a system-wide AIR installation and try and install that if it's not there
		return True

	metainf_dir = os.path.join(folder, 'META-INF', 'AIR')
	if os.path.isdir(metainf_dir):
		if os.path.isfile(os.path.join(metainf_dir, 'application.xml')) and os.path.isfile(os.path.join(metainf_dir, 'hash')):
			return True

	#file named "mimetype" might also exist with content of "application/vnd.adobe.air-application-installer-package+zip"

	return False

def add_metadata_from_nw_package_json(package_json, metadata):
	#main might come in handy
	metadata.descriptions['Package-Description'] = package_json.get('description')
	metadata.add_alternate_name(package_json.get('name'), 'Name')
	window = package_json.get('window')
	if window:
		#I need a better way of doing that…
		metadata.specific_info['Icon-Relative-Path'] = window.get('icon')
		metadata.add_alternate_name(window.get('title'), 'Window-Title')

def try_detect_nw(folder, metadata=None):
	if not os.path.isfile(os.path.join(folder, 'nw.pak')) and not os.path.isfile(os.path.join(folder, 'nw_100_percent.pak')) and not os.path.isfile(os.path.join(folder, 'nw_200_percent.pak')):
		return False
	
	have_package = False
	package_json_path = os.path.join(folder, 'package.json')
	package_nw_path = os.path.join(folder, 'package.nw')
	if os.path.isfile(package_json_path):
		have_package = True
		if metadata:
			with open(package_json_path, 'rb') as package_json:
				add_metadata_from_nw_package_json(json.load(package_json), metadata)
			if 'Icon-Relative-Path' in metadata.specific_info:
				icon_path = os.path.join(folder, metadata.specific_info.pop('Icon-Relative-Path'))
				if os.path.isfile(icon_path) and 'Icon' not in metadata.images:
					metadata.images['Icon'] = icon_path
	elif os.path.isfile(package_nw_path):
		have_package = True
		if metadata:
			try:
				with zipfile.ZipFile(package_nw_path) as package_nw:
					try:
						with package_nw.open('package.json', 'r') as package_json:
							add_metadata_from_nw_package_json(json.load(package_json), metadata)
						if 'Icon-Relative-Path' in metadata.specific_info:
							icon_path = metadata.specific_info.pop('Icon-Relative-Path')
							if 'Icon' not in metadata.images:
								try:
									with package_nw.open(icon_path, 'r') as icon_data:
										metadata.images['Icon'] = Image.open(io.BytesIO(icon_data.read()))
								except KeyError:
									pass

					except KeyError:
						return False #Maybe
			except zipfile.BadZipFile:
				return False
	
	if not have_package:
		return False

	return True

def try_detect_cryengine(folder):
	cryengine32_path = os.path.join(folder, 'Bin32', 'CrySystem.dll')
	cryengine64_path = os.path.join(folder, 'Bin64', 'CrySystem.dll')
	if os.path.isfile(cryengine64_path):
		cryengine_dll = cryengine64_path
	elif os.path.isfile(cryengine32_path):
		cryengine_dll = cryengine32_path
	else:
		return False

	engine_version = 'CryEngine'
	#If we don't have pefile, this will safely return none and it's not so bad to just say "CryEngine" when it's specifically CryEngine 2
	info = get_exe_properties(cryengine_dll)
	if info:
		if info.get('ProductName') == 'CryEngine2':
			engine_version = 'CryEngine 2'
	return engine_version

def try_and_detect_engine_from_folder(folder, metadata=None):
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]

	#Godot = .pck with "GDPC" magic, but that requires poking inside files and I don't wanna do that just yet
	#XNA: Might have a "common redistributables" folder with an installer in it?

	#These are simple enough to detect with just one line…	
	if 'fna.dll' in files:
		return 'FNA'
	if 'monogame.framework.dll' in files or 'monogame.framework.lite.dll' in files:
		return 'MonoGame'
	if 'renpy' in subdirs and 'game' in subdirs and 'lib' in subdirs:
		return "Ren'Py"
	if 'data.dcp' in files or 'data_sd.dcp' in files or 'data_hd.dcp' in files:
		#Hmm, hopefully there's no false positives here without actually looking inside the file
		return 'Wintermute'
	if 'acsetup.cfg' in files:
		#The better way to do this would be to look for 'Adventure Creator Game File' in dat or exe I guess (and then we can get game title from there), but also the effort way
		return 'Adventure Game Studio'
	if 'rpg_rt.exe' in files:
		#TODO: Get title from RPG_RT.ini section RPG_RT line GameTitle= (this is not always there though…)
		return 'RPG Maker 2000/2003'
	if 'logdir' in files and 'object' in files and 'picdir' in files and 'viewdir' in files and 'snddir' in files and 'vol.0' in files and 'words.tok' in files:
		#Apparently there can be .wag files?
		return 'AGI' #v2
	if ('visplayer' in files and any(f.endswith('.vis') for f in files)) or ('data.vis' in files): #.vis magic is "VIS3"?
		return 'Visionaire Studio'
	if any(f.endswith('.rgssad') for f in files):
		return 'RPG Maker XP/VX' #If mkxp.conf is there, uses mkxp replacement implementation
	if any(f.endswith('.rvproj2') for f in files):
		return 'RPG Maker VX Ace'
	if 'rgss102j.dll' in files or 'rgss102e.dll' in files:
		return 'RPG Maker XP'
	if any(f.endswith('.cf') for f in files):
		if 'data.xp3' in files and 'plugin' in subdirs:
			return 'KiriKiri'
	if os.path.isfile(os.path.join(folder, 'Build', 'Final', 'DefUnrealEd.ini')):
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if os.path.isfile(os.path.join(folder, 'Builds', 'Binaries', 'DefUnrealEd.ini')):
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if os.path.isfile(os.path.join(folder, 'System', 'Engine.u')):
		return 'Unreal Engine 1'
	if 'data.wolf' in files and 'config.exe' in files:
		#TODO: Also might have a Data folder with .wolf files inside it
		#Is GuruguruSMF4.dll always there? Doesn't seem to be part of the thing
		return 'Wolf RPG Editor'
	if 'game.dmanifest' in files and 'game.arcd' in files and 'game.arci' in files:
		return 'Defold'
	if 'libogremain.so' in files or 'ogremain.dll' in files:
		return 'OGRE'
	if os.path.isfile(os.path.join(folder, 'bin', 'libUnigine_x64.so')) or os.path.isfile(os.path.join(folder, 'bin', 'libUnigine_x86.so')) or os.path.isfile(os.path.join(folder, 'bin', 'Unigine_x86.dll')) or os.path.isfile(os.path.join(folder, 'bin', 'Unigine_x64.dll')):
		return 'Unigine'

	if try_detect_gamemaker(folder, metadata):
		return 'GameMaker'
	if try_detect_build(folder):
		return 'Build'
	if try_detect_ue3(folder):
		return 'Unreal Engine 3'
	if try_detect_ue4(folder):
		return 'Unreal Engine 4'
	if try_detect_unity(folder, metadata):
		return 'Unity'
	if try_detect_source(folder):
		return 'Source'
	if try_detect_adobe_air(folder):
		return 'Adobe AIR'
	if try_detect_nw(folder, metadata):
		return 'NW.js'
	cryengine_version = try_detect_cryengine(folder)
	if cryengine_version:
		return cryengine_version
	
	return None

def detect_engine_recursively(folder, metadata=None):
	engine = try_and_detect_engine_from_folder(folder, metadata)
	if engine:
		return engine

	for subdir in os.scandir(folder):
		if subdir.is_dir():
			engine = try_and_detect_engine_from_folder(subdir.path, metadata)
			if engine:
				return engine

	return None

def check_for_interesting_things_in_folder(folder, metadata, find_wrappers=False):
	#Let's check for things existing because we can (there's not really any other reason to do this, it's just fun)
	#Not sure if any of these are in lowercase? Or they might be in a different directory
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]
	
	if 'libdiscord-rpc.so' in files or 'discord-rpc.dll' in files:
		metadata.specific_info['Discord-Rich-Presence'] = True

	if find_wrappers:
		#This is only really relevant for Steam etc
		if 'dosbox' in subdirs or any(f.startswith('dosbox') for f in files):
			metadata.specific_info['Wrapper'] = 'DOSBox'

		if any(f.startswith('scummvm_') for f in subdirs) or any(f.startswith('scummvm') for f in files):
			metadata.specific_info['Wrapper'] = 'ScummVM'

		if os.path.isfile(os.path.join(folder, 'support', 'UplayInstaller.exe')):
			metadata.specific_info['Launcher'] = 'uPlay'

fluff_editions = ['GOTY', 'Game of the Year', 'Definitive', 'Enhanced', 'Special', 'Ultimate', 'Premium', 'Gold', 'Extended', 'Super Turbo Championship', 'Digital', 'Megaton', 'Deluxe', 'Masterpiece']
demo_suffixes = ['Demo', 'Playable Teaser']
name_suffixes = demo_suffixes + ['Beta', 'GOTY', "Director's Cut", 'Unstable', 'Complete', 'Complete Collection', "Developer's Cut"] + [e + ' Edition' for e in fluff_editions]
name_suffix_matcher = re.compile(r'(?: | - |: )?(?:The )?(' + '|'.join(name_suffixes) + ')$', re.RegexFlag.IGNORECASE)
def normalize_name_case(name, name_to_test_for_upper=None):
	if not name_to_test_for_upper:
		name_to_test_for_upper = name

	if main_config.normalize_name_case == 1:
		if name_to_test_for_upper.isupper():
			return title_case(name, words_to_ignore_case=capitalized_words)
		return name
	if main_config.normalize_name_case == 2:
		if name_to_test_for_upper.isupper():
			return title_case(name, words_to_ignore_case=capitalized_words)

		#Assume minimum word length of 4 to avoid acronyms, although those should be in capitalized_words I guess
		return re.sub(r"[\w'-]{4,}", lambda match: title_case(match[0], words_to_ignore_case=capitalized_words) if match[0].isupper() else match[0], name)
	if main_config.normalize_name_case == 3:
		return title_case(name, words_to_ignore_case=capitalized_words)
	
	return name

why = re.compile(r' -(?=\w)') #This bothers me
def fix_name(name):
	name = name.replace('™', '')
	name = name.replace('®', '')
	name = name.replace(' : ', ': ') #Oi mate what kinda punctuation is this
	name = name.replace('[diary]', 'diary') #Stop that
	name = name.replace('(VI)', 'VI') #Why is Tomb Raider: The Angel of Darkness like this
	name = why.sub(' - ', name)

	if name.startswith('ARCADE GAME SERIES'):
		#This is slightly subjective as to whether or not one should do this, but I believe it should
		name = name[20:] + ' (ARCADE GAME SERIES)'

	name_to_test_for_upper = chapter_matcher.sub('', name)
	name_to_test_for_upper = name_suffix_matcher.sub('', name_to_test_for_upper)
	name = normalize_name_case(name, name_to_test_for_upper)
		
	#Hmm... this is primarily so series_detect and disambiguate work well, it may be worthwhile putting them back afterwards (put them in some kind of field similar to Filename-Tags but disambiguate always adds them in); depending on how important it is to have "GOTY" or "Definitive Edition" etc in the name if not ambiguous
	name = name_suffix_matcher.sub(r' (\1)', name)
	return name

tool_names = ('settings', 'setup', 'config', 'dedicated server', 'editor')
def is_probably_related_tool(name):
	lower = name.lower()
	return any(tool_name in lower for tool_name in tool_names)

mode_names = ('safe mode', 'play windowed')
def is_probably_different_mode(name):
	lower = name.lower()
	return any(mode_name in lower for mode_name in mode_names)
