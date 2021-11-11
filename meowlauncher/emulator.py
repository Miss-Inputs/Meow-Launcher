import os
from typing import Any, NoReturn, Optional
from collections.abc import Callable

from meowlauncher.common_types import (ConfigValueType, EmulatorPlatform,
                                       EmulatorStatus)
from meowlauncher.config.emulator_config_type import (EmulatorConfig,
                                                      EmulatorConfigValue)
from meowlauncher.config.main_config import main_config
from meowlauncher.launcher import (LaunchCommand, MultiLaunchCommands,
                                   get_wine_launch_params)
from meowlauncher.runner import Runner

LaunchParamsFunc = Callable[..., LaunchCommand]

class Emulator(Runner):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_params_func: LaunchParamsFunc, configs: Optional[dict[str, EmulatorConfigValue]]=None, host_platform=EmulatorPlatform.Native):
		self._name = name
		self.status = status
		self.default_exe_name = default_exe_name
		self.launch_params_func = launch_params_func
		self.host_platform: EmulatorPlatform = host_platform
		self.configs = {
			'gamemode': EmulatorConfigValue(ConfigValueType.Bool, False, 'Run with gamemoderun'),
			'mangohud': EmulatorConfigValue(ConfigValueType.Bool, False, 'Run with MangoHUD'),
			'force_opengl_version': EmulatorConfigValue(ConfigValueType.Bool, False, 'Hack to force Mesa OpenGL version to 4.3 by environment variable if you need it'),
		}
		if configs:
			self.configs.update(configs)

	@property
	def name(self) -> str:
		return self._name

	@property
	def is_emulated(self) -> bool:
		return True

	def get_launch_params(self, game, platform_config_options: dict[str, Any], emulator_config: EmulatorConfig):
		params = self.launch_params_func(game, platform_config_options, emulator_config)

		if self.host_platform == EmulatorPlatform.Windows:
			if isinstance(params, MultiLaunchCommands):
				params = MultiLaunchCommands(params.pre_commands, get_wine_launch_params(params.main_command.exe_name, params.main_command.exe_args), params.post_commands)
			else:
				params = get_wine_launch_params(params.exe_name, params.exe_args)
		elif self.host_platform == EmulatorPlatform.DotNet:
			params = params.wrap('mono')
		
		if emulator_config.options.get('mangohud', False):
			params = params.wrap('mangohud')
			if isinstance(params, MultiLaunchCommands):
				params.main_command.env_vars['MANGOHUD_DLSYM'] = '1'
			else:
				params.env_vars['MANGOHUD_DLSYM'] = '1'
		if emulator_config.options.get('gamemode', False):
			params = params.wrap('gamemoderun')
		if emulator_config.options.get('force_opengl_version', False):
			if isinstance(params, MultiLaunchCommands):
				params.main_command.env_vars['MESA_GL_VERSION_OVERRIDE'] = '4.3'
			else:
				params.env_vars['MESA_GL_VERSION_OVERRIDE'] = '4.3'
		return params

class StandardEmulator(Emulator):
	#Not very well named, but I mean like "something that by itself you give a ROM as a path and it launches it" or something among those lines
	def __init__(self, display_name: str, status: EmulatorStatus, default_exe_name: str, launch_params_func: LaunchParamsFunc, supported_extensions: list[str], supported_compression: Optional[list[str]]=None, configs: Optional[dict[str, EmulatorConfigValue]]=None, host_platform=EmulatorPlatform.Native):
		super().__init__(display_name, status, default_exe_name, launch_params_func, configs, host_platform)
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression if supported_compression else []
		self.supports_folders = '/' in supported_extensions
		
class MednafenModule(StandardEmulator):
	def __init__(self, status: EmulatorStatus, supported_extensions: list[str], params_func: LaunchParamsFunc, configs: Optional[dict[str, EmulatorConfigValue]]=None):
		StandardEmulator.__init__(self, 'Mednafen', status, 'mednafen', params_func, supported_extensions, ['zip', 'gz'], configs)

