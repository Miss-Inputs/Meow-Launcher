import pathlib
import re


def ensure_exist(path: pathlib.Path) -> None:
	"""Makes sure @path is a file that exists (by touching it if not), and that its parent folders exist"""
	path.parent.mkdir(exist_ok=True, parents=True)
	path.touch()

def read_file(path: pathlib.Path, seek_to: int=0, amount: int=-1) -> bytes:
	"""Reads a certain amount from an ordinary file from a certain position… why is this here?"""
	with path.open('rb') as f:
		f.seek(seek_to)
		if amount < 0:
			return f.read()

		return f.read(amount)

def sanitize_name(s: str | None, safe_for_fat32: bool=False, no_janky_chars: bool=True) -> str:
	"""Get rid of any characters that should never be a folder/filename, or would be a bad idea to have in a filename, or may cause more trouble than it's worth in a filename"""
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
		s = s.replace(': ', ' - ')
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
		while s.startswith('.'):
			s = s[1:]
	
	if not s:
		return 'blank'

	return s

def ensure_unique_path(path: pathlib.Path) -> pathlib.Path:
	"""BEEP BOOP BEEP BOOP yes there is probably an alarm sounding for anyone familiar with the words "race condition", anyway this "ensures" that a filename is unique by incrementing a number at the end if it is not"""
	new_path = path

	i = 1
	while new_path.is_file():
		existing_stem = new_path.stem
		numbers_match = re.search(r'(\d+)$', existing_stem)
		#If we already have numbers at the end of the filename, count from there
		if numbers_match:
			i = int(numbers_match[1])
			existing_stem = existing_stem[:numbers_match.start()]
		i += 1 #Effectively starts appending numbers from 2
		new_path = new_path.with_stem(existing_stem + str(i))
	return new_path
