from abc import ABC, abstractmethod
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, final

from meowlauncher.common_types import MediaType
from meowlauncher.game import Game
from meowlauncher.info import Date
from meowlauncher.launcher import Launcher
from meowlauncher.util.name_utils import fix_name

if TYPE_CHECKING:
	from collections.abc import Collection, Mapping

	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.configured_emulator import ConfiguredEmulator


class ManuallySpecifiedGame(Game, ABC):
	def __init__(self, json: 'Mapping[str, Any]', platform_config: 'PlatformConfig'):
		self.platform_config = platform_config
		self.json = json
		self.is_on_cd: bool = json.get('is_on_cd', False)
		self.path: str = json[
			'path'
		]  # Could be a host path (e.g. DOS) or could be some special path particular to that platform (e.g. Mac using PathInsideHFS, DOS using paths inside CDs when is_on_cd)
		self.args = json.get('args', [])
		self.cd_path: Path | None = None
		self.other_cd_paths: 'Collection[PurePath]' = (
			set()
		)  # Could be None I guess, if cd_path not in info
		if 'cd_path' in json:
			_cd_paths = json['cd_path'] if isinstance(json['cd_path'], list) else [json['cd_path']]
			cd_paths = tuple(
				self.base_folder.joinpath(cd_path)
				if self.base_folder and not cd_path.startswith('/')
				else cd_path
				for cd_path in _cd_paths
			)
			self.cd_path = Path(cd_paths[0])
			self.other_cd_paths = cd_paths[1:]
		elif self.is_on_cd:
			raise KeyError('cd_path is mandatory if is_on_cd is true')
		self._name: str = json.get('name', fix_name(self.fallback_name))

	@property
	def name(self) -> str:
		return self._name

	def __str__(self) -> str:
		return f'{self.path} ({self.name})'

	@property
	def base_folder(self) -> Path | None:
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
	def add_info(self) -> None:
		self.info.platform = self.platform_config.name  # TODO Not necessarily a thing
		self.info.media_type = MediaType.Executable
		if 'developer' in self.json:
			self.info.developer = self.json['developer']
		if 'publisher' in self.json:
			self.info.publisher = self.json['publisher']
		if 'year' in self.json:
			self.info.release_date = Date(self.json['year'])
		if 'category' in self.json:
			self.info.categories = [self.json['category']]
		if 'genre' in self.json:
			self.info.genre = self.json['genre']
		if 'subgenre' in self.json:
			self.info.subgenre = self.json['subgenre']
		if 'notes' in self.json:
			self.info.add_notes(self.json['notes'])
		self.additional_info()

	@property
	def is_valid(self) -> bool:
		"To be overriden by subclass - return true if this config is pointing to something that actually exists"
		return Path(self.path).is_file()

	@abstractmethod
	def additional_info(self) -> None:
		"To be overriden by subclass - optional, put any other platform-specific info you want in here"


class ManuallySpecifiedLauncher(Launcher):
	def __init__(
		self,
		app: ManuallySpecifiedGame,
		emulator: 'ConfiguredEmulator',
		platform_config: 'PlatformConfig',
	) -> None:
		self.game: ManuallySpecifiedGame = app
		self.platform_name = platform_config.name
		super().__init__(app, emulator)

	@property
	# Could do as a default, or maybe you should override it
	def game_id(self) -> str:
		if self.game.is_on_cd:
			# Need the game ID to show it's on a CD otherwise non_existent_games won't work
			return f'{self.game.cd_path}:{self.game.path}'
		return self.game.path
