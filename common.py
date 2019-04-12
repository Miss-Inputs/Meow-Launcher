import re

find_filename_tags = re.compile(r'(\([^)]+?\)+|\[[^]]+?\]+)')
remove_extra_spaces = re.compile(r'\s(?=\s|$)')
def remove_filename_tags(name):
	if name.startswith(('(', '[')) and name.endswith((')', ']')):
		return name

	return remove_extra_spaces.sub('', find_filename_tags.sub('', name))

def starts_with_any(s, prefixes):
	#Allows s.startswith() with any iterable, not just tuple
	for prefix in prefixes:
		if s.startswith(prefix):
			return True
	return False

class NotAlphanumericException(Exception):
	pass

def convert_alphanumeric(byte_array):
	string = ''
	for byte in byte_array:
		char = chr(byte)
		if char not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
			raise NotAlphanumericException(char)
		string += char
	return string

junk_suffixes = re.compile(r'((?:(?:,)? (?:Inc|LLC|Kft)|(?:Co\.)?(?:,)? Ltd|Corp|GmbH)(?:\.)?|Co\.)$')

def pluralize(n, singular, plural=None):
	if not plural:
		plural = singular + 's'
	if n == 1:
		return singular
	return '%d %s' % (n, plural)

def convert_roman_numeral(s):
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
			elif unit_index < next_unit_index:
				raise ValueError('Numerals out of order: ' + c + ', ' + next_char)
		value += char_value
		i += 1
	return value

def is_roman_numeral(s):
	try:
		convert_roman_numeral(s)
		return True
	except ValueError:
		return False

def convert_roman_numerals_in_title(s):
	words = s.split(' ')
	converted_words = []
	for word in words:
		try:
			converted_words.append(str(convert_roman_numeral(word)))
		except ValueError:
			converted_words.append(word)
	return ' '.join(converted_words)

dont_capitalize_these = ['the', 'a', 'an', 'and', 'or', 'at', 'with', 'to', 'of', 'is']
def title_case_sentence_part(s, words_to_ignore_case=None):
	words = re.split(' ', s)
	if not words_to_ignore_case:
		words_to_ignore_case = []

	titled_words = []
	titled_words.append(words[0] if words[0] in words_to_ignore_case else words[0].title())
	words = words[1:]
	for word in words:
		if word in words_to_ignore_case or is_roman_numeral(word):
			titled_words.append(word)
		elif word.lower() in dont_capitalize_these:
			titled_words.append(word.lower())
		else:
			titled_words.append(word.title())
	return ' '.join(titled_words)

def title_case(s, words_to_ignore_case=None):
	sentence_parts = re.split(r'(\s+-\s+|:\s+)', s)
	titled_parts = [title_case_sentence_part(part, words_to_ignore_case) for part in sentence_parts]
	return ''.join(titled_parts)
