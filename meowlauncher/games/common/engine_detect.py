import configparser
import io
import json
import re
import zipfile
from collections.abc import Collection, Mapping
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from xml.etree import ElementTree

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.common_types import SaveType
from meowlauncher.util.utils import junk_suffixes

from .pc_common_metadata import get_exe_properties

if TYPE_CHECKING:
	from meowlauncher.metadata import Metadata

def add_unity_metadata(data_folder: Path, metadata: 'Metadata') -> None:
	icon_path = data_folder.joinpath('Resources', 'UnityPlayer.png')
	if icon_path.is_file():
		metadata.images['Icon'] = icon_path
	screen_selector_path = data_folder.joinpath('ScreenSelector.png')
	if screen_selector_path.is_file():
		metadata.images['Banner'] = screen_selector_path #kind of a banner? We'll just call it that
	appinfo_path = data_folder.joinpath('app.info')
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
				metadata.add_alternate_name(appinfo_lines[1], 'Engine Name')
	except FileNotFoundError:
		pass

def add_unity_web_metadata(folder: Path, metadata: 'Metadata') -> None:
	for file in folder.joinpath('Build').iterdir():
		if file.suffix == '.json':
			info_json = json.loads(file.read_text('utf-8'))
			if not metadata.publisher and not metadata.developer:
				company_name = info_json.get('companyName')
				if company_name:
					while junk_suffixes.search(company_name):
						company_name = junk_suffixes.sub('', company_name)
					metadata.developer = metadata.publisher = company_name
			metadata.add_alternate_name(info_json.get('productName'), 'Engine Name')
			break

def _try_detect_unity(folder: Path, metadata: Optional['Metadata'], executable: Optional['Path']) -> Optional[str]:
	if folder.joinpath('Build', 'UnityLoader.js').is_file():
		#Web version of Unity, there should be some .unityweb files here
		if metadata:
			add_unity_web_metadata(folder, metadata)
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
		if metadata:
			add_unity_metadata(unity_data_folder, metadata)

		try:
			props = get_exe_properties(str(folder / 'UnityPlayer.dll'))
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
			props = get_exe_properties(str(exe_path))
			if props:
				unity_version = props.get('UnityVersion', props.get('Unity Version'))
				if unity_version:
					return f'Unity ({unity_version})'
		return 'Unity'

	return None

def _try_detect_ue4(folder: Path, metadata: Optional['Metadata']) -> bool:
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
		if metadata:
			metadata.specific_info['Internal Title'] = project_name
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

def _add_gamemaker_metadata(folder: Path, metadata: 'Metadata') -> None:
	#game.unx seems to also always have FORM magic
	options_ini_path = folder.joinpath('options.ini')
	if not options_ini_path.is_file():
		options_ini_path = folder.joinpath('assets', 'options.ini')
	if options_ini_path.is_file():
		parser = configparser.ConfigParser(interpolation=None)
		parser.optionxform = str #type: ignore[assignment]
		parser.read(options_ini_path)
		if parser.has_section('Linux'):
			#There is also an Icon and Splash that seem to refer to images that don't exist…
			#What could AppId be for?
			metadata.add_alternate_name(parser['Linux']['DisplayName'], 'Engine Name')
				
	icon_path = folder.joinpath('icon.png')
	if not icon_path.is_file():
		icon_path = folder.joinpath('assets', 'icon.png')
	if icon_path.is_file():
		metadata.images['Icon'] = icon_path

def _try_detect_gamemaker(folder: Path, metadata: Optional['Metadata']) -> bool:
	possible_data_file_paths = [folder / 'data.win', folder / 'game.unx', folder.joinpath('assets', 'data.win'), folder.joinpath('assets', 'game.unx')]
	for data_file_path in possible_data_file_paths:
		try:
			with open(data_file_path, 'rb') as f:
				if f.read(4) == b'FORM':
					if metadata:
						_add_gamemaker_metadata(folder, metadata)
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

