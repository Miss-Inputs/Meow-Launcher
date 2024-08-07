#For engine_detect to use to add metadata while it's detecting engines, but could also be useful if something is already known to be that engine

import io
import json
import re
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from meowlauncher.common_types import SaveType
from meowlauncher.util.utils import NoNonsenseConfigParser, junk_suffixes

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

if TYPE_CHECKING:
	from collections.abc import Mapping

	from meowlauncher.info import GameInfo

def add_unity_metadata(data_folder: Path, game_info: 'GameInfo') -> None:
	icon_path = data_folder.joinpath('Resources', 'UnityPlayer.png')
	if icon_path.is_file():
		game_info.images['Icon'] = icon_path
	screen_selector_path = data_folder.joinpath('ScreenSelector.png')
	if screen_selector_path.is_file():
		game_info.images['Banner'] = screen_selector_path #kind of a banner? We'll just call it that
	appinfo_path = data_folder.joinpath('app.info')
	try:
		with appinfo_path.open('rt', encoding='utf-8') as appinfo:
			appinfo_lines = appinfo.readlines(2)
			if not game_info.publisher and not game_info.developer:
				company_name = appinfo_lines[0]
				if company_name:
					while junk_suffixes.search(company_name):
						company_name = junk_suffixes.sub('', company_name)
					game_info.developer = game_info.publisher = company_name
			if len(appinfo_lines) > 1:
				game_info.add_alternate_name(appinfo_lines[1], 'Engine Name')
	except FileNotFoundError:
		pass

def add_unity_web_metadata(folder: Path, game_info: 'GameInfo') -> None:
	for file in folder.joinpath('Build').iterdir():
		if file.suffix == '.json':
			info_json = json.loads(file.read_text('utf-8'))
			if not game_info.publisher and not game_info.developer:
				company_name = info_json.get('companyName')
				if company_name:
					while junk_suffixes.search(company_name):
						company_name = junk_suffixes.sub('', company_name)
					game_info.developer = game_info.publisher = company_name
			game_info.add_alternate_name(info_json.get('productName'), 'Engine Name')
			break

def add_metadata_for_adobe_air(root_path: Path, application_xml: Path, game_info: 'GameInfo') -> None:
	iterator = ElementTree.iterparse(application_xml)
	for _, element in iterator:
		#Namespaces are annoying
		_, _, element.tag = element.tag.rpartition('}')
	app_xml = iterator.root #type: ignore[attr-defined]
	air_id = app_xml.findtext('id')
	if air_id:
		game_info.specific_info['Adobe AIR ID'] = air_id #Something like com.blah.whatever
	name = app_xml.find('name')
	if name:
		name_text = name.findtext('text')
		game_info.add_alternate_name(name_text if name_text else name.text, 'Engine Name')
	version_number = app_xml.findtext('versionNumber')
	version_label = app_xml.findtext('versionLabel')
	if version_label:
		game_info.specific_info['Version'] = version_label
		game_info.specific_info['Version Number'] = version_number
	else:
		version = app_xml.findtext('version', version_number)
		if version:
			game_info.specific_info['Version'] = version
	description = app_xml.find('description')
	if description:
		description_text = description.findtext('text')
		game_info.descriptions['Adobe AIR Description'] = description_text if description_text else description.text
	copyright_text = app_xml.findtext('copyright')
	if copyright_text:
		game_info.specific_info['Copyright'] = copyright_text
	#supportedProfiles (extendedDesktop desktop)? customUpdateUI? allowBrowserInvocation? installFolder? programMenuFolder?
	initial_window = app_xml.find('initialWindow')
	if initial_window:
		#content: SWF file, or is that obvious?
		#systemChrome (?), transparent
		title = initial_window.findtext('title')
		if title:
			game_info.add_alternate_name(title, 'Window Title')
		game_info.specific_info['Minimizable?'] = initial_window.findtext('minimizable') == 'true'
		game_info.specific_info['Maximizable?'] = initial_window.findtext('maximizable') == 'true'
		resizable = initial_window.findtext('resizable', 'true') == 'true'
		game_info.specific_info['Resizable?'] = resizable
		if not resizable:
			width = initial_window.findtext('width')
			height = initial_window.findtext('height')
			if width and height:
				game_info.specific_info['Display Resolution'] = f'{width}x{height}'
		game_info.specific_info['Minimum Resolution'] = initial_window.findtext('minSize', '').replace(' ', 'x')
		game_info.specific_info['Start in Fullscreen?'] = initial_window.findtext('fullScreen') == 'true'
		render_mode = initial_window.findtext('renderMode')
		game_info.specific_info['Render Mode'] = render_mode
		game_info.specific_info['Start Visible?'] = initial_window.findtext('visible') == 'true'
	icon = app_xml.find('icon')
	if icon:
		best_icon: str | None = None
		best_icon_size: int | None = None
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
			game_info.images['Icon'] = root_path / best_icon

def add_metadata_from_nw_package_json(package_json: 'Mapping[str, Any]', game_info: 'GameInfo') -> None:
	#main might come in handy (index.html, etc)
	#no-edit-menu and position maybe not
	#single-instance, dom_storage_quota, maybe? I dunno
	description = package_json.get('description')
	if description:
		game_info.descriptions['Package Description'] = description
	package_name = package_json.get('name')
	if package_name:
		game_info.add_alternate_name(package_name, 'Engine Name')
	game_info.specific_info['Version'] = package_json.get('version')
	game_info.specific_info['User Agent'] = package_json.get('user-agent')
	game_info.specific_info['Chromium Arguments'] = package_json.get('chromium-args')
	window = package_json.get('window')
	if window:
		#toolbar, frame, kiosk, show?
		min_width = window.get('min_width')
		min_height = window.get('min_height')
		if min_width and min_height:
			game_info.specific_info['Minimum Resolution'] = f'{min_width}x{min_height}'
		resizable = window.get('resizable')
		if not resizable:
			width = window.get('width')
			height = window.get('height')
			if height and width:
				game_info.specific_info['Display Resolution'] = f'{width}x{height}'
		#I need a better way of doing that… I can't just return a path since it might be from a zip
		game_info.specific_info['Icon Relative Path'] = window.get('icon')
		game_info.add_alternate_name(window.get('title'), 'Window Title')

def add_info_from_package_json_file(folder: Path, package_json_path: Path, game_info: 'GameInfo') -> None:
	add_metadata_from_nw_package_json(json.loads(package_json_path.read_bytes()), game_info)
	if 'Icon-Relative-Path' in game_info.specific_info:
		icon_path = folder.joinpath(game_info.specific_info.pop('Icon Relative Path'))
		if icon_path.is_file() and 'Icon' not in game_info.images:
			game_info.images['Icon'] = icon_path

def add_info_from_package_json_zip(package_nw_path: Path, game_info: 'GameInfo') -> bool:
	with zipfile.ZipFile(package_nw_path) as package_nw:
		try:
			with package_nw.open('package.json', 'r') as package_json:
				add_metadata_from_nw_package_json(json.load(package_json), game_info)
			if 'Icon-Relative-Path' in game_info.specific_info:
				icon_path = game_info.specific_info.pop('Icon Relative Path')
				if 'Icon' not in game_info.images:
					try:
						with package_nw.open(icon_path, 'r') as icon_data:
							game_info.images['Icon'] = Image.open(io.BytesIO(icon_data.read()))
					except KeyError:
						pass
		except KeyError:
			return False #Maybe
	return True

#Multiline string, translatable string, normal string and boolean respectively
define_line = re.compile(r'^define\s+(?P<key>[\w.]+)\s+=\s+(?:_p\("""(?P<multiline_string>.+?)"""\)|_\("(?P<translated_string>.+?)"\)|"(?P<string>.+?)"|(?P<bool>True|False))', re.DOTALL | re.MULTILINE)
def add_metadata_from_renpy_options(game_folder: Path, options_path: Path, game_info: 'GameInfo') -> None:
	options = options_path.read_text('utf-8', errors='ignore')
	#d = {match[1]: match[2] if match[2] else (match[3] if match[3] else (match[4] if match[4] else bool(match[5]))) for match in define_line.finditer(options)}
	for match in define_line.finditer(options):
		if match['key'] == 'config.name':
			game_info.add_alternate_name(match['translated_string'] if match['translated_string'] else match['string'], 'Engine Name')
		if match['key'] == 'config.version':
			game_info.specific_info['Version'] = match['string']
		if match['key'] == 'gui.about':
			game_info.descriptions['About Screen'] = match['multiline_string']
		if match['key'] == 'build.name':
			game_info.specific_info['Internal Title'] = match['string']
		if match['key'] == 'config.has_sound':
			game_info.specific_info['Has Sound Effects?'] = bool(match['bool'])
		if match['key'] == 'config.has_music':
			game_info.specific_info['Has Music?'] = bool(match['bool'])
		if match['key'] == 'config.has_voice':
			game_info.specific_info['Has Voices?'] = bool(match['bool'])
		if match['key'] == 'config.save_directory' and match['string']:
			#The actual save directory in itself doesn't matter, but it means we do have one
			game_info.save_type = SaveType.Internal
		if match['key'] == 'config.window_icon':
			icon_path = game_folder.joinpath(match['string'])
			if icon_path.is_file():
				game_info.images['Icon'] = icon_path
				
def add_gamemaker_metadata(folder: Path, game_info: 'GameInfo') -> None:
	options_ini_path = folder.joinpath('options.ini')
	if not options_ini_path.is_file():
		options_ini_path = folder.joinpath('assets', 'options.ini')
	if options_ini_path.is_file():
		parser = NoNonsenseConfigParser()
		parser.read(options_ini_path)
		if parser.has_section('Linux'):
			#There is also an Icon and Splash that seem to refer to images that don't exist…
			#What could AppId be for?
			game_info.add_alternate_name(parser['Linux']['DisplayName'], 'Engine Name')
				
	icon_path = folder.joinpath('icon.png')
	if not icon_path.is_file():
		icon_path = folder.joinpath('assets', 'icon.png')
	if icon_path.is_file():
		game_info.images['Icon'] = icon_path

def add_metadata_from_pixel_game_maker_mv_info_json(info_json_path: Path, game_info: 'GameInfo') -> None:
	info: 'Mapping[str, str]' = json.loads(info_json_path.read_bytes())
	title = info.get('title')
	author = info.get('author')
	genre = info.get('genre')
	description = info.get('description')
	#Dunno what key does
	if title:
		game_info.add_alternate_name(info['title'], 'Engine Name')
	if author and not game_info.developer:
		game_info.developer = author
	if genre and not game_info.genre:
		game_info.genre = genre
	if description:
		game_info.descriptions['Pixel Game Maker MV Description'] = description
		
def add_piko_mednafen_info(folder: Path, data_path: Path, game_info: 'GameInfo') -> None:
	game_info.save_type = SaveType.Internal #You get savestates either way, so we won't use nosram to determine that
	for line in data_path.read_text('utf-8').splitlines():
		if '=' not in line:
			continue
		k, v = line.strip().split('=')
		if k == 'title':
			game_info.add_alternate_name(v, 'Window Title')
		if k == 'nosram':
			game_info.specific_info['No SRAM?'] = v == '1'
		if k == 'players':
			game_info.specific_info['Number of Players'] = v
		#Dunno what xgui does (always 1 if there?), or padstyle/padui (always 0?) (yes the source is there but I don't know anything)
	background_image_path = folder / 'res' / 'back'
	if background_image_path.is_file():
		game_info.images['Background Image'] = background_image_path
	overlay_path = folder / 'res' / 'overlay'
	if overlay_path.is_file(): #Seems to always be?
		game_info.images['Overlay Image'] = overlay_path
	splash_path = folder / 'res' / 'splash'
	if splash_path.is_file():
		game_info.images['Splash Screen'] = splash_path
	#NP (or sometimes 0P, 1P, 2P) = thumbnails for the save slots, or something?
