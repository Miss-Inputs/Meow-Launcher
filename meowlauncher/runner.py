from abc import ABC, abstractmethod
from enum import Enum, auto

from meowlauncher.config_types import RunnerConfigValue

class HostPlatform(Enum):
	"""Platform this runner runs on"""
	Native = auto() #Well I guess this really means Linux x86_64
	Windows = auto()
	DotNet = auto()

class Runner(ABC):
	"""Base class for a runner (an emulator, compatibility layer, anything that runs a thing). Defines the capabilities/options/etc of the runner, see ConfiguredRunner for the instance with options applied"""
	def __init__(self, host_platform: HostPlatform=HostPlatform.Native) -> None:
		self.host_platform = host_platform
		self.configs = {
			'gamemode': RunnerConfigValue(bool, False, 'Run with gamemoderun'),
			'mangohud': RunnerConfigValue(bool, False, 'Run with MangoHUD'),
			'force_opengl_version': RunnerConfigValue(bool, False, 'Hack to force Mesa OpenGL version to 4.3 by environment variable if you need it'),
		}

	@property
	def is_available(self) -> bool:
		'If this is installed, etc.'
		return True

	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def is_emulated(self) -> bool:
		#Basically just decides if we should use the "Emulator" field or not
		return False

	def __hash__(self) -> int:
		return self.name.__hash__()
		
__doc__ = Runner.__doc__ or ""
