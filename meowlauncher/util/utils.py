import importlib.resources
import logging
import re
from collections.abc import Mapping, Sequence
from configparser import RawConfigParser
from importlib.abc import Traversable

from meowlauncher.exceptions import NotLaunchableError

try:
	import termcolor

	have_termcolor = True
except ImportError:
	have_termcolor = False

_find_brackets_at_end = re.compile(r'(?:\([^)]+?\)+|\[[^]]+?\]+)$')


def find_tags(name: str) -> tuple[str, Sequence[str]]:
	"""(name without tags, tags)
	Where did I come up with the word "tags" anyway"""
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
			# Handle the whole name being (all in parentheses)
			return name, ()
		if result[-1] == ' ':
			result = result[:-1]
	return result, tags[::-1]


def find_filename_tags_at_end(name: str) -> Sequence[str]:
	return find_tags(name)[1]


def remove_filename_tags(name: str) -> str:
	return find_tags(name)[0]


class NotAlphanumericError(Exception):
	"""Thrown from convert_alphanumeric"""


def convert_alphanumeric(byte_array: bytes) -> str:
	"""Decodes byte_array as though it was UTF-8 or ASCII, but enforces it is alphanumeric
	Questionable if this is useful as opposed to just decoding normally but checking .isalnum() afterwards
	:raises NotAlphanumericException: If a character is not alphanumeric"""
	string = ''
	for byte in byte_array:
		char = chr(byte)
		if not char.isalnum():
			raise NotAlphanumericError(char)
		string += char
	return string


junk_suffixes = re.compile(
	r'((?:(?:,)? (?:Inc|LLC|Kft)|(?:Co\.)?(?:,)? Ltd|Corp|GmbH)(?:\.)?|Co\.)$'
)


def pluralize(n: int, singular: str, plural: str | None = None) -> str:
	"""Naive pluralization that just makes sure you don't have 1 Somethings, does not take into account wanky edge cases in the English language"""
	if n == 1:
		return singular
	if not plural:
		plural = singular + 's'
	return f'{n} {plural}'


def convert_roman_numeral(s: str) -> int:
	"""If s is a Roman numeral, returns the integer value
	I guess it's used for normalizing titles of sequels for comparison and such
	:raises ValueError: If s is not a Roman numeral"""
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
			if next_unit_index == unit_index + 1 or (
				int(next_unit_index) == unit_index and next_unit_index != unit_index
			):
				# Subtractive notation thingo
				# IV and IX are valid, but VX is not valid, probably
				value += next_char_value - char_value
				i += 2
				continue
			if unit_index < next_unit_index:
				raise ValueError('Numerals out of order: ' + c + ', ' + next_char)
		value += char_value
		i += 1
	return value


def is_roman_numeral(s: str) -> bool:
	"""Detects if s is convertible using convert_roman_numeral"""
	try:
		convert_roman_numeral(s)
	except ValueError:
		return False
	else:
		return True


def title_word(s: str) -> str:
	"""Like str.title but actually bloody works how I expect for compound-words and contract'ns"""
	actual_word_parts = re.split(r"([\w']+)", s)
	return ''.join(part.capitalize() for part in actual_word_parts)


def remove_capital_article(s: str | None) -> str:
	"""Returns copy of s with words such as "the" or "a" at the beginning removed"""
	if not s:
		return ''

	words = s.split(' ')
	new_words = [words[0]]
	for word in words[1:]:
		lower = word.lower()
		new_words.append(lower if lower in {'the', 'a'} else word)
	return ' '.join(new_words)


def clean_string(s: str, *, preserve_newlines: bool = False) -> str:
	"""Returns a copy of s with all the unprintable characters removed"""
	return ''.join(
		c for c in s if c.isprintable() or c == '\t' or (c in {'\n', '\r'} and preserve_newlines)
	)


def byteswap(b: bytes) -> bytes:
	"""Returns copy of b with every pair of bytes swapped"""
	# Does it really make sense to byteswap an array with odd length? I guess it happens sometimes
	bb = b if len(b) % 2 == 0 else b[:-1]
	last_byte = b[-1]
	byte_array = bytearray(bb)
	byte_array[0::2] = bb[1::2]
	byte_array[1::2] = bb[0::2]
	if len(b) % 2 != 0:
		byte_array.append(last_byte)
	return bytes(byte_array)


def get_resource(subpackage: str | None, name: str) -> Traversable:
	"""Gets a non-Python file from the data package"""
	package = 'meowlauncher.data'
	if subpackage:
		package = f'{package}.{subpackage}'
	return next(file for file in importlib.resources.files(package).iterdir() if file.name == name)


