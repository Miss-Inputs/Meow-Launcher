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


franchise_matcher = re.compile(r'(?P<Franchise>.+?)\b\s+#?(?P<Number>\d{1,3}|[IVX]+?)\b(?:\s|$)')
chapter_matcher = re.compile(r'\b(?:Chapter|Vol|Volume|Episode|Part)\b(?:\.)?', flags=re.RegexFlag.IGNORECASE)
#"Phase" might also be a chapter marker thing?
subtitle_splitter = re.compile(r'\s*(?:\s+-\s+|:\s+|\/)')
#"&" and "and" and "+" might also go in here?
blah_in_1_matcher = re.compile(r'.+\s+in\s+1')
def find_franchise_from_game_name(name):
	franchise_overrides = {
		#TODO: Put this in data folder in separate thing, probably
		#These names are too clever for my regex to work properly so I'll just not use the regex on them
		'Killer 7': None,
	}
	if name in franchise_overrides and False:
		return franchise_overrides[name]
	else:
		#TODO: Because we're doing fullmatch, should take out "Complete Edition" or "GOTY Edition" or "Demo" or whatever at the end, particularly affects Steam stuff that doesn't have things in brackets

		name_chunks = subtitle_splitter.split(name, maxsplit=1)
		name_chunks = [blah_in_1_matcher.sub('', chunk) for chunk in name_chunks]
		name_chunks = [chunk for chunk in name_chunks if chunk]
		if not name_chunks:
			return None
		name_chunk = name_chunks[0]
		franchise_match = franchise_matcher.fullmatch(name_chunk)
		if franchise_match:
			franchise_name = franchise_match['Franchise']
			number = franchise_match['Number']
			try:
				if int(number) > 50:
					#Assume that a number over 50 is probably not referring to the 50th or higher entry in the series, but is probably just any old number that means something. I should convert Roman numerals too
					return None
			except ValueError:
				pass
			if franchise_match['Number'] in ('XXX', '007'):
				#These generally aren't entries in a series, and are just there at the end
				return None
			return chapter_matcher.sub('', franchise_name).rstrip()
		#if len(name_chunks) > 1:
		#	return name_chunks[0]
		#This looks like a good idea, and that works for detecting the franchise for a lot of stuff that doesn't have numbers because it's the first game in a series or it's just too cool for that. But then sometimes it doesn't work. Hmm. Maybe I want to only set it if that franchise/series already exists and is valid?
	return None
