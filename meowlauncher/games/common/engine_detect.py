import configparser
import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from meowlauncher.util.utils import NoNonsenseConfigParser

from .engine_info import (add_gamemaker_metadata,
                          add_info_from_package_json_file,
                          add_info_from_package_json_zip,
                          add_metadata_for_adobe_air,
                          add_metadata_from_pixel_game_maker_mv_info_json,
                          add_metadata_from_renpy_options,
                          add_piko_mednafen_info, add_unity_metadata,
                          add_unity_web_metadata)
from .pc_common_info import get_exe_properties

if TYPE_CHECKING:
	from meowlauncher.info import GameInfo

def _try_detect_unity(folder: Path, game_info: 'GameInfo | None', executable: Optional['Path']) -> str | None:
	if folder.joinpath('Build', 'UnityLoader.js').is_file():
		#Web version of Unity, there should be some .unityweb files here
		if game_info:
			add_unity_web_metadata(folder, game_info)
		return 'Unity Web'

	unity_data_folder = None
	if executable and executable.suffix != '.sh':
		unity_data_folder_name = executable.stem.removesuffix('_Debug') + '_Data'
		if folder.joinpath(unity_data_folder_name).is_file():
			unity_data_folder = folder / unity_data_folder_name
	else:
		for f in folder.iterdir():
			if not f.is_dir():
				continue

			if f.name.endswith('_Data'):
				#This folder "blah_Data" seems to always go with an executable named "blah", "blah.exe" (on Windows), "blah.x86", "blah.x86_64"
				#boot.config may be interesting? I dunno there's a vr-enabled in there
				if f.joinpath('Managed', 'UnityEngine.dll').is_file() or f.joinpath('Resources', 'unity default resources').is_file():
					unity_data_folder = f

	if unity_data_folder:
		if game_info:
			add_unity_metadata(unity_data_folder, game_info)

		try:
			props = get_exe_properties(folder / 'UnityPlayer.dll')[0]
			if props:
				unity_version = props.get('UnityVersion', props.get('Unity Version'))
				if unity_version:
					return f'Unity ({unity_version})'
		except FileNotFoundError:
			pass
		if executable and executable.suffix.lower() == '.exe':
			exe_path = executable
		else:
			exe_path = folder.joinpath(unity_data_folder.name.removesuffix('_Name') + '.exe')
		if exe_path.is_file():
			props = get_exe_properties(exe_path)[0]
			if props:
				unity_version = props.get('UnityVersion', props.get('Unity Version'))
				if unity_version:
					return f'Unity ({unity_version})'
				
		#Well, that's all well and good on Windows, but on Linux one will probably need to look here
		default_resources_path = unity_data_folder.joinpath('Resources', 'unity default resources')
		if default_resources_path.is_file():
			with default_resources_path.open('rb') as default_resources:
				default_resources.seek(0x30)
				try:
					version_bytes = default_resources.read(10).rstrip(b'\0')
					if not 0x30 < version_bytes[0] < 0x3a:
						raise ValueError('Megan is too lazy to refactor this function with proper flow')
					version = version_bytes.decode('utf-8', 'strict')					
				except ValueError:
					try:
						#Hmm might be over here sometimes
						default_resources.seek(0x14)
						version_bytes = default_resources.read(8).rstrip(b'\0')
						if not 0x30 < version_bytes[0] < 0x3a:
							raise
						version = version_bytes.decode('utf-8', 'strict')
					except ValueError:
						return 'Unity'

				return f'Unity ({version})'
		return 'Unity'

	return None

def _try_detect_ue4(folder: Path, game_info: 'GameInfo | None') -> bool:
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
	
	if binaries_folder.joinpath('Linux', project_name + '-Linux-Shipping').is_file() or binaries_folder.joinpath('Linux', project_name).is_file() or binaries_folder.joinpath('Win64', project_name + '-Win64-Shipping.exe').is_file():
		if game_info:
			game_info.specific_info['Internal Title'] = project_name
		return True
	
	return False

def _try_detect_build(folder: Path) -> bool:
	files = {f.name.lower() for f in folder.iterdir() if f.is_file()}
	if 'build.exe' in files and 'bsetup.exe' in files and 'editart.exe' in files:
		return True
	for f in folder.iterdir():
		if f.name.lower() == 'build' and f.is_dir():
			if _try_detect_build(f):
				return True
	return False

