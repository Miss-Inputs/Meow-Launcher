from abc import ABC
from collections.abc import Callable, Collection, Mapping, MutableMapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from meowlauncher.common_types import MediaType
from meowlauncher.config_types import ConfigValueType, TypeOfConfigValue

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import ROM, FolderROM

@dataclass(frozen=True)
class PlatformConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	type: ConfigValueType
	default_value: TypeOfConfigValue
	description: str

class ChooseableEmulatedPlatform(ABC):
	def __init__(self, valid_emulator_names: Collection[str], name: str, options: Optional[Mapping[str, PlatformConfigValue]]) -> None:
		self.valid_emulator_names = valid_emulator_names
		self.name = name
		self.options: MutableMapping[str, PlatformConfigValue] = {} #But please don't mutate it if you are not a subclass in the __init__ method
		if options:
			self.options.update(options)

	def __hash__(self) -> int:
		return self.name.__hash__()
		
class StandardEmulatedPlatform(ChooseableEmulatedPlatform):
	def __init__(self, name: str, mame_drivers: Collection[str], software_list_names: Collection[str], emulators: Collection[str], file_types: Mapping[MediaType, Collection[str]]|None=None, options: Mapping[str, PlatformConfigValue]|None=None, is_virtual: bool=False, dat_names: Collection[str]|None=None, dat_uses_serial: bool=False, databases_are_byteswapped: bool=False, autodetect_tv_type: bool=False, folder_check: Callable[['FolderROM'], Optional[MediaType]]|None=None):
		super().__init__(emulators, name, options)
		self.mame_drivers = mame_drivers #Parent drivers that represent this system
		self.software_list_names = software_list_names
		self.file_types = file_types if file_types else {}
		self.is_virtual = is_virtual #Maybe needs better name
		self.dat_names = dat_names if dat_names else () #For libretro-database
		self.dat_uses_serial = dat_uses_serial
		self.databases_are_byteswapped = databases_are_byteswapped #Arguably I should create two separate parameters for both MAME SL and libretro-database, but so far this is only needed for N64 which has both swapped
		self.autodetect_tv_type = autodetect_tv_type
		self.folder_check = folder_check

		if software_list_names:
			self.options['find_software_by_name'] = PlatformConfigValue(ConfigValueType.Bool, False, 'Use game name to search software list')
			self.options['find_software_by_product_code'] = PlatformConfigValue(ConfigValueType.Bool, False, 'Use game product code to search software list')

	def is_valid_file_type(self, extension: str) -> bool:
		return any(extension in extensions for extensions in self.file_types.values())

	def get_media_type(self, rom: 'ROM') -> Optional[MediaType]:
		return next((media_type for media_type, extensions in self.file_types.items() if rom.extension in extensions), None)

class ManuallySpecifiedPlatform(ChooseableEmulatedPlatform):
	#TODO: Not necessarily emulated! But it does need to be treated as a platform, so like I dunno, maybe we just pretend it is and that works out
	def __init__(self, name: str, json_name: str, emulators: Collection[str], options: Mapping[str, PlatformConfigValue]=None):
		super().__init__(emulators, name, options)
		self.json_name = json_name
