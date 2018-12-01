import os
import pathlib

import archives

def ensure_exist(path):
	pathlib.Path(os.path.dirname(path)).mkdir(exist_ok=True, parents=True)
	pathlib.Path(path).touch()

def get_real_size(path, compressed_entry=None):
	if compressed_entry is None:
		return os.path.getsize(path)

	return archives.compressed_getsize(path, compressed_entry)

def read_file(path, compressed_entry=None, seek_to=0, amount=-1):
	if compressed_entry is None:
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

		if s == 'NUL':
			return 'null'

	if s == '.':
		return 'dot'
	if s == '..':
		return 'dotdot'
	return s

def sanitize_path(path, supersafe=False):
	#TODO Sanitize folder names too
	folder, name = os.path.split(path)
	sanitized = sanitize_name(name, supersafe)
	return os.path.join(folder, sanitized)
