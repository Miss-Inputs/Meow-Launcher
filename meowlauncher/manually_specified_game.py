import os
from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Optional, final

from meowlauncher.common_types import MediaType
from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.metadata import Date
from meowlauncher.util.name_utils import fix_name

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.configured_emulator import ConfiguredEmulator

class ManuallySpecifiedGame(EmulatedGame, ABC):
	#TODO: Should not necessarily be emulated
	def __init__(self, info: Mapping[str, Any], platform_config: 'PlatformConfig'):
		super().__init__(platform_config)
		self.info = info
		self.is_on_cd: bool = info.get('is_on_cd', False)
		self.path: str = info['path'] #Could be a host path (e.g. DOS) or could be some special path particular to that platform (e.g. Mac using PathInsideHFS, DOS using paths inside CDs when is_on_cd)
		self.args = info.get('args', [])
		self.cd_path: Optional[Path] = None
		self.other_cd_paths: Collection[PurePath] = set() #Could be None I guess, if cd_path not in info
		if 'cd_path' in info:
			_cd_paths = info['cd_path'] if isinstance(info['cd_path'], list) else [info['cd_path']]
			cd_paths = tuple(self.base_folder.joinpath(cd_path) if self.base_folder and not cd_path.startswith('/') else cd_path for cd_path in _cd_paths)
			self.cd_path = Path(cd_paths[0])
			self.other_cd_paths = cd_paths[1:]
		elif self.is_on_cd:
			raise KeyError('cd_path is mandatory if is_on_cd is true')
		self._name: str = info.get('name', fix_name(self.fallback_name))

	@property
	def name(self) -> str:
		return self._name

	def __str__(self) -> str:
		return f'{self.path} ({self.name})'

	@property
	def base_folder(self) -> Optional[Path]:
		"""
		Might want to override this in subclass, returns a folder on the host that might have other files related to the game (CD images, etc)
		Return None if this is not relevant
		"""
		return Path(self.path).parent

	@property
	def fallback_name(self) -> str:
		"""
		Might want to override in subclass, maybe not - return something that should be used as the name if the user doesn't put any name in the config
		By default, path stem
		"""
		return PurePath(self.path).stem
	
	@final
	def add_metadata(self) -> None:
		self.metadata.platform = self.platform_config.name #TODO Not necessarily a thing
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
		'To be overriden by subclass - return true if this config is pointing to something that actually exists'
		return os.path.isfile(self.path)

	@abstractmethod
	def additional_metadata(self) -> None:
		'To be overriden by subclass - optional, put any other platform-specific metadata you want in here'

class ManuallySpecifiedLauncher(EmulatorLauncher):
	def __init__(self, app: ManuallySpecifiedGame, emulator: 'ConfiguredEmulator', platform_config: 'PlatformConfig') -> None:
		self.game: ManuallySpecifiedGame = app
		self.platform_name = platform_config.name
		super().__init__(app, emulator, platform_config.options)
		
	@property
	#Could do as a default, or maybe you should override it
	def game_id(self) -> str:
		return self.game.path

	@final
	@property
	def game_type(self) -> str:
		return self.platform_name