def _try_detect_ue3(folder: Path) -> bool:
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

def _try_detect_gamemaker(folder: Path, game_info: 'GameInfo | None') -> bool:
	possible_data_file_paths = [folder / 'data.win', folder / 'game.unx', folder.joinpath('assets', 'data.win'), folder.joinpath('assets', 'game.unx')]
	for data_file_path in possible_data_file_paths:
		try:
			with data_file_path.open('rb') as f:
				if f.read(4) == b'FORM':
					if game_info:
						add_gamemaker_metadata(folder, game_info)
					return True
		except FileNotFoundError:
			continue

	return False

def _try_detect_source(folder: Path) -> bool:
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

def _try_detect_adobe_air(folder: Path, game_info: 'GameInfo | None') -> bool:
	metainf_dir = folder.joinpath('META-INF', 'AIR')
	if metainf_dir.is_dir():
		application_xml = metainf_dir.joinpath('application.xml')
		if application_xml.is_file() and metainf_dir.joinpath('hash').is_file():
			if game_info:
				add_metadata_for_adobe_air(folder, application_xml, game_info)
			return True
	
	share = folder / 'share'
	if share.is_dir() and _try_detect_adobe_air(folder / 'share', game_info):
		return True

	if folder.joinpath('Adobe AIR').is_dir():
		return True
	if folder.joinpath('runtimes', 'Adobe AIR').is_dir():
		return True
	
	if folder.joinpath('AIR', 'arh').is_file():
		#"Adobe Redistribution Helper" but I dunno how reliable this detection is, to be honest, but it seems to be used sometimes; games like this seem to instead check for a system-wide AIR installation and try and install that if it's not there
		return True
	
	#file named "mimetype" might also exist with content of "application/vnd.adobe.air-application-installer-package+zip"

	return False

def _try_detect_nw(folder: Path, game_info: 'GameInfo | None') -> str | None:
	if not folder.joinpath('nw.pak').is_file() and not folder.joinpath('nw_100_percent.pak').is_file() and not folder.joinpath('nw_200_percent.pak').is_file():
		return None
	
	have_package = False
	package_json_path = folder.joinpath('package.json')
	package_nw_path = folder.joinpath('package.nw')
	if package_json_path.is_file():
		have_package = True
		if game_info:
			add_info_from_package_json_file(folder, package_json_path, game_info)
	elif package_nw_path.is_file():
		subengine = None
		try:
			with zipfile.ZipFile(package_nw_path) as package_nw:
				if 'c2runtime.js' in package_nw.namelist() or 'scripts/c2runtime.js' in package_nw.namelist():
					subengine = 'Construct 2'
				elif 'c3runtime.js' in package_nw.namelist() or 'scripts/c3runtime.js' in package_nw.namelist():
					subengine = 'Construct 3'
		except zipfile.BadZipFile:
			return None

		have_package = True
		if game_info:
			if not add_info_from_package_json_zip(package_nw_path, game_info):
				return None
		if subengine: #If we detected something more specific in there
			return subengine
	
	if not have_package:
		return None

	try:
		with folder.joinpath('www', 'js', 'rpg_core.js').open('rt', encoding='utf-8') as f:
			for line in f:
				line = line.strip()
				if line.startswith('Utils.RPGMAKER_NAME = '):
					rpgmaker_name = line[len('Utils.RPGMAKER_NAME = '):].rstrip(';').strip('"\'')
					return f'RPG Maker {rpgmaker_name}'
	except FileNotFoundError:
		pass
	try:
		with folder.joinpath('js', 'rmmz_core.js').open('rt', encoding='utf-8') as f:
			#Although I guess it's sort of implied to be RPG Maker MZ already by the filename being rmmz… but who knows
			for line in f:
				line = line.strip()
				if line.startswith('Utils.RPGMAKER_NAME = '):
					rpgmaker_name = line[len('Utils.RPGMAKER_NAME = '):].rstrip(';').strip('"')
					return f'RPG Maker {rpgmaker_name}'
	except FileNotFoundError:
		pass

	return 'nw.js'