class MameDriver(StandardEmulator):
	def __init__(self, status: EmulatorStatus, launch_params: LaunchParamsFunc, supported_extensions: list[str], configs: Optional[dict[str, EmulatorConfigValue]]=None):
		if configs is None:
			configs = {}
		configs.update({
			'software_compatibility_threshold': EmulatorConfigValue(ConfigValueType.Integer, 1, '0 = broken 1 = imperfect 2 = working other value = ignore; anything in the software list needs this to be considered compatible or -1 to ignore'),
			'skip_unknown_stuff': EmulatorConfigValue(ConfigValueType.Bool, False, "Skip anything that doesn't have a match in the software list"),
		})
		
		StandardEmulator.__init__(self, 'MAME', status, 'mame', launch_params, supported_extensions, ['7z', 'zip'], configs)

class ViceEmulator(StandardEmulator):
	def __init__(self, status: EmulatorStatus, default_exe_name: str, params: LaunchParamsFunc):
		#Also does z and zoo compression but I haven't done those in archives.py yet
		#TODO: Maybe just put z and zoo in the ordinary file extensions if we don't want to do that just yet?
		#WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
		#Does support compressed tapes/disks (gz/bz2/zip/tgz) but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here. So for now we pretend it supports no compression so we end up getting 7z to put the thing in a temporarily folder regardless
		StandardEmulator.__init__(self, 'VICE', status, default_exe_name, params, ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m'] + ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin'] + ['p00', 'prg', 'tap', 't64'], [])

class LibretroCore(Emulator):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_params_func: Optional[LaunchParamsFunc], supported_extensions: list[str], configs: Optional[dict[str, EmulatorConfigValue]]=None):
		self.supported_extensions = supported_extensions
		default_path = os.path.join(main_config.libretro_cores_directory, default_exe_name + '_libretro.so') if main_config.libretro_cores_directory else None
		#TODO: Should rework this later so that default_path and launch_params_func are fine for Emulator but don't have to be Optional, somehow
		super().__init__(name, status, default_path, launch_params_func, configs=configs)
	
	def get_launch_params(self, _, __, ___) -> NoReturn:
		raise NotImplementedError('Needs a frontend')

class PCEmulator(Emulator):
	#Nothing to define here for now, actually
	pass

class LibretroFrontend(Emulator):
	#While these are not really emulators on their own, we pretend they are because it's easier to code that way or whatever
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_params_func: LaunchParamsFunc, supported_compression: Optional[list[str]]=None, configs: Optional[dict[str, EmulatorConfigValue]]=None, host_platform=EmulatorPlatform.Native):
		self.supported_compression = supported_compression if supported_compression else []
		super().__init__(name, status, default_exe_name, launch_params_func, configs, host_platform)

	def get_launch_params(self, _, __, ___) -> NoReturn:
		raise NotImplementedError("You shouldn't be calling get_launch_params on a libretro frontend")

class LibretroCoreWithFrontend(StandardEmulator):
	def __init__(self, core: LibretroCore, frontend: LibretroFrontend, frontend_config: EmulatorConfig):
		self.core = core
		self.frontend = frontend
		self.frontend_config = frontend_config
		def launch_params_func(game, platform_config, emulator_config):
			if core.launch_params_func:
				#We do actually want to ignore args here as then we can reuse the same launch params func for a libretro core and the standalone emulator and that should probably work in most cases, and if it doesn't, we can just do command_lines.blah_libretro
				core.launch_params_func(game, platform_config, emulator_config)
			return frontend.launch_params_func(game, platform_config, emulator_config, frontend_config)

		self.launch_params_func = launch_params_func
		super().__init__(f'{self.frontend.name} ({self.core.name} core)', core.status, frontend_config.exe_path, launch_params_func, core.supported_extensions, frontend.supported_compression, None, frontend.host_platform)
