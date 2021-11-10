import os
from enum import Enum, auto
from typing import Any, Callable

from meowlauncher.common_types import (ConfigValueType,
                                       EmulationNotSupportedException)
from meowlauncher.config.emulator_config_type import (EmulatorConfig,
                                                      EmulatorConfigValue)
from meowlauncher.config.main_config import main_config
from meowlauncher.info.emulator_command_line_helpers import \
    simple_mednafen_module
from meowlauncher.launchers import (LaunchParams, MultiCommandLaunchParams,
                                    get_wine_launch_params)


class EmulatorStatus(Enum):
	#I have not actually thought of concrete definitions for what these mean
	Good = 6
	Imperfect = 5
	ExperimentalButSeemsOkay = 4
	Experimental = 3
	Janky = 2 #Weird to set up or launch normally
	Borked = 1

class EmulatorPlatform():
	Native = auto()
	Windows = auto()
	DotNet = auto()

class Emulator():
	def __init__(self, status: EmulatorStatus, default_exe_name: str, launch_params_func: Callable[..., LaunchParams], configs: dict[str, EmulatorConfigValue]=None, host_platform=EmulatorPlatform.Native):
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

	def get_launch_params(self, game, system_config: dict[str, Any], emulator_config: EmulatorConfig):
		params = self.launch_params_func(game, system_config, emulator_config)

		if self.host_platform == EmulatorPlatform.Windows:
			if isinstance(params, MultiCommandLaunchParams):
				params = MultiCommandLaunchParams(params.pre_commands, get_wine_launch_params(params.main_command.exe_name, params.main_command.exe_args), params.post_commands)
			else:
				params = get_wine_launch_params(params.exe_name, params.exe_args)
		elif self.host_platform == EmulatorPlatform.DotNet:
			params = params.wrap('mono')
		
		if emulator_config.options.get('mangohud', False):
			params = params.wrap('mangohud')
			if isinstance(params, MultiCommandLaunchParams):
				params.main_command.env_vars['MANGOHUD_DLSYM'] = '1'
			else:
				params.env_vars['MANGOHUD_DLSYM'] = '1'
		if emulator_config.options.get('gamemode', False):
			params = params.wrap('gamemoderun')
		if emulator_config.options.get('force_opengl_version', False):
			if isinstance(params, MultiCommandLaunchParams):
				params.main_command.env_vars['MESA_GL_VERSION_OVERRIDE'] = '4.3'
			else:
				params.env_vars['MESA_GL_VERSION_OVERRIDE'] = '4.3'
		return params

class StandardEmulator(Emulator):
	#Not very well named, but I mean like "something that by itself you give a ROM as a path and it launches it" or something among those lines
	def __init__(self, status: EmulatorStatus, default_exe_name, launch_params_func, supported_extensions, supported_compression=None, configs=None, host_platform=EmulatorPlatform.Native):
		super().__init__(status, default_exe_name, launch_params_func, configs, host_platform)
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression if supported_compression else []
		self.supports_folders = '/' in supported_extensions

class MednafenModule(StandardEmulator):
	def __init__(self, status: EmulatorStatus, module, supported_extensions, params_func=None, configs=None):
		if not params_func:
			params_func = simple_mednafen_module(module)
		StandardEmulator.__init__(self, status, 'mednafen', params_func, supported_extensions, ['zip', 'gz'], configs)

class MameDriver(StandardEmulator):
	def __init__(self, status: EmulatorStatus, launch_params, supported_extensions, configs=None):
		if configs is None:
			configs = {}
		configs.update({
			'software_compatibility_threshold': EmulatorConfigValue(ConfigValueType.Integer, 1, '0 = broken 1 = imperfect 2 = working other value = ignore; anything in the software list needs this to be considered compatible or -1 to ignore'),
			'skip_unknown_stuff': EmulatorConfigValue(ConfigValueType.Bool, False, "Skip anything that doesn't have a match in the software list"),
		})
		
		StandardEmulator.__init__(self, status, 'mame', launch_params, supported_extensions, ['7z', 'zip'], configs)

class ViceEmulator(StandardEmulator):
	def __init__(self, status: EmulatorStatus, default_exe_name, params):
		#Also does z and zoo compression but I haven't done those in archives.py yet
		#WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
		#Does support compressed tapes/disks (gz/bz2/zip/tgz) but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here. So for now we pretend it supports no compression so we end up getting 7z to put the thing in a temporarily folder regardless
		StandardEmulator.__init__(self, status, default_exe_name, params, ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m'] + ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin'] + ['p00', 'prg', 'tap', 't64'], [])

class LibretroCore(Emulator):
	def __init__(self, status: EmulatorStatus, default_exe_name, launch_params_func, supported_extensions, configs=None):
		self.supported_extensions = supported_extensions
		if main_config.libretro_cores_directory:
			default_path = os.path.join(main_config.libretro_cores_directory, default_exe_name + '_libretro.so')
		else:
			default_path = None
		super().__init__(status, default_path, launch_params_func, configs=configs)
	
	def get_launch_params(self, _, __, ___):
		raise EmulationNotSupportedException('Needs a frontend')

class PCEmulator(Emulator):
	#Nothing to define here for now, actually
	pass

class LibretroFrontend(Emulator):
	#While these are not really emulators on their own, we pretend they are because it's easier to code that way or whatever
	def __init__(self, status: EmulatorStatus, default_exe_name, launch_params_func, supported_compression=None, configs=None, host_platform=EmulatorPlatform.Native):
		self.supported_compression = supported_compression if supported_compression else []
		super().__init__(status, default_exe_name, launch_params_func, configs, host_platform)

	def get_launch_params(self, _, __, ___):
		raise EmulationNotSupportedException("You shouldn't be calling get_launch_params on a libretro frontend")

class LibretroCoreWithFrontend(StandardEmulator):
	def __init__(self, core: LibretroCore, frontend: LibretroFrontend, frontend_config):
		self.core = core
		self.frontend = frontend
		self.frontend_config = frontend_config
		def launch_params_func(game, system_config, emulator_config):
			if core.launch_params_func:
				#We do actually want to ignore args here as then we can reuse the same launch params func for a libretro core and the standalone emulator and that should probably work in most cases, and if it doesn't, we can just do command_lines.blah_libretro
				core.launch_params_func(game, system_config, emulator_config)
			return frontend.launch_params_func(game, system_config, emulator_config, frontend_config)

		self.launch_params_func = launch_params_func
		super().__init__(core.status, frontend_config.exe_path, launch_params_func, core.supported_extensions, frontend.supported_compression, None, frontend.host_platform)
