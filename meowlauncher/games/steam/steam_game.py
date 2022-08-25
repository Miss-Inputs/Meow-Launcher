from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Optional

from meowlauncher.common_types import MediaType
from meowlauncher.config.main_config import main_config
from meowlauncher.config_types import RunnerConfig
from meowlauncher.configured_runner import ConfiguredRunner
from meowlauncher.game import Game
from meowlauncher.games.common.engine_detect import detect_engine_recursively
from meowlauncher.games.common.pc_common_metadata import \
    check_for_interesting_things_in_folder
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.launcher import Launcher
from meowlauncher.runner import Runner
from meowlauncher.util.name_utils import fix_name

if TYPE_CHECKING:
	from .steam_installation import SteamInstallation

@dataclass(frozen=True)
class LauncherInfo():
	exe: Optional[PurePath]
	args: Optional[str] #Not a list as it turns out?
	description: Optional[str]
	launcher_type: Optional[str]
	platform: Optional[str]

class SteamGame(Game):
	def __init__(self, appid: int, folder: Path, app_state: Mapping[str, Any], steam_installation: 'SteamInstallation') -> None:
		super().__init__()
		self.appid = appid
		self.library_folder = folder
		self.app_state = app_state
		self.steam_installation = steam_installation

		#TODO: These should probably be returned from some method instead
		self.launchers: MutableMapping[Optional[str], LauncherInfo] = {}
		self.extra_launchers: MutableMapping[Optional[str], list[LauncherInfo]] = {}

	@property
	def name(self) -> str:
		name = self.app_state.get('name')
		if not name:
			name = f'<unknown game {self.appid}>'
		name = fix_name(name)
		return name

	@property
	def install_dir(self) -> Path:
		return self.library_folder.joinpath('steamapps', 'common', self.app_state['installdir'])

	@cached_property
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

	@property
	def _appinfo_common_section(self) -> Optional[Mapping[bytes, Any]]:
		if not self.appinfo:
			return None
		return self.appinfo.get(b'common')

	@property
	def type(self) -> str:
		if not self._appinfo_common_section:
			return 'Game' #Assumed
		return self._appinfo_common_section.get(b'type', b'Unknown').decode('utf-8', errors='backslashreplace')

	def add_metadata(self) -> None:
		#Hmmm… may make sense for this to go on individual SteamLauncher, if we add some metadata based on that
		self.metadata.specific_info['Steam AppID'] = self.appid
		self.metadata.specific_info['Library Folder'] = self.library_folder
		self.metadata.media_type = MediaType.Digital
		lowviolence = self.app_state.get('UserConfig', {}).get('lowviolence')
		if lowviolence:
			self.metadata.specific_info['Low Violence?'] = lowviolence == '1'

		app_type = self.type
		#https://github.com/fire64/opensteamworks/blob/master/EAppType.h (but it is in Title Case here… usually?)
		if app_type in {'game', 'Game'}:
			#This makes the categories consistent with other stuff
			self.metadata.categories = ('Games', )
		elif app_type in {'Application', 'software'}:
			self.metadata.categories = ('Applications', )
		elif app_type == 'Tool':
			#Tool is for SDK/level editor/dedicated server/etc stuff, Application is for general purchased software
			self.metadata.categories = ('Tools', )
		elif app_type == 'Demo':
			self.metadata.categories = ('Trials', )
		elif app_type:
			self.metadata.categories = [app_type]

		try:
			self.poke_around_in_install_dir()
		except OSError as oserror:
			if main_config.debug:
				print('oh dear', oserror)

	def poke_around_in_install_dir(self) -> None:
		install_dir = self.install_dir
		if not install_dir.is_dir():
			# if main_config.debug:
			# 	print('uh oh installdir does not exist', game.name, game.app_id, folder)
			#Hmm I would need to make this case insensitive for some cases
			return

		if not self.metadata.specific_info.get('Engine'):
			engine = detect_engine_recursively(install_dir, self.metadata)
			if engine:
				self.metadata.specific_info['Engine'] = engine

		check_for_interesting_things_in_folder(install_dir, self.metadata, find_wrappers=True)
		for f in install_dir.iterdir():
			if f.is_dir():
				check_for_interesting_things_in_folder(f, self.metadata, find_wrappers=True)
		
class _SteamRunner(Runner):
	@property
	def name(self) -> str:
		return 'Steam'

class SteamLauncher(Launcher):
	def __init__(self, game: SteamGame) -> None:
		self.game: SteamGame = game
		runner = _SteamRunner()
		configured_runner = ConfiguredRunner(runner, RunnerConfig('steam'))
		super().__init__(game, configured_runner)

	@property
	def game_id(self) -> str:
		return str(self.game.appid)

	@property
	def game_type(self) -> str:
		return 'Steam'

	@property
	def command(self) -> LaunchCommand:
		#-applaunch <appid>? steam://run/<id>? Does not seem as though it lets us have arguments no matter which way you do it, so you will only ever be able to run the "main" launcher
		return LaunchCommand(self.runner.config.exe_path, [f'steam://rungameid/{self.game.appid}'])
