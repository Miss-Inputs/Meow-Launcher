from abc import ABC, abstractmethod
from enum import Enum, auto

from meowlauncher.settings.settings import Settings


class HostPlatform(Enum):
	"""Platform this runner runs on"""
	Linux = auto() #Assume this means x86 for now
	Windows = auto()
	DotNet = auto()
	Java = auto()
	Love = auto()
	HTML = auto()

class BaseRunnerConfig(Settings):
	"""All runners would have this config. Section not defined here, so it is still abstract"""
	
	gamemode: bool = False
	"""Run this with gamemoderun"""
	
	mangohud: bool = False
	"""Run this with MangoHUD"""
	
	force_opengl_version: bool = False
	"""Forces Mesa OpenGL version to 4.3 via environment variable if you need it
	Is this still needed? I don't know"""
	
class Runner(ABC):
	"""Base class for a runner (an emulator, compatibility layer, anything that runs a thing). Defines the capabilities/options/etc of the runner, see ConfiguredRunner for the instance with options applied"""
	def __init__(self, host_platform: HostPlatform=HostPlatform.Linux) -> None:
		self.host_platform = host_platform
	
	@property
	@abstractmethod
	def name(self) -> str:
		"""Name (readable) of this runner"""

	def __hash__(self) -> int:
		return self.name.__hash__()
	
	@classmethod
	def config_class(cls) -> type[Settings] | None:
		"""Return a Config class containing configuration for this runner/emulator or don't"""
		return None
		
__doc__ = Runner.__doc__ or Runner.__name__
