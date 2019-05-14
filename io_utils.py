import os
import pathlib
import zlib

import archives

crc_chunk_size = 64 * 1024 * 1024

def ensure_exist(path):
	pathlib.Path(os.path.dirname(path)).mkdir(exist_ok=True, parents=True)
	pathlib.Path(path).touch()

def get_real_size(path, compressed_entry=None):
	if compressed_entry is None:
		return os.path.getsize(path)

	return archives.compressed_getsize(path, compressed_entry)

def read_file(path, compressed_entry=None, seek_to=0, amount=-1):
	if not compressed_entry:
		with open(path, 'rb') as f:
			f.seek(seek_to)
			if amount < 0:
				return f.read()

			return f.read(amount)

	data = archives.compressed_get(path, compressed_entry)
	if seek_to:
		if amount > -1:
			return data[seek_to: seek_to + amount]
		return data[seek_to:]

	if amount > -1:
		return data[:amount]

	return data

def get_crc32(path, compressed_entry=None):
	if not compressed_entry:
		with open(path, 'rb') as f:
			crc = 0
			for chunk in iter(lambda: f.read(crc_chunk_size), b''):
				crc = zlib.crc32(chunk, crc)
			return crc & 0xffffffff

	return archives.get_crc32_of_archive(path, compressed_entry)

def sanitize_name(s, supersafe=False):
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

def sanitize_path(path, supersafe=False):
	parts = pathlib.Path(path).parts
	if not parts:
		return None #hmm
	has_slash = False
	if parts[0] == '/':
		has_slash = True
		parts = parts[1:]

	sanitized_parts = [sanitize_name(path_part, supersafe) for path_part in parts]
	if has_slash:
		sanitized_parts = ['/'] + sanitized_parts
	return os.path.join(*sanitized_parts)
