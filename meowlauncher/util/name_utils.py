import re
from collections.abc import Iterable
from typing import Optional

from meowlauncher.config.main_config import main_config
from meowlauncher.data.name_cleanup.capitalized_words_in_names import \
    capitalized_words

from .utils import convert_roman_numeral, is_roman_numeral, title_word

chapter_matcher = re.compile(r'\b(?:Chapter|Vol|Volume|Episode|Part|Version)\b(?:\.)?', flags=re.RegexFlag.IGNORECASE)

fluff_editions = {'GOTY', 'Game of the Year', 'Definitive', 'Enhanced', 'Special', 'Ultimate', 'Premium', 'Gold', 'Extended', 'Super Turbo Championship', 'Digital', 'Megaton', 'Deluxe', 'Masterpiece'}
demo_suffixes = {'Demo', 'Playable Teaser'}
name_suffixes = demo_suffixes.union({'Beta', 'GOTY', "Director's Cut", 'Unstable', 'Complete', 'Complete Collection', "Developer's Cut"}).union({e + ' Edition' for e in fluff_editions})
name_suffix_matcher = re.compile(r'(?: | - |: )?(?:The )?(' + '|'.join(name_suffixes) + ')$', re.RegexFlag.IGNORECASE)
def normalize_name_case(name: str, name_to_test_for_upper: Optional[str]=None) -> str:
	if not name_to_test_for_upper:
		name_to_test_for_upper = name

	if main_config.normalize_name_case == 1:
		if name_to_test_for_upper.isupper():
			return title_case(name, words_to_ignore_case=capitalized_words)
		return name
	if main_config.normalize_name_case == 2:
		if name_to_test_for_upper.isupper():
			return title_case(name, words_to_ignore_case=capitalized_words)

		#Assume minimum word length of 4 to avoid acronyms, although those should be in capitalized_words I guess
		return re.sub(r"[\w'-]{4,}", lambda match: title_case(match[0], words_to_ignore_case=capitalized_words) if match[0].isupper() else match[0], name)
	if main_config.normalize_name_case == 3:
		return title_case(name, words_to_ignore_case=capitalized_words)
	
	return name

why = re.compile(r' -(?=\w)') #This bothers me
def fix_name(name: str) -> str:
	name = name.replace('™', '')
	name = name.replace('®', '')
	name = name.replace(' : ', ': ') #Oi mate what kinda punctuation is this
	name = name.replace('[diary]', 'diary') #Stop that
	name = name.replace('(VI)', 'VI') #Why is Tomb Raider: The Angel of Darkness like this
	name = why.sub(' - ', name)

	if name.startswith('ARCADE GAME SERIES: '):
		#This is slightly subjective as to whether or not one should do this, but I believe it should
		name = name.removeprefix('ARCADE GAME SERIES: ') + ' (ARCADE GAME SERIES)'

	name_to_test_for_upper = chapter_matcher.sub('', name)
	name_to_test_for_upper = name_suffix_matcher.sub('', name_to_test_for_upper)
	name = normalize_name_case(name, name_to_test_for_upper)
		
	#Hmm... this is primarily so series_detect and disambiguate work well, it may be worthwhile putting them back afterwards (put them in some kind of field similar to Filename-Tags but disambiguate always adds them in); depending on how important it is to have "GOTY" or "Definitive Edition" etc in the name if not ambiguous
	name = name_suffix_matcher.sub(r' (\1)', name)
	return name

tool_names = ('settings', 'setup', 'config', 'dedicated server', 'editor')
def is_probably_related_tool(name: Optional[str]) -> bool:
	if not name:
		return False
	lower = name.lower()
	return any(tool_name in lower for tool_name in tool_names)

mode_names = ('safe mode', 'play windowed', 'launch fullscreen', 'launch windowed')
def is_probably_different_mode(name: Optional[str]) -> bool: 
	if not name:
		return False
	lower = name.lower()
	return any(mode_name in lower for mode_name in mode_names)

document_names = ('faq', 'manual', 'map of avernum', 'reference card')
def is_probably_documentation(name: Optional[str]) -> bool:
	if not name:
		return False
	lower = name.lower()
	return any(document_name in lower for document_name in document_names)

def convert_roman_numerals_in_title(s: str) -> str:
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

words_regex = re.compile(r'[\w()]+')
apostrophes_at_word_boundary_regex = re.compile(r"\B'|'\B")
def normalize_name(name: str, care_about_spaces=True, normalize_words=True, care_about_numerals=False) -> str:
	if care_about_numerals:
		name = convert_roman_numerals_in_title(name)
	name = name.lower()
	name = name.replace('3-d', '3d')
	name = name.replace('&', 'and')
	name = name.replace('é', 'e')
	name = name.replace(': ', ' - ')
	name = apostrophes_at_word_boundary_regex.sub('', name)

	if normalize_words:
		return ('-' if care_about_spaces else '').join(words_regex.findall(name))
	return name

dont_capitalize_these = {'the', 'a', 'an', 'and', 'or', 'at', 'with', 'to', 'of', 'is'}
def _title_case_sentence_part(s: str, words_to_ignore_case: Optional[Iterable[str]]=None) -> str:
	words = re.split(' ', s)
	if not words_to_ignore_case:
		words_to_ignore_case = set()

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

def title_case(s: str, words_to_ignore_case: Optional[Iterable[str]]=None) -> str:
	sentence_parts = re.split(r'(\s+-\s+|:\s+)', s)
	return ''.join(_title_case_sentence_part(part, words_to_ignore_case) for part in sentence_parts)
