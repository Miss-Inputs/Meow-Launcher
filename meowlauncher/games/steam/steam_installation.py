import io
import logging
import re
import zipfile
from collections.abc import Collection, Iterator, Mapping
from operator import attrgetter
from pathlib import Path
from typing import Any

from steamfiles import acf, appinfo

try:
	from PIL import IcoImagePlugin, Image

	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config import main_config

from .steam_types import StateFlags

logger = logging.getLogger(__name__)


class IconError(Exception):
	pass


class IconNotFoundError(Exception):
	pass


class SteamInstallation:
	"""Stores the parsed results of various Steam files in a given install directory"""

	def __init__(self, path: Path):
		self.steamdir = path
		try:
			self.app_info = appinfo.loads(self.app_info_path.read_bytes())
			self.app_info_available = True
		except (FileNotFoundError, ValueError):
			# ValueError will be thrown by steamfiles.appinfo if the appinfo.vdf structure is different than expected, which apparently has happened in earlier versions of it, so I should probably be prepared for that
			self.app_info = None
			self.app_info_available = False
		self.config: dict[str, Any] | None
		try:
			# That part manspreads over multiple lines and breaks steamfiles parsing which is annoying
			config_file = re.sub(
				r'\n\s*"SDL_GamepadBind"\s+"(?:[^"]+|[\r\n]+)"',
				'',
				self.config_path.read_text(encoding='utf-8'),
			)
			self.config = acf.loads(config_file)
		except FileNotFoundError:
			self.config = None
		self.localization: dict[str, Any] | None
		try:
			self.localization = acf.loads(self.localization_path.read_text('utf-8'))
		except FileNotFoundError:
			self.localization = None

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
		# Probably the most lazy way to do it, but if this is a bad idea, please don't send me to jail
		return {user.name for user in self.userdata_folder.iterdir() if user.name != 'ac'}

	def get_user_library_cache_folder(self, user_id: str) -> Path:
		return self.userdata_folder.joinpath(user_id, 'config', 'librarycache')

	def iter_steam_library_folders(self) -> Iterator[Path]:
		steam_library_list = acf.loads(self.steam_library_list_path.read_text('utf-8'))
		library_folders = steam_library_list.get('libraryfolders')
		if library_folders:
			# Should always happen unless the format of this file changes
			for k, v in library_folders.items():
				if k.isnumeric():
					yield Path(v['path'])
		# yield self.steamdir #No, it'll do that by itself now

	@property
	def steamplay_overrides(self) -> Mapping[str, str]:
		if not self.config:
			return {}

		try:
			mapping = self.config['InstallConfigStore']['Software']['Valve']['Steam'][
				'CompatToolMapping'
			]

			return {k: v.get('name') for k, v in mapping.items()}
		except KeyError:
			return {}

	@property
	def _steamplay_appinfo_extended(self) -> Mapping[bytes, Any] | None:
		steamplay_manifest_appid = 891390

		if not self.app_info:
			return None
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
	def steamplay_compat_tools(
		self,
	) -> Mapping[str, tuple[int | None, str | None, str | None, str | None]]:
		extended = self._steamplay_appinfo_extended
		if not extended:
			return {}
		compat_tools_list = extended.get(b'compat_tools')
		if not compat_tools_list:
			return {}

		tools = {}
		for k, v in compat_tools_list.items():
			# appid, to_oslist might be useful in some situation
			# This just maps "proton_37" to "Proton 3.7-8" etc
			display_name = v.get(b'display_name')
			appid = v.get(b'appid')
			from_oslist = v.get(b'from_oslist')
			to_oslist = v.get(b'to_oslist')
			tools[k.decode('utf-8', errors='backslashreplace')] = (
				appid.data if appid else None,
				display_name.decode('utf-8', errors='backslashreplace') if display_name else None,
				from_oslist.decode('utf-8', errors='backslashreplace') if from_oslist else None,
				to_oslist.decode('utf-8', errors='backslashreplace') if to_oslist else None,
			)
		return tools

	@property
	def steamplay_whitelist(self) -> 'Mapping[str, str]':
		extended = self._steamplay_appinfo_extended
		if not extended:
			return {}
		app_mappings = extended.get(b'app_mappings')
		if not app_mappings:
			return {}

		apps = {}
		for k, v in app_mappings.items():
			# v has an "appid" key which seems pointless, but oh well
			# Only other keys are "config" which is "none" except for Google Earth VR so whatevs, "comment" which is the game name but might have inconsistent formatting, and "platform" which is only Linux
			tool = v.get(b'tool')
			if tool:
				apps[k.decode('utf-8', 'backslashreplace')] = tool.decode(
					'utf-8', 'backslashreplace'
				)
		return apps

	def iter_steam_installed_appids(self) -> Iterator[tuple[Path, int, Mapping[str, Any]]]:
		compat_tool_appids = {
			compat_tool[0] for compat_tool in self.steamplay_compat_tools.values() if compat_tool[0]
		}

		for library_folder in self.iter_steam_library_folders():
			for acf_file_path in library_folder.joinpath('steamapps').glob('*.acf'):
				# Technically I could try and parse it without steamfiles, but that would be irresponsible, so I shouldn't do that
				app_manifest = acf.loads(acf_file_path.read_text('utf-8'))
				app_state = app_manifest.get('AppState')
				if not app_state:
					# Should only happen if .acf is junk (or format changes dramatically), there's no other keys than AppState
					logger.error(
						'This should not happen %s is invalid or format is weird and new and spooky, has no AppState',
						acf_file_path,
					)
					continue

				appid_str = app_state.get('appid')
				if appid_str is None:
					# Yeah we need that
					logger.error(
						'%s %s has no appid which is weird and this should not happen',
						acf_file_path,
						app_state.get('name'),
					)
					continue

				try:
					appid = int(appid_str)
				except ValueError:
					logger.error(
						'Skipping %s %s %s as appid is not numeric which is weird',
						acf_file_path,
						app_state.get('name'),
						appid_str,
					)
					continue

				if appid in compat_tool_appids:
					continue

				try:
					state_flags = StateFlags(int(app_state.get('StateFlags')))
					if not state_flags:
						continue
				except ValueError:
					logger.info(
						'Skipping %s %s as StateFlags are invalid: %s',
						app_state.get('name'),
						appid,
						app_state.get('StateFlags'),
					)
					continue

				# Only yield fully installed games
				if (state_flags & StateFlags.FullyInstalled) == 0:
					logger.info(
						'Skipping %s %s as it is not actually installed (StateFlags = %s)',
						app_state.get('name'),
						appid,
						state_flags,
					)
					continue

				if state_flags & StateFlags.SharedOnly:
					logger.info(
						'Skipping %s %s as it is shared only (StateFlags = %s)',
						app_state.get('name'),
						appid,
						state_flags,
					)
					continue

				yield library_folder, appid, app_state

	def find_image(self, appid: int, image_name: str) -> Path | None:
		basename = self.library_cache_folder.joinpath(f'{appid}_{image_name}')
		# Can be either png or jpg, I guess… could also listdir or glob I guess but ehhh brain broke lately
		for ext in ('png', 'jpg', 'jpeg'):
			path = basename.with_suffix('.' + ext)
			if path.is_file():
				return path
		return None

	def look_for_icon(self, icon_hash: str) -> 'Image.Image | Path | None':
		icon_hash = icon_hash.lower()
		for icon_path in self.icon_folder.iterdir():
			if icon_path.stem.lower() == icon_hash and icon_path.suffix in {'.ico', '.png', '.zip'}:
				is_zip = zipfile.is_zipfile(icon_path)
				# Can't just rely on the extension because some zip files like to hide and pretend to be .ico files for some reason

				with icon_path.open('rb') as test:
					magic = test.read(4)
					if magic == b'Rar!':
						raise IconError(
							f'icon {icon_hash} is secretly a RAR file and cannot be opened'
						)

				if icon_path.suffix == '.ico' and not is_zip:
					if have_pillow:
						# .ico files can be a bit flaky with Tumbler thumbnails and some other image-reading stuff, so if we can convert them, that might be a good idea just in case (well, there definitely are some icons that don't thumbnail properly so yeah)
						try:
							image = Image.open(icon_path)
						except (ValueError, OSError) as ex:
							# Try and handle the "This is not one of the allowed sizes of this image" error caused by .ico files having incorrect headers which I guess happens more often than I would have thought otherwise
							# This is gonna get ugly
							try:
								# Use BytesIO here to prevent "seeking a closed file" errors, which is probably a sign that I don't actually know what I'm doing
								ico = IcoImagePlugin.IcoFile(io.BytesIO(icon_path.read_bytes()))
								biggest_size = (0, 0)
								for size in ico.sizes():
									if size[0] > biggest_size[0] and size[1] > biggest_size[1]:
										biggest_size = size
								if biggest_size == (0, 0):
									raise IconError(
										f'.ico file {icon_path} has no valid sizes'
									) from ex
								return ico.getimage(biggest_size)
							except SyntaxError as syntax_error:
								# Of all the errors it throws, it throws this one? Well, okay fine whatever
								raise IconError(
									f'.ico file {icon_path} is not actually an .ico file at all'
								) from syntax_error
						except Exception as ex:
							# Guess it's still broken
							raise IconError(
								f'.ico file {icon_path} has some annoying error: {ex}'
							) from ex
						else:
							return image
					return icon_path

				if not is_zip:
					return icon_path

				with zipfile.ZipFile(icon_path, 'r') as zip_file:
					# TODO: Should just make this a comprehension I think, and for that matter could just be a generator since we are only passing it to max
					icon_files: set[zipfile.ZipInfo] = set()
					for zip_info in zip_file.infolist():
						if zip_info.is_dir():
							continue
						if zip_info.filename.startswith('__MACOSX'):
							# Yeah that happens with retail Linux games apparently
							continue
						if zip_info.filename.lower().endswith(('.ico', '.png')):
							icon_files.add(zip_info)

					# Get the biggest image file and assume that's the best icon we can have
					# extracted_icon_file = sorted(icon_files, key=lambda zip_info: zip_info.file_size, reverse=True)[0]
					extracted_icon_file = max(icon_files, key=attrgetter('file_size'))
					extracted_icon_folder = main_config.image_folder.joinpath(
						'Icon', 'extracted_from_zip', icon_hash
					)
					return Path(zip_file.extract(extracted_icon_file, path=extracted_icon_folder))

		raise IconNotFoundError(f'{icon_hash} not found')
