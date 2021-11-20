import os
import pathlib
import re
from typing import Optional

from .archives import compressed_get

def ensure_exist(path: pathlib.Path):
	path.parent.mkdir(exist_ok=True, parents=True)
	path.touch()

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
