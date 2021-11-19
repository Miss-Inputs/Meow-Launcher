from abc import ABC
from collections.abc import Collection, Callable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Optional

from meowlauncher.common_types import (ConfigValueType, MediaType,
                                       TypeOfConfigValue)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM, FolderROM


class PlatformConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type: ConfigValueType, default_value: TypeOfConfigValue, description: str):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class ChooseableEmulatedPlatform(ABC):
	def __init__(self, valid_emulator_names: Collection[str], name: str, options: Optional[Mapping[str, PlatformConfigValue]]) -> None:
		self.valid_emulator_names = valid_emulator_names
		self.name = name
		self.options: MutableMapping[str, PlatformConfigValue] = {} #But please don't mutate it if you are not a subclass in the __init__ method
		if options:
			self.options.update(options)

class StandardEmulatedPlatform(ChooseableEmulatedPlatform):
	def __init__(self, name: str, mame_drivers: Collection[str], mame_software_lists: Collection[str], emulators: Collection[str], file_types: Mapping[MediaType, Collection[str]]=None, options: Mapping[str, PlatformConfigValue]=None, is_virtual: bool=False, dat_names: Collection[str]=None, dat_uses_serial: bool=False, databases_are_byteswapped: bool=False, autodetect_tv_type: bool=False, folder_check: Callable[['FolderROM'], Optional[MediaType]]=None):
		super().__init__(emulators, name, options)
		self.mame_drivers = mame_drivers #Parent drivers that represent this system
		self.mame_software_lists = mame_software_lists
		self.file_types = file_types if file_types else {}
		self.is_virtual = is_virtual #Maybe needs better name
		self.dat_names = dat_names if dat_names else () #For libretro-database
		self.dat_uses_serial = dat_uses_serial
		self.databases_are_byteswapped = databases_are_byteswapped #Arguably I should create two separate parameters for both MAME SL and libretro-database, but so far this is only needed for N64 which has both swapped
		self.autodetect_tv_type = autodetect_tv_type
		self.folder_check = folder_check

		if mame_software_lists:
			self.options['find_software_by_name'] = PlatformConfigValue(ConfigValueType.Bool, False, 'Use game name to search software list')
			self.options['find_software_by_product_code'] = PlatformConfigValue(ConfigValueType.Bool, False, 'Use game product code to search software list')

	def is_valid_file_type(self, extension: str) -> bool:
		return any(extension in extensions for extensions in self.file_types.values() if isinstance(extension, str))

	def get_media_type(self, rom: 'FileROM') -> Optional[MediaType]:
		for media_type, extensions in self.file_types.items():
			if rom.extension in extensions:
				return media_type
		return None

class PCPlatform(ChooseableEmulatedPlatform):
	def __init__(self, name: str, json_name: str, emulators: Collection[str], options: Mapping[str, PlatformConfigValue]=None):
		super().__init__(emulators, name, options)
		self.json_name = json_name