def add_metadata_for_adobe_air(root_path: Path, application_xml: Path, metadata: 'Metadata') -> None:
	iterator = ElementTree.iterparse(application_xml)
	for _, element in iterator:
		#Namespaces are annoying
		_, _, element.tag = element.tag.rpartition('}')
	app_xml = iterator.root #type: ignore[attr-defined]
	air_id = app_xml.findtext('{*}id')
	if air_id:
		metadata.specific_info['Adobe AIR ID'] = air_id #Something like com.blah.whatever
	name = app_xml.findtext('name')
	if name:
		metadata.add_alternate_name(name, 'Engine Name')
	version = app_xml.findtext('version', app_xml.findtext('versionNumber'))
	if version:
		metadata.specific_info['Version'] = version
	description = app_xml.findtext('description')
	if description:
		metadata.descriptions['Adobe AIR Description'] = description
	initial_window = app_xml.find('initialWindow')
	if initial_window:
		#content: SWF file, or is that obvious?
		title = initial_window.findtext('title')
		if title:
			metadata.add_alternate_name(title, 'Window Title')
		metadata.specific_info['Maximizable?'] = initial_window.findtext('maximizable') == 'true'
		resizable = initial_window.findtext('resizable', 'true') == 'true'
		metadata.specific_info['Resizable?'] = resizable
		if not resizable:
			width = initial_window.findtext('width')
			height = initial_window.findtext('height')
			if width and height:
				metadata.specific_info['Display Resolution'] = f'{width}x{height}'
		metadata.specific_info['Minimum Size'] = initial_window.findtext('minSize', '').replace(' ', 'x')
		metadata.specific_info['Start in Fullscreen?'] = initial_window.findtext('fullScreen') == 'true'
		render_mode = initial_window.findtext('renderMode')
		metadata.specific_info['Render Mode'] = render_mode
		metadata.specific_info['Start Visible?'] = initial_window.findtext('visible') == 'true'
	icon = app_xml.find('icon')
	if icon:
		best_icon: Optional[str] = None
		best_icon_size: Optional[int] = None
		for child in icon:
			size = child.tag.rsplit('x', 1)[-1] if 'x' in child.tag else None
			if not best_icon or not best_icon_size:
				best_icon = child.text
				try:
					if size:
						best_icon_size = int(size)
				except ValueError:
					pass
			elif size and int(size) > best_icon_size:
				best_icon = child.text
				try:
					best_icon_size = int(size)
				except ValueError:
					pass

		if best_icon:
			metadata.images['Icon'] = root_path / best_icon

def _try_detect_adobe_air(folder: Path, metadata: Optional['Metadata']) -> bool:
	metainf_dir = folder.joinpath('META-INF', 'AIR')
	if metainf_dir.is_dir():
		application_xml = metainf_dir.joinpath('application.xml')
		if application_xml.is_file() and metainf_dir.joinpath('hash').is_file():
			if metadata:
				add_metadata_for_adobe_air(folder, application_xml, metadata)
			return True
	
	share = folder / 'share'
	if share.is_dir() and _try_detect_adobe_air(folder / 'share', metadata):
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

def add_metadata_from_nw_package_json(package_json: Mapping[str, Any], metadata: 'Metadata') -> None:
	#main might come in handy (index.html, etc)
	#no-edit-menu and position maybe not
	package_description = package_json.get('description')
	if package_description:
		metadata.descriptions['Package Description'] = package_description
	package_name = package_json.get('name')
	if package_name:
		metadata.add_alternate_name(package_name, 'Engine Name')
	window = package_json.get('window')
	if window:
		#toolbar, frame, width, height…
		min_width = window.get('min_width')
		min_height = window.get('min_height')
		if min_width and min_height:
			metadata.specific_info['Minimum Size'] = f'{min_width}x{min_height}'
		#I need a better way of doing that… I can't just return a path since it might be from a zip
		metadata.specific_info['Icon Relative Path'] = window.get('icon')
		metadata.add_alternate_name(window.get('title'), 'Window Title')

def add_info_from_package_json_file(folder: Path, package_json_path: Path, metadata: 'Metadata') -> None:
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