def _try_detect_rpg_maker_200x(folder: Path, game_info: 'GameInfo | None', executable: Path | None) -> str | None:
	rpg_rt_ini_path = folder / 'RPG_RT.ini' #This should always be here I think?
	if rpg_rt_ini_path.is_file():
		if game_info:
			try:
				rpg_rt_ini = NoNonsenseConfigParser()
				rpg_rt_ini.read(rpg_rt_ini_path)
				game_info.add_alternate_name(rpg_rt_ini['RPG_RT']['GameTitle'], 'Engine Name')
				if 'FullPackageFlag' in rpg_rt_ini['RPG_RT']:
					game_info.specific_info['Uses RTP?'] = rpg_rt_ini['RPG_RT']['FullPackageFlag'] == '0'
			except KeyError:
				pass
			titles_path = folder / 'Title' / 'titles.png' #Sometimes this exists and title.png is a black screen
			if titles_path.is_file():
				game_info.images['Title Screen'] = titles_path
			else:
				title_path = folder / 'Title' / 'title.png'
				if title_path.is_file():
					game_info.images['Title Screen'] = title_path
		
		product_names = {'RPG Maker 2000': '2000', 'RPG Maker 2000 Value!': '2000', 'RPG Maker 2003': '2003'}
		if executable:
			props = get_exe_properties(executable)
			if props[0]:
				product_name = props[0].get('ProductName')
				if product_name in product_names:
					return 'RPG Maker ' + product_names[product_name]
			
		for file in folder.iterdir():
			if file.suffix.lower() == '.r3proj':
				return 'RPG Maker 2003'
			if not executable and file.suffix.lower() == '.exe':
				#Usually RPG_RT.exe but can be renamed (often to Game.exe)
				#There are some with a blank ProductName and a ProductVersion of 1.0.8.0 but I dunno what that corresponds to
				props = get_exe_properties(file)
				if props[0]:
					product_name = props[0].get('ProductName')
					if product_name in product_names:
						return 'RPG Maker ' + product_names[product_name]
					break
			if file.name.lower() == 'ultimate_rt_eb.dll':
				props = get_exe_properties(file)
				if props[0]:
					product_name = props[0].get('ProductName')
					if product_name in product_names:
						return 'RPG Maker ' + product_names[product_name]
					break
		return 'RPG Maker 2000/2003'

	return None

version_tuple_definition = re.compile(r'^version_tuple\s*=\s*\((.+?)\)$')
def _try_detect_renpy(folder: Path, game_info: 'GameInfo | None') -> str | None:
	renpy_folder = folder / 'renpy'
	if renpy_folder.is_dir():
		if game_info:
			game_folder = folder / 'game'
			options = game_folder / 'options.rpy'
			if options.is_file():
				#Not always here, maybe only games that aren't compiled into .rpa
				#There probably would be a way to use the Ren'Py library right there to open the rpa, but that seems like it might be a bit excessive
				add_metadata_from_renpy_options(game_folder, options, game_info)

		init = renpy_folder / '__init__.py'
		#Don't worry we won't actually execute it or anything silly like that… just going to grab a variable
		try:
			with init.open('rt', encoding='utf-8') as f:
				for line in f:
					line = line.strip()
					version_tuple_match = version_tuple_definition.match(line)
					if version_tuple_match:
						version_with_dots = '.'.join(version_tuple_match[1].replace(',', '').split())
						return f'Ren\'Py (v{version_with_dots})'.replace('.vc_version', '')

					if line.startswith('version = ') and '+' not in line:
						rest_of_line = line[len('version = '):].strip('"\'')
						if rest_of_line.startswith('Ren\'Py'):
							return rest_of_line
		except FileNotFoundError:
			return None
		return 'Ren\'Py'
	return None

def _try_detect_godot(folder: Path) -> bool:
	for f in folder.iterdir():
		if f.is_file() and f.suffix.lower() == '.pck':
			with f.open('rb') as pck:
				if pck.read(4) == b'GDPC':
					return True
			break
	return False

def _try_detect_rpg_paper_maker(folder: Path) -> bool:
	#TODO: Use this - just need to make sure, is that a different package.json from nw.js, or should I be merging the two functions
	package_json_path = folder.joinpath('resources', 'app', 'package.json')
	try:
		j = json.loads(package_json_path.read_bytes())
		#This isn't a valid URL but it's what it is, I dunno
		return cast(str, j['homepage']) == 'https://github.com/RPG-Paper-Maker/Game#readme'
	except FileNotFoundError:
		return False

