from collections.abc import Mapping
from pathlib import Path
from typing import Any, NamedTuple, Optional

from meowlauncher.config.main_config import main_config
from meowlauncher.game import Game
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.output.desktop_files import make_launcher
from meowlauncher.util.name_utils import fix_name

from .steam_installation import SteamInstallation


class LauncherInfo(NamedTuple):
	exe: Optional[str]
	args: Optional[str] #Not a list as it turns out?
	description: Optional[str]
	launcher_type: Optional[str]
	platform: Optional[str]

class SteamGame(Game):
	def __init__(self, appid: int, folder: Path, app_state: Mapping, steam_installation: SteamInstallation) -> None:
		super().__init__()
		self.appid = appid
		self.library_folder = folder
		self.app_state = app_state
		self.steam_installation = steam_installation
		
		self.launchers: dict[Optional[str], LauncherInfo] = {}
		self.extra_launchers: dict[Optional[str], list[LauncherInfo]] = {}

	@property
	def name(self) -> str:
		name = self.app_state.get('name')
		if not name:
			name = f'<unknown game {self.appid}>'
		name = fix_name(name)
		return name

	@property
	def install_dir(self) -> Path:
		install_dir_name = self.app_state.get('installdir')
		if not install_dir_name:
			#TODO: Does this ever happen?
			return None
		return self.library_folder.joinpath('steamapps', 'common', install_dir_name)

	@property
	def appinfo(self) -> Optional[Mapping[bytes, Any]]:
		if self.steam_installation.app_info_available:
			game_app_info = self.steam_installation.app_info.get(self.appid)
			if game_app_info is None:
				#Probably shouldn't happen if all is well and that game is supposed to be there
				if main_config.debug:
					print(self.name, self.appid, 'does not have an entry in appinfo.vdf')
				return None

			#There are other keys here too but I dunno if they're terribly useful, just stuff about size and state and access token and bleh
			#last_update is a Unix timestamp for the last time the user updated the game
			sections = game_app_info.get('sections')
			if sections is None:
				if main_config.debug:
					print(self.name, self.appid, 'does not have a sections key in appinfo.vdf')
				return None
			#This is the only key in sections, and from now on everything is a bytes instead of a str, seemingly
			app_info_section = sections.get(b'appinfo')
			if app_info_section is None:
				if main_config.debug:
					print(self.name, self.appid, 'does not have a appinfo section in appinfo.vdf sections')
				return None
			return app_info_section
		return None

	def make_launcher(self) -> None:
		params = LaunchCommand('steam', ['steam://rungameid/{0}'.format(self.appid)])
		make_launcher(params, self.name, self.metadata, 'Steam', str(self.appid))