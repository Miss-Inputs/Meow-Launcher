from collections.abc import Collection, Mapping
from typing import Any

from meowlauncher.config.main_config import main_config
from meowlauncher.data.name_cleanup.steam_developer_overrides import \
    developer_overrides
from meowlauncher.util.region_info import (Language,
                                           get_language_by_english_name,
                                           languages_by_english_name)
from meowlauncher.util.utils import junk_suffixes, load_dict

store_categories = load_dict(None, 'steam_store_categories')
genre_ids = load_dict(None, 'steam_genre_ids')

def format_genre(genre_id: str) -> str:
	return genre_ids.get(genre_id, f'unknown {genre_id}')

def translate_language_list(languages: Mapping[bytes, Any]) -> Collection[Language]:
	langs = set()
	for language_name_bytes in languages.keys():
		#value is an Integer object but it's always 1, I dunno what the 0 means, because it's like, if the language isn't there, it just wouldn't be in the dang list anyway
		language_name = language_name_bytes.decode('utf-8', errors='backslashreplace')
		if language_name == 'koreana': #I don't know what the a at the end is for, but Steam does that
			langs.add(languages_by_english_name['Korean'])
		elif language_name == 'schinese': #Simplified Chinese
			langs.add(languages_by_english_name['Chinese'])
		elif language_name == 'tchinese':
			langs.add(languages_by_english_name['Traditional Chinese'])
		elif language_name == 'brazilian':
			langs.add(languages_by_english_name['Brazilian Portugese'])
		elif language_name == 'latam':
			langs.add(languages_by_english_name['Latin American Spanish'])
		else:
			language = get_language_by_english_name(language_name, case_insensitive=True)
			if language:
				langs.add(language)
			elif main_config.debug:
				print('Unknown language:', language_name)

	return langs

def normalize_developer(dev: str) -> str:
	while junk_suffixes.search(dev):
		dev = junk_suffixes.sub('', dev)
	dev = dev.strip()

	if dev in developer_overrides:
		return developer_overrides[dev]
	return dev
