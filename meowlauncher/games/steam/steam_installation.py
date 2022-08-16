import io
import zipfile
from collections.abc import Collection, Iterator, Mapping
from operator import attrgetter
from pathlib import Path
from typing import Any, Optional, Union

from steamfiles import acf, appinfo

try:
	from PIL import IcoImagePlugin, Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config.main_config import main_config


class IconError(Exception):
	pass

class IconNotFoundError(Exception):
	pass

class SteamInstallation():
	def __init__(self, path: Path):
		self.steamdir = path
		try:
			with self.app_info_path.open('rb') as app_info_file:
				try:
					self.app_info = appinfo.load(app_info_file)
					self.app_info_available = True
				except ValueError:
					#This will be thrown by steamfiles.appinfo if the appinfo.vdf structure is different than expected, which apparently has happened in earlier versions of it, so I should probably be prepared for that
					self.app_info = None
					self.app_info_available = False
		except FileNotFoundError:
			self.app_info = None
			self.app_info_available = False
		try:
			with self.config_path.open('rt', encoding='utf-8') as config_file:
				self.config = acf.load(config_file)
				self.config_available = True
		except FileNotFoundError:
			self.config = None
			self.config_available = False
		try:
			with self.localization_path.open('rt', encoding='utf8') as localization_file:
				self.localization = acf.load(localization_file)
				self.localization_available = True
		except FileNotFoundError:
			self.localization = None
			self.localization_available = False

	@property
	def app_info_path(self) -> Path:
		return self.steamdir.joinpath('appcache', 'appinfo.vdf')

	@property
	def config_path(self) -> Path:
		return self.steamdir.joinpath('config', 'config.vdf')

	@property
	def localization_path(self) -> Path:
		return self.steamdir.joinpath('appcache', 'localization.vdf')

	@property
	def icon_folder(self) -> Path:
		return self.steamdir.joinpath('steam', 'games')

	@property
	def library_cache_folder(self) -> Path:
		return self.steamdir.joinpath('appcache', 'librarycache')

	@property
	def steam_library_list_path(self) -> Path:
		return self.steamdir.joinpath('steamapps', 'libraryfolders.vdf')

	@property
	def userdata_folder(self) -> Path:
		return self.steamdir.joinpath('userdata')

	@property
	def user_ids(self) -> Collection[str]:
		#Probably the most lazy way to do it, but if this is a bad idea, please don't send me to jail
		return {user.name for user in self.userdata_folder.iterdir() if user.name != 'ac'}

	def get_user_library_cache_folder(self, user_id: str) -> Path:
		return self.userdata_folder.joinpath(user_id, 'config', 'librarycache')

	def iter_steam_library_folders(self) -> Iterator[Path]:
		with self.steam_library_list_path.open('rt', encoding='utf-8') as steam_library_list_file:
			steam_library_list = acf.load(steam_library_list_file)
			library_folders = steam_library_list.get('libraryfolders')
			if library_folders:
				#Should always happen unless the format of this file changes
				for k, v in library_folders.items():
					if k.isnumeric():
						yield Path(v['path'])
		yield self.steamdir

	@property
	def steamplay_overrides(self) -> Mapping[str, str]:
		if not self.config_available:
			return {}

		try:
			mapping = self.config['InstallConfigStore']['Software']['Valve']['Steam']['CompatToolMapping']

			return {k: v.get('name') for k, v in mapping.items()}
		except KeyError:
			return {}

	@property
	def _steamplay_appinfo_extended(self) -> Optional[Mapping[bytes, Any]]:
		steamplay_manifest_appid = 891390

		steamplay_appinfo = self.app_info.get(steamplay_manifest_appid)
		if steamplay_appinfo is None:
			return None
		sections = steamplay_appinfo.get('sections')
		if sections is None:
			return None
		app_info_section = sections.get(b'appinfo')
		if app_info_section is None:
			return None
		return app_info_section.get(b'extended')

	@property
	def steamplay_compat_tools(self) -> Mapping[str, tuple[Optional[int], Optional[str], Optional[str], Optional[str]]]:
		extended = self._steamplay_appinfo_extended
		if not extended:
			return {}
		compat_tools_list = extended.get(b'compat_tools')
		if not compat_tools_list:
			return {}

		tools = {}
		for k, v in compat_tools_list.items():
			#appid, to_oslist might be useful in some situation
			#This just maps "proton_37" to "Proton 3.7-8" etc
			display_name = v.get(b'display_name')
			appid = v.get(b'appid')
			from_oslist = v.get(b'from_oslist')
			to_oslist = v.get(b'to_oslist')
			tools[k.decode('utf-8', errors='ignore')] = (appid.data if appid else None, display_name.decode('utf-8', errors='ignore') if display_name else None, from_oslist.decode('utf-8', errors='ignore') if from_oslist else None, to_oslist.decode('utf-8', errors='ignore') if to_oslist else None)
		return tools

	@property
	def steamplay_whitelist(self) -> Mapping[str, str]:
		extended = self._steamplay_appinfo_extended
		if not extended:
			return {}
		app_mappings = extended.get(b'app_mappings')
		if not app_mappings:
			return {}

		apps = {}
		for k, v in app_mappings.items():
			#v has an "appid" key which seems pointless, but oh well
			#Only other keys are "config" which is "none" except for Google Earth VR so whatevs, "comment" which is the game name but might have inconsistent formatting, and "platform" which is only Linux
			tool = v.get(b'tool')
			if tool:
				apps[k.decode('utf-8', errors='ignore')] = tool.decode('utf-8', errors='ignore')
		return apps

	def find_image(self, appid: int, image_name: str) -> Optional[Path]:
		basename = self.library_cache_folder.joinpath(f'{appid}_{image_name}')
		#Can be either png or jpg, I guess… could also listdir or glob I guess but ehhh brain broke lately
		for ext in ('png', 'jpg', 'jpeg'):
			path = basename.with_suffix('.' + ext)
			if path.is_file():
				return path
		return None

	def look_for_icon(self, icon_hash: str) -> Optional[Union['Image.Image', str]]:
		icon_hash = icon_hash.lower()
		for icon_path in self.icon_folder.iterdir():
			if icon_path.stem.lower() == icon_hash and icon_path.suffix in {'.ico', '.png', '.zip'}:
				is_zip = zipfile.is_zipfile(icon_path)
				#Can't just rely on the extension because some zip files like to hide and pretend to be .ico files for some reason

				with icon_path.open('rb') as test:
					magic = test.read(4)
					if magic == b'Rar!':
						raise IconError(f'icon {icon_hash} is secretly a RAR file and cannot be opened')

				if icon_path.suffix == '.ico' and not is_zip:
					if have_pillow:
						#.ico files can be a bit flaky with Tumbler thumbnails and some other image-reading stuff, so if we can convert them, that might be a good idea just in case (well, there definitely are some icons that don't thumbnail properly so yeah)
						try:
							image = Image.open(icon_path)
							return image
						except (ValueError, OSError) as ex:
							#Try and handle the "This is not one of the allowed sizes of this image" error caused by .ico files having incorrect headers which I guess happens more often than I would have thought otherwise
							#This is gonna get ugly
							try:
								#Use BytesIO here to prevent "seeking a closed file" errors, which is probably a sign that I don't actually know what I'm doing
								ico = IcoImagePlugin.IcoFile(io.BytesIO(icon_path.read_bytes()))
								biggest_size = (0, 0)
								for size in ico.sizes():
									if size[0] > biggest_size[0] and size[1] > biggest_size[1]:
										biggest_size = size
								if biggest_size == (0, 0):
									raise IconError(f'.ico file {icon_path} has no valid sizes') from ex
								return ico.getimage(biggest_size)
							except SyntaxError as syntax_error:
								#Of all the errors it throws, it throws this one? Well, okay fine whatever
								raise IconError(f'.ico file {icon_path} is not actually an .ico file at all') from syntax_error
						except Exception as ex:
							#Guess it's still broken
							raise IconError(f'.ico file {icon_path} has some annoying error: {ex}') from ex
					return icon_path

				if not is_zip:
					return icon_path

				with zipfile.ZipFile(icon_path, 'r') as zip_file:
					#TODO: Should just make this a comprehension I think, and for that matter could just be a generator since we are only passing it to max
					icon_files: set[zipfile.ZipInfo] = set()
					for zip_info in zip_file.infolist():
						if zip_info.is_dir():
							continue
						if zip_info.filename.startswith('__MACOSX'):
							#Yeah that happens with retail Linux games apparently
							continue
						if zip_info.filename.lower().endswith(('.ico', '.png')):
							icon_files.add(zip_info)

					#Get the biggest image file and assume that's the best icon we can have
					#extracted_icon_file = sorted(icon_files, key=lambda zip_info: zip_info.file_size, reverse=True)[0]
					extracted_icon_file = max(icon_files, key=attrgetter('file_size'))
					extracted_icon_folder = main_config.image_folder.joinpath('Icon', 'extracted_from_zip', icon_hash)
					return zip_file.extract(extracted_icon_file, path=extracted_icon_folder)

		raise IconNotFoundError(f'{icon_hash} not found')
