import importlib.resources
import json
import math
import re
from collections.abc import Collection, Sequence, Mapping
from typing import Optional, Union

_find_brackets_at_end = re.compile(r'(?:\([^)]+?\)+|\[[^]]+?\]+)$')

def _find_tags(name: str) -> tuple[str, Sequence[str]]:
	#Where did I come up with the word "tags" anyway
	result = name
	tags = []
	while True:
		search = _find_brackets_at_end.search(result)
		if not search:
			break
		tags.append(search[0])
		start = search.span()[0]
		result = result[:start]
		if not result:
			#Handle the whole name being (all in parentheses)
			return name, ()
		if result[-1] == ' ':
			result = result[:-1]
	return result, tags[::-1]

def find_filename_tags_at_end(name: str) -> Sequence[str]:
	return _find_tags(name)[1]

def remove_filename_tags(name: str) -> str:
	return _find_tags(name)[0]

def starts_with_any(s: str, prefixes: Collection[str]) -> bool:
	#Allows s.startswith() with any iterable, not just tuple
	return any(s.startswith(prefix) for prefix in prefixes)

class NotAlphanumericException(Exception):
	pass

def convert_alphanumeric(byte_array: bytes) -> str:
	string = ''
	for byte in byte_array:
		char = chr(byte)
		if char not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
			raise NotAlphanumericException(char)
		string += char
	return string

junk_suffixes = re.compile(r'((?:(?:,)? (?:Inc|LLC|Kft)|(?:Co\.)?(?:,)? Ltd|Corp|GmbH)(?:\.)?|Co\.)$')

def pluralize(n: int, singular: str, plural: str=None) -> str:
	if not plural:
		plural = singular + 's'
	if n == 1:
		return singular
	return '%d %s' % (n, plural)

def convert_roman_numeral(s: str) -> int:
	s = s.upper()

	units = {
		'M': (1000, 4),
		'D': (500, 3.5),
		'C': (100, 3),
		'L': (50, 2.5),
		'X': (10, 2),
		'V': (5, 1.5),
		'I': (1, 1),
	}
	value = 0
	i = 0
	while i < len(s):
		c = s[i]
		if c not in units:
			raise ValueError('Invalid char: ' + c)
		char_value, unit_index = units[c]

		if i + 1 < len(s):
			next_char = s[i + 1]
			if next_char not in units:
				raise ValueError('Invalid char: ' + next_char)
			next_char_value, next_unit_index = units[next_char]
			if next_unit_index == unit_index + 1 or (int(next_unit_index) == unit_index and next_unit_index != unit_index):
				#Subtractive notation thingo
				#IV and IX are valid, but VX is not valid, probably
				value += (next_char_value - char_value)
				i += 2
				continue
			if unit_index < next_unit_index:
				raise ValueError('Numerals out of order: ' + c + ', ' + next_char)
		value += char_value
		i += 1
	return value

def is_roman_numeral(s: str) -> bool:
	try:
		convert_roman_numeral(s)
		return True
	except ValueError:
		return False

def title_word(s: str) -> str:
	#Like str.title or str.capitalize but actually bloody works how I expect for compound-words and contract'ns
	actual_word_parts = re.split(r"([\w']+)", s)
	return ''.join(part.capitalize() for part in actual_word_parts)

def remove_capital_article(s: Optional[str]) -> str:
	if not s:
		return ''

	words = s.split(' ')
	new_words = [words[0]]
	for word in words[1:]:
		lower = word.lower()
		new_words.append(lower if lower in {'the', 'a'} else word)
	return ' '.join(new_words)

def clean_string(s: str, preserve_newlines: bool=False) -> str:
	return ''.join(c for c in s if c.isprintable() or c == '\t' or (c in {'\n', '\r'} and preserve_newlines))

def byteswap(b: bytes) -> bytes:
	bb = b if len(b) % 2 == 0 else b[:-1]
	last_byte = b[-1]
	byte_array = bytearray(bb)
	byte_array[0::2] = bb[1::2]
	byte_array[1::2] = bb[0::2]
	if len(b) % 2 != 0:
		byte_array.append(last_byte)
	return bytes(byte_array)

_dict_line_regex = re.compile(r'(?P<kquote>\'|\"|)(?P<key>.+?)(?P=kquote):\s*(?P<vquote>\'|\")(?P<value>.+?)(?P=vquote),?(?:\s*#.+)?$')
def load_dict(subpackage: Optional[str], resource: str) -> Mapping[Union[int, str], str]:
	d = {}
	package = 'meowlauncher.data'
	if subpackage:
		package += '.' + subpackage
	for line in importlib.resources.read_text(package, resource + '.dict').splitlines():
		if line.startswith('#'):
			continue
		match = _dict_line_regex.match(line)
		if match:
			key: Union[int, str] = match['key']
			if not match['kquote']:
				key = int(key)
			d[key] = match['value']
	return d

def load_list(subpackage: Optional[str], resource: str) -> Sequence[str]:
	package = 'meowlauncher.data'
	if subpackage:
		package += '.' + subpackage
	return tuple(line for line in (line.split('#', 1)[0] for line in importlib.resources.read_text(package, resource + '.list').splitlines()) if line)

def load_json(subpackage: Optional[str], resource: str) -> Mapping:
	package = 'meowlauncher.data'
	if subpackage:
		package += '.' + subpackage
	with importlib.resources.open_binary(package, resource) as f: #It would be text, but I don't know if I wanna accidentally fuck around with encodings
		return json.load(f)

def _format_unit(n: int, suffix: str, base_unit: int=1000, singular_suffix: str=None) -> str:
	try:
		if n < base_unit:
			return '{0} {1}'.format(n, singular_suffix if singular_suffix else suffix)
	except TypeError:
		return str(n)
	
	exp = int(math.log(n, base_unit))
	unit_suffix = 'KMGTPE'[exp - 1]
	d = round(n / math.pow(base_unit, exp), 2)
	return '{0} {1}{2}'.format(d, unit_suffix, suffix)

def format_byte_size(b: int, metric: bool=True) -> str:
	return _format_unit(b, 'B' if metric else 'iB', 1000 if metric else 1024, 'bytes')
	
def decode_bcd(i: int) -> int:
	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo
