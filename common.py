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
is_roman_numeral = re.compile(r'[IVXL]+') #Hmm would it make more sense to just generate a static list of the first 50 (or so) Roman numerals
def title_case_sentence_part(s, words_to_ignore_case=None):
	words = re.split(' ', s)
	if not words_to_ignore_case:
		words_to_ignore_case = []

	titled_words = []
	if words[0].lower() in dont_capitalize_these:
		titled_words.append(words[0].lower())
		words = words[1:]
	for word in words:
		if word in words_to_ignore_case or is_roman_numeral.fullmatch(word):
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


franchise_matcher = re.compile(r'(?P<Franchise>.+?)\b\s*(?:\d{1,3}|[IVX]+?)\b')
chapter_matcher = re.compile(r'\b(?:Chapter|Vol|Volume|Episode)(?:\.)?', flags=re.RegexFlag.IGNORECASE)

def find_franchise_from_game_name(name):
	franchise_overrides = {
		#TODO: Put this in data folder in separate thing, probably
		#These names are too clever for my regex to work properly so I'll just not use the regex on them
		'Left 4 Dead 2': 'Left 4 Dead',
		'Hyperdimension Neptunia Re;Birth3 V Generation': 'Hyperdimension Neptunia', #The other games don't have their franchise detected, though
		'I Have No Mouth, and I Must Scream': None,
		'TIS-100': None,
		'Tis-100': None, #In case normalize_name_case is on... yeah I need to fix that I guess
		'Transmissions: Element 120': None,
	}
	if name in franchise_overrides:
		return franchise_overrides[name]
	else:
		franchise_match = franchise_matcher.match(name)
		if franchise_match:
			franchise_name = franchise_match['Franchise']
			return chapter_matcher.sub('', franchise_name)
	return None
