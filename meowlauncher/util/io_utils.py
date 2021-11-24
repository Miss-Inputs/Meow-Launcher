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

def sanitize_name(s: Optional[str], safe_for_fat32: bool=False, no_janky_chars: bool=True) -> str:
	#These must never be filenames or folder names!  Badbadbad!
	if not s:
		return 'Nothing'

	s = s.replace('/', '-')
	s = s.replace('\x00', ' ')
	s = s.replace('\n', ' ')
	s = s.replace('\t', ' ')
	s = s.replace('\r', ' ')

	if no_janky_chars:
		#Get rid of chars that are potentially evil with various kinds of shell syntax or various kinds of filesystems, or other things that have special meanings
		s = s.replace('#', '-')
		s = s.replace('=', '_')
		s = s.replace('&', 'and')
		# ! ~ $ ; { } could also potentially be evil against sloppily written shell scripts/shells/etc (although not allowing these is pretty sloppy already, it's just also common for that to not work)

	if safe_for_fat32 or no_janky_chars:
		s = s.replace('"', '\'') #I guess no_quotes_at_all could be an option, but in many cases you do want that
		s = s.replace('*', '_')
		s = s.replace(':', '-')
		s = s.replace('<', '_')
		s = s.replace('>', '_')
		s = s.replace('?', '')
		s = s.replace('\\', '_')
		s = s.replace('|', '_')

	if safe_for_fat32:
		#ext4 will be fine without this, FAT32 will not
		#So I guess other filesystems you wanna be safe too
		if len(s) > 200:
			s = s[:199] + '…'

		if s == 'NUL':
			return 'null'

	if s == '.':
		return 'dot'
	if s == '..':
		return 'dotdot'

	if no_janky_chars:
		#Having - at the beginning can be weird
		while s.startswith('-'):
			s = s[1:]
	
	if not s:
		return 'blank'

	return s

def pick_new_path(folder: pathlib.Path, base_filename: str, extension: str) -> pathlib.Path:
	new_path = folder.joinpath(base_filename + os.extsep + extension)

	i = 2
	while new_path.is_file():
		new_path = new_path.with_stem(base_filename + str(i))
		i += 1
	return new_path
