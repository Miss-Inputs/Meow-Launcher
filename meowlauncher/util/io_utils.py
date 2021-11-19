import os
import pathlib
import re
import zlib
from typing import Optional

from .archives import compressed_get, compressed_getsize, get_crc32_of_archive

crc_chunk_size = 128 * 1024 * 1024

def ensure_exist(path: pathlib.Path):
	path.parent.mkdir(exist_ok=True, parents=True)
	path.touch()

def get_real_size(path: pathlib.Path, compressed_entry: str=None) -> int:
	if compressed_entry is None:
		return path.stat().st_size

	return compressed_getsize(path, compressed_entry)

def read_file(path: pathlib.Path, compressed_entry: str=None, seek_to: int=0, amount: int=-1) -> bytes:
	if not compressed_entry:
		with open(path, 'rb') as f:
			f.seek(seek_to)
			if amount < 0:
				return f.read()

			return f.read(amount)

	data = compressed_get(path, compressed_entry)
	if seek_to:
		if amount > -1:
			return data[seek_to: seek_to + amount]
		return data[seek_to:]

	if amount > -1:
		return data[:amount]

	return data

def get_crc32(path: pathlib.Path, compressed_entry: str=None) -> int:
	if not compressed_entry:
		with open(path, 'rb') as f:
			crc = 0
			for chunk in iter(lambda: f.read(crc_chunk_size), b''):
				crc = zlib.crc32(chunk, crc)
			return crc & 0xffffffff

	return get_crc32_of_archive(path, compressed_entry)

def sanitize_name(s: Optional[str], supersafe: bool=False) -> str:
	#These must never be filenames or folder names!  Badbadbad!
	if not s:
		return 'Nothing'

	s = s.replace('/', '-')
	s = s.replace('\x00', ' ')

	if supersafe:
		#ext4 will be fine without this, FAT32 will not
		#So I guess other filesystems you wanna be safe too
		s = s.replace('"', '\'')
		s = s.replace('*', '-')
		s = s.replace(':', '-')
		s = s.replace('<', '-')
		s = s.replace('>', '-')
		s = s.replace('?', '-')
		s = s.replace('\\', '-')
		s = s.replace('|', '-')

		if len(s) > 200:
			s = s[:199] + '…'

		if s == 'NUL':
			return 'null'

	if s == '.':
		return 'dot'
	if s == '..':
		return 'dotdot'
	return s

def sanitize_path(path: pathlib.Path, supersafe: bool=False) -> pathlib.Path:
	#This isn't even used anywhere right now?
	parts = path.parts
	has_slash = False
	if parts[0] == '/':
		has_slash = True
		parts = parts[1:]

	sanitized_parts = [sanitize_name(path_part, supersafe) for path_part in parts]
	if has_slash:
		sanitized_parts = ['/'] + sanitized_parts
	return pathlib.Path(*sanitized_parts)

remove_brackety_things_for_filename = re.compile(r'[]([)]')
clean_for_filename = re.compile(r'[^A-Za-z0-9_]')
def make_filename(name: str) -> str:
	name = name.lower()
	name = remove_brackety_things_for_filename.sub('', name)
	name = clean_for_filename.sub('-', name)
	while name.startswith('-'):
		name = name[1:]
	if not name:
		name = 'blank'
	return name

def pick_new_filename(folder: pathlib.Path, display_name: str, extension: str) -> str:
	base_filename = make_filename(display_name)
	filename = base_filename + os.extsep + extension

	i = 2
	while folder.joinpath(filename).is_file():
		filename = base_filename + str(i) + os.extsep + extension
		i += 1
	return filename