def _try_detect_rpg_maker_xp_vx(folder: Path, game_info: 'GameInfo | None', executable: Path | None) -> str | None:
	engine_versions = {'rgss1': 'RPG Maker XP', 'rgss2': 'RPG Maker VX', 'rgss3': 'RPG Maker VX Ace'}
	mkxp_path = folder / 'mkxp.conf'
	engine = None
	game_stem = None #Usually "Game", also the name of the exe
	if executable:
		if executable.suffix.lower() != '.exe':
			game_stem = executable.stem
		elif not mkxp_path.is_file():
			#This is otherwise a Windows engine, so if the executable is not that, not really possible without a compatibility thing like that
			return None
	else:
		for f in folder.iterdir():
			if not f.is_file():
				continue

			ext = f.suffix.lower()[1:]
			if ext == 'rgssad':
				game_stem = f.stem
				engine = 'RPG Maker XP/VX/Ace'
				#We know we have something… so don't break and potentially find something more specific
			if ext in {'rvproj', 'rgss2a'}:
				game_stem = f.stem
				engine = 'RPG Maker VX'
				break
			if ext in {'rvproj2', 'rgss3a', 'rgss3d'}:
				game_stem = f.stem
				engine = 'RPG Maker VX Ace'
				break

			if ext == 'dll' and f.stem[:5].lower() in engine_versions:
				#The full filename is something like RGSS301.dll for specific builds of each engine
				engine = engine_versions[f.stem[:5].lower()]
				break
	if mkxp_path.is_file() and not engine:
		engine = 'RPG Maker XP/VX/Ace'

	if engine:
		if not game_stem:
			game_stem = 'Game' #Make an assumption; mkxp seems to default to this at least
		game_ini_path = folder / f'{game_stem}.ini'
		if game_ini_path.is_file(): #Should be?
			game_ini = NoNonsenseConfigParser()
			try:
				game_ini.read(game_ini_path)
				game = game_ini['Game']
				library = game['Library'].lower().removeprefix('system\\') #Might not always be in that folder
				#Also note that the DLL doesn't actually have to exist (as is the case with mkxp)
				if library[:5] in engine_versions:
					engine = engine_versions[library[:5]]
				if game_info:
					game_info.add_alternate_name(game['Title'], 'Engine Name')
					#Not sure if Fullscreen=1 implies it starts in fullscreen, or it always is
					if 'Play_Music' in game:
						game_info.specific_info['Has Music?'] = game['Play_Music'] == '1'
					if 'Play_Sound_Effects' in game:
						game_info.specific_info['Has Sound Effects?'] = game['Play_Sound_Effects'] == '1'
					if 'Mouse' in game:
						game_info.specific_info['Uses Mouse?'] = game['Mouse'] == '1'
			except (KeyError, UnicodeDecodeError, configparser.ParsingError):
				pass
			#Sometimes there is a Fullscreen++ section, not sure what it could tell me, whether the game starts in fullscreen or supports it differently or what
		if mkxp_path.is_file():
			engine += ' (mkxp)'
			if game_info:
				for line in mkxp_path.read_text().splitlines():
					if '=' not in line:
						continue
					k, v = line.strip().split('=', 1)
					if k == 'iconPath':
						game_info.images['Icon'] = folder / v

		return engine

	return None

def _try_detect_cryengine(folder: Path) -> str | None:
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
	info = get_exe_properties(cryengine_dll)
	if info[0]:
		if info[0].get('ProductName') == 'CryEngine2':
			engine_version = 'CryEngine 2'
	return engine_version

