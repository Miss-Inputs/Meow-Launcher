import os
from typing import Optional
from zlib import crc32

from meowlauncher import archives, cd_read, io_utils
from meowlauncher.config.main_config import main_config


class FileROM():
	def __init__(self, path: str):
		self.path = path
		self.ignore_name: bool = False

		original_name = os.path.basename(path)
		self.original_extension = None
		if os.extsep in original_name:
			name_without_extension, self.original_extension = original_name.rsplit(os.extsep, 1)
			self.original_extension = self.original_extension.lower()
		else:
			name_without_extension = original_name

		self.extension = self.original_extension

		if self.original_extension in archives.compressed_exts:
			self.is_compressed = True

			for entry in archives.compressed_list(self.path):

				if os.extsep in entry:
					self.name, extension = entry.rsplit(os.extsep, 1)
					self.extension = extension.lower()
				else:
					self.name = entry
				self.compressed_entry = entry
		else:
			self.is_compressed = False
			self.compressed_entry = None
			self.name = name_without_extension

		if self.extension == 'png' and self.name.endswith('.p8'):
			self.name = self.name[:-3]
			self.extension = 'p8.png'
			
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
		
	def _read(self, seek_to=0, amount=-1) -> bytes:
		return io_utils.read_file(self.path, self.compressed_entry, seek_to, amount)

	def read(self, seek_to=0, amount=-1) -> bytes:
		if self.store_entire_file:
			if amount == -1:
				return self.entire_file[seek_to:]
			return self.entire_file[seek_to: seek_to + amount]
		return self._read(seek_to, amount)

	def _get_size(self) -> int:
		return io_utils.get_real_size(self.path, self.compressed_entry)

	def get_size(self) -> int:
		if self.store_entire_file:
			return len(self.entire_file)
		return self._get_size()

	def _get_crc32(self) -> int:
		return io_utils.get_crc32(self.path, self.compressed_entry)

	def get_crc32(self) -> int:
		if self.crc_for_database:
			return self.crc_for_database
		
		if self.header_length_for_crc_calculation > 0:
			crc = crc32(self.read(seek_to=self.header_length_for_crc_calculation)) & 0xffffffff
			self.crc_for_database = crc
			return crc

		if self.store_entire_file:
			crc = crc32(self.entire_file) & 0xffffffff
		else:
			crc = self._get_crc32()
		self.crc_for_database = crc
		return crc
	
	@property
	def is_folder(self) -> bool:
		return False

class GCZFileROM(FileROM):
	def read(self, seek_to=0, amount=-1):
		return cd_read.read_gcz(self.path, seek_to, amount)

def rom_file(path):
	ext = path.rsplit(os.extsep, 1)[-1]
	if ext.lower() == 'gcz':
		return GCZFileROM(path)
	return FileROM(path)

