import os
import pathlib
from typing import Optional


def ensure_exist(path: pathlib.Path):
	path.parent.mkdir(exist_ok=True, parents=True)
	path.touch()

def read_file(path: pathlib.Path, seek_to: int=0, amount: int=-1) -> bytes:
	with path.open('rb') as f:
		f.seek(seek_to)
		if amount < 0:
			return f.read()

		return f.read(amount)

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

def pick_new_path(folder: pathlib.Path, base_filename: str, extension: str) -> pathlib.Path:
	new_path = folder.joinpath(base_filename + os.extsep + extension)

	i = 2
	while new_path.is_file():
		new_path = new_path.with_stem(base_filename + str(i))
		i += 1
	return new_path