_dict_line_regex = re.compile(
	r'(?P<kquote>\'|\"|)(?P<key>.+?)(?P=kquote):\s*(?P<vquote>\'|\")(?P<value>.+?)(?P=vquote),?(?:\s*#.+)?$'
)


def load_dict(subpackage: str | None, resource: str) -> Mapping[int | str, str]:
	d = {}
	for line in get_resource(subpackage, resource + '.dict').read_text().splitlines():
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
	return tuple(
		line
		for line in (
			line.split('#', 1)[0]
			for line in get_resource(subpackage, resource + '.list').read_text().splitlines()
		)
		if line
	)


def format_unit(
	n: float, suffix: str, base_unit: int = 1000, singular_suffix: str | None = None
) -> str:
	try:
		if n < base_unit:
			return f'{n:n} {singular_suffix if singular_suffix else suffix}'
	except TypeError:
		return str(n)
	unit_suffixes = 'KMGTPE'
	for i, unit_suffix in enumerate(unit_suffixes, 1):
		if n >= base_unit ** (i + 1):
			continue
		unit = base_unit**i
		div, mod = divmod(n, unit)
		if not mod:
			return f'{div:n} {unit_suffix}{suffix}'
		# Would like to use :n here, but then it doesn't work for having only two decimal points (ideally I'd want one or two or none, but not precisely 2, and not removing decimals if there is one)
		return f'{n / unit:.2f}'.rstrip('0') + f' {unit_suffix}{suffix}'
	return (
		f'{n / (base_unit ** len(unit_suffixes)):.2f}'.rstrip('0') + f' {unit_suffixes[-1]}{suffix}'
	)


def format_byte_size(b: int, *, metric: bool = False) -> str:
	"""Formats an int representing an amount of bytes as human-readable (actually understands the difference between SI prefixes and IEC binary prefixes, unlike e.g. bad file managers for bad operating systems)
	Every library and its dog has something akin to this, so you may want to leverage pydantic.ByteSize instead if you can"""
	return format_unit(b, 'B' if metric else 'iB', 1000 if metric else 1024, 'bytes')


def decode_bcd(i: int) -> int:
	"""Decodes a binary-coded decimal, which is used inside video games sometimes (mostly older ones before technology could just store larger numbers like a normal person)"""
	hi = (i & 0xF0) >> 4
	lo = i & 0x0F
	return (hi * 10) + lo


class ColouredFormatter(logging.Formatter):
	"""Formats stuff as different colours with termcolor (if it can) depending on log level"""

	default_mapping: Mapping[int, str] = {
		logging.WARNING: 'yellow',
		logging.ERROR: 'red',
		logging.DEBUG: 'green',
	}

	def __init__(
		self, fmt: str | None = None, colour_mapping: Mapping[int, str] | None = None
	) -> None:
		""":param fmt: Logging format string, as per logging.Formatter
		:param colour_mapping: Mapping of logging levels to termcolor values"""
		# Yeah I'm taking out a lot of those default logging.Formatter constructor arguments, sue me
		self.colour_mapping = colour_mapping if colour_mapping is not None else self.default_mapping
		super().__init__(fmt)

	def format(self, record: logging.LogRecord) -> str:
		message = super().format(record)
		if have_termcolor:
			message = termcolor.colored(message, self.colour_mapping.get(record.levelno))
		return message


class NotLaunchableExceptionFormatter(ColouredFormatter):
	"""Puts NotLaunchableException on one line as to read more naturally"""
	#TODO: Have something in main config to change colour mapping

	def format(self, record: logging.LogRecord) -> str:
		if record.exc_info and isinstance(record.exc_info[1], NotLaunchableError):
			# Avoid super().format putting it on a new line
			record.msg += f' because {"".join(record.exc_info[1].args)}'
			record.exc_text = None
			record.exc_info = None
		return super().format(record)


class NoNonsenseConfigParser(RawConfigParser):
	"""No "interpolation", no using : as a delimiter, no lowercasing every option, that's all silly"""

	def __init__(
		self,
		defaults=None,
		*,
		allow_no_value=False,
		strict=True,
		empty_lines_in_values=True,
		comment_prefixes='#',
	):
		# Less of these weird options please, just parse the ini
		super().__init__(
			defaults=defaults,
			allow_no_value=allow_no_value,
			delimiters='=',
			comment_prefixes=comment_prefixes,
			strict=strict,
			empty_lines_in_values=empty_lines_in_values,
		)

	def optionxform(self, optionstr: str) -> str:
		#If you just create a RawConfigParser and then set configparser.optionxform = str, type checkers and linters will grouch at you, so we do it their way by making a whole ass class
		return optionstr
