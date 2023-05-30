from abc import ABC, abstractmethod
from enum import Enum, auto

from meowlauncher.config_types import RunnerConfigValue
from meowlauncher.config.config import Config, configoption

class HostPlatform(Enum):
	"""Platform this runner runs on"""
	Linux = auto() #Assume this means x86 for now
	Windows = auto()
	DotNet = auto()
	Java = auto()
	Love = auto()
	HTML = auto()

class BaseRunnerConfig(Config):
	"""All runners would have this config. Section not defined here, so it is still abstract
	TODO: Use this once we refactor Emulator and Emulator.configs"""
	
	@configoption
	def gamemode(self) -> bool:
		"""Run this with gamemoderun"""
		return False
	
	@configoption
	def mangohud(self) -> bool:
		"""Run this with MangoHUD"""
		return False

	@configoption
	def force_opengl_version(self) -> bool:
		"""Forces Mesa OpenGL version to 4.3 via environment variable if you need it
		Is this still needed? I don't know"""
		return False

class Runner(ABC):
	"""Base class for a runner (an emulator, compatibility layer, anything that runs a thing). Defines the capabilities/options/etc of the runner, see ConfiguredRunner for the instance with options applied"""
	def __init__(self, host_platform: HostPlatform=HostPlatform.Linux) -> None:
		self.host_platform = host_platform
		self.configs = {
			'gamemode': RunnerConfigValue(bool, False, 'Run with gamemoderun'),
			'mangohud': RunnerConfigValue(bool, False, 'Run with MangoHUD'),
			'force_opengl_version': RunnerConfigValue(bool, False, 'Hack to force Mesa OpenGL version to 4.3 by environment variable if you need it'),
		}

	@property
	@abstractmethod
	def name(self) -> str:
		"""Name (readable) of this runner"""

	def __hash__(self) -> int:
		return self.name.__hash__()
		
__doc__ = Runner.__doc__ or Runner.__name__
