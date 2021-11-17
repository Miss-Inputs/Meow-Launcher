from abc import ABC
from collections.abc import Collection
from typing import Any, Optional

from meowlauncher.common_types import ConfigValueType, MediaType
from meowlauncher.games.roms.rom import FileROM


class PlatformConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value: Any, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class ChooseableEmulatedPlatform(ABC):
	def __init__(self, valid_emulator_names: Collection[str], name: str) -> None:
		self.valid_emulator_names = valid_emulator_names
		self.name = name

class StandardEmulatedPlatform(ChooseableEmulatedPlatform):
	def __init__(self, name: str, mame_drivers: Collection[str], mame_software_lists: Collection[str], emulators: Collection[str], file_types: dict[MediaType, list[str]]=None, options: dict[str, PlatformConfigValue]=None, is_virtual: bool=False, dat_names: Collection[str]=None, dat_uses_serial: bool=False, databases_are_byteswapped: bool=False, autodetect_tv_type: bool=False):
		super().__init__(emulators, name)
		self.mame_drivers = mame_drivers #Parent drivers that represent this system
		self.mame_software_lists = mame_software_lists
		self.file_types = file_types if file_types else {}
		self.is_virtual = is_virtual #Maybe needs better name
		self.dat_names = dat_names if dat_names else [] #For libretro-database
		self.dat_uses_serial = dat_uses_serial
		self.databases_are_byteswapped = databases_are_byteswapped #Arguably I should create two separate parameters for both MAME SL and libretro-database, but so far this is only needed for N64 which has both swapped
		self.autodetect_tv_type = autodetect_tv_type

		self.options = {}
		if options:
			self.options.update(options)
		if mame_software_lists:
			self.options['find_software_by_name'] = PlatformConfigValue(ConfigValueType.Bool, False, 'Use game name to search software list')
			self.options['find_software_by_product_code'] = PlatformConfigValue(ConfigValueType.Bool, False, 'Use game product code to search software list')

	def is_valid_file_type(self, extension: str) -> bool:
		return any(extension in extensions for extensions in self.file_types.values() if isinstance(extension, str))

	def get_media_type(self, rom: FileROM) -> Optional[MediaType]:
		for media_type, extensions in self.file_types.items():
			if rom.extension in extensions:
				return media_type
		return None

class PCPlatform(ChooseableEmulatedPlatform):
	def __init__(self, name: str, json_name: str, emulators: Collection[str], options: dict[str, PlatformConfigValue]=None):
		super().__init__(emulators, name)
		self.json_name = json_name
		self.options = options if options else {}