def _try_detect_nw(folder: Path, metadata: Optional['Metadata']) -> Optional[str]:
	if not folder.joinpath('nw.pak').is_file() and not folder.joinpath('nw_100_percent.pak').is_file() and not folder.joinpath('nw_200_percent.pak').is_file():
		return None
	
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
				return None
	
	if not have_package:
		return None

	try:
		with open(folder.joinpath('www', 'js', 'rpg_core.js'), 'rt', encoding='utf-8') as f:
			for line in f:
				line = line.strip()
				if line.startswith('Utils.RPGMAKER_NAME = '):
					rpgmaker_name = line[len('Utils.RPGMAKER_NAME = '):].rstrip(';').strip('"\'')
					return f'RPG Maker {rpgmaker_name}'
	except FileNotFoundError:
		pass
	try:
		with open(folder.joinpath('js', 'rmmz_core.js'), 'rt', encoding='utf-8') as f:
			#Although I guess it's sort of implied to be RPG Maker MZ already by the filename being rmmz… but who knows
			for line in f:
				line = line.strip()
				if line.startswith('Utils.RPGMAKER_NAME = '):
					rpgmaker_name = line[len('Utils.RPGMAKER_NAME = '):].rstrip(';').strip('"')
					return f'RPG Maker {rpgmaker_name}'
	except FileNotFoundError:
		pass

	return 'nw.js'

def _try_detect_rpg_maker_200x(folder: Path, metadata: Optional['Metadata'], executable: Optional[Path]) -> Optional[str]:
	rpg_rt_ini_path = folder / 'RPG_RT.ini' #This should always be here I think?
	if rpg_rt_ini_path.is_file():
		if metadata:
			try:
				rpg_rt_ini = configparser.ConfigParser(interpolation=None)
				rpg_rt_ini.optionxform = str #type: ignore[assignment]
				rpg_rt_ini.read(rpg_rt_ini_path)
				metadata.add_alternate_name(rpg_rt_ini['RPG_RT']['GameTitle'], 'Engine Name')
				if 'FullPackageFlag' in rpg_rt_ini['RPG_RT']:
					metadata.specific_info['Uses RTP?'] = rpg_rt_ini['RPG_RT']['FullPackageFlag'] == '0'
			except KeyError:
				pass
			titles_path = folder / 'Title' / 'titles.png' #Sometimes this exists and title.png is a black screen
			if titles_path.is_file():
				metadata.images['Title Screen'] = titles_path
			else:
				title_path = folder / 'Title' / 'title.png'
				if title_path.is_file():
					metadata.images['Title Screen'] = title_path
		
		product_names = {'RPG Maker 2000': '2000', 'RPG Maker 2000 Value!': '2000', 'RPG Maker 2003': '2003'}
		if executable:
			props = get_exe_properties(str(executable))
			if props:
				product_name = props.get('ProductName')
				if product_name in product_names:
					return 'RPG Maker ' + product_names[product_name]
			
		for file in folder.iterdir():
			if file.suffix.lower() == '.r3proj':
				return 'RPG Maker 2003'
			if not executable and file.suffix.lower() == '.exe':
				#Usually RPG_RT.exe but can be renamed (often to Game.exe)
				#There are some with a blank ProductName and a ProductVersion of 1.0.8.0 but I dunno what that corresponds to
				props = get_exe_properties(str(file))
				if props:
					product_name = props.get('ProductName')
					if product_name in product_names:
						return 'RPG Maker ' + product_names[product_name]
					break
			if file.name.lower() == 'ultimate_rt_eb.dll':
				props = get_exe_properties(str(file))
				if props:
					product_name = props.get('ProductName')
					if product_name in product_names:
						return 'RPG Maker ' + product_names[product_name]
					break
		return 'RPG Maker 2000/2003'

	return None

