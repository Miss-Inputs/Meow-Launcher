import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from meowlauncher.config import current_config, main_config
from meowlauncher.emulator import Emulator, LibretroCore, LibretroCoreWithFrontend

if TYPE_CHECKING:
	from collections.abc import Iterator, Mapping, Sequence

	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.emulated_platform import ChooseableEmulatedPlatform
	from meowlauncher.game import Game
	from meowlauncher.launcher import Launcher
	from meowlauncher.settings.settings import Settings

logger = logging.getLogger(__name__)


class GameSource(ABC):
	"""Base class for all game sources. For now you will need to put a reference to the GameSource in meowlauncher/game_sources/__init__.py, and a reference to the config class in meowlauncher/config.py"""

	def __init__(self) -> None:
		config_class = self.config_class()
		self.config = current_config(config_class) if config_class else None

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

	@abstractmethod
	def iter_games(self) -> 'Iterator[Game]':
		"""Yield all games from this source"""

	# TODO: Should have has_been_done somewhere in here? Maybe

	@abstractmethod
	def iter_all_launchers(self) -> 'Iterator[Launcher]':
		"""Yield all valid launchers for this source"""

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

	def iter_games(self) -> 'Iterator[Game]':
		for source in self.sources:
			if source.is_available:
				yield from source.iter_games()

	def iter_all_launchers(self) -> 'Iterator[Launcher]':
		for source in self.sources:
			if source.is_available:
				yield from source.iter_all_launchers()

	@property
	def is_available(self) -> bool:
		return any(source.is_available for source in self.sources)

	def no_longer_exists(self, game_id: str) -> bool:
		return all(source.no_longer_exists(game_id) for source in self.sources)


EmulatorType_co = TypeVar('EmulatorType_co', bound=Emulator['Game'], covariant=True)


class ChooseableEmulatorGameSource(GameSource, ABC, Generic[EmulatorType_co]):
	"""Game source that has options for the user to choose which emulators they use or prefer"""

	# TODO: Maybe this should have try_emulator moved into here, all that kind of logic that checks whether each emulator will work
	# TODO: Should also be possible to bump up or down a preference based on the game, if Emu A is usually preferred over Emu B but Emu B has support for some niche feature that only some games use (but they both play the game)

	@classmethod
	@abstractmethod
	def platform(cls) -> 'ChooseableEmulatedPlatform':
		...

	@classmethod
	@abstractmethod
	def emulator_types(cls) -> 'Mapping[str, type[EmulatorType_co]]':
		"""All possible emulator classes for EmulatorType_co. I'm not sure how much sense this makes"""

	@classmethod
	@abstractmethod
	def libretro_core_types(cls) -> 'Mapping[str, type[LibretroCore]] | None':
		"""All possible emulator classes for EmulatorType_co that are libretro cores. Yeah this definitely doesn't make sense"""

	def __init__(self, platform_config: 'PlatformConfig') -> None:
		super().__init__()
		self.platform_config = platform_config
		self.chosen_emulators = tuple(self.iter_chosen_emulators())

	def _parse_chosen_emulator(self, emulator_name: str) -> type[LibretroCore] | type[EmulatorType_co] | None:
		libretro_core_types = self.libretro_core_types()
		cls: type[LibretroCore | EmulatorType_co] | None
		if libretro_core_types and emulator_name.endswith(' (libretro)'):
			cls = libretro_core_types.get(emulator_name)
		else:
			cls = self.emulator_types().get(emulator_name)
			if libretro_core_types and not cls:
				cls = libretro_core_types.get(f'{emulator_name} (libretro)')

		if not cls:
			logger.warning(
				'Config warning: %s is not a known emulator, specified in %s',
				emulator_name,
				self.name(),
			)
			return None

		if cls.name() not in self.platform().valid_emulator_names:
			logger.warning(
				'Config warning: %s is not a valid emulator for %s', emulator_name, self.name()
			)
			return None

		return cls

	def iter_chosen_emulators(self) -> 'Iterator[EmulatorType_co | LibretroCoreWithFrontend]':
		"""Gets the actual emulator objects for the user's choices, in order"""
		for emulator_name in self.platform_config.chosen_emulators:
			cls = self._parse_chosen_emulator(emulator_name)
			if cls:
				if issubclass(cls, LibretroCore):
					from meowlauncher.data.emulators import libretro_frontends

					core = cls()
					frontend_class = next(
						(
							f
							for f in libretro_frontends
							if f.name() == main_config.libretro_frontend
						),
						None,
					)
					if frontend_class:
						yield LibretroCoreWithFrontend(frontend_class(), core)
				else:
					yield cls()


__doc__ = GameSource.__doc__ or GameSource.__name__
