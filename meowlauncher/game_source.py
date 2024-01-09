import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from meowlauncher.emulator import Emulator

if TYPE_CHECKING:
	from collections.abc import Iterator, Mapping, Sequence

	from meowlauncher.settings.settings import Settings
	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.emulated_game import EmulatedGame
	from meowlauncher.emulated_platform import ChooseableEmulatedPlatform
	from meowlauncher.emulator import LibretroCore
	from meowlauncher.launcher import Launcher

logger = logging.getLogger(__name__)


class GameSource(ABC):
	"""Base class for all game sources. For now you will need to put this in meowlauncher/game_sources/__init__.py"""

	def __init__(self) -> None:
		from meowlauncher.config import current_config

		self.config = current_config.get(self)

	@classmethod
	def name(cls) -> str:
		"""Display name for humans to read, though defaults to the class name"""
		return cls.__name__

	@classmethod
	def description(cls) -> str:
		"""Full name of sorts, e.g. "blah games" (defaults to self.name + "games"), maybe description is the wrong word here whoops"""
		return f'{cls.name()} games'

	@classmethod
	def config_class(cls) -> 'type[Settings] | None':
		"""Return a Config class containing configuration for this GameSource or don't"""
		return None

	def __str__(self) -> str:
		return f'{self.name()} ({self.description()})'

	@property
	@abstractmethod
	def is_available(self) -> bool:
		"""Return true if this is ready for calling iter_launchers"""

	@abstractmethod
	def no_longer_exists(self, game_id: str) -> bool:
		"""Called when full_rescan is false, after checking the game type to see which class to go to. Checks if the game specified by game_id still exists (in the sense that it would be created if full_rescan was true), and deletes if not"""

	# TODO: Should have has_been_done somewhere in here? Maybe
	@abstractmethod
	def iter_launchers(self) -> 'Iterator[Launcher]':
		"""Create all the launchers and iterate over them"""

	def __hash__(self) -> int:
		return self.name().__hash__()

	@classmethod
	def game_type(cls) -> str:
		"""Stored in the ID section to uniquely identify this launcher, to know if no_longer_exists should be called by remove_existing_games, you should also check for this in iter_launchers to skip over launchers that are done already
		Other than that, output/* needs to know this, so it just gets it from add_games currently, to know what to put in the launcher file
		I guess we could also just have it on Launcher after all… hrm
		It also could be @final and just use __name__"""
		return cls.__name__


class CompoundGameSource(GameSource, ABC):
	"""Chains GameSources together, so that iter_launchers returns each one that's available"""

	@property
	@abstractmethod
	def sources(self) -> 'Sequence[GameSource]':
		"""Individual GameSources"""

	def iter_launchers(self) -> 'Iterator[Launcher]':
		for source in self.sources:
			if source.is_available:
				yield from source.iter_launchers()

	@property
	def is_available(self) -> bool:
		return any(source.is_available for source in self.sources)


EmulatorType_co = TypeVar('EmulatorType_co', bound=Emulator['EmulatedGame'], covariant=True)


class ChooseableEmulatorGameSource(GameSource, ABC, Generic[EmulatorType_co]):
	"""Game source that has options for the user to choose which emulators they use or prefer"""

	def __init__(
		self,
		platform_config: 'PlatformConfig',
		platform: 'ChooseableEmulatedPlatform',
		emulators: 'Mapping[str, EmulatorType_co]',
		libretro_cores: 'Mapping[str, LibretroCore] | None' = None,
	) -> None:
		super().__init__()
		self.platform_config = platform_config
		self.platform = platform
		self.emulators = emulators
		self.libretro_cores = libretro_cores

	def iter_chosen_emulators(self) -> 'Iterator[EmulatorType_co | LibretroCore]':
		"""Gets the actual emulator objects for the user's choices, in order"""
		for emulator_name in self.platform_config.chosen_emulators:
			emulator = (
				self.libretro_cores.get(emulator_name.removesuffix(' (libretro)'))
				if (self.libretro_cores and emulator_name.endswith(' (libretro)'))
				else self.emulators.get(emulator_name)
			)

			if not emulator:
				if self.libretro_cores:
					emulator = self.libretro_cores.get(emulator_name)
			if not emulator:
				logger.warning(
					'Config warning: %s is not a known emulator, specified in %s',
					emulator_name,
					self.name(),
				)
				continue

			if emulator.config_name not in self.platform.valid_emulator_names:
				logger.warning(
					'Config warning: %s is not a valid %s for %s',
					emulator_name,
					emulator.friendly_type_name,
					self.name(),
				)
				continue

			yield emulator


__doc__ = GameSource.__doc__ or GameSource.__name__
