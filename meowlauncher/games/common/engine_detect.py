import configparser
import io
import json
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Optional

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.util.utils import junk_suffixes

from .pc_common_metadata import get_exe_properties

if TYPE_CHECKING:
	from meowlauncher.metadata import Metadata

def try_detect_unity(folder: Path, metadata: Optional['Metadata']=None) -> bool:
	if folder.joinpath('Build', 'UnityLoader.js').is_file():
		#Web version of Unity, there should be some .unityweb files here
		if metadata:
			for file in folder.joinpath('Build').iterdir():
				if file.suffix == '.json':
					with file.open('rt', encoding='utf-8') as json_file:
						info_json = json.load(json_file)
						if not metadata.publisher and not metadata.developer:
							company_name = info_json.get('companyName')
							if company_name:
								while junk_suffixes.search(company_name):
									company_name = junk_suffixes.sub('', company_name)
								metadata.developer = metadata.publisher = company_name
						metadata.add_alternate_name(info_json.get('productName'), 'Unity Name')
		return True

	for f in folder.iterdir():
		if not f.is_dir():
			continue

		if f.name.endswith('_Data'):
			#This folder "blah_Data" seems to always go with an executable named "blah", "blah.exe" (on Windows), "blah.x86", "blah.x86_64"
			#boot.config may be interesting? I dunno there's a vr-enabled in there
			if f.joinpath('Managed', 'UnityEngine.dll').is_file() or f.joinpath('Resources', 'unity default resources').is_file():
				if metadata:
					icon_path = f.joinpath('Resources', 'UnityPlayer.png')
					if icon_path.is_file():
						metadata.images['Icon'] = icon_path
					screen_selector_path = f.joinpath('ScreenSelector.png')
					if screen_selector_path.is_file():
						metadata.images['Banner'] = screen_selector_path #kind of a banner? We'll just call it that
					appinfo_path = f.joinpath('app.info')
					try:
						with appinfo_path.open('rt', encoding='utf-8') as appinfo:
							appinfo_lines = appinfo.readlines(2)
							if not metadata.publisher and not metadata.developer:
								company_name = appinfo_lines[0]
								if company_name:
									while junk_suffixes.search(company_name):
										company_name = junk_suffixes.sub('', company_name)
									metadata.developer = metadata.publisher = company_name
							if len(appinfo_lines) > 1:
								metadata.add_alternate_name(appinfo_lines[1], 'Unity Name')
					except FileNotFoundError:
						pass

				return True
	return False

def try_detect_ue4(folder: Path) -> bool:
	#TODO: What's this one supposed to do, it was os.path.basename() before, did I get it mixed up with dirname? Since there is no point calling os.path.isfile() on something relative to the Meow Launcher working directory
	#Search again where I saw this .uproject and see what logic I was trying to do here - this would have done nothing useful before I converted everything to Path, and this is kind of why I did, because string path manipulations can get confusing and evidently I got myself confused
	if folder.joinpath(folder.name + '.uproject').is_file():
		return True

	engine_folder = folder.joinpath('Engine') #I guess this is always there… dunno if anything is _always_ in there though (Binaries + Content?)
	if not engine_folder.is_dir():
		return False
	
	if engine_folder.joinpath('Binaries', 'Linux', 'UE4Game-Linux-Shipping').is_file():
		return True
	if engine_folder.joinpath('Binaries', 'Win64', 'UE4Game-Win64-Shipping.exe').is_file():
		return True

	redist_folder = engine_folder.joinpath('Extras', 'Redist')
	if redist_folder.is_dir():
		for subdir in redist_folder.iterdir():
			if not subdir.is_dir():
				continue
			#subdir will probably be something like "en-us" but that's a language so maybe it's not a good idea to check that, could be who knows what
			#Is it safe though to assume that if the first subdir doesn't have this prereq setup exe in there, that none of the other subdirs in redist_folder will?
			if subdir.joinpath('UE4PrereqSetup_x64.exe').is_file() or subdir.joinpath('UE4PrereqSetup_x86.exe').is_file():
				return True

	#Hmm…
	#Something like Blah/Binaries/Linux/Blah-Linux-Shipping
	project_name: str
	binaries_folder = None
	for subdir in folder.iterdir():
		if subdir.name == 'Engine':
			continue
		if not subdir.is_dir():
			continue
		maybe_binaries_path = subdir.joinpath('Binaries')
		if maybe_binaries_path.is_dir():
			project_name = subdir.name
			binaries_folder = maybe_binaries_path
			break

	if not binaries_folder:
		#Gonna assume probably not then
		return False

	if not folder.joinpath(project_name, 'Content', 'Paks').is_dir():
		return False
	
	if binaries_folder.joinpath('Linux', project_name + '-Linux-Shipping').is_file() or binaries_folder.joinpath('Linux', project_name).is_file():
		return True
	if binaries_folder.joinpath('Win64', project_name + '-Win64-Shipping.exe').is_file():
		return True	
	
	return False

