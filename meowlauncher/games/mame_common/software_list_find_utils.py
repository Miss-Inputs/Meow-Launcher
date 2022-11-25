import itertools
import logging
import os
import zlib
from collections.abc import (Collection, Iterable, Iterator, MutableSet,
                             Sequence)
from functools import cache
from pathlib import Path
from typing import Any

from meowlauncher.util.name_utils import normalize_name
from meowlauncher.util.utils import (find_filename_tags_at_end, load_dict,
                                     remove_filename_tags)

from .mame_helpers import default_mame_configuration
from .software_list import (Software, SoftwareCustomMatcher, SoftwareList,
                            SoftwareMatcherArgs, SoftwarePart)

logger = logging.getLogger(__name__)

subtitles = load_dict(None, 'subtitles')

def iter_all_software_lists() -> Iterator[tuple[Path, SoftwareList]]:
	if not default_mame_configuration:
		return
	hashpaths = default_mame_configuration.core_config.get('hashpath')
	if not hashpaths:
		return
	generator = (Path(hash_path).iterdir() for hash_path in hashpaths)
	try:
		for hash_xml_path in itertools.chain.from_iterable(generator):
			try:
				yield hash_xml_path, SoftwareList(hash_xml_path)
			except SyntaxError: #I guess that is the error it throws?
				logger.info('%s is fuckin borked for some reason', hash_xml_path, exc_info=True)
				continue
	except FileNotFoundError:
		pass

def iter_software_lists_by_name(names: Iterable[str]) -> Iterator[SoftwareList]:
	if not default_mame_configuration:
		return
	hashpaths = default_mame_configuration.core_config.get('hashpath')
	if not hashpaths:
		return
	generator = (Path(hash_path) for hash_path in hashpaths)
	try:
		for hash_path in generator:
			for name in names:
				yield SoftwareList(hash_path.joinpath(name).with_suffix(os.extsep + 'xml'))
	except FileNotFoundError:
		pass

@cache
def get_software_list_by_name(name: str) -> SoftwareList | None:
	return next(iter_software_lists_by_name((name, )), None)

def find_in_software_lists_with_custom_matcher(software_lists: Collection[SoftwareList], matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Software | None:
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
			if normalize_name(f'{name_without_brackety_bois}: {subtitles[name_without_brackety_bois]}') != software_normalized_name:
				return False
		elif software_name_without_brackety_bois in subtitles:
			if normalize_name(f'{software_name_without_brackety_bois}: {subtitles[software_name_without_brackety_bois]}') != normalized_name:
				return False
		else:
			return False
	if 'demo' in software_tags and 'demo' not in ', '.join(name_tags):
		return False
	if 'demo' in name_tags and 'demo' not in software_tags:
		return False

	software_is_prototype = any(t.startswith('prototype') for t in software_tags)

	for t in proto_tags:
		if t in name_tags and not (software_is_prototype or t in software_tags):
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

def find_software_by_name(software_lists: Collection[SoftwareList], name: str) -> Software | None:
	fuzzy_name_matches = set(itertools.chain.from_iterable(software_list.iter_all_software_with_custom_matcher(_does_name_fuzzy_match, [name]) for software_list in software_lists))

	if len(fuzzy_name_matches) == 1:
		#TODO: Don't do this, we still need to check the region… but only if the region needs to be checked at all, see below comment
		#Bold of you to assume I understand this code, past Megan
		#TODO: Okay I think I see what Past Megan was trying to do here… we want to first get the matches from _does_name_fuzzy_match, then we want to filter down by region _unless_ we don't have to (because regions aren't involved), and then version if needed, so this really all happens in three parts, and yeah I guess that does mean we need to collect everything in a set so we can test length == 1
		return fuzzy_name_matches.pop()
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
			return name_and_region_matches.pop()

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
			return name_and_region_and_version_matches.pop()

		#print(name, 'matched too many', [m.description for m in name_and_region_matches])
		
	return None

def find_in_software_lists(software_lists: Collection[SoftwareList], args: SoftwareMatcherArgs) -> Software | None:
	#Does not handle hash collisions… should be fine in real life, though
	for software_list in software_lists:
		software = software_list.find_software(args)
		if software:
			return software
	return None

def matcher_args_for_bytes(data: bytes) -> SoftwareMatcherArgs:
	#We _could_ use sha1 here, but there's not really a need to
	return SoftwareMatcherArgs(zlib.crc32(data), None, len(data), lambda offset, amount: data[offset:offset+amount])
