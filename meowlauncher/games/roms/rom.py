import logging
import os
import zlib
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterator, MutableMapping
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from meowlauncher.common_types import ByteAmount, MediaType
from meowlauncher.config.main_config import main_config
from meowlauncher.games.mame_common.software_list import (
    SoftwareMatcherArgs, format_crc32_for_software_list)
from meowlauncher.games.mame_common.software_list_find_utils import \
    find_in_software_lists
from meowlauncher.util import archives, cd_read, io_utils
from meowlauncher.util.utils import byteswap

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import (Software,
	                                                          SoftwareList)

logger = logging.getLogger(__name__)

class ROM(ABC):
	def __init__(self, path: Path) -> None:
		self.path = path
		self.ignore_name: bool = False
		self._name = self.path.stem
		self._extension = self.path.suffix[1:].lower()

	def __str__(self) -> str:
		return str(self.path)

	#To word a different way: Does this point to other files, or should anything else be considered part of this
	@property
	def contains_other_files(self) -> bool:
		return False

	@property
	def contained_files(self) -> Collection[Path]:
		return tuple()

	@property
	def should_read_whole_thing(self) -> bool:
		return False

	def read_whole_thing(self) -> None:
		raise NotImplementedError(f'Do not read_whole_thing on {type(self)}, check should_read_whole_thing first')

	@property
	def name(self) -> str:
		return self._name

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
	def get_software_list_entry(self, software_lists: Collection['SoftwareList'], needs_byteswap: bool=False) -> Optional['Software']:
		pass

	@cached_property
	def size(self) -> ByteAmount:
		if self.contains_other_files:
			return ByteAmount(sum(contained_file.stat().st_size for contained_file in self.contained_files))
		return ByteAmount(self.path.stat().st_size)

class FileROM(ROM):
	def __init__(self, path: Path):
		super().__init__(path)	

		self._store_entire_file: bool = False
		self._entire_file: bytes = b''
		self._crc32: Optional[int] = None
		self.header_length_for_crc_calculation: int = 0

	@property
	def should_read_whole_thing(self) -> bool:
		max_size_for_storing_in_memory = cast(int, main_config.max_size_for_storing_in_memory)
		if max_size_for_storing_in_memory < 0:
			return False
		return self._get_size() < max_size_for_storing_in_memory

	def read_whole_thing(self) -> None:
		"""
		Call this before doing any potential reading, it's just so you can check if the extension is something even relevant before reading a whole entire file in there
		I guess you don't have to if you think there's a good chance it's like a CD image or whatever, this whole thing is just an optimization
		"""
		self._store_entire_file = True
		self._entire_file = self._read()
		
	def _read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return io_utils.read_file(self.path, seek_to, amount)

	def read(self, seek_to: int=0, amount: int=-1) -> bytes:
		if self._store_entire_file:
			if amount == -1:
				return self._entire_file[seek_to:]
			return self._entire_file[seek_to: seek_to + amount]
		return self._read(seek_to, amount)

	def _get_size(self) -> ByteAmount:
		return super().size

	@property
	def size(self) -> ByteAmount:
		if self._store_entire_file:
			return ByteAmount(len(self._entire_file))
		return self._get_size()

	def _get_crc32(self) -> int:
		return zlib.crc32(self.path.read_bytes()) & 0xffffffff

	@property
	def crc32(self) -> int:
		if self._crc32 is not None:
			return self._crc32
		
		if self.header_length_for_crc_calculation > 0:
			crc32 = zlib.crc32(self.read(seek_to=self.header_length_for_crc_calculation)) & 0xffffffff
			self._crc32 = crc32
			return crc32

		crc32 = zlib.crc32(self._entire_file) & 0xffffffff if self._store_entire_file else self._get_crc32()
		self._crc32 = crc32
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
	
	def get_software_list_entry(self, software_lists: Collection['SoftwareList'], needs_byteswap: bool=False) -> Optional['Software']:
		crc32 = zlib.crc32(byteswap(self.read())) & 0xffffffff if needs_byteswap else self.crc32
		
		def _file_rom_reader(offset: int, amount: int) -> bytes:
			data = self.read(seek_to=offset, amount=amount)
			if needs_byteswap:
				return byteswap(data)
			return data
		
		#TODO Hmm does that make the most sense, why get the crc32 if the header has a length
		size_arg = self.size - self.header_length_for_crc_calculation if self.header_length_for_crc_calculation else None
		args = SoftwareMatcherArgs(format_crc32_for_software_list(crc32), None, size_arg, _file_rom_reader)
		return find_in_software_lists(software_lists, args)

class CompressedROM(FileROM):
	def __init__(self, path: Path):
		super().__init__(path)
		self._size = None
		
		for name, size, crc32 in archives.compressed_list(self.path):
			self._size = size
			self._crc32 = crc32
			if os.extsep in name:
				self.inner_name, extension = name.rsplit(os.extsep, 1)
				self.inner_extension = extension.lower()
			else:
				self.inner_name = name
				self.inner_extension = ''
			self.inner_filename = name
			#Only use the first file, if there is more, then you're weird
			return
		raise IOError(f'Nothing in {path}')

	@property
	def outer_extension(self) -> str:
		return self._extension

	@property
	def extension(self) -> str:
		return self.inner_extension

	@property
	def name(self) -> str:
		return self.inner_name
		
	def _read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return archives.compressed_get(self.path, self.inner_filename, seek_to, amount)

	def _get_size(self) -> ByteAmount:
		return ByteAmount(archives.compressed_getsize(self.path, self.inner_filename))

	@cached_property
	def compressed_size(self) -> ByteAmount:
		return ByteAmount(self.path.stat().st_size)

	@property
	def size(self) -> ByteAmount:
		if self._size is None:
			self._size = super().size
		return self._size

	def _get_crc32(self) -> int:
		return archives.get_crc32_of_archive(self.path, self.inner_filename)

