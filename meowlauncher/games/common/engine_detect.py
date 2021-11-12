import configparser
import io
import json
import os
import zipfile
from typing import Optional, cast

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.metadata import Metadata
from meowlauncher.util.utils import junk_suffixes

from .pc_common_metadata import get_exe_properties


def try_detect_unity(folder: str, metadata: Optional[Metadata]=None) -> bool:
	if os.path.isfile(os.path.join(folder, 'Build', 'UnityLoader.js')):
		#Web version of Unity, there should be some .unityweb files here
		if metadata:
			for file in os.listdir(os.path.join(folder, 'Build')):
				if file.endswith('.json'):
					with open(os.path.join(folder, 'Build', file), encoding='utf-8') as json_file:
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
						with open(appinfo_path, 'rt', encoding='utf-8') as appinfo:
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

def try_detect_ue4(folder: str) -> bool:
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
	project_name: str
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
			break

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

def try_detect_build(folder: str) -> bool:
	files = [f.name.lower() for f in os.scandir(folder) if f.is_file()]
	if 'build.exe' in files and 'bsetup.exe' in files and 'editart.exe' in files:
		return True
	for f in os.scandir(folder):
		if f.name.lower() == 'build' and f.is_dir():
			if try_detect_build(os.path.join(folder, f)):
				return True
	return False

def try_detect_ue3(folder: str) -> bool:
	for f in os.scandir(folder):
		if f.name in {'Game', 'GAME'}:
			continue
		if f.name.endswith('Game') or f.name == 'P13' or (f.name.isupper() and f.name.endswith('GAME')):
			#What the heck is P13 about? Oh well
			if f.is_dir():
				if os.path.isfile(os.path.join(f.path, 'CookedPC', 'Engine.u')):
					return True
				if os.path.isdir(os.path.join(f.path, 'CookedPCConsole')) or os.path.isdir(os.path.join(f.path, 'CookedPCConsole_FR')) or os.path.isdir(os.path.join(f.path, 'CookedPCConsoleFinal')):
					return True
				if os.path.isfile(os.path.join(f.path, 'CookedWiiU', 'Engine.xxx')):
					return True
				if os.path.isfile(os.path.join(f.path, 'COOKEDPS3', 'ENGINE.XXX')): #PS3 filesystems are in yelling case
					return True
	return False

def try_detect_gamemaker(folder: str, metadata: Optional[Metadata]=None) -> bool:
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
			parser.optionxform = str #type: ignore[assignment]
			parser.read(options_ini_path)
			if parser.has_section('Linux'):
				#There is also an Icon and Splash that seem to refer to images that don't exist…
				#What could AppId be for?
				metadata.add_alternate_name(parser['Linux']['DisplayName'], 'Display-Name')
		return True

	return False

def try_detect_source(folder: str) -> bool:
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

def try_detect_adobe_air(folder: str) -> bool:
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

def add_metadata_from_nw_package_json(package_json: dict, metadata: Metadata):
	#main might come in handy
	metadata.descriptions['Package-Description'] = cast(str, package_json.get('description'))
	metadata.add_alternate_name(cast(str, package_json.get('name')), 'Name')
	window = package_json.get('window')
	if window:
		#I need a better way of doing that…
		metadata.specific_info['Icon-Relative-Path'] = window.get('icon')
		metadata.add_alternate_name(window.get('title'), 'Window-Title')

def try_detect_nw(folder: str, metadata: Optional[Metadata]=None) -> bool:
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

def try_detect_cryengine(folder: str) -> Optional[str]:
	cryengine32_path = os.path.join(folder, 'Bin32', 'CrySystem.dll')
	cryengine64_path = os.path.join(folder, 'Bin64', 'CrySystem.dll')
	if os.path.isfile(cryengine64_path):
		cryengine_dll = cryengine64_path
	elif os.path.isfile(cryengine32_path):
		cryengine_dll = cryengine32_path
	else:
		return None

	engine_version = 'CryEngine'
	#If we don't have pefile, this will safely return none and it's not so bad to just say "CryEngine" when it's specifically CryEngine 2
	info = get_exe_properties(cryengine_dll)
	if info:
		if info.get('ProductName') == 'CryEngine2':
			engine_version = 'CryEngine 2'
	return engine_version

def try_and_detect_engine_from_folder(folder: str, metadata: Metadata=None) -> Optional[str]:
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
	if all(f in files for f in ('logdir', 'object', 'picdir', 'viewdir', 'snddir', 'vol.0', 'words.tok')):
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

def detect_engine_recursively(folder: str, metadata: Optional[Metadata]=None) -> Optional[str]:
	engine = try_and_detect_engine_from_folder(folder, metadata)
	if engine:
		return engine

	for subdir in os.scandir(folder):
		if subdir.is_dir():
			engine = try_and_detect_engine_from_folder(subdir.path, metadata)
			if engine:
				return engine

	return None
