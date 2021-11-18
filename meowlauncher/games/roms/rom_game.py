import tempfile
import zlib
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from meowlauncher.common_types import MediaType
from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.games.mame_common.software_list import (
    SoftwareMatcherArgs, format_crc32_for_software_list)
from meowlauncher.games.mame_common.software_list_info import (
    UnsupportedCHDError, find_in_software_lists,
    find_in_software_lists_with_custom_matcher, find_software_by_name,
    matcher_args_for_bytes)
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.util.io_utils import make_filename, read_file
from meowlauncher.util.utils import byteswap, find_filename_tags_at_end

from .rom import ROM, CompressedROM, FileROM

if TYPE_CHECKING:
	from meowlauncher.config.platform_config import PlatformConfig
	from meowlauncher.configured_emulator import ConfiguredStandardEmulator
	from meowlauncher.emulated_platform import StandardEmulatedPlatform
	from meowlauncher.games.mame_common.software_list import (Software,
	                                                          SoftwareList,
	                                                          SoftwarePart)


def _get_sha1_from_chd(chd_path: Path) -> str:
	header = read_file(chd_path, amount=124)
	if header[0:8] != b'MComprHD':
		raise UnsupportedCHDError('Header magic %s unknown' % str(header[0:8]))
	chd_version = int.from_bytes(header[12:16], 'big')
	if chd_version == 4:
		sha1 = header[48:68]
	elif chd_version == 5:
		sha1 = header[84:104]
	else:
		raise UnsupportedCHDError('Version %d unknown' % chd_version)
	return bytes.hex(sha1)


def _software_list_product_code_matcher(part: 'SoftwarePart', product_code: str) -> bool:
	part_code = part.software.serial
	if not part_code:
		return False

	return product_code in part_code.split(', ')

class ROMGame(EmulatedGame):
	def __init__(self, rom: ROM, platform: 'StandardEmulatedPlatform', platform_config: 'PlatformConfig'):
		super().__init__(platform_config)
		self.rom = rom
		self.metadata.platform = platform.name
		self.platform = platform
		self.metadata.categories = []
		self.filename_tags = find_filename_tags_at_end(rom.path.name)

		self.subroms: list[FileROM] = []
		self.software_lists: list['SoftwareList'] = []
		self.exception_reason: Optional[BaseException] = None
	
	@property
	def name(self) -> str:
		name = self.rom.name
		if self.rom.ignore_name and self.metadata.names:
			name = self.metadata.names.get('Name', list(self.metadata.names.values())[0])
			
		return name

	def get_software_list_entry(self, skip_header: int=0) -> Optional['Software']:
		#TODO: Could this be methods inside ROM?
		if not self.software_lists:
			return None

		if self.metadata.media_type == MediaType.OpticalDisc:
			software = None
			if self.rom.extension == 'chd':
				try:
					sha1 = _get_sha1_from_chd(self.rom.path)
					args = SoftwareMatcherArgs(None, sha1, None, None)
					software = find_in_software_lists(self.software_lists, args)
				except UnsupportedCHDError:
					pass
		else:
			if self.subroms:
				#TODO: Get first floppy for now, because right now we don't differentiate with parts or anything; this part of the code sucks
				data = self.subroms[0].read(seek_to=skip_header)
				software = find_in_software_lists(self.software_lists, matcher_args_for_bytes(data))
			else:
				if self.rom.is_folder:
					raise TypeError('This should not be happening, we are calling get_software_list_entry on a folder')
				file_rom = cast(FileROM, self.rom)
				if skip_header:
					#Hmm might deprecate this in favour of header_length_for_crc_calculation
					data = file_rom.read(seek_to=skip_header)
					software = find_in_software_lists(self.software_lists, matcher_args_for_bytes(data))
				else:
					if self.platform.databases_are_byteswapped:
						crc32 = format_crc32_for_software_list(zlib.crc32(byteswap(file_rom.read())) & 0xffffffff)
					else:
						crc32 = format_crc32_for_software_list(file_rom.get_crc32())
						
					def _file_rom_reader(offset, amount) -> bytes:
						data = file_rom.read(seek_to=offset, amount=amount)
						if self.platform.databases_are_byteswapped:
							return byteswap(data)
						return data
						
					args = SoftwareMatcherArgs(crc32, None, file_rom.get_size() - file_rom.header_length_for_crc_calculation, _file_rom_reader)
					software = find_in_software_lists(self.software_lists, args)

		if not software and self.platform_config.options.get('find_software_by_name', False):
			software = find_software_by_name(self.software_lists, self.rom.name)
		if not software and (self.platform_config.options.get('find_software_by_product_code', False) and self.metadata.product_code):
			software = find_in_software_lists_with_custom_matcher(self.software_lists, _software_list_product_code_matcher, [self.metadata.product_code])

		return software

class ROMLauncher(EmulatorLauncher):
	def __init__(self, game: ROMGame, emulator: 'ConfiguredStandardEmulator', platform_config: 'PlatformConfig') -> None:
		self.game: ROMGame = game
		self.runner: 'ConfiguredStandardEmulator' = emulator
		super().__init__(game, emulator, platform_config.options)

	@property
	def game_type(self) -> str:
		return 'ROM'
	
	@property
	def game_id(self) -> str:
		return str(self.game.rom.path)

	def get_launch_command(self) -> LaunchCommand:
		#TODO: Ideally EmulatorLauncher would do something useful with self.runner and then we call super() but that also needs refactoring
		command = super().get_launch_command()
		if self.game.rom.is_compressed:
			rom = cast(CompressedROM, self.game.rom)
			if not self.runner.supports_compressed_extension(rom.extension):
				temp_extraction_folder = Path(tempfile.gettempdir(), 'meow-launcher-' + make_filename(self.game.name))
				extracted_path = temp_extraction_folder.joinpath(rom.inner_filename)
				command = command.replace_path_argument(extracted_path)
				command = command.prepend_command(LaunchCommand('7z', ['x', '-o' + temp_extraction_folder.as_posix(), self.game.rom.path.as_posix()]))
				command = command.append_command(LaunchCommand('rm', ['-rf', temp_extraction_folder.as_posix()]))
		else:
			command = command.replace_path_argument(self.game.rom.path)
		return command
