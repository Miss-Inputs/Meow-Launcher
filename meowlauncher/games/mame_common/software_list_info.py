import os
import zlib
from collections.abc import Iterable, Sequence
from typing import Any, Optional, cast

from meowlauncher.common_types import MediaType
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.data.emulated_platforms import platforms
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.util import io_utils
from meowlauncher.util.name_utils import normalize_name
from meowlauncher.util.utils import (byteswap, find_filename_tags_at_end,
                                     load_dict, remove_filename_tags)

from .mame_helpers import default_mame_configuration
from .software_list import (Software, SoftwareCustomMatcher, SoftwareList,
                            SoftwareMatcherArgs, SoftwarePart,
                            format_crc32_for_software_list,
                            get_crc32_for_software_list)

subtitles = load_dict(None, 'subtitles')

def get_software_lists_by_names(names: Sequence[str]) -> list[SoftwareList]:
	if not names:
		return []
	return [software_list for software_list in [get_software_list_by_name(name) for name in names] if software_list]

def get_software_list_by_name(name: str) -> Optional[SoftwareList]:
	if not hasattr(get_software_list_by_name, 'cache'):
		get_software_list_by_name.cache = {} #type: ignore[attr-defined]

	if name in get_software_list_by_name.cache: #type: ignore[attr-defined]
		return get_software_list_by_name.cache[name] #type: ignore[attr-defined]

	try:
		if not default_mame_configuration:
			return None
		for hash_path in default_mame_configuration.core_config.get('hashpath', []):
			if os.path.isdir(hash_path):
				list_path = os.path.join(hash_path, name + '.xml')
				if os.path.isfile(list_path):
					software_list = SoftwareList(list_path)
					get_software_list_by_name.cache[name] = software_list #type: ignore[attr-defined]
					return software_list
		#if main_config.debug:
		#	print('Programmer (not user) error - called get_software_list_by_name with non-existent {0} softlist'.format(name))
		#We should print that warning but not like 900000 times
		return None #In theory though, we shouldn't be asking for software lists that don't exist
	except FileNotFoundError:
		return None

def find_in_software_lists_with_custom_matcher(software_lists: Sequence[SoftwareList], matcher: SoftwareCustomMatcher, args: Sequence[Any]) -> Optional[Software]:
	for software_list in software_lists:
		software = software_list.find_software_with_custom_matcher(matcher, args)
		if software:
			return software
	return None

def _does_name_fuzzy_match(part: SoftwarePart, name: str) -> bool:
	#TODO Handle annoying multiple discs
	proto_tags = ['beta', 'proto', 'sample']

	software_name_without_brackety_bois = remove_filename_tags(part.software.description)
	name_without_brackety_bois = remove_filename_tags(name)
	software_normalized_name = normalize_name(software_name_without_brackety_bois)
	normalized_name = normalize_name(name_without_brackety_bois)
	name_tags = [t.lower()[1:-1] for t in find_filename_tags_at_end(name)]
	#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
	software_tags = ', '.join([t.lower()[1:-1] for t in find_filename_tags_at_end(part.software.description)]).split(', ')
	
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

def find_software_by_name(software_lists: Sequence[SoftwareList], name: str) -> Optional[Software]:
	fuzzy_name_matches: list[Software] = []
	if not software_lists:
		return None
	for software_list in software_lists:
		results = software_list.find_all_software_with_custom_matcher(_does_name_fuzzy_match, [name])
		fuzzy_name_matches += results
	if len(fuzzy_name_matches) == 1:
		#TODO: Don't do this, we still need to check the region… but only if the region needs to be checked at all, see below comment
		return fuzzy_name_matches[0]
	if len(fuzzy_name_matches) > 1:
		name_and_region_matches: list[Software] = []
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
		name_brackets = [t.lower()[1:-1] for t in find_filename_tags_at_end(name)]
		for match in fuzzy_name_matches:
			#Narrow down by region
			#Sometimes (often) these will appear as (Region, Special Version) and not (Region) (Special Version) etc, so let's dismantle them
			#TODO: Don't narrow down by region if we don't have to, e.g. a region is in the name but nowhere in the software name
			match_brackets = ', '.join([t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)]).split(', ')
			for abbrev_region, region in regions.items():				
				if (abbrev_region.lower() in match_brackets or region.lower() in match_brackets) and region.lower() in name_brackets:
					name_and_region_matches.append(match)

		if len(name_and_region_matches) == 1:
			return name_and_region_matches[0]

		name_and_region_and_version_matches = []
		for match in name_and_region_matches:
			match_brackets = ', '.join([t.lower()[1:-1] for t in find_filename_tags_at_end(match.description)]).split(', ')
			if 'v1.1' in match_brackets:
				if 'v1.1' in name_brackets or 'reprint' in name_brackets or 'rerelease' in name_brackets or 'rev 1' in name_brackets:
					name_and_region_and_version_matches.append(match)
					break
			#TODO Should look at the rest of name_brackets or match_brackets for anything else looking like rev X or v1.X
			#TODO Consider special versions
			#Seen in the wild:  "Limited Edition", "32X", "Sega All Stars", "Amiga CD32 Special"

			if 'v1.0' in match_brackets:
				orig_version = True
				for b in name_brackets:
					if (b not in ('rev 0', 'v1.0') and b.startswith(('rev', 'v1.'))) or b in {'reprint', 'rerelease'}:
						orig_version = False
						break
				if orig_version:
					name_and_region_and_version_matches.append(match)
		
		if len(name_and_region_and_version_matches) == 1:
			return name_and_region_and_version_matches[0]

		#print(name, 'matched too many', [m.description for m in name_and_region_matches])
		
	return None

