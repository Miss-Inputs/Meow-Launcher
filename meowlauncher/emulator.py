from enum import Enum
from typing import TYPE_CHECKING, Generic, TypeVar

from meowlauncher.config.main_config import old_main_config
from meowlauncher.config_types import (EmulatorConfig,
                                       RunnerConfigValue, TypeOfConfigValue)

from .emulated_game import EmulatedGame
from .runner import HostPlatform, Runner

EmulatorGameType_co = TypeVar('EmulatorGameType_co', bound=EmulatedGame, covariant=True)
if TYPE_CHECKING:
	from collections.abc import Callable, Collection, Mapping, MutableMapping
	from meowlauncher.games.roms.rom_game import ROMGame

	from .launch_command import LaunchCommand
	LibretroFrontendLaunchCommandFunc = Callable[[EmulatedGame, Mapping[str, TypeOfConfigValue], EmulatorConfig, EmulatorConfig], LaunchCommand]

	GenericLaunchCommandFunc = Callable[[EmulatorGameType_co, Mapping[str, TypeOfConfigValue], EmulatorConfig], LaunchCommand]
	ROMGameLaunchFunc = GenericLaunchCommandFunc[ROMGame] #Was hoping that if I'm inside StandardEmulator, I wouldn't have to manually specify that because it should know already that I'm emulating a ROMGame, but it doesn't work that way

class EmulatorStatus(Enum):
	"""How good an emulator is last time we checked and decided to form an opinion on it. Hmm I'm not sure why I needed this, maybe for a frontend to choose the allegedly best emulator automatically? Yeah it'd probs be that
	I have not actually thought of concrete definitions for what these mean"""
	Good = 6
	Imperfect = 5
	ExperimentalButSeemsOkay = 4
	Experimental = 3
	Janky = 2 #Weird to set up or launch normally… hmm this would indicate there is a "compatibility status" as well as a "usability status", in an ideal world where I'm not just putting all this here for either source code as reference, or future use for frontends
	Borked = 1

class Emulator(Runner, Generic[EmulatorGameType_co]):
	"""I decided what actually defines an "emulator" vs. a Runner with is_emulated -> True is that this is more of a "chooseable emulator", but ChooseableEmulator sounds silly as a class name, so like I dunno
	Pretend launch_command_func is not optional if instantiating this oneself, it's just for LibretroCore purposes"""
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: 'GenericLaunchCommandFunc[EmulatorGameType_co] | None', configs: 'Mapping[str, RunnerConfigValue] | None'=None, host_platform: HostPlatform=HostPlatform.Native, config_name: str|None=None):
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
	def friendly_type_name(self) -> str:
		return type(self).__name__.lower()

	@property
	def is_emulated(self) -> bool:
		return True

class StandardEmulator(Emulator['ROMGame']):
	"""Not very well named, but I mean like "something that by itself you give a ROM as a path and it launches it" or something among those lines"""
	def __init__(self, display_name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: 'ROMGameLaunchFunc', supported_extensions: 'Collection[str]', supported_compression: 'Collection[str] | None'=None, configs: 'Mapping[str, RunnerConfigValue] | None'=None, host_platform: HostPlatform=HostPlatform.Native, config_name: str | None=None):
		super().__init__(display_name, status, default_exe_name, launch_command_func, configs, host_platform, config_name)
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression if supported_compression else ()
		
class MednafenModule(StandardEmulator):
	def __init__(self, name: str, status: EmulatorStatus, supported_extensions: 'Collection[str]', params_func: 'ROMGameLaunchFunc', configs: 'Mapping[str, RunnerConfigValue] | None'=None):
		StandardEmulator.__init__(self, 'Mednafen', status, 'mednafen', params_func, supported_extensions, {'zip', 'gz'}, configs, config_name=f'Mednafen ({name})')

class MAMEDriver(StandardEmulator):
	def __init__(self, name: str, status: EmulatorStatus, launch_params: 'ROMGameLaunchFunc', supported_extensions: 'Collection[str]', configs: 'Mapping[str, RunnerConfigValue] | None'=None):
		_configs: 'MutableMapping[str, RunnerConfigValue]' = {}
		if configs:
			_configs.update(configs)
		_configs.update({
			'software_compatibility_threshold': RunnerConfigValue(int, 1, '0 = broken 1 = imperfect 2 = working other value = ignore; anything in the software list needs this to be considered compatible or -1 to ignore'),
			'skip_unknown_stuff': RunnerConfigValue(bool, False, "Skip anything that doesn't have a match in the software list"),
		})
		
		StandardEmulator.__init__(self, 'MAME', status, 'mame', launch_params, supported_extensions, {'7z', 'zip'}, _configs, config_name=f'MAME ({name})')

class ViceEmulator(StandardEmulator):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, params: 'ROMGameLaunchFunc'):
		#Also does z and zoo compression but I haven't done those in archives.py yet
		#TODO: Maybe just put z and zoo in the ordinary file extensions if we don't want to do that just yet?
		#WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
		#Does support compressed tapes/disks (gz/bz2/zip/tgz) but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here. So for now we pretend it supports no compression so we end up getting 7z to put the thing in a temporarily folder regardless
		StandardEmulator.__init__(self, 'VICE', status, default_exe_name, params, {'d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m', '20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin', 'p00', 'prg', 'tap', 't64'}, set(), config_name=f'VICE ({name})')

class LibretroCore(Emulator['EmulatedGame']):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: 'GenericLaunchCommandFunc[EmulatedGame] | None', supported_extensions: 'Collection[str]', configs: 'Mapping[str, RunnerConfigValue] | None'=None):
		self.supported_extensions = supported_extensions
		default_path = str(old_main_config.libretro_cores_directory.joinpath(default_exe_name + '_libretro.so').resolve()) if old_main_config.libretro_cores_directory else ''
		super().__init__(name, status, default_path, launch_command_func, configs=configs, config_name=name + ' (libretro)')

	@property
	def friendly_type_name(self) -> str:
		return 'libretro core'

class LibretroFrontend(Runner):
	def __init__(self, name: str, status: EmulatorStatus, default_exe_name: str, launch_command_func: 'LibretroFrontendLaunchCommandFunc', supported_compression: 'Collection[str] | None'=None, configs: 'Mapping[str, RunnerConfigValue] | None'=None, host_platform: HostPlatform=HostPlatform.Native):
		self._name = name
		self.status = status
		self.default_exe_name = default_exe_name
		self.launch_command_func = launch_command_func
		self.supported_compression = supported_compression if supported_compression else ()
		self.config_name = name #emulator_configs needs this, as we have decided that frontends can have their own config
		if configs:
			self.configs.update(configs)
		super().__init__(host_platform)

	@property
	def name(self) -> str:
		return self._name
