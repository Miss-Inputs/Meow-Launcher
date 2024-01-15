import logging
import os
from abc import abstractmethod
from collections.abc import Mapping
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from meowlauncher.config import main_config
from meowlauncher.data.emulated_platforms import platforms
from meowlauncher.data.emulators import libretro_cores_by_name, standalone_emulators_by_name
from meowlauncher.emulator import LibretroCore, StandardEmulator
from meowlauncher.exceptions import (
	EmulationNotSupportedError,
	ExtensionNotSupportedError,
	NotActuallyLaunchableGameError,
)
from meowlauncher.game_source import ChooseableEmulatorGameSource, CompoundGameSource, GameSource
from meowlauncher.games.roms.rom import ROM, FolderROM, get_rom
from meowlauncher.games.roms.rom_game import ROMGame, ROMLauncher
from meowlauncher.games.roms.rom_info import add_info
from meowlauncher.games.roms.roms_config import ROMsConfig
from meowlauncher.settings.platform_config import platform_configs
from meowlauncher.settings.settings import Settings, ignored_directories
from meowlauncher.util import archives
from meowlauncher.util.desktop_files import has_been_done

if TYPE_CHECKING:
	from collections.abc import Iterator, Sequence

	from meowlauncher.emulated_platform import StandardEmulatedPlatform
	from meowlauncher.game import Game

logger = logging.getLogger(__name__)


class ROMPlatform(ChooseableEmulatorGameSource[StandardEmulator]):
	"""An emulated game system, as an individual source. Use with ROMs to cycle through all of them"""

	@classmethod
	def emulator_types(cls) -> Mapping[str, type[StandardEmulator]]:
		return standalone_emulators_by_name

	@classmethod
	def libretro_core_types(cls) -> Mapping[str, type[LibretroCore]] | None:
		return libretro_cores_by_name

	@classmethod
	@abstractmethod
	def platform(cls) -> 'StandardEmulatedPlatform':
		...

	def __init__(self, roms_config: ROMsConfig, platform_config) -> None:
		# Bit naughty, because it has a different signature? Hmm maybe not
		self.roms_config = roms_config
		super().__init__(platform_config)

	@property
	def is_available(self) -> bool:
		return self.platform_config.is_available

	def iter_roms_and_subfolders(self) -> 'Iterator[tuple[ROM, Sequence[str]]]':
		platform = self.platform()
		for rom_dir in self.platform_config.paths:
			if not rom_dir.is_dir():
				logger.warning('Oh no %s has invalid ROM dir: %s', self.name(), rom_dir)
				continue
			# used_m3u_filenames = []
			for root, dirs, files in os.walk(rom_dir):
				root_path = PurePath(root)

				if any(
					root_path.is_relative_to(ignored_directory)
					for ignored_directory in ignored_directories
				):
					continue

				subfolders = root_path.relative_to(rom_dir).parts
				if subfolders and any(
					subfolder in self.roms_config.skipped_subfolder_names
					for subfolder in subfolders
				):
					continue

				folder_check = platform.folder_check
				if folder_check:
					remaining_subdirs = []  # The subdirectories of rom_dir that aren't folder ROMs
					for d in dirs:
						folder_path = Path(root, d)
						if not main_config.full_rescan and has_been_done('ROM', str(folder_path)):
							continue

						folder_rom = FolderROM(folder_path)
						media_type = folder_check(folder_rom)
						if not media_type:
							# This was not a folder we want, descend into it normally
							remaining_subdirs.append(d)
							continue
						folder_rom.media_type = media_type
						yield folder_rom, subfolders
					dirs[:] = remaining_subdirs
				dirs.sort()

				for name in sorted(files):
					path = Path(root, name)
					# TODO: We might actually want to do something with associated documents later, but for now, we know we aren't doing anything with them
					if (not platform.is_valid_file_type(path.suffix[1:].lower())) and path.suffix[
						1:
					].lower() in {'txt', 'md', 'jpg', 'nfo', 'gif', 'bmp'}:
						continue
					if not main_config.full_rescan and has_been_done('ROM', str(path)):
						continue

					try:
						rom = get_rom(path)
					except archives.BadArchiveError:
						logger.exception(
							'Uh oh fucky wucky! %s is an archive file that we tried to open to list its contents, but it was invalid',
							path,
						)
						continue
					except OSError:
						logger.exception(
							'Uh oh fucky wucky! %s is an archive file that has nothing in it or something else weird',
							path,
						)
						continue

					if not rom.is_folder and not platform.is_valid_file_type(rom.extension):
						# TODO: Probs want a warn_about_invalid_extension main_config (or platform_config)
						logger.debug(
							'Invalid extension for this platform in %s %s: %s',
							type(rom).__name__,
							rom,
							rom.extension,
						)
						continue

					try:
						if rom.should_read_whole_thing:
							rom.read_whole_thing()
					except Exception:  # pylint: disable=broad-except
						logger.exception('Bother!!! Reading %s produced an error', rom)
						continue
					yield rom, subfolders

	def iter_games(self) -> 'Iterator[ROMGame]':
		platform = self.platform()
		for rom, subfolders in self.iter_roms_and_subfolders():
			# TODO: Should have a categories_from_subfolders option
			try:
				game = ROMGame(rom, platform, self.platform_config)
				categories = (
					subfolders[:-1]
					if subfolders and subfolders[-1] == game.rom.name
					else subfolders
				)
				game.info.categories = categories

				add_info(game)

				if not game.info.categories and game.info.platform:
					game.info.categories = (game.info.platform,)
				yield game
			except Exception:
				logger.exception('Could not load %s as game', rom)

	def try_emulator(self, game: ROMGame, chosen_emulator: StandardEmulator) -> 'ROMLauncher':
		# potential_emulator_config = _get_emulator_config(chosen_emulator)
		# potential_emulator: ConfiguredStandardEmulator
		# if isinstance(chosen_emulator, LibretroCore):
		# 	if (
		# 		not main_config.libretro_frontend
		# 	):  # TODO: This should be in the config of LibretroCore actually, see secret evil plan
		# 		raise EmulationNotSupportedError('Must choose a frontend to run libretro cores')
		# 	frontend_config = emulator_configs[main_config.libretro_frontend]
		# 	frontend = libretro_frontends[main_config.libretro_frontend]
		# 	potential_emulator = LibretroCoreWithFrontend(
		# 		chosen_emulator, potential_emulator_config, frontend, frontend_config
		# 	)
		# else:
		# 	potential_emulator = ConfiguredStandardEmulator(
		# 		chosen_emulator, potential_emulator_config
		# 	)

		chosen_emulator.check_game(game)

		return ROMLauncher(game, chosen_emulator, self.platform_config)

	def iter_launchers(self, game: 'Game') -> 'Iterator[ROMLauncher]':
		if not isinstance(game, ROMGame):
			raise TypeError(f'game should always be ROMGame, not {type(game)}')

		exception = None
		chosen_emulator_names = []  # For warning message
		for emulator in self.chosen_emulators:
			chosen_emulator_names.append(emulator.name())
			try:
				launcher = self.try_emulator(game, emulator)
			except (EmulationNotSupportedError, NotActuallyLaunchableGameError) as ex:
				exception = ex
			else:
				yield launcher
				# TODO: Some kind of option to generate launchers for the same game with different emulators, if you're into that sort of thing
				return

		# TODO: We also need a warn_about_unemulated_extensions type thing
		# Actually is it better to use some kind of custom level or logging field for that?
		if isinstance(exception, EmulationNotSupportedError):
			if isinstance(exception, ExtensionNotSupportedError):
				logger.info(
					'%s could not be launched by %s',
					game,
					chosen_emulator_names,
					exc_info=exception,
				)
			else:
				logger.warning(
					'%s could not be launched by %s',
					game,
					chosen_emulator_names,
					exc_info=exception,
				)
		else:
			logger.debug(
				'%s could not be launched by %s', game, chosen_emulator_names, exc_info=exception
			)

	def iter_all_launchers(self) -> 'Iterator[ROMLauncher]':
		for game in self.iter_games():
			yield from self.iter_launchers(game)

	def no_longer_exists(self, game_id: str) -> bool:
		return not Path(game_id).exists()

	@classmethod
	def game_type(cls) -> str:
		return 'ROMs'


def _rom_platform(platform: 'StandardEmulatedPlatform') -> type[ROMPlatform]:
	"""Using this because otherwise I'm not sure how I get name to return the platform name since that requires construction
	This feels REALLY cursed"""

	class _ROMPlatform(ROMPlatform):
		@classmethod
		def name(cls) -> str:
			return platform.name

		@classmethod
		def platform(cls) -> 'StandardEmulatedPlatform':
			return platform

	return _ROMPlatform


class ROMs(CompoundGameSource):
	"""Source for emulated games that are "normal" and are mostly just one file for each game (if not a folder or a few files), and are simple conceptually"""

	config: ROMsConfig

	def _iter_platform_sources(self) -> 'Iterator[ROMPlatform]':
		"""Returns an iterator for a ROMPlatform for every platform in platform_configs, excpet DOS/Mac/etc and anything in main_config.excluded_platforms"""

		if self.config.platforms:
			for platform_name in self.config.platforms:
				yield _rom_platform(platforms[platform_name])(
					self.config, platform_configs[platform_name]
				)
		else:
			for platform_name, platform_config in platform_configs.items():
				platform = platforms.get(platform_name)
				if not platform:
					# As DOS, Mac, etc would be in platform_configs too
					continue
				if platform_name in self.config.excluded_platforms:
					continue
				yield _rom_platform(platform)(self.config, platform_config)

	@property
	def sources(self) -> 'Sequence[GameSource]':
		return [platform for platform in self._iter_platform_sources() if platform.is_available]

	@classmethod
	def description(cls) -> str:
		return 'ROMs'

	def no_longer_exists(self, game_id: str) -> bool:
		return not Path(game_id).exists()

	@classmethod
	def config_class(cls) -> type[Settings] | None:
		return ROMsConfig


__doc__ = ROMs.__doc__ or ROMs.__name__
