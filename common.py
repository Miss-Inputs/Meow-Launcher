import re

find_filename_tags = re.compile(r'(\([^)]+?\)+|\[[^]]+?\]+)')
def remove_filename_tags(name):
	stripped_name = find_filename_tags.sub('', name)
	if not stripped_name:
		#Handle weird hipster games that have (one thing in parentheses) as the title for no good reason
		stripped_name = name

	if stripped_name[-1] == ' ':
		stripped_name = stripped_name[:-1]

	return stripped_name

words_regex = re.compile(r'[\w()]+')
def normalize_name(name, care_about_spaces=True, normalize_words=True):
	name = convert_roman_numerals_in_title(name)
	name = name.lower()
	name = name.replace('3-d', '3d')
	name = name.replace('&', 'and')
	name = name.replace('é', 'e')
	name = name.replace(': ', ' - ')

	if normalize_words:
		return ('-' if care_about_spaces else '').join(words_regex.findall(name))
	return name
	
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
			if unit_index < next_unit_index:
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
		actual_word_match = re.match('[A-Za-z]+', word)
		if not actual_word_match:
			converted_words.append(word)
			continue
		span_start, span_end = actual_word_match.span()
		prefix_punctuation = word[:span_start]
		suffix_punctuation = word[span_end:]
		actual_word = actual_word_match[0]

		try:
			converted_words.append(prefix_punctuation + str(convert_roman_numeral(actual_word)) + suffix_punctuation)
		except ValueError:
			converted_words.append(word)
	return ' '.join(converted_words)

def title_word(s):
	#Like str.title or str.capitalize but actually bloody works how I expect for compound-words and contract'ns
	actual_word_parts = re.split(r"([\w']+)", s)
	return ''.join([part.capitalize() for part in actual_word_parts])

dont_capitalize_these = ['the', 'a', 'an', 'and', 'or', 'at', 'with', 'to', 'of', 'is']
def title_case_sentence_part(s, words_to_ignore_case=None):
	words = re.split(' ', s)
	if not words_to_ignore_case:
		words_to_ignore_case = []

	titled_words = []
	titled_words.append(words[0] if words[0] in words_to_ignore_case else title_word(words[0]))
	words = words[1:]
	for word in words:
		if word in words_to_ignore_case or is_roman_numeral(word):
			titled_words.append(word)
		elif word.lower() in dont_capitalize_these:
			titled_words.append(word.lower())
		else:
			titled_words.append(title_word(word))
	return ' '.join(titled_words)

def title_case(s, words_to_ignore_case=None):
	sentence_parts = re.split(r'(\s+-\s+|:\s+)', s)
	titled_parts = [title_case_sentence_part(part, words_to_ignore_case) for part in sentence_parts]
	return ''.join(titled_parts)

def remove_capital_article(s):
	if not s:
		return ''

	words = s.split(' ')
	new_words = [words[0]]
	for word in words[1:]:
		if word.lower() in ('the', 'a'):
			new_words.append(word.lower())
		else:
			new_words.append(word)
	return ' '.join(new_words)

def clean_string(s):
	return ''.join([c for c in s if c.isprintable()])
