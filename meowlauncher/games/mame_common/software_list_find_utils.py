import itertools
import os
from collections.abc import Collection, MutableSet, Sequence
from pathlib import Path
from typing import Any, Optional

from meowlauncher.util.name_utils import normalize_name
from meowlauncher.util.utils import (find_filename_tags_at_end, load_dict,
                                     remove_filename_tags)

from .mame_helpers import default_mame_configuration
from .software_list import (Software, SoftwareCustomMatcher, SoftwareList,
                            SoftwareMatcherArgs, SoftwarePart,
                            get_crc32_for_software_list)

subtitles = load_dict(None, 'subtitles')

def get_software_list_by_name(name: str) -> Optional[SoftwareList]:
	if not hasattr(get_software_list_by_name, 'cache'):
		get_software_list_by_name.cache = {} #type: ignore[attr-defined]

	if name in get_software_list_by_name.cache: #type: ignore[attr-defined]
		return get_software_list_by_name.cache[name] #type: ignore[attr-defined]

	try:
		if not default_mame_configuration:
			return None
		for hash_path in default_mame_configuration.core_config.get('hashpath', ()):
			if os.path.isdir(hash_path):
				list_path = Path(hash_path, name + '.xml')
				if list_path.is_file():
					software_list = SoftwareList(list_path)
					get_software_list_by_name.cache[name] = software_list #type: ignore[attr-defined]
					return software_list
		#if main_config.debug:
		#	print('Programmer (not user) error - called get_software_list_by_name with non-existent {0} softlist'.format(name))
		#We should print that warning but not like 900000 times
		return None #In theory though, we shouldn't be asking for software lists that don't exist
	except FileNotFoundError:
		return None

def find_in_software_lists_with_custom_matcher(software_lists: Collection[SoftwareList], matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Optional[Software]:
	for software_list in software_lists:
		software = software_list.find_software_with_custom_matcher(matcher, args)
		if software:
			return software
	return None

def _does_name_fuzzy_match(part: SoftwarePart, name: str) -> bool:
	#TODO Handle annoying multiple discs
	proto_tags = {'beta', 'proto', 'sample'}

	software_name_without_brackety_bois = remove_filename_tags(part.software.description)
	name_without_brackety_bois = remove_filename_tags(name)
	software_normalized_name = normalize_name(software_name_without_brackety_bois)
	normalized_name = normalize_name(name_without_brackety_bois)
	name_tags = {t.lower()[1:-1] for t in find_filename_tags_at_end(name)}
	#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
	software_tags = ', '.join(t.lower()[1:-1] for t in find_filename_tags_at_end(part.software.description)).split(', ')
	
	if software_normalized_name != normalized_name:
		if name_without_brackety_bois in subtitles:
			if normalize_name(name_without_brackety_bois + ': ' + subtitles[name_without_brackety_bois]) != software_normalized_name:
				return False
		elif software_name_without_brackety_bois in subtitles:
			if normalize_name(software_name_without_brackety_bois + ': ' + subtitles[software_name_without_brackety_bois]) != normalized_name:
				return False
		else:
			return False
	if 'demo' in software_tags and 'demo' not in (', ').join(name_tags):
		return False
	if 'demo' in name_tags and 'demo' not in software_tags:
		return False

	software_is_prototype = any(t.startswith('prototype') for t in software_tags)

	for t in proto_tags:
		if t in name_tags and not (t in software_tags or software_is_prototype):
			return False
		if t in software_tags and not t in name_tags:
			return False
	if software_is_prototype:
		matches_proto = False
		for t in proto_tags:
			if t in name_tags:
				matches_proto = True
		if not matches_proto:
			return False
	return True

def find_software_by_name(software_lists: Collection[SoftwareList], name: str) -> Optional[Software]:
	fuzzy_name_matches = set(itertools.chain.from_iterable(software_list.iter_all_software_with_custom_matcher(_does_name_fuzzy_match, [name]) for software_list in software_lists))

	if len(fuzzy_name_matches) == 1:
		#TODO: Don't do this, we still need to check the region… but only if the region needs to be checked at all, see below comment
		#Bold of you to assume I understand this code, past Megan
		for first_fuzzy_match in fuzzy_name_matches:
			return first_fuzzy_match
	if len(fuzzy_name_matches) > 1:
		name_and_region_matches: MutableSet[Software] = set()
		regions = {
			'USA': 'USA',
			'Euro': 'Europe',
			'Jpn': 'Japan',
			'Aus': 'Australia',
			'As': 'Asia',
			'Fra': 'France',
			'Ger': 'Germany',
			'Spa': 'Spain',
			'Ita': 'Italy',
			'Ned': 'Netherlands',
			'Bra': 'Brazil',
		}
		name_brackets = {t.lower()[1:-1] for t in find_filename_tags_at_end(name)}
		for match in fuzzy_name_matches:
			#Narrow down by region
			#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
			#TODO: Don't narrow down by region if we don't have to, e.g. a region is in the name but nowhere in the software name
			match_brackets = ', '.join(t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)).split(', ')
			for abbrev_region, region in regions.items():				
				if (abbrev_region.lower() in match_brackets or region.lower() in match_brackets) and region.lower() in name_brackets:
					name_and_region_matches.add(match)

		if len(name_and_region_matches) == 1:
			for first in name_and_region_matches:
				return first

		name_and_region_and_version_matches = set()
		for match in name_and_region_matches:
			match_brackets = ', '.join(t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)).split(', ')
			if 'v1.1' in match_brackets:
				if 'v1.1' in name_brackets or 'reprint' in name_brackets or 'rerelease' in name_brackets or 'rev 1' in name_brackets:
					name_and_region_and_version_matches.add(match)
					break
			#TODO Should look at the rest of name_brackets or match_brackets for anything else looking like rev X or v1.X
			#TODO Consider special versions
			#Seen in the wild:  "Limited Edition", "32X", "Sega All Stars", "Amiga CD32 Special"

			if 'v1.0' in match_brackets:
				orig_version = True
				for b in name_brackets:
					if (b not in {'rev 0', 'v1.0'} and b.startswith(('rev', 'v1.'))) or b in {'reprint', 'rerelease'}:
						orig_version = False
						break
				if orig_version:
					name_and_region_and_version_matches.add(match)
		
		if len(name_and_region_and_version_matches) == 1:
			return next(iter(name_and_region_and_version_matches))

		#print(name, 'matched too many', [m.description for m in name_and_region_matches])
		
	return None

def find_in_software_lists(software_lists: Collection[SoftwareList], args: SoftwareMatcherArgs) -> Optional[Software]:
	#Does not handle hash collisions… should be fine in real life, though
	for software_list in software_lists:
		software = software_list.find_software(args)
		if software:
			return software
	return None

def matcher_args_for_bytes(data: bytes) -> SoftwareMatcherArgs:
	#We _could_ use sha1 here, but there's not really a need to
	return SoftwareMatcherArgs(get_crc32_for_software_list(data), None, len(data), lambda offset, amount: data[offset:offset+amount])
