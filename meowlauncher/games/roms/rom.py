import os
import zlib
from abc import ABC, abstractmethod
from collections.abc import Collection
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from meowlauncher.common_types import MediaType
from meowlauncher.config.main_config import main_config
from meowlauncher.games.mame_common.software_list import (
    SoftwareMatcherArgs, format_crc32_for_software_list)
from meowlauncher.games.mame_common.software_list_info import (
    find_in_software_lists, matcher_args_for_bytes)
from meowlauncher.util import archives, cd_read, io_utils
from meowlauncher.util.utils import byteswap

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import (Software,
	                                                          SoftwareList)

class ROM(ABC):
	def __init__(self, path: Path) -> None:
		self.path = path
		self.ignore_name: bool = False
		self._name = self.path.name
		self._extension = '' #hmm what if it was None
		if self.path.suffix:
			self._extension = self.path.suffix.lower()[1:]

	@property
	def should_read_whole_thing(self) -> bool:
		return False

	def read_whole_thing(self) -> None:
		raise NotImplementedError(f'Do not read_whole_thing on {type(self)}, check should_read_whole_thing first')

	@property
	def name(self) -> str:
		return self.path.stem

	@property
	def is_folder(self) -> bool:
		return False

	@property
	def is_compressed(self) -> bool:
		return False

	@property
	def extension(self) -> str:
		return self._extension

	@abstractmethod
	def get_software_list_entry(self, software_lists: Collection['SoftwareList'], needs_byteswap: bool=False, skip_header: int=0) -> Optional['Software']:
		pass

class FileROM(ROM):
	def __init__(self, path: Path):
		super().__init__(path)	

		self._store_entire_file: bool = False
		self._entire_file: bytes = b''
		self.crc_for_database: Optional[int] = None
		self.header_length_for_crc_calculation: int = 0

	@property
	def should_read_whole_thing(self) -> bool:
		return self._get_size() < main_config.max_size_for_storing_in_memory

	def read_whole_thing(self) -> None:
		#Call this before doing any potential reading, it's just so you can check if the extension is something even relevant before reading a whole entire file in there
		#I guess you don't have to if you think there's a good chance it's like a CD image or whatever, this whole thing is just an optimization
		self._store_entire_file = True
		self._entire_file = self._read()
		
	def _read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return io_utils.read_file(self.path, None, seek_to, amount)

	def read(self, seek_to: int=0, amount: int=-1) -> bytes:
		if self._store_entire_file:
			if amount == -1:
				return self._entire_file[seek_to:]
			return self._entire_file[seek_to: seek_to + amount]
		return self._read(seek_to, amount)

	def _get_size(self) -> int:
		return io_utils.get_real_size(self.path)

	def get_size(self) -> int:
		if self._store_entire_file:
			return len(self._entire_file)
		return self._get_size()

	def _get_crc32(self) -> int:
		return io_utils.get_crc32(self.path)

	def get_crc32(self) -> int:
		if self.crc_for_database:
			return self.crc_for_database
		
		if self.header_length_for_crc_calculation > 0:
			crc32 = zlib.crc32(self.read(seek_to=self.header_length_for_crc_calculation)) & 0xffffffff
			self.crc_for_database = crc32
			return crc32

		crc32 = zlib.crc32(self._entire_file) & 0xffffffff if self._store_entire_file else self._get_crc32()
		self.crc_for_database = crc32
		return crc32

	@property
	def name(self) -> str:
		if self._extension == 'png' and self._name.endswith('.p8'):
			return self._name[:-3]
			
		return super().name

	@property
	def extension(self) -> str:
		#Hmm… potentially we can just check .suffixes instead of .suffix, but this is only needed for Pico-8 right now so why be confusing if we don't have to
		if self._extension == 'png' and self._name.endswith('.p8'):
			return 'p8.png'
			
		return self._extension
	
	def get_software_list_entry(self, software_lists: Collection['SoftwareList'], needs_byteswap: bool=False, skip_header: int=0) -> Optional['Software']:
		if skip_header:
			#Hmm might deprecate this in favour of header_length_for_crc_calculation
			data = self.read(seek_to=skip_header)
			return find_in_software_lists(software_lists, matcher_args_for_bytes(data))

		if needs_byteswap:
			crc32 = format_crc32_for_software_list(zlib.crc32(byteswap(self.read())) & 0xffffffff)
		else:
			crc32 = format_crc32_for_software_list(self.get_crc32())
			
		def _file_rom_reader(offset, amount) -> bytes:
			data = self.read(seek_to=offset, amount=amount)
			if needs_byteswap:
				return byteswap(data)
			return data
			
		args = SoftwareMatcherArgs(crc32, None, self.get_size() - self.header_length_for_crc_calculation, _file_rom_reader)
		return find_in_software_lists(software_lists, args)

