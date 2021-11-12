from abc import ABC
import os
from pathlib import Path
from typing import Optional
from zlib import crc32

from meowlauncher.common_types import MediaType
from meowlauncher.config.main_config import main_config
from meowlauncher.util import archives, cd_read, io_utils

class ROM(ABC):
	def __init__(self, path: str) -> None:
		self.path = Path(path)
		self.ignore_name: bool = False
		self._name = self.path.name
		self._extension = '' #hmm what if it was None
		if self.path.suffix:
			self._extension = self.path.suffix.lower()[1:]
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

class FileROM(ROM):
	def __init__(self, path: str):
		super().__init__(path)	

		self.store_entire_file: bool = False
		self.entire_file: bytes = b''
		self.crc_for_database: Optional[int] = None
		self.header_length_for_crc_calculation: int = 0

	def maybe_read_whole_thing(self) -> None:
		#Please call this before doing anything, it's just so you can check if the extension is something even relevant before reading a whole entire file in there
		#I guess you don't have to if you think there's a good chance it's like a CD image or whatever, this whole thing is just an optimization
		if self._get_size() < main_config.max_size_for_storing_in_memory:
			self.store_entire_file = True
			self.entire_file = self._read()
		
	def _read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return io_utils.read_file(str(self.path), None, seek_to, amount)

	def read(self, seek_to: int=0, amount: int=-1) -> bytes:
		if self.store_entire_file:
			if amount == -1:
				return self.entire_file[seek_to:]
			return self.entire_file[seek_to: seek_to + amount]
		return self._read(seek_to, amount)

	def _get_size(self) -> int:
		return io_utils.get_real_size(str(self.path))

	def get_size(self) -> int:
		if self.store_entire_file:
			return len(self.entire_file)
		return self._get_size()

	def _get_crc32(self) -> int:
		return io_utils.get_crc32(str(self.path))

	def get_crc32(self) -> int:
		if self.crc_for_database:
			return self.crc_for_database
		
		if self.header_length_for_crc_calculation > 0:
			crc = crc32(self.read(seek_to=self.header_length_for_crc_calculation)) & 0xffffffff
			self.crc_for_database = crc
			return crc

		crc = crc32(self.entire_file) & 0xffffffff if self.store_entire_file else self._get_crc32()
		self.crc_for_database = crc
		return crc

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
	
class CompressedROM(FileROM):
	def __init__(self, path: str):
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
		return io_utils.read_file(str(self.path), self.inner_filename, seek_to, amount)

	def _get_size(self) -> int:
		return io_utils.get_real_size(str(self.path), self.inner_filename)

	def _get_crc32(self) -> int:
		return io_utils.get_crc32(str(self.path), self.inner_filename)

class GCZFileROM(FileROM):
	def read(self, seek_to: int=0, amount: int=-1) -> bytes:
		return cd_read.read_gcz(str(self.path), seek_to, amount)

def rom_file(path) -> FileROM:
	ext = path.rsplit(os.extsep, 1)[-1]
	if ext.lower() == 'gcz':
		return GCZFileROM(path)
	if ext in archives.compressed_exts:
		return CompressedROM(path)
	return FileROM(path)

class FolderROM(ROM):
	def __init__(self, path) -> None:
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
			if f.is_file() and f.name.endswith(os.path.extsep + extension):
				return True
		return False
	
	@property
	def is_folder(self):
		return True
	
	@property
	def is_compressed(self):
		return False
