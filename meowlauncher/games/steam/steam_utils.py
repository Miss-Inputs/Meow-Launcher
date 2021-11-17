from collections.abc import Mapping, Sequence
from typing import Any

from meowlauncher.config.main_config import main_config
from meowlauncher.data.name_cleanup.steam_developer_overrides import \
    developer_overrides
from meowlauncher.util.region_info import (Language,
                                           get_language_by_english_name,
                                           languages_by_english_name)
from meowlauncher.util.utils import junk_suffixes


def translate_language_list(languages: Mapping[bytes, Any]) -> Sequence[Language]:
	langs = []
	for language_name_bytes, _ in languages.items():
		#value is an Integer object but it's always 1, I dunno what the 0 means, because it's like, if the language isn't there, it just wouldn't be in the dang list anyway
		language_name = language_name_bytes.decode('utf-8', errors='backslashreplace')
		if language_name == 'koreana': #I don't know what the a at the end is for, but Steam does that
			langs.append(languages_by_english_name['Korean'])
		elif language_name == 'schinese': #Simplified Chinese
			langs.append(languages_by_english_name['Chinese'])
		elif language_name == 'tchinese':
			langs.append(languages_by_english_name['Traditional Chinese'])
		elif language_name == 'brazilian':
			langs.append(languages_by_english_name['Brazilian Portugese'])
		elif language_name == 'latam':
			langs.append(languages_by_english_name['Latin American Spanish'])
		else:
			language = get_language_by_english_name(language_name, case_insensitive=True)
			if language:
				langs.append(language)
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