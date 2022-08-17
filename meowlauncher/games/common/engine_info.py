#For engine_detect to use to add metadata while it's detecting engines, but could also be useful if something is already known to be that engine

import configparser
import io
import json
import re
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from xml.etree import ElementTree

from meowlauncher.common_types import SaveType
from meowlauncher.util.utils import junk_suffixes

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

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
	add_metadata_from_nw_package_json(json.loads(package_json_path.read_bytes()), metadata)
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
				
def add_gamemaker_metadata(folder: Path, metadata: 'Metadata') -> None:
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
		