def _try_detect_jackbox_games(folder: Path, game_info: 'GameInfo | None') -> bool:
	jbg_config_jet_path = folder / 'jbg.config.jet'
	if folder.joinpath('platform.swf').is_file() and jbg_config_jet_path.is_file():
		if game_info:
			jbg_config_jet = json.loads(jbg_config_jet_path.read_text())
			game_name = jbg_config_jet.get('gameName')
			if game_name:
				game_info.specific_info['Internal Title'] = game_name
			#gameShortName (e.g. "q2i"), canPauseOnPressStart, needExitbutton, env ("pc"), uaVersionId (e.g. 0.1.0), isBundle, analyticsApi, pause-inputs, uaAppId (e.g. drawful2? Just uaAppName/gameName but lowercase?) may also be interesting
			build_timestamp = jbg_config_jet.get('buildTimeStamp')
			if build_timestamp:
				try:
					game_info.specific_info['Build Date'] = datetime.fromisoformat(build_timestamp)
				except ValueError:
					pass
			build_version = jbg_config_jet.get('buildVersion')
			if build_version:
				game_info.specific_info['Build Version'] = build_version
			game_info.specific_info['Supports Fullscreen?'] = jbg_config_jet.get('supportsFullScreen', 'true') != 'false'
			#Nothing these are strings representing bools, we're just seeing if they exist before looking at them
			#I don't know if I want to mess with input info just yet, or if I want to give up on that idea anyway
			supports_mouse = jbg_config_jet.get('supportsMouse')
			supports_keyboard = jbg_config_jet.get('supportsKeyboard')
			supports_gamepad_hotplug = jbg_config_jet.get('supportsJoysticksHotplugging')
			if supports_mouse:
				game_info.specific_info['Uses Mouse?'] = supports_mouse == 'true'
			if supports_keyboard:
				game_info.specific_info['Uses Keyboard?'] = supports_keyboard == 'true'
			if supports_gamepad_hotplug:
				game_info.specific_info['Supports Hotplugging Gamepads?'] = supports_gamepad_hotplug != 'false'
		return True
	return False

def _try_detect_piko_mednafen(folder: Path, game_info: 'GameInfo | None') -> str | None:
	"""Piko's fork of Mednafen for emulated rereleases, probably has an actual name, but I don't know/care (also it is not really an engine)"""
	data_path = folder / 'res' / 'data'
	game_path = folder / 'res' / 'game'
	game_cue_path = folder / 'res' / 'game.cue'
	if data_path.is_file() and (game_path.is_file() or game_cue_path.is_file()):
		#Hopefully this should be enough to ensure a lack of false positives
		#Actually, sometimes that's all there is other than back
		if game_info:
			add_piko_mednafen_info(folder, data_path, game_info)
		#Big brain time: Detect what kind of game is being emulated
		if game_cue_path.is_file():
			#Making an assumption here, but I don't think they're brave enough to re-release games for any other disc-based systems yet (other than DOS stuff using DOSBox)
			#mcd1 and mcd2 being present probably is a strong indicator if there is doubt, or find the "Licensed By Sony" etc text in the disc
			return "Piko's Mednafen fork (PlayStation)"
		with game_path.open('rb') as game:
			magic = game.read(25)
			if magic[:4] == b'NES\x1a':
				return "Piko's Mednafen fork (NES)"
			if magic == b'\x78\x54\xA9\xFF\x53\x01\xAD\x00\x10\x29\x40\xF0\x0C\xA9\x90\x53\x04\x4C\x00\x40 NEC ':
				#Not really file magic, but a secret trick to detect Turbografx-16… this is the region protection code, and would not be in the same place for everything and also not present on some carts, so this is a bad idea and shouldn't be relied on
				return "Piko's Mednafen fork (Turbografx-16)"
				
			game.seek(0x100)
			if game.read(4) == b'SEGA':
				return "Piko's Mednafen fork (Mega Drive/Genesis)"
			game.seek(0x7fdc)
			checksum = int.from_bytes(game.read(2), 'little')
			inverse_checksum = int.from_bytes(game.read(2), 'little')
			if (checksum | inverse_checksum) == 0xffff:
				#Hmm there's never a good way to do this
				return "Piko's Mednafen fork (SNES)"
			game.seek(0xffc0)
			checksum = int.from_bytes(game.read(2), 'little')
			inverse_checksum = int.from_bytes(game.read(2), 'little')
			if (checksum | inverse_checksum) == 0xffff:
				return "Piko's Mednafen fork (SNES)"
			game.seek(0x134)
			try:
				#Hmm I guess this isn't the best way to do it
				#file/magic reads the first 4 bytes of the Nintendo logo and compares it directly, but I'm too much of a wuss, but also can't be bothered comparing a checksum, and then that just doesn't seem right anyway
				if game.read(15).decode('ascii').isascii():
					return "Piko's Mednafen fork (Game Boy)"
			except UnicodeDecodeError:
				pass
			game.seek(0xa0)
			try:
				if game.read(18).decode('ascii').isascii():
					if game.read(1) == b'\x96':
						return "Piko's Mednafen fork (GBA)"
			except UnicodeDecodeError:
				pass
			#There's nothing really that can detect Jaguar, though there is only one game (Attack of the Mutant Penguins) released on Steam that I am aware of and it is DOSBox anyway, so if I move this function around to detect this as a wrapper and not an engine properly, it would detect DOSBox first anyway
			
		return "Piko's Mednafen fork"
	return None

