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

dont_capitalize_these = ['the', 'a', 'an', 'and', 'or', 'at', 'with', 'to', 'of', 'is']
is_roman_numeral = re.compile(r'[IVXL]+') #Hmm
def title_case_sentence_part(s, words_to_ignore_case=None):
	words = re.split(' ', s)
	if not words_to_ignore_case:
		words_to_ignore_case = []

	titled_words = []
	if words[0].lower() in dont_capitalize_these:
		titled_words.append(words[0].lower())
		words = words[1:]
	for word in words:
		if word in words_to_ignore_case or is_roman_numeral.match(word):
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
