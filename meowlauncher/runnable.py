import shutil
from abc import ABC, abstractmethod
from enum import Enum, auto
from functools import cache
from pathlib import Path

from meowlauncher.settings.settings import Settings


class HostPlatform(Enum):
	"""Platforms that runners/emulators could use"""

	Linux = auto()  # Assume this means x86 for now
	Windows = auto()
	DotNet = auto()
	Java = auto()
	Love = auto()
	HTML = auto()
	DOS = auto()


class BaseRunnableConfig(Settings):
	"""All runners would have this config. Section not defined here, so it is still abstract"""

	path: Path | None = None
	"""Path to the runner's executable, or if None, use the default exe name and the launcher can look for it in the system path when run"""

	gamemode: bool = False
	"""Run this with gamemoderun"""

	mangohud: bool = False
	"""Run this with MangoHUD"""

	force_opengl_version: bool = False
	"""Forces Mesa OpenGL version to 4.3 via environment variable if you need it
	Is this still needed? I don't know"""


@cache
def _make_default_config(name: str) -> type[BaseRunnableConfig]:
	"""The cache is important here because who knows what screwiness would result if you just returned a new class every time you accessed config_class"""

	class RunnableConfig(BaseRunnableConfig):
		_is_boilerplate = True

		@classmethod
		def section(cls) -> str:
			return name

		@classmethod
		def prefix(cls) -> str:
			return name.lower()

	return RunnableConfig


class Runnable(ABC):
	"""Something that can be ran, I guess"""

	def __init__(self) -> None:
		from meowlauncher.config import current_config

		config_class = self.config_class()
		self.config = current_config(config_class)

	@classmethod
	def config_class(cls) -> type[BaseRunnableConfig]:
		"""If you have special settings, derive from BaseRunnerConfig and put them in here"""
		return _make_default_config(cls.name())

	@classmethod
	def host_platform(cls) -> HostPlatform:
		"""The platform that this runs on, by default will be Linux"""
		return HostPlatform.Linux

	@classmethod
	def name(cls) -> str:
		"""Name (readable) of this runner"""
		return cls.__name__

	@classmethod
	@abstractmethod
	def exe_name(cls) -> str:
		"""Executable name of this runner, which will be the default path if not set to something else"""

	@property
	def is_path_valid(self) -> bool:
		"""Returns true if the default exe name is available on the system path, or if the configured exe path points to a valid executable"""
		return (
			self.config.path.is_file()
			if self.config.path
			else shutil.which(self.exe_name()) is not None
		)

	@property
	def is_available(self) -> bool:
		"""Override if this should check something other than is_path_valid"""
		return self.is_path_valid

	def __str__(self) -> str:
		return self.name()

	@property
	def exe_path(self) -> Path:
		return self.config.path if self.config.path else Path(self.exe_name())
