from abc import ABC, abstractmethod

from meowlauncher.common_types import ConfigValueType, HostPlatform

from .runner_config import RunnerConfigValue


class Runner(ABC):
	def __init__(self, host_platform: HostPlatform=HostPlatform.Native) -> None:
		self.host_platform: HostPlatform = host_platform
		self.configs = {
			'gamemode': RunnerConfigValue(ConfigValueType.Bool, False, 'Run with gamemoderun'),
			'mangohud': RunnerConfigValue(ConfigValueType.Bool, False, 'Run with MangoHUD'),
			'force_opengl_version': RunnerConfigValue(ConfigValueType.Bool, False, 'Hack to force Mesa OpenGL version to 4.3 by environment variable if you need it'),
		}

	@property
	#Override this to show if something is not installed, etc
	def is_available(self) -> bool:
		return True

	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def is_emulated(self) -> bool:
		#Basically just decides if we should use the "Emulator" field or not
		return False
