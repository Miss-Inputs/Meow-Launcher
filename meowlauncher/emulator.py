from abc import abstractmethod
from collections.abc import Collection
from enum import Enum
from functools import cache
from itertools import chain
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, TypeVar

from meowlauncher.config import main_config
from meowlauncher.exceptions import ExtensionNotSupportedError
from meowlauncher.games.roms.rom_game import ROMGame

from .game import Game
from .runnable import BaseRunnableConfig, Runnable
from .runner import Runner

if TYPE_CHECKING:
	from meowlauncher.launch_command import LaunchCommand

EmulatorGameType_co = TypeVar('EmulatorGameType_co', bound=Game, covariant=True)


class EmulatorStatus(Enum):
	"""How good an emulator is last time we checked and decided to form an opinion on it. Hmm I'm not sure why I needed this, maybe for a frontend to choose the allegedly best emulator automatically? Yeah it'd probs be that
	I have not actually thought of concrete definitions for what these mean"""

	Good = 6
	Imperfect = 5
	ExperimentalButSeemsOkay = 4
	Experimental = 3
	Janky = 2  # Weird to set up or launch normally… hmm this would indicate there is a "compatibility status" as well as a "usability status", in an ideal world where I'm not just putting all this here for either source code as reference, or future use for frontends
	Borked = 1


class BaseEmulatorConfig(BaseRunnableConfig):
	"""Not really much different than BaseRunnableConfig other than the default config_file_name, but might make things easier"""

	@classmethod
	def section(cls) -> str:
		return cls.__name__.removesuffix('Config')

	@classmethod
	def prefix(cls) -> str:
		return cls.__name__.removesuffix('Config').lower()

	@classmethod
	def config_file_name(cls) -> str:
		return 'emulators'


@cache
def _make_default_config(name: str) -> type[BaseEmulatorConfig]:
	"""The cache is important here because who knows what screwiness would result if you just returned a new class every time you accessed config_class"""

	class EmulatorConfig(BaseEmulatorConfig):
		_is_boilerplate = True

		@classmethod
		def section(cls) -> str:
			return name

		@classmethod
		def prefix(cls) -> str:
			return name.lower()

	return EmulatorConfig


class Emulator(Runner[EmulatorGameType_co]):
	@classmethod
	def config_class(cls) -> type[BaseEmulatorConfig]:
		return _make_default_config(cls.name())

	@classmethod
	def status(cls) -> EmulatorStatus:
		return EmulatorStatus.Good

	@property
	def info_name(self) -> str:
		"""Return a name which should be added to the Emulator key of a launcher's info
		Basically, serves as the name after it's constructed"""
		return self.name()


class StandardEmulator(Emulator[ROMGame]):
	"""Not very well named, but I mean like "something that by itself you give a ROM as a path and it launches it" or something among those lines"""

	@classmethod
	@abstractmethod
	def supported_extensions(cls) -> 'Collection[str]':
		...

	@classmethod
	def supported_compression(cls) -> 'Collection[str]':
		return frozenset()

	def supports_extension(self, extension: str) -> bool:
		# Is there a need for this to be a method and not classmethod? Would we ever change it dynamically depending on config?
		return extension in self.supported_extensions()

	def supports_compressed_extension(self, extension: str) -> bool:
		return extension in self.supported_compression()

	@property
	def supports_folders(self) -> bool:
		return '/' in self.supported_extensions()

	def check_game(self, game: ROMGame) -> None:
		"""Raises GameNotSupportedError/ExtensionNotSupportedError/etc for any reason the game is not supported, or do nothing if the game is supported
		:raises GameNotSupportedError: If the game is not supported"""
		if game.rom.is_folder and not self.supports_folders:
			raise ExtensionNotSupportedError(f'{self} does not support folders')
		if not self.supports_extension(game.rom.extension):
			raise ExtensionNotSupportedError(
				f'{self} does not support extension {game.rom.extension}'
			)


class LibretroCore(Runnable):
	@classmethod
	def status(cls) -> EmulatorStatus:
		return EmulatorStatus.Good

	@property
	def exe_path(self) -> Path:
		return (
			self.config.path
			if self.config.path
			else main_config.libretro_cores_directory / f'{self.exe_name()}_libretro.so'
		)

	@property
	def is_path_valid(self) -> bool:
		return self.exe_path.is_file()

	@classmethod
	def config_class(cls) -> type[BaseEmulatorConfig]:
		return _make_default_config(cls.name())

	def check_game(self, game: Game):
		"""Override this if you need to check compatibility for a game"""


class LibretroFrontend(Runnable):
	@classmethod
	def status(cls) -> EmulatorStatus:
		return EmulatorStatus.Good

	@abstractmethod
	def get_command(self, core_path: PurePath, game: 'Game | None' = None) -> 'LaunchCommand':
		"""Return a command that launches core_path, and game if there is a game to launch"""

	@classmethod
	@abstractmethod
	def supported_compression(cls) -> Collection[str]:
		"""Extensions for archives that this fronted will uncompress for games"""

	@classmethod
	def config_class(cls) -> type[BaseEmulatorConfig]:
		# Ensure we get a BaseEmulatorConfig instead, to read from emulators.ini, even if that's kind of weird
		return _make_default_config(cls.name())


class LibretroCoreWithFrontend(Emulator[Game]):
	def __init__(self, frontend: LibretroFrontend, core: LibretroCore) -> None:
		self.frontend = frontend
		self.core = core
		self._name = f'{frontend} + {core.name().removesuffix(" (libretro)")}'
		super().__init__()
		for k, v in chain(self.frontend.config, self.core.config):
			setattr(self.config, k, v)

	@property
	def info_name(self) -> str:
		return self._name

	@property
	def is_available(self) -> bool:
		return self.frontend.is_available and self.core.is_available

	@classmethod
	def exe_name(cls) -> str:
		raise NotImplementedError(
			'Attempting to get exe_name of combined core + frontend, which should not happen'
		)

	def supports_compressed_extension(self, extension: str) -> bool:
		return extension in self.frontend.supported_compression()

	def check_game(self, game: Game) -> None:
		self.core.check_game(game)

	def get_game_command(self, game: Game) -> 'LaunchCommand':
		return self.frontend.get_command(self.core.exe_path, game)
