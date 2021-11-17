from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import Optional

from meowlauncher.common_types import (ConfigValueType, EmulatorStatus,
                                       HostPlatform, TypeOfConfigValue)
from meowlauncher.config.main_config import main_config

from .emulated_game import EmulatedGame
from .launcher import LaunchCommand
from .runner import Runner
from .runner_config import EmulatorConfig, RunnerConfigValue

LaunchCommandFunc = Callable[[EmulatedGame, Mapping[str, TypeOfConfigValue], EmulatorConfig], LaunchCommand] #for now
LibretroFrontendLaunchCommandFunc = Callable[[EmulatedGame, Mapping[str, TypeOfConfigValue], EmulatorConfig, EmulatorConfig], LaunchCommand]

class Emulator(Runner):
	#I decided what actually defines an "emulator" vs. a Runner with is_emulated -> True is that this is more of a "chooseable emulator", but ChooseableEmulator sounds silly as a class name, so like I dunno
	#Pretend launch_command_func is not optional if instantiating this oneself, it's just for LibretroCore purposes
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: Optional[LaunchCommandFunc], configs: Mapping[str, RunnerConfigValue]=None, host_platform=HostPlatform.Native, config_name: str=None):
		super().__init__(host_platform)
		self._name = name
		self.config_name = config_name if config_name else name
		self.status = status
		self.default_exe_name = default_exe_name
		self.launch_command_func = launch_command_func
		if configs:
			self.configs.update(configs)

	@property
	def name(self) -> str:
		return self._name

	@property
	def is_emulated(self) -> bool:
		return True

class StandardEmulator(Emulator):
	#Not very well named, but I mean like "something that by itself you give a ROM as a path and it launches it" or something among those lines
	def __init__(self, display_name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: Optional[LaunchCommandFunc], supported_extensions: Sequence[str], supported_compression: Sequence[str]=None, configs: Mapping[str, RunnerConfigValue]=None, host_platform=HostPlatform.Native, config_name: str=None):
		super().__init__(display_name, status, default_exe_name, launch_command_func, configs, host_platform, config_name)
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression if supported_compression else []
		
class MednafenModule(StandardEmulator):
	def __init__(self, name: str, status: EmulatorStatus, supported_extensions: Sequence[str], params_func: LaunchCommandFunc, configs: Mapping[str, RunnerConfigValue]=None):
		StandardEmulator.__init__(self, 'Mednafen', status, 'mednafen', params_func, supported_extensions, ['zip', 'gz'], configs, config_name=f'Mednafen ({name})')

class MAMEDriver(StandardEmulator):
	def __init__(self, name: str, status: EmulatorStatus, launch_params: LaunchCommandFunc, supported_extensions: list[str], configs: Optional[MutableMapping[str, RunnerConfigValue]]=None):
		if configs is None:
			configs = {}
		configs.update({
			'software_compatibility_threshold': RunnerConfigValue(ConfigValueType.Integer, 1, '0 = broken 1 = imperfect 2 = working other value = ignore; anything in the software list needs this to be considered compatible or -1 to ignore'),
			'skip_unknown_stuff': RunnerConfigValue(ConfigValueType.Bool, False, "Skip anything that doesn't have a match in the software list"),
		})
		
		StandardEmulator.__init__(self, 'MAME', status, 'mame', launch_params, supported_extensions, ['7z', 'zip'], configs, config_name=f'MAME ({name})')

class ViceEmulator(StandardEmulator):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, params: LaunchCommandFunc):
		#Also does z and zoo compression but I haven't done those in archives.py yet
		#TODO: Maybe just put z and zoo in the ordinary file extensions if we don't want to do that just yet?
		#WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
		#Does support compressed tapes/disks (gz/bz2/zip/tgz) but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here. So for now we pretend it supports no compression so we end up getting 7z to put the thing in a temporarily folder regardless
		StandardEmulator.__init__(self, 'VICE', status, default_exe_name, params, ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m'] + ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin'] + ['p00', 'prg', 'tap', 't64'], [], config_name=f'VICE ({name})')

class LibretroCore(Emulator):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: Optional[LaunchCommandFunc], supported_extensions: Sequence[str], configs: Optional[dict[str, RunnerConfigValue]]=None):
		self.supported_extensions = supported_extensions
		default_path = str(main_config.libretro_cores_directory.joinpath(default_exe_name + '_libretro.so').resolve()) if main_config.libretro_cores_directory else ''
		super().__init__(name, status, default_path, launch_command_func, configs=configs, config_name=name + ' (libretro)')
	
class PCEmulator(Emulator):
	#Nothing to define here for now, actually
	pass

class LibretroFrontend(Runner):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: LibretroFrontendLaunchCommandFunc, supported_compression: Optional[list[str]]=None, configs: Optional[dict[str, RunnerConfigValue]]=None, host_platform=HostPlatform.Native):
		self._name = name
		self.status = status
		self.default_exe_name = default_exe_name
		self.launch_command_func = launch_command_func
		self.supported_compression = supported_compression if supported_compression else []
		self.config_name = name #emulator_configs needs this, as we have decided that frontends can have their own config
		if configs:
			self.configs.update(configs)
		super().__init__(host_platform)

	@property
	def name(self) -> str:
		return self._name