class GCZFileROM(FileROM):
	@property
	def should_read_whole_thing(self) -> bool:
		return False

	@property
	def size(self) -> ByteAmount:
		return ByteAmount.from_bytes(self._read(seek_to=16, amount=8), 'little')

	@property
	def compressed_size(self) -> ByteAmount:
		return super().size

	def read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return cd_read.read_gcz(self.path, seek_to, amount)

	@property
	def crc32(self) -> int:
		raise NotImplementedError('Trying to hash a .gcz file is silly and should not be done')

	def get_software_list_entry(self, _: Collection['SoftwareList'], __: bool = False, ___: int = 0) -> Optional['Software']:
		raise NotImplementedError('Trying to get software of a .gcz file is silly and should not be done')

class UnsupportedCHDError(Exception):
	pass

class CHDFileROM(ROM):
	#There is an argument to be made that this _could_ be a FileROM that raises NotImplementedError on read() I guess… maybe if/once we can read from it and then don't need to throw that exception, otherwise it's a good way to avoid accidentally thinking we can
	@property
	def should_read_whole_thing(self) -> bool:
		return False

	def _get_sha1(self) -> str:
		with self.path.open('rb') as my_file:
			header = my_file.read(124)
			if header[0:8] != b'MComprHD':
				raise UnsupportedCHDError(f'Header magic {header[0:8]!r} unknown')
			chd_version = int.from_bytes(header[12:16], 'big')
			if chd_version == 4:
				sha1 = header[48:68]
			elif chd_version == 5:
				sha1 = header[84:104]
			else:
				raise UnsupportedCHDError(f'Version {chd_version} unknown')
			return bytes.hex(sha1)

	def get_software_list_entry(self, software_lists: Collection['SoftwareList'], __: bool = False, ___: int = 0) -> Optional['Software']:
		try:
			args = SoftwareMatcherArgs(None, self._get_sha1(), None, None)
			return find_in_software_lists(software_lists, args)
		except UnsupportedCHDError as e:
			logger.warning('UnsupportedCHDError %s in %s', e.args, self)
			return None

class FolderROM(ROM):
	def __init__(self, path: Path) -> None:
		super().__init__(path)
		self.relevant_files: MutableMapping[str, Path] = {}
		self.media_type: Optional[MediaType] = None
		self.ignore_name = False

	@property
	def contains_other_files(self) -> bool:
		return True

	@property
	def contained_files(self) -> Collection[Path]:
		return set(self.path.rglob('*'))

	def get_subfolder(self, subpath: str, ignore_case: bool=False) -> Optional[Path]:
		path = self.path.joinpath(subpath)
		if path.is_dir():
			return path
		if ignore_case and subpath:
			for f in self.path.iterdir():
				if f.is_dir() and f.name.lower() == subpath.lower():
					return f
		return None
	
	def get_file(self, subpath: str, ignore_case: bool=False) -> Optional[Path]:
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
			suffix = f.suffix[1:]
			if ignore_case:
				suffix = suffix.lower()
			if f.is_file() and suffix == extension:
				return True
		return False
	
	@property
	def is_folder(self) -> bool:
		return True
	
	@property
	def is_compressed(self) -> bool:
		return False

	def get_software_list_entry(self, _: Collection['SoftwareList'], __: bool = False, ___: int = 0) -> Optional['Software']:
		raise NotImplementedError('Trying to get software of a folder is silly and should not be done')

def _parse_m3u(path: Path) -> Iterator[ROM]:
	with path.open('rt', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if line.startswith("#"):
				continue
		
			try:
				referenced_file = Path(line) if line.startswith('/') else path.parent / line
				if not referenced_file.is_file():
					logger.info('M3U file %s has a broken reference: %s', path, referenced_file)
					continue
				yield get_rom(referenced_file)
			except ValueError:
				logger.info('M3U file %s has a broken line: %s', path, line)

class M3UPlaylist(ROM):
	def __init__(self, path: Path):
		super().__init__(path)
		self.subroms = tuple(_parse_m3u(path))

	@property
	def contains_other_files(self) -> bool:
		return bool(self.subroms)

	@property
	def contained_files(self) -> Collection[Path]:
		return {subrom.path for subrom in self.subroms}

	@property
	def should_read_whole_thing(self) -> bool:
		return False
	
	def get_software_list_entry(self, software_lists: Collection['SoftwareList'], needs_byteswap: bool = False) -> Optional['Software']:
		if not self.subroms:
			raise FileNotFoundError('m3u does not have any valid files in it, which is weird and should not happen')
		#TODO: Maybe this isnt' even correct - we want to find which SoftwarePart matches what, in theory
		return self.subroms[0].get_software_list_entry(software_lists, needs_byteswap)

def get_rom(path: Path) -> ROM:
	if path.is_dir():
		return FolderROM(path)
	ext = path.suffix
	if ext: #To be fair if it's '' it won't match any file ever… hmm
		if ext[1:].lower() == 'gcz':
			return GCZFileROM(path)
		if ext[1:].lower() == 'chd':
			return CHDFileROM(path)
		if ext[1:].lower() == 'm3u':
			return M3UPlaylist(path)
		if ext[1:].lower() in archives.compressed_exts:
			return CompressedROM(path)
	return FileROM(path)
