import os
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Optional, final

from meowlauncher.common_types import MediaType
from meowlauncher.config.platform_config import PlatformConfig
from meowlauncher.configured_emulator import ConfiguredEmulator
from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.metadata import Date
from meowlauncher.util.name_utils import fix_name


class App(EmulatedGame, ABC):
	def __init__(self, info: Mapping[str, Any]):
		super().__init__()
		self.info = info
		self.is_on_cd: bool = info.get('is_on_cd', False)
		self.path = info['path']
		self.args = info.get('args', [])
		self.cd_path: Optional[str] = None
		self.other_cd_paths: list[str] = []
		if 'cd_path' in info:
			cd_paths = info['cd_path'] if isinstance(info['cd_path'], list) else [info['cd_path']]
			cd_paths = [os.path.join(self.base_folder, cd_path) if self.base_folder and not cd_path.startswith('/') else cd_path for cd_path in cd_paths]
			self.cd_path = cd_paths[0]
			self.other_cd_paths = cd_paths[1:]
		elif self.is_on_cd:
			raise KeyError('cd_path is mandatory if is_on_cd is true')
		self._name = info.get('name', fix_name(self.get_fallback_name()))

	@property
	def name(self) -> str:
		return self._name

	@property
	def base_folder(self) -> str:
		#Might want to override this in subclass, returns a folder on the host that might have other files related to the game (CD images, etc)
		#Return none if this is not relevant
		return os.path.dirname(self.path)

	def get_fallback_name(self) -> str:
		#Might want to override in subclass, maybe not - return something that should be used as the name if the user doesn't put any name in the config
		return os.path.basename(self.path)
	
	def get_launcher_id(self) -> str:
		#For overriding in subclass (but maybe this will do as a default), for Unique-ID in [X-Meow Launcher ID] section of launcher
		return self.path

	@final
	def add_metadata(self) -> None:
		self.metadata.media_type = MediaType.Executable
		if 'developer' in self.info:
			self.metadata.developer = self.info['developer']
		if 'publisher' in self.info:
			self.metadata.publisher = self.info['publisher']
		if 'year' in self.info:
			self.metadata.release_date = Date(self.info['year'])
		if 'category' in self.info:
			self.metadata.categories = [self.info['category']]
		if 'genre' in self.info:
			self.metadata.genre = self.info['genre']
		if 'subgenre' in self.info:
			self.metadata.subgenre = self.info['subgenre']
		if 'notes' in self.info:
			self.metadata.add_notes(self.info['notes'])
		self.additional_metadata()

	@property
	def is_valid(self) -> bool:
		#To be overriden by subclass - return true if this config is pointing to something that actually exists
		return os.path.isfile(self.path)

	@abstractmethod
	def additional_metadata(self) -> None:
		#To be overriden by subclass - optional, put any other platform-specific metadata you want in here
		pass

class AppLauncher(EmulatorLauncher):
	def __init__(self, app: App, emulator: ConfiguredEmulator, platform_config: PlatformConfig) -> None:
		self.game: App = app
		self.platform = platform_config.name
		super().__init__(app, emulator, platform_config.options)
		
	@property
	#Could do as a default, or maybe you should override it
	def game_id(self) -> str:
		return self.game.path

	@final
	@property
	def game_type(self) -> str:
		return self.platform