class CompressedROM(FileROM):
	def __init__(self, path: Path):
		super().__init__(path)
		
		for entry in archives.compressed_list(str(self.path)):
			if os.extsep in entry:
				self.inner_name, extension = entry.rsplit(os.extsep, 1)
				self.inner_extension = extension.lower()
			else:
				self.inner_name = entry
				self.inner_extension = ''
			self.inner_filename = entry
			#Only use the first file, if there is more, then you're weird
			return
		raise IOError(f'Nothing in {path}')

	@property
	def extension(self) -> str:
		return self.inner_extension

	@property
	def name(self) -> str:
		return self.inner_name
		
	def _read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return io_utils.read_file(self.path, self.inner_filename, seek_to, amount)

	def _get_size(self) -> int:
		return io_utils.get_real_size(self.path, self.inner_filename)

	def _get_crc32(self) -> int:
		return io_utils.get_crc32(self.path, self.inner_filename)

class GCZFileROM(FileROM):
	@property
	def should_read_whole_thing(self) -> bool:
		return False

	def read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return cd_read.read_gcz(self.path, seek_to, amount)

	def get_crc32(self) -> int:
		raise NotImplementedError('Trying to hash a .gcz file is silly and should not be done')

	def get_software_list_entry(self, _: Collection['SoftwareList'], __: bool = False, ___: int = 0) -> Optional['Software']:
		raise NotImplementedError('Trying to get software of a .gcz file is silly and should not be done')

def rom_file(path: Path) -> FileROM:
	ext = path.suffix 
	if ext: #To be fair if it's '' it won't match any file ever… hmm
		if ext[1:].lower() == 'gcz':
			return GCZFileROM(path)
		if ext[1:].lower() in archives.compressed_exts:
			return CompressedROM(path)
	return FileROM(path)

class FolderROM(ROM):
	def __init__(self, path: Path) -> None:
		super().__init__(path)
		self.relevant_files: dict[str, Path] = {}
		self.media_type: Optional[MediaType] = None
		self.ignore_name = False
	
	def get_subfolder(self, subpath: str, ignore_case=False) -> Optional[Path]:
		path = self.path.joinpath(subpath)
		if path.is_dir():
			return path
		if ignore_case and subpath:
			for f in self.path.iterdir():
				if f.is_dir() and f.name.lower() == subpath.lower():
					return f
		return None
	
	def get_file(self, subpath: str, ignore_case=False) -> Optional[Path]:
		path = self.path.joinpath(subpath)
		if path.is_file():
			return path
		if ignore_case and subpath:
			for f in self.path.iterdir():
				if f.is_file() and f.name.lower() == subpath.lower():
					return f
		return None

	def has_subfolder(self, subpath: str) -> bool:
		return self.path.joinpath(subpath).is_dir()
	
	def has_file(self, subpath: str) -> bool:
		return self.path.joinpath(subpath).is_file()

	def has_any_file_with_extension(self, extension: str, ignore_case: bool=False) -> bool:
		if ignore_case:
			extension = extension.lower()
		for f in self.path.iterdir():
			name = f.name
			if ignore_case:
				name = name.lower()
			if f.is_file() and f.suffix == os.path.extsep + extension:
				return True
		return False
	
	@property
	def is_folder(self):
		return True
	
	@property
	def is_compressed(self):
		return False

	def get_software_list_entry(self, _: Collection['SoftwareList'], __: bool = False, ___: int = 0) -> Optional['Software']:
		raise NotImplementedError('Trying to get software of a folder is silly and should not be done')