#Multiline string, translatable string, normal string and boolean respectively
define_line = re.compile(r'^define\s+(?P<key>[\w.]+)\s+=\s+(?:_p\("""(?P<multiline_string>.+?)"""\)|_\("(?P<translated_string>.+?)"\)|"(?P<string>.+?)"|(?P<bool>True|False))', re.DOTALL | re.MULTILINE)
def add_metadata_from_renpy_options(game_folder: Path, options_path: Path, metadata: 'Metadata') -> None:
	options = options_path.read_text('utf-8', errors='ignore')
	#d = {match[1]: match[2] if match[2] else (match[3] if match[3] else (match[4] if match[4] else bool(match[5]))) for match in define_line.finditer(options)}
	for match in define_line.finditer(options):
		if match['key'] == 'config.name':
			metadata.add_alternate_name(match['translated_string'] if match['translated_string'] else match['string'], 'Engine Name')
		if match['key'] == 'config.version':
			metadata.specific_info['Version'] = match['string']
		if match['key'] == 'gui.about':
			metadata.descriptions['About Screen'] = match['multiline_string']
		if match['key'] == 'build.name':
			metadata.specific_info['Internal Title'] = match['string']
		if match['key'] == 'config.has_sound':
			metadata.specific_info['Has Sound Effects?'] = bool(match['bool'])
		if match['key'] == 'config.has_music':
			metadata.specific_info['Has Music?'] = bool(match['bool'])
		if match['key'] == 'config.has_voice':
			metadata.specific_info['Has Voices?'] = bool(match['bool'])
		if match['key'] == 'config.save_directory' and match['string']:
			#The actual save directory in itself doesn't matter, but it means we do have one
			metadata.save_type = SaveType.Internal
		if match['key'] == 'config.window_icon':
			icon_path = game_folder.joinpath(match['string'])
			if icon_path.is_file():
				metadata.images['Icon'] = icon_path

version_tuple_definition = re.compile(r'^version_tuple\s*=\s*\((.+?)\)$')
def _try_detect_renpy(folder: Path, metadata: Optional['Metadata']) -> Optional[str]:
	renpy_folder = folder / 'renpy'
	if renpy_folder.is_dir():
		if metadata:
			game_folder = folder / 'game'
			options = game_folder / 'options.rpy'
			if options.is_file():
				#Not always here, maybe only games that aren't compiled into .rpa
				#There probably would be a way to use the Ren'Py library right there to open the rpa, but that seems like it might be a bit excessive
				add_metadata_from_renpy_options(game_folder, options, metadata)

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
		with package_json_path.open('rb') as f:
			j = json.load(f)
			#This isn't a valid URL but it's what it is, I dunno
			return j['homepage'] == 'https://github.com/RPG-Paper-Maker/Game#readme'
	except FileNotFoundError:
		return False

def _try_detect_rpg_maker_xp_vx(folder: Path, metadata: Optional['Metadata'], executable: Optional[Path]) -> Optional[str]:
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
			if ext == 'rvproj':
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
			game_ini = configparser.ConfigParser(interpolation=None)
			game_ini.optionxform = str #type: ignore[assignment]
			game_ini.read(game_ini_path)
			try:
				game = game_ini['Game']
				library = game['Library'].lower().removeprefix('system\\') #Might not always be in that folder
				#Also note that the DLL doesn't actually have to exist (as is the case with mkxp)
				if library[:5] in engine_versions:
					engine = engine_versions[library[:5]]
				if metadata:
					metadata.add_alternate_name(game['Title'], 'Engine Name')
					#Not sure if Fullscreen=1 implies it starts in fullscreen, or it always is
					if 'Play_Music' in game:
						metadata.specific_info['Has Music?'] = game['Play_Music'] == '1'
					if 'Play_Sound_Effects' in game:
						metadata.specific_info['Has Sound Effects?'] = game['Play_Sound_Effects'] == '1'
					if 'Mouse' in game:
						metadata.specific_info['Uses Mouse?'] = game['Mouse'] == '1'
			except KeyError:
				pass
			#Sometimes there is a Fullscreen++ section, not sure what it could tell me, whether the game starts in fullscreen or supports it differently or what
		if mkxp_path.is_file():
			engine += ' (mkxp)'
			if metadata:
				for line in mkxp_path.read_text().splitlines():
					if '=' not in line:
						continue
					k, v = line.strip().split('=', 1)
					if k == 'iconPath':
						metadata.images['Icon'] = folder / v

		return engine

	return None

def _try_detect_cryengine(folder: Path) -> Optional[str]:
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