def _try_detect_engines_from_filenames(folder: Path) -> str | None:
	dir_entries = set(folder.iterdir())
	files = {f.name.lower() for f in dir_entries if f.is_file()}

	#These are simple enough to detect with just one line…	
	if 'acsetup.cfg' in files:
		#TODO The better way to do this would be to look for 'Adventure Creator Game File' in dat or exe I guess (and then we can get game title from there), but also the effort way
		return 'Adventure Game Studio'
	if all(f in files for f in ('logdir', 'object', 'picdir', 'viewdir', 'snddir', 'words.tok')):
		#Apparently there can be .wag files?
		return 'AGI' #v2/v3 (could determine version by whether vol files are named VOL.* (v2) or *VOL (v3)?)
	if 'game.dmanifest' in files and 'game.arcd' in files and 'game.arci' in files:
		return 'Defold'
	if 'fna.dll' in files:
		return 'FNA'
	if 'data.xp3' in files and any(f.suffix.lower() == '.cf' for f in folder.iterdir()):
		#TODO: Check exe to see if it is KiriKiri Z (ProductName = "TVP(KIRIKIRI) Z core / Scripting Platform for Win32")
		return 'KiriKiri'
	if 'monogame.framework.dll' in files or 'monogame.framework.lite.dll' in files:
		return 'MonoGame'
	if 'libogremain.so' in files or 'ogremain.dll' in files or 'ogremain_x64.dll' in files:
		return 'OGRE'
	if 'sierra.exe' in files and any(f.endswith('.scr') for f in files):
		return 'SCI'
	if ('visplayer' in files and any(f.endswith('.vis') for f in files)) or ('data.vis' in files): #.vis magic is "VIS3"?
		return 'Visionaire Studio'
	if 'data.dcp' in files or 'data_sd.dcp' in files or 'data_hd.dcp' in files:
		#Hmm, hopefully there's no false positives here without actually looking inside the file
		return 'Wintermute'
	if 'data.wolf' in files and 'config.exe' in files:
		#TODO: Also might have a Data folder with .wolf files inside it
		#Is GuruguruSMF4.dll always there? Doesn't seem to be part of the thing
		return 'Wolf RPG Editor'

	if folder.joinpath('Pack', 'data').is_dir() and any(f.suffix.lower() == '.ttarch' for f in folder.joinpath('Pack', 'data').iterdir()):
		return 'Telltale Tool'
	if folder.joinpath('bin', 'libUnigine_x64.so').is_file() or folder.joinpath('bin', 'libUnigine_x86.so').is_file() or folder.joinpath('bin', 'Unigine_x86.dll').is_file() or folder.joinpath('bin', 'Unigine_x64.dll').is_file():
		return 'Unigine'
	if folder.joinpath('System', 'Engine.u').is_file():
		#Also check Editor.u or Core.u if this gets false positives somehow
		return 'Unreal Engine 1'
	if folder.joinpath('Build', 'Final', 'DefUnrealEd.ini').is_file():
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if folder.joinpath('Builds', 'Binaries', 'DefUnrealEd.ini').is_file():
		return 'Unreal Engine 2' #Possibly 2.5 specifically

	if 'alldata.psb.m' in files or folder.joinpath('windata', 'alldata.psb.m').is_file():
		return 'M2Engage'
	
	return None

