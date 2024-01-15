#!/usr/bin/env python3

import logging
from collections.abc import Iterator, Sequence
from pathlib import Path

from meowlauncher.config import main_config
from meowlauncher.exceptions import GameNotSupportedError
from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.game_sources.settings import (
	GOGConfig,
	default_gog_folder,
	default_wine_gog_folder,
)
from meowlauncher.games.gog import (
	DOSBoxGOGGame,
	GameInfoFile,
	GOGGame,
	LinuxGOGLauncher,
	NormalGOGGame,
	ScummVMGOGGame,
	WindowsGOGGame,
	WindowsGOGLauncher,
	WineGOGGame,
)
from meowlauncher.util.desktop_files import has_been_done

logger = logging.getLogger(__name__)


class LinuxGOG(GameSource):
	def __init__(self, config: GOGConfig) -> None:
		self.config: GOGConfig = config

	@classmethod
	def name(cls) -> str:
		return 'Linux GOG'

	@property
	def is_available(self) -> bool:
		return any(folder.is_dir() for folder in self.config.folders)

	def no_longer_exists(self, game_id: str) -> bool:
		return not Path(game_id).exists()

	def look_in_linux_gog_folder(self, folder: Path) -> GOGGame | None:
		"""Finds a GOGGame inside folder, if it is a GOG game folder, or None"""
		gameinfo_path = folder.joinpath('gameinfo')
		if not gameinfo_path.is_file():
			return None
		gameinfo = GameInfoFile(gameinfo_path)

		launch_script = folder.joinpath('start.sh')
		if not launch_script.is_file():
			return None

		# .mojosetup, uninstall-*.sh, docs are also here
		support_folder = folder.joinpath('support')
		if not support_folder.is_dir():
			return None

		if folder.joinpath('dosbox').is_dir():
			return DOSBoxGOGGame(folder, gameinfo, launch_script, support_folder, self.config)
		if folder.joinpath('scummvm').is_dir():
			return ScummVMGOGGame(folder, gameinfo, launch_script, support_folder, self.config)
		if folder.joinpath('game').is_dir():
			if folder.joinpath('game', 'Wine').is_dir():
				return WineGOGGame(folder, gameinfo, launch_script, support_folder, self.config)
			return NormalGOGGame(folder, gameinfo, launch_script, support_folder, self.config)

		return None

	def iter_games(self) -> 'Iterator[GOGGame]':
		for gog_folder in self.config.folders:
			if not gog_folder.is_dir():
				if gog_folder != default_gog_folder:
					logger.warning('%s does not exist/is not a directory', gog_folder)
				continue

			for subfolder in gog_folder.iterdir():
				if not main_config.full_rescan and has_been_done('GOG', str(subfolder)):
					continue
				if not subfolder.is_dir():
					continue
				if not (game := self.look_in_linux_gog_folder(subfolder)):
					logger.info(
						'GOG subfolder does not have a GOG game (detection may have failed): %s',
						subfolder,
					)
					continue

				game.add_info()
				yield game

	def iter_all_launchers(self) -> 'Iterator[LinuxGOGLauncher]':
		for game in self.iter_games():
			yield LinuxGOGLauncher(game)


class WindowsGOG(GameSource):
	def __init__(self, config: GOGConfig) -> None:
		self.config: GOGConfig = config

	@classmethod
	def name(cls) -> str:
		return 'Windows GOG'

	@property
	def is_available(self) -> bool:
		return any(folder.is_dir() for folder in self.config.windows_gog_folders)

	def no_longer_exists(self, game_id: str) -> bool:
		return not Path(game_id).exists()

	def look_in_windows_gog_folder(self, folder: Path) -> WindowsGOGGame | None:
		"""Checks if folder has a goggame-<gameid>.info file in it and returns WindowsGOGGame if so"""
		info_file = next(
			(
				file
				for file in folder.iterdir()
				if file.stem.startswith('goggame-') and file.suffix == '.info'
			),
			None,
		)
		# Other files that may exist: goggame-<gameid>.dll, goggame-<gameid>.hashdb (Galaxy related?), goggame-<gameid>.ico (but this is a generic GOG icon), goglog.ini, goggame-galaxyFileList.ini, goggame.sdb, unins000.exe, unins000.dat, unins000.msg, other stuff that user probably actually wants to delete because it sucks
		if not info_file:
			# There are actually instances where this isn't here: Bonus content items (Prisoner of Ice UK version, SOTC Floppy version, etc) but I don't really know what to do with those right now to be quite honest, I guess I could look for "Launch <blah>.lnk" and extract which game to launch from there? But that's weird
			# Or user could have deleted it
			return None
		game_id = info_file.stem.removeprefix('goggame-')
		return WindowsGOGGame(folder, info_file, game_id, self.config)

	def iter_games(self) -> Iterator[WindowsGOGGame]:
		for windows_gog_folder in self.config.windows_gog_folders:
			if not windows_gog_folder.is_dir():
				if windows_gog_folder != default_wine_gog_folder:
					logger.warning('%s does not exist/is not a directory', windows_gog_folder)
				continue

			for subfolder in windows_gog_folder.iterdir():
				if not main_config.full_rescan and has_been_done('GOG', str(subfolder)):
					continue
				if not subfolder.is_dir():
					continue
				if not (windows_game := self.look_in_windows_gog_folder(subfolder)):
					logger.info(
						'GOG subfolder does not have a GOG game (detection may have failed): %s',
						subfolder,
					)
					continue

				windows_game.add_info()
				yield windows_game

	def iter_all_launchers(self) -> Iterator[WindowsGOGLauncher]:
		for game in self.iter_games():
			try:
				yield WindowsGOGLauncher(game)
			except GameNotSupportedError:
				logger.exception('Game %s not supported', game)


class GOG(CompoundGameSource):
	"""Locally installed GOG games"""

	config: GOGConfig

	@classmethod
	def config_class(cls) -> type[GOGConfig]:
		return GOGConfig

	@property
	def sources(self) -> Sequence[GameSource]:
		return (LinuxGOG(self.config), WindowsGOG(self.config))