def _try_detect_jackbox_games(folder: Path, metadata: Optional['Metadata']) -> bool:
	jbg_config_jet_path = folder / 'jbg.config.jet'
	if folder.joinpath('platform.swf').is_file() and jbg_config_jet_path.is_file():
		if metadata:
			jbg_config_jet = json.loads(jbg_config_jet_path.read_text())
			game_name = jbg_config_jet.get('gameName')
			if game_name:
				metadata.specific_info['Internal Title'] = game_name
			#gameShortName (e.g. "q2i"), canPauseOnPressStart, needExitbutton, env ("pc"), uaVersionId (e.g. 0.1.0), isBundle, analyticsApi, pause-inputs, uaAppId (e.g. drawful2? Just uaAppName/gameName but lowercase?) may also be interesting
			build_timestamp = jbg_config_jet.get('buildTimeStamp')
			if build_timestamp:
				try:
					metadata.specific_info['Build Date'] = datetime.fromisoformat(build_timestamp)
				except ValueError:
					pass
			build_version = jbg_config_jet.get('buildVersion')
			if build_version:
				metadata.specific_info['Build Version'] = build_version
			metadata.specific_info['Supports Fullscreen?'] = jbg_config_jet.get('supportsFullScreen', 'true') != 'false'
			#Nothing these are strings representing bools, we're just seeing if they exist before looking at them
			#I don't know if I want to mess with input info just yet, or if I want to give up on that idea anyway
			supports_mouse = jbg_config_jet.get('supportsMouse')
			supports_keyboard = jbg_config_jet.get('supportsKeyboard')
			supports_gamepad_hotplug = jbg_config_jet.get('supportsJoysticksHotplugging')
			if supports_mouse:
				metadata.specific_info['Uses Mouse?'] = supports_mouse == 'true'
			if supports_keyboard:
				metadata.specific_info['Uses Keyboard?'] = supports_keyboard == 'true'
			if supports_gamepad_hotplug:
				metadata.specific_info['Supports Hotplugging Gamepads?'] = supports_gamepad_hotplug != 'false'
		return True
	return False

def _try_detect_engines_from_filenames(folder: Path, files: Collection[str], subdirs: Collection[str]) -> Optional[str]:
	#These are simple enough to detect with just one line…	
	if 'acsetup.cfg' in files:
		#TODO The better way to do this would be to look for 'Adventure Creator Game File' in dat or exe I guess (and then we can get game title from there), but also the effort way
		return 'Adventure Game Studio'
	if all(f in files for f in ('logdir', 'object', 'picdir', 'viewdir', 'snddir', 'vol.0', 'words.tok')):
		#Apparently there can be .wag files?
		return 'AGI' #v2
	if 'game.dmanifest' in files and 'game.arcd' in files and 'game.arci' in files:
		return 'Defold'
	if 'fna.dll' in files:
		return 'FNA'
	if 'data.xp3' in files and 'plugin' in subdirs:
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

	if folder.joinpath('bin', 'libUnigine_x64.so').is_file() or folder.joinpath('bin', 'libUnigine_x86.so').is_file() or folder.joinpath('bin', 'Unigine_x86.dll').is_file() or folder.joinpath('bin', 'Unigine_x64.dll').is_file():
		return 'Unigine'
	if folder.joinpath('System', 'Engine.u').is_file():
		return 'Unreal Engine 1'
	if folder.joinpath('Build', 'Final', 'DefUnrealEd.ini').is_file():
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if folder.joinpath('Builds', 'Binaries', 'DefUnrealEd.ini').is_file():
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	
	return None

def add_metadata_from_pixel_game_maker_mv_info_json(info_json_path: Path, metadata: 'Metadata') -> None:
	info: Mapping[str, str] = json.loads(info_json_path.read_bytes())
	title = info.get('title')
	author = info.get('author')
	genre = info.get('genre')
	description = info.get('description')
	#Dunno what key does
	if title:
		metadata.add_alternate_name(info['title'], 'Engine Name')
	if author and not metadata.developer:
		metadata.developer = author
	if genre and not metadata.genre:
		metadata.genre = genre
	if description:
		metadata.descriptions['Pixel Game Maker MV Description'] = description