def try_detect_engine_from_exe_properties(exe_path: Path, game_info: 'GameInfo | None') -> str | None:
	if exe_path.suffix.lower() != '.exe':
		#Since .dll can't be launched, exe would be the only valid extension for this
		return None
	props = get_exe_properties(exe_path)
	if props[0]:
		file_description = props[0].get('FileDescription')
		if file_description == 'Wintermute Engine Runtime':
			return 'Wintermute'
		if file_description == 'Clickteam Fusion Application Runtime':
			return 'Clickteam Fusion'
		if file_description == 'Pixel Game Maker MV player':
			if game_info:
				info_json = exe_path.parent.joinpath('Resources', 'data', 'info.json')
				add_metadata_from_pixel_game_maker_mv_info_json(info_json, game_info)
			return 'Pixel Game Maker MV'
		internal_name = props[0].get('InternalName')
		if internal_name and internal_name.startswith('LuaSTG'):
			return internal_name

	return None

def try_detect_engine_from_exe(exe_path: Path, game_info: 'GameInfo | None') -> str | None:
	engine = try_detect_engine_from_exe_properties(exe_path, game_info)
	if engine:
		return engine

	engine = try_and_detect_engine_from_folder(exe_path.parent, game_info, exe_path)
	if engine:
		return engine

	if exe_path.suffix.lower() == '.exe':
		with exe_path.open('rb') as f:
			f.seek(-4, os.SEEK_END)
			offset = int.from_bytes(f.read(4), 'little')
			f.seek(offset)
			magic = f.read(4)
			if magic in {b'PJ93', b'39JP'}:
				return 'Director (v4)'
			if magic in {b'PJ95', b'59JP'}:
				return 'Director (v5)'
			if magic in {b'PJ97', b'79JP'}:
				return 'Director (v6)'
			if magic in {b'PJ00', b'00JP', b'PJ01', b'10JP'}:
				return 'Director (v7)'

	return None

def try_and_detect_engine_from_folder(folder: Path, game_info: 'GameInfo | None'=None, executable: Path | None=None) -> str | None:
	#Get the most likely things out of the way first
	unity_version = _try_detect_unity(folder, game_info, executable)
	if unity_version:
		return unity_version
	if _try_detect_ue4(folder, game_info):
		return 'Unreal Engine 4'
	if _try_detect_ue3(folder):
		return 'Unreal Engine 3'
	renpy_version = _try_detect_renpy(folder, game_info)
	if renpy_version:
		return renpy_version
	nw_version = _try_detect_nw(folder, game_info) #Not really the right name for this variable, it's to check if it's just nw.js or has RPG Maker MV/MZ inside
	if nw_version:
		return nw_version
	if _try_detect_gamemaker(folder, game_info):
		return 'GameMaker'
	rpg_maker_xp_version = _try_detect_rpg_maker_xp_vx(folder, game_info, executable)
	if rpg_maker_xp_version:
		return rpg_maker_xp_version

	#XNA: Might have a "common redistributables" folder with an installer in it?
	engine = _try_detect_engines_from_filenames(folder)
	if engine:
		return engine

	if _try_detect_adobe_air(folder, game_info):
		return 'Adobe AIR'
	if _try_detect_build(folder):
		return 'Build'
	if _try_detect_godot(folder):
		return 'Godot'
	if _try_detect_jackbox_games(folder, game_info):
		return 'Jackbox Games Engine'
	if _try_detect_source(folder):
		return 'Source'

	cryengine_version = _try_detect_cryengine(folder)
	if cryengine_version:
		return cryengine_version
	piko_mednafen = _try_detect_piko_mednafen(folder, game_info)
	if piko_mednafen:
		return piko_mednafen
	rpg_maker_200x_version = _try_detect_rpg_maker_200x(folder, game_info, executable)
	if rpg_maker_200x_version:
		return rpg_maker_200x_version

	if not executable:
		for f in folder.iterdir():
			#Last ditch effort if we still didn't detect an engine from the folder… not great, since there could be all sorts of exes, but whaddya do
			if f.is_file() and f.suffix.lower() == '.exe':
				engine = try_detect_engine_from_exe_properties(f, game_info)
				if engine:
					return engine
	
	return None

def detect_engine_recursively(folder: Path, game_info: 'GameInfo | None'=None) -> str | None:
	#This can be slow, so maybe you should avoid using it
	engine = try_and_detect_engine_from_folder(folder, game_info)
	if engine:
		return engine

	for subdir in folder.iterdir():
		if subdir.is_dir() and not subdir.is_symlink():
			engine = detect_engine_recursively(subdir, game_info)
			if engine:
				return engine

	return None
