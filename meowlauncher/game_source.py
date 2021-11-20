from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Generic, TypeVar, Union

from meowlauncher.emulator import Emulator

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig
	from meowlauncher.emulated_platform import ChooseableEmulatedPlatform
	from meowlauncher.launcher import Launcher
	from meowlauncher.emulator import LibretroCore

class GameSource(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def description(self) -> str:
		return f'{self.name} games'

	@property
	@abstractmethod
	def is_available(self) -> bool:
		pass

	@abstractmethod
	def no_longer_exists(self, game_id: str) -> bool:
		pass

	#TODO: Should have has_been_done somewhere in here? Maybe

	@abstractmethod
	def iter_launchers(self) -> Iterable['Launcher']:
		pass

class CompoundGameSource(GameSource, ABC):
	def __init__(self, sources: Sequence[GameSource]) -> None:
		self.sources = sources

	def iter_launchers(self) -> Iterable['Launcher']:
		for source in self.sources:
			if source.is_available:
				yield from source.iter_launchers()

	@property
	def is_available(self) -> bool:
		return any(source.is_available for source in self.sources)

EmulatorType = TypeVar('EmulatorType', bound=Emulator)
class ChooseableEmulatorGameSource(GameSource, ABC, Generic[EmulatorType]):
	def __init__(self, platform_config: 'PlatformConfig', platform: 'ChooseableEmulatedPlatform', emulators: Mapping[str, EmulatorType], libretro_cores: Mapping[str, 'LibretroCore']=None) -> None:
		self.platform_config = platform_config
		self.platform = platform
		self.emulators = emulators
		self.libretro_cores = libretro_cores
	
	def iter_chosen_emulators(self) -> Iterable[Union[EmulatorType, 'LibretroCore']]:
		for emulator_name in self.platform_config.chosen_emulators:
			emulator = self.libretro_cores.get(emulator_name.removesuffix(' (libretro)')) if \
				(self.libretro_cores and emulator_name.endswith(' (libretro)')) else \
				self.emulators.get(emulator_name)

			if not emulator:
				if self.libretro_cores:
					emulator = self.libretro_cores.get(emulator_name)
			if not emulator:
				print('Config warning:', emulator_name, 'is not a valid emulator, specified in', self.name)
				continue

			if emulator.config_name not in self.platform.valid_emulator_names:
				print('Config warning:', emulator_name, 'is not a valid', emulator.friendly_type_name, 'for', self.name)
				continue
			
			yield emulator
