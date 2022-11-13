import importlib.resources
import json
import logging
import re
from collections.abc import Collection, Mapping, Sequence
from configparser import RawConfigParser
from typing import Any

from meowlauncher.exceptions import NotLaunchableException

try:
	import termcolor
	have_termcolor = True
except ImportError:
	have_termcolor = False

_find_brackets_at_end = re.compile(r'(?:\([^)]+?\)+|\[[^]]+?\]+)$')

def find_tags(name: str) -> tuple[str, Sequence[str]]:
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
	return find_tags(name)[1]

def remove_filename_tags(name: str) -> str:
	return find_tags(name)[0]

def starts_with_any(s: str, prefixes: Collection[str]) -> bool:
	'Allows s.startswith() with any iterable, not just tuple'
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

def pluralize(n: int, singular: str, plural: str|None=None) -> str:
	if not plural:
		plural = singular + 's'
	if n == 1:
		return singular
	return f'{n} {plural}'

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
	"""Like str.title or str.capitalize but actually bloody works how I expect for compound-words and contract'ns"""
	actual_word_parts = re.split(r"([\w']+)", s)
	return ''.join(part.capitalize() for part in actual_word_parts)

def remove_capital_article(s: str | None) -> str:
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
def load_dict(subpackage: str | None, resource: str) -> Mapping[int | str, str]:
	d = {}
	package = 'meowlauncher.data'
	if subpackage:
		package += '.' + subpackage
	for line in importlib.resources.read_text(package, resource + '.dict').splitlines():
		if line.startswith('#'):
			continue
		match = _dict_line_regex.match(line)
		if match:
			key: int | str = match['key']
			if not match['kquote']:
				key = int(key)
			d[key] = match['value']
	return d

def load_list(subpackage: str | None, resource: str) -> Sequence[str]:
	package = 'meowlauncher.data'
	if subpackage:
		package += '.' + subpackage
	return tuple(line for line in (line.split('#', 1)[0] for line in importlib.resources.read_text(package, resource + '.list').splitlines()) if line)

def load_json(subpackage: str | None, resource: str) -> Any:
	package = 'meowlauncher.data'
	if subpackage:
		package += '.' + subpackage
	with importlib.resources.open_binary(package, resource) as f: #It would be text, but I don't know if I wanna accidentally fuck around with encodings
		return json.load(f)

def _format_unit(n: int, suffix: str, base_unit: int=1000, singular_suffix: str|None=None) -> str:
	try:
		if n < base_unit:
			return f'{n:n} {singular_suffix if singular_suffix else suffix}'
	except TypeError:
		return str(n)
	#unit_suffixes = 'KMGTPE'
	unit_suffixes = 'KM'
	for i, unit_suffix in enumerate(unit_suffixes, 1):
		if n >= base_unit ** (i + 1):
			continue
		unit = base_unit ** i
		div, mod = divmod(n, unit)
		if not mod:
			return f'{div:n} {unit_suffix}{suffix}'
		#Would like to use :n here, but then it doesn't work for having only two decimal points (ideally I'd want one or two or none, but not precisely 2, and not removing decimals if there is one)
		return f'{n / unit:.2f}'.rstrip('0') + f' {unit_suffix}{suffix}'
	return f'{n / (base_unit ** len(unit_suffixes)):.2f}'.rstrip('0') + f' {unit_suffixes[-1]}{suffix}'
	
def format_byte_size(b: int, metric: bool=False) -> str:
	return _format_unit(b, 'B' if metric else 'iB', 1000 if metric else 1024, 'bytes')
	
def decode_bcd(i: int) -> int:
	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

class ColouredFormatter(logging.Formatter):
	"""Formats stuff as different colours with termcolor (if it can) depending on log level"""
	def format(self, record: logging.LogRecord) -> str:
		message = super().format(record)
		if have_termcolor:
			#TODO: Make this configurable lol whoops
			message = termcolor.colored(message, {logging.WARNING: 'yellow', logging.ERROR: 'red', logging.DEBUG: 'green'}.get(record.levelno))
		return message
		
class NotLaunchableExceptionFormatter(ColouredFormatter):
	"""Puts NotLaunchableException on one line as to read more naturally"""
	def format(self, record: logging.LogRecord) -> str:
		if record.exc_info:
			if isinstance(record.exc_info[1], NotLaunchableException):
				#Avoid super().format putting it on a new line
				record.msg += f' because {"".join(record.exc_info[1].args)}'
				record.exc_text = None
				record.exc_info = None
		return super().format(record)

class NoNonsenseConfigParser(RawConfigParser):
	"""No "interpolation", no using : as a delimiter, no lowercasing every option, that's all silly"""
	def __init__(self, defaults=None, allow_no_value=False, strict=True, empty_lines_in_values=True, comment_prefixes='#'):
		#Less of these weird options please, just parse the ini
		super().__init__(defaults=defaults, allow_no_value=allow_no_value, delimiters='=', comment_prefixes=comment_prefixes, strict=strict, empty_lines_in_values=empty_lines_in_values)

	def optionxform(self, optionstr: str) -> str:
		return optionstr

def sentence_case(s: str) -> str:
	words = s.lower().split(' ')
	return ' '.join([words[0].title(), ' '] + words[1:])
	