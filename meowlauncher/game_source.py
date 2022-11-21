import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar, Union

from meowlauncher.emulator import Emulator

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.emulated_game import EmulatedGame
	from meowlauncher.emulated_platform import ChooseableEmulatedPlatform
	from meowlauncher.emulator import LibretroCore
	from meowlauncher.launcher import Launcher
	from collections.abc import Iterator, Mapping, Sequence

logger = logging.getLogger(__name__)

class GameSource(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def description(self) -> str:
		return f'{self.name} games'

	def __str__(self) -> str:
		return f'{self.name} ({self.description})'

	@property
	@abstractmethod
	def is_available(self) -> bool:
		"""Return true if this is ready for calling iter_launchers"""
		
	@abstractmethod
	def no_longer_exists(self, game_id: str) -> bool:
		"""Called when full_rescan is false, after checking the game type to see which class to go to. Checks if the game specified by game_id still exists (in the sense that it would be created if full_rescan was true), and deletes if not"""

	#TODO: Should have has_been_done somewhere in here? Maybe
	#TODO: I think this should have game_type instead of Launcher…

	@abstractmethod
	def iter_launchers(self) -> 'Iterator[Launcher]':
		"""Create all the launchers and iterate over them"""

	def __hash__(self) -> int:
		return self.name.__hash__()

class CompoundGameSource(GameSource, ABC):
	"""Chains GameSources together, so that iter_launchers returns each one that's available"""
	def __init__(self, sources: 'Sequence[GameSource]') -> None:
		self.sources = sources

	def iter_launchers(self) -> 'Iterator[Launcher]':
		for source in self.sources:
			if source.is_available:
				yield from source.iter_launchers()

	@property
	def is_available(self) -> bool:
		return any(source.is_available for source in self.sources)

EmulatorType_co = TypeVar('EmulatorType_co', bound=Emulator['EmulatedGame'], covariant=True)
class ChooseableEmulatorGameSource(GameSource, ABC, Generic[EmulatorType_co]):
	def __init__(self, platform_config: 'PlatformConfig', platform: 'ChooseableEmulatedPlatform', emulators: 'Mapping[str, EmulatorType_co]', libretro_cores: 'Mapping[str, LibretroCore] | None'=None) -> None:
		self.platform_config = platform_config
		self.platform = platform
		self.emulators = emulators
		self.libretro_cores = libretro_cores
	
	def iter_chosen_emulators(self) -> 'Iterator[Union[EmulatorType_co, LibretroCore]]':
		for emulator_name in self.platform_config.chosen_emulators:
			emulator = self.libretro_cores.get(emulator_name.removesuffix(' (libretro)')) if \
				(self.libretro_cores and emulator_name.endswith(' (libretro)')) else \
				self.emulators.get(emulator_name)

			if not emulator:
				if self.libretro_cores:
					emulator = self.libretro_cores.get(emulator_name)
			if not emulator:
				logger.warning('Config warning: %s is not a known emulator, specified in %s', emulator_name, self.name)
				continue

			if emulator.config_name not in self.platform.valid_emulator_names:
				logger.warning('Config warning: %s is not a valid %s for %s', emulator_name, emulator.friendly_type_name, self.name)
				continue
			
			yield emulator
