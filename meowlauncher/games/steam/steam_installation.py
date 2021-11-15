import os
from collections.abc import Mapping
from typing import Optional, Any
from pathlib import Path

from steamfiles import acf, appinfo

class SteamInstallation():
	def __init__(self, path: Path):
		self.steamdir = path
		try:
			with open(self.app_info_path, 'rb') as app_info_file:
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
			with open(self.config_path, 'rt', encoding='utf-8') as config_file:
				self.config = acf.load(config_file)
				self.config_available = True
		except FileNotFoundError:
			self.config = None
			self.config_available = False
		try:
			with open(self.localization_path, 'rt', encoding='utf8') as localization_file:
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

	def get_users(self) -> list[str]:
		#Probably the most lazy way to do it, but if this is a bad idea, please don't send me to jail
		return [user for user in os.listdir(self.userdata_folder) if user != 'ac']

	def get_user_library_cache_folder(self, user_id: str) -> Path:
		return self.userdata_folder.joinpath(user_id, 'config', 'librarycache')

	@property
	def steam_library_folders(self) -> list[Path]:
		with open(self.steam_library_list_path, 'rt', encoding='utf-8') as steam_library_list_file:
			steam_library_list = acf.load(steam_library_list_file)
			library_folders = steam_library_list.get('libraryfolders')
			if not library_folders:
				#Shouldn't happen unless the format of this file changes
				return [self.steamdir]
			return [Path(v['path']) for k, v in library_folders.items() if k.isdigit()] + [self.steamdir]

	@property
	def steamplay_overrides(self) -> dict:
		if not self.config_available:
			return {}

		try:
			mapping = self.config['InstallConfigStore']['Software']['Valve']['Steam']['CompatToolMapping']

			overrides = {}
			for k, v in mapping.items():
				overrides[k] = v.get('name')
			return overrides
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
	def steamplay_compat_tools(self) -> dict[str, tuple[Optional[int], Optional[str], Optional[str], Optional[str]]]:
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
	def steamplay_whitelist(self) -> dict[str, str]:
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
		if self.library_cache_folder:
			basename = self.library_cache_folder.joinpath(f'{appid}_{image_name}')
			#Can be either png or jpg, I guess… could also listdir or glob I guess but ehhh brain broke lately
			for ext in ('png', 'jpg', 'jpeg'):
				path = basename.with_suffix('.' + ext)
				if os.path.isfile(path):
					return path
		return None