def try_detect_engine_from_exe_properties(exe_path: Path, metadata: Optional['Metadata']) -> Optional[str]:
	if exe_path.suffix.lower() != '.exe':
		#Since .dll can't be launched, exe would be the only valid extension for this
		return None
	props = get_exe_properties(str(exe_path))
	if props:
		file_description = props.get('FileDescription')
		if file_description == 'Wintermute Engine Runtime':
			return 'Wintermute'
		if file_description == 'Clickteam Fusion Application Runtime':
			return 'Clickteam Fusion'
		if file_description == 'Pixel Game Maker MV player':
			if metadata:
				info_json = exe_path.parent.joinpath('Resources', 'data', 'info.json')
				add_metadata_from_pixel_game_maker_mv_info_json(info_json, metadata)
			return 'Pixel Game Maker MV'
		internal_name = props.get('InternalName')
		if internal_name and internal_name.startswith('LuaSTG'):
			return internal_name

	return None

def try_detect_engine_from_exe(exe_path: Path, metadata: Optional['Metadata']) -> Optional[str]:
	engine = try_detect_engine_from_exe_properties(exe_path, metadata)
	if engine:
		return engine

	engine = try_and_detect_engine_from_folder(exe_path.parent, metadata, exe_path)
	if engine:
		return engine

	return None

def try_and_detect_engine_from_folder(folder: Path, metadata: 'Metadata'=None, executable: Optional[Path]=None) -> Optional[str]:
	dir_entries = set(folder.iterdir())
	files = {f.name.lower() for f in dir_entries if f.is_file()}
	subdirs = {f.name.lower() for f in dir_entries if f.is_dir()}

	#Get the most likely things out of the way first
	unity_version = _try_detect_unity(folder, metadata, executable)
	if unity_version:
		return unity_version
	if _try_detect_ue4(folder, metadata):
		return 'Unreal Engine 4'
	if _try_detect_ue3(folder):
		return 'Unreal Engine 3'
	renpy_version = _try_detect_renpy(folder, metadata)
	if renpy_version:
		return renpy_version
	nw_version = _try_detect_nw(folder, metadata) #Not really the right name for this variable, it's to check if it's just nw.js or has RPG Maker MV/MZ inside
	if nw_version:
		return nw_version
	if _try_detect_gamemaker(folder, metadata):
		return 'GameMaker'
	rpg_maker_xp_version = _try_detect_rpg_maker_xp_vx(folder, metadata, executable)
	if rpg_maker_xp_version:
		return rpg_maker_xp_version

	#XNA: Might have a "common redistributables" folder with an installer in it?
	engine = _try_detect_engines_from_filenames(folder, files, subdirs)
	if engine:
		return engine

	if _try_detect_adobe_air(folder, metadata):
		return 'Adobe AIR'
	if _try_detect_build(folder):
		return 'Build'
	if _try_detect_godot(folder):
		return 'Godot'
	if _try_detect_jackbox_games(folder, metadata):
		return 'Jackbox Games Engine'
	if _try_detect_source(folder):
		return 'Source'

	cryengine_version = _try_detect_cryengine(folder)
	if cryengine_version:
		return cryengine_version
	rpg_maker_200x_version = _try_detect_rpg_maker_200x(folder, metadata, executable)
	if rpg_maker_200x_version:
		return rpg_maker_200x_version

	if not executable:
		for f in folder.iterdir():
			#Last ditch effort if we still didn't detect an engine from the folder… not great, since there could be all sorts of exes, but whaddya do
			if f.is_file() and f.suffix.lower() == '.exe':
				engine = try_detect_engine_from_exe_properties(f, metadata)
				if engine:
					return engine
	
	return None

def detect_engine_recursively(folder: Path, metadata: Optional['Metadata']=None) -> Optional[str]:
	#This can be slow, so maybe you should avoid using it
	engine = try_and_detect_engine_from_folder(folder, metadata)
	if engine:
		return engine

	for subdir in folder.iterdir():
		if subdir.is_dir():
			engine = detect_engine_recursively(subdir, metadata)
			if engine:
				return engine

	return None