def try_detect_build(folder: Path) -> bool:
	files = {f.name.lower() for f in folder.iterdir() if f.is_file()}
	if 'build.exe' in files and 'bsetup.exe' in files and 'editart.exe' in files:
		return True
	for f in folder.iterdir():
		if f.name.lower() == 'build' and f.is_dir():
			if try_detect_build(f):
				return True
	return False

def try_detect_ue3(folder: Path) -> bool:
	for f in folder.iterdir():
		if f.name in {'Game', 'GAME'}:
			continue
		if f.name.endswith('Game') or f.name == 'P13' or (f.name.isupper() and f.name.endswith('GAME')):
			#What the heck is P13 about? Oh well
			if f.is_dir():
				if f.joinpath('CookedPC', 'Engine.u').is_file():
					return True
				if f.joinpath('CookedPCConsole').is_dir() or f.joinpath('CookedPCConsole_FR').is_dir() or f.joinpath('CookedPCConsoleFinal').is_dir():
					return True
				if f.joinpath('CookedWiiU', 'Engine.xxx').is_file():
					return True
				if f.joinpath('COOKEDPS3', 'ENGINE.XXX').is_file(): #PS3 filesystems are in yelling case
					return True
	return False

def try_detect_gamemaker(folder: Path, metadata: Optional['Metadata']=None) -> bool:
	if folder.joinpath('audiogroup1.dat').is_file() and folder.joinpath('data.win').is_file() and folder.joinpath('options.ini').is_file():
		#Hmmmmmmmmmmmmm probably
		#data.win generally has "FORM" magic? audiogroup1/2/3.dat and options.ini might not always be there but I wanna be more sure if I don't poke around in files
		#TODO: Is icon.png ever there in Windows builds? I feel like we could do better with this
		return True
	
	#Linux ports are a bit different (assets folder seems to always be there? But game.unx is not always in there)
	assets_folder = folder.joinpath('assets')
	if not assets_folder.is_dir():
		return False
	#icon.png might be in here, usually seems to be

	#game.unx seems to also always have FORM magic
	options_ini_path = assets_folder.joinpath('options.ini')
	if (folder.joinpath('game.unx').is_file() or assets_folder.joinpath('game.unx').is_file()) and options_ini_path.is_file():
		if metadata:
			icon_path = assets_folder.joinpath('icon.png')
			if icon_path.is_file():
				metadata.images['Icon'] = icon_path
			parser = configparser.ConfigParser(interpolation=None)
			parser.optionxform = str #type: ignore[assignment]
			parser.read(options_ini_path)
			if parser.has_section('Linux'):
				#There is also an Icon and Splash that seem to refer to images that don't exist…
				#What could AppId be for?
				metadata.add_alternate_name(parser['Linux']['DisplayName'], 'Display Name')
		return True

	return False

def try_detect_source(folder: Path) -> bool:
	have_bin = folder.joinpath('bin').is_dir()
	have_platform = folder.joinpath('platform').is_dir()
	if not (have_bin or have_platform):
		return False

	game_folder = None
	for subdir in folder.iterdir():
		if not subdir.is_dir():
			continue

		#Checking for 'hl2', 'ep1', etc
		if subdir.joinpath('gameinfo.txt').is_file():
			game_folder = subdir
		 	#gameinfo.txt contains metadata but then this would probably only appear on games that are from Steam and we get all the metadata from there anyway
		 	#Also there might be more than one gameinfo.txt inside multiple subdirs in folder (like the Half-Life 2 install dir having all the episodes)
			#I guess we are just only checking that there is one, though
			break
	if have_bin and have_platform and game_folder:
		return True
	
	return False

def try_detect_adobe_air(folder: Path) -> bool:
	if folder.joinpath('Adobe AIR').is_dir():
		return True
	if folder.joinpath('runtimes', 'Adobe AIR').is_dir():
		return True
	
	if folder.joinpath('AIR', 'arh').is_file():
		#"Adobe Redistribution Helper" but I dunno how reliable this detection is, to be honest, but it seems to be used sometimes; games like this seem to instead check for a system-wide AIR installation and try and install that if it's not there
		return True

	metainf_dir = folder.joinpath('META-INF', 'AIR')
	if metainf_dir.is_dir():
		if metainf_dir.joinpath('application.xml').is_file() and metainf_dir.joinpath('hash').is_file():
			return True

	#file named "mimetype" might also exist with content of "application/vnd.adobe.air-application-installer-package+zip"

	return False

def add_metadata_from_nw_package_json(package_json: Mapping, metadata: 'Metadata'):
	#main might come in handy
	package_description = package_json.get('description')
	if package_description:
		metadata.descriptions['Package Description'] = package_description
	package_name = package_json.get('name')
	if package_name:
		metadata.add_alternate_name(package_name, 'Name')
	window = package_json.get('window')
	if window:
		#I need a better way of doing that…
		metadata.specific_info['Icon Relative Path'] = window.get('icon')
		metadata.add_alternate_name(window.get('title'), 'Window Title')

