from typing import Any, Optional
from collections.abc import Sequence

from meowlauncher.common_types import ConfigValueType, MediaType
from meowlauncher.games.roms.rom import FileROM

class PlatformConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value: Any, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class EmulatedPlatform():
	def __init__(self, mame_drivers: list[str], mame_software_lists: list[str], emulators: list[str], file_types: dict[MediaType, list[str]]=None, options: dict[str, PlatformConfigValue]=None, is_virtual: bool=False, dat_names: list[str]=None, dat_uses_serial: bool=False, databases_are_byteswapped: bool=False, autodetect_tv_type: bool=False):
		self.mame_drivers = mame_drivers #Parent drivers that represent this system
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators
		self.file_types = file_types if file_types else {}
		self.options = options if options else {}
		self.is_virtual = is_virtual #Maybe needs better name
		self.dat_names = dat_names if dat_names else [] #For libretro-database
		self.dat_uses_serial = dat_uses_serial
		self.databases_are_byteswapped = databases_are_byteswapped #Arguably I should create two separate parameters for both MAME SL and libretro-database, but so far this is only needed for N64 which has both swapped
		self.autodetect_tv_type = autodetect_tv_type

	def is_valid_file_type(self, extension: str) -> bool:
		return any(extension in extensions for extensions in self.file_types.values() if isinstance(extension, str))

	def get_media_type(self, rom: FileROM) -> Optional[MediaType]:
		for media_type, extensions in self.file_types.items():
			if rom.extension in extensions:
				return media_type
		return None

class PCPlatform():
	def __init__(self, json_name: str, emulators: Sequence[str], options: dict[str, PlatformConfigValue]=None):
		self.json_name = json_name
		self.emulators = emulators
		self.options = options if options else {}