def software_list_product_code_matcher(part: SoftwarePart, product_code: str) -> bool:
	part_code = part.software.serial
	if not part_code:
		return False

	return product_code in part_code.split(', ')

def find_in_software_lists(software_lists: Iterable[SoftwareList], args: SoftwareMatcherArgs) -> Optional[Software]:
	#TODO: Handle hash collisions. Could happen, even if we're narrowing down to specific software lists
	if not software_lists:
		return None
	for software_list in software_lists:
		software = software_list.find_software(args)
		if software:
			return software
	return None

class UnsupportedCHDError(Exception):
	pass

def get_sha1_from_chd(chd_path) -> str:
	header = io_utils.read_file(chd_path, amount=124)
	if header[0:8] != b'MComprHD':
		raise UnsupportedCHDError('Header magic %s unknown' % str(header[0:8]))
	chd_version = int.from_bytes(header[12:16], 'big')
	if chd_version == 4:
		sha1 = header[48:68]
	elif chd_version == 5:
		sha1 = header[84:104]
	else:
		raise UnsupportedCHDError('Version %d unknown' % chd_version)
	return bytes.hex(sha1)

def matcher_args_for_bytes(data: bytes) -> SoftwareMatcherArgs:
	#We _could_ use sha1 here, but there's not really a need to
	return SoftwareMatcherArgs(get_crc32_for_software_list(data), None, len(data), lambda offset, amount: data[offset:offset+amount])

def get_software_list_entry(game: ROMGame, skip_header=0) -> Optional[Software]:
	if game.software_lists:
		software_lists = game.software_lists
	else:
		software_list_names = platforms[game.platform_name].mame_software_lists
		software_lists = get_software_lists_by_names(software_list_names)

	if game.metadata.media_type == MediaType.OpticalDisc:
		software = None
		if game.rom.extension == 'chd':
			try:
				sha1 = get_sha1_from_chd(game.rom.path)
				args = SoftwareMatcherArgs(None, sha1, None, None)
				software = find_in_software_lists(software_lists, args)
			except UnsupportedCHDError:
				pass
	else:
		if game.subroms:
			#TODO: Get first floppy for now, because right now we don't differentiate with parts or anything; this part of the code sucks
			data = game.subroms[0].read(seek_to=skip_header)
			software = find_in_software_lists(software_lists, matcher_args_for_bytes(data))
		else:
			if game.rom.is_folder:
				raise TypeError('This should not be happening, we are calling get_software_list_entry on a folder')
			file_rom = cast(FileROM, game.rom)
			if skip_header:
				#Hmm might deprecate this in favour of header_length_for_crc_calculation
				data = file_rom.read(seek_to=skip_header)
				software = find_in_software_lists(software_lists, matcher_args_for_bytes(data))
			else:
				if game.platform.databases_are_byteswapped:
					crc32 = format_crc32_for_software_list(zlib.crc32(byteswap(file_rom.read())) & 0xffffffff)
				else:
					crc32 = format_crc32_for_software_list(file_rom.get_crc32())
					
				def _file_rom_reader(offset, amount) -> bytes:
					data = file_rom.read(seek_to=offset, amount=amount)
					if game.platform.databases_are_byteswapped:
						return byteswap(data)
					return data
					
				args = SoftwareMatcherArgs(crc32, None, file_rom.get_size() - file_rom.header_length_for_crc_calculation, _file_rom_reader)
				software = find_in_software_lists(software_lists, args)

	if not software and (platform_configs.get(game.platform_name, {}).options.get('find_software_by_name', False)):
		software = find_software_by_name(game.software_lists, game.rom.name)
	if not software and (platform_configs.get(game.platform_name, {}).options.get('find_software_by_product_code', False) and game.metadata.product_code):
		software = find_in_software_lists_with_custom_matcher(game.software_lists, software_list_product_code_matcher, [game.metadata.product_code])

	return software