def add_info_from_package_json_file(folder: Path, package_json_path: Path, metadata: 'Metadata'):
	with package_json_path.open('rb') as package_json:
		add_metadata_from_nw_package_json(json.load(package_json), metadata)
	if 'Icon-Relative-Path' in metadata.specific_info:
		icon_path = folder.joinpath(metadata.specific_info.pop('Icon Relative Path'))
		if icon_path.is_file() and 'Icon' not in metadata.images:
			metadata.images['Icon'] = icon_path

def add_info_from_package_json_zip(package_nw_path: Path, metadata: 'Metadata') -> bool:
	try:
		with zipfile.ZipFile(package_nw_path) as package_nw:
			try:
				with package_nw.open('package.json', 'r') as package_json:
					add_metadata_from_nw_package_json(json.load(package_json), metadata)
				if 'Icon-Relative-Path' in metadata.specific_info:
					icon_path = metadata.specific_info.pop('Icon Relative Path')
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
	return True

def try_detect_nw(folder: Path, metadata: Optional['Metadata']=None) -> bool:
	if not folder.joinpath('nw.pak').is_file() and not folder.joinpath('nw_100_percent.pak').is_file() and not folder.joinpath('nw_200_percent.pak').is_file():
		return False
	
	have_package = False
	package_json_path = folder.joinpath('package.json')
	package_nw_path = folder.joinpath('package.nw')
	if package_json_path.is_file():
		have_package = True
		if metadata:
			add_info_from_package_json_file(folder, package_json_path, metadata)
	elif package_nw_path.is_file():
		have_package = True
		if metadata:
			if not add_info_from_package_json_zip(package_nw_path, metadata):
				return False
	
	if not have_package:
		return False

	return True

def try_detect_cryengine(folder: Path) -> Optional[str]:
	cryengine32_path = folder.joinpath('Bin32', 'CrySystem.dll')
	cryengine64_path = folder.joinpath('Bin64', 'CrySystem.dll')
	if cryengine64_path.is_file():
		cryengine_dll = cryengine64_path
	elif cryengine32_path.is_file():
		cryengine_dll = cryengine32_path
	else:
		return None

	engine_version = 'CryEngine'
	#If we don't have pefile, this will safely return none and it's not so bad to just say "CryEngine" when it's specifically CryEngine 2
	info = get_exe_properties(str(cryengine_dll))
	if info:
		if info.get('ProductName') == 'CryEngine2':
			engine_version = 'CryEngine 2'
	return engine_version

def try_detect_engines_from_filenames(folder: Path, files: Iterable[str], subdirs: Iterable[str]) -> Optional[str]:
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
	if 'data.wolf' in files and 'config.exe' in files:
		#TODO: Also might have a Data folder with .wolf files inside it
		#Is GuruguruSMF4.dll always there? Doesn't seem to be part of the thing
		return 'Wolf RPG Editor'
	if 'game.dmanifest' in files and 'game.arcd' in files and 'game.arci' in files:
		return 'Defold'
	if 'libogremain.so' in files or 'ogremain.dll' in files:
		return 'OGRE'

	if folder.joinpath('Build', 'Final', 'DefUnrealEd.ini').is_file():
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if folder.joinpath('Builds', 'Binaries', 'DefUnrealEd.ini').is_file():
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if folder.joinpath('System', 'Engine.u').is_file():
		return 'Unreal Engine 1'
	if folder.joinpath('bin', 'libUnigine_x64.so').is_file() or folder.joinpath('bin', 'libUnigine_x86.so').is_file() or folder.joinpath('bin', 'Unigine_x86.dll').is_file() or folder.joinpath('bin', 'Unigine_x64.dll').is_file():
		return 'Unigine'
	
	return None

def try_and_detect_engine_from_folder(folder: Path, metadata: 'Metadata'=None) -> Optional[str]:
	dir_entries = set(folder.iterdir())
	files = {f.name.lower() for f in dir_entries if f.is_file()}
	subdirs = {f.name.lower() for f in dir_entries if f.is_dir()}

	#Godot = .pck with "GDPC" magic, but that requires poking inside files and I don't wanna do that just yet
	#XNA: Might have a "common redistributables" folder with an installer in it?
	try_detect_engines_from_filenames(folder, files, subdirs)

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

def detect_engine_recursively(folder: Path, metadata: Optional['Metadata']=None) -> Optional[str]:
	engine = try_and_detect_engine_from_folder(folder, metadata)
	if engine:
		return engine

	for subdir in folder.iterdir():
		if subdir.is_dir():
			engine = try_and_detect_engine_from_folder(subdir, metadata)
			if engine:
				return engine

	return None
