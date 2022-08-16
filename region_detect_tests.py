#!/usr/bin/env python3
#I can't be stuffed figuring out if there's some fancy unit test thing that all the cool kids use so I'm just gonna do my own thing
#TODO: Spice up this class a bit, haven't bothered touching it in a while
#TODO: Yeah I'm not sure this actually works properly

from collections.abc import Collection
from typing import Optional

from meowlauncher.util.detect_things_from_filename import (
    get_languages_from_filename_tags, get_regions_from_filename_tags,
    get_tv_system_from_filename_tags)
from meowlauncher.util.region_info import (Language, Region, TVSystem,
                                           get_common_language_from_regions,
                                           get_tv_system_from_regions)
from meowlauncher.util.utils import find_filename_tags_at_end


def are_regions_equal(region, other_region) -> bool:
	#TODO: Is this even right? Why are we testing for isinstance == Region?
	if region == other_region:
		return True

	if isinstance(region, Region) and not isinstance(other_region, Region):
		return region.name == other_region

	if isinstance(other_region, Region) and not isinstance(region, Region):
		return region == other_region.name

	return False

def region_array_equal(regions: Optional[Collection[Region]], other_regions: Optional[Collection[Region]]) -> bool:
	if regions == other_regions:
		return True

	if regions is None:
		return other_regions is None

	if other_regions is None:
		return regions is None

	length = len(regions)
	if len(other_regions) != length:
		return False

	if not all(are_regions_equal(region, other_region) for region, other_region in zip(regions, other_regions)):
		return False
	
	return True

def languages_equal(language, other_language):
	if language == other_language:
		return True

	if isinstance(language, Language) and not isinstance(other_language, Language):
		return language.english_name == other_language

	if isinstance(other_language, Language) and not isinstance(language, Language):
		return language == other_language.english_name

	return False

def language_array_equal(languages: Optional[Collection[Language]], other_languages: Optional[Collection[Language]]):
	if languages == other_languages:
		return True

	if languages is None:
		return other_languages is None

	if other_languages is None:
		return languages is None

	length = len(languages)
	if len(other_languages) != length:
		return False

	if not all(languages_equal(language, other_language) for language, other_language in zip(languages, other_languages)):
		return False

	return True


class Test():
	def __init__(self, name: str, filename: str, expected_regions: Optional[Collection[str]], expected_languages: Optional[Collection[str]], expected_tv_type: Optional[TVSystem]):
		self.name = name
		self.filename = filename
		self.expected_regions = expected_regions
		self.expected_languages = expected_languages
		self.expected_tv_type = expected_tv_type

	def run(self) -> None:
		try:
			tags = find_filename_tags_at_end(self.filename)

			regions = get_regions_from_filename_tags(tags)
			if not region_array_equal(regions, self.expected_regions):
				print(f'Oh no! {self.name} failed: Regions = {regions}, expected = {self.expected_regions}')

			languages: Collection[Language] = get_languages_from_filename_tags(tags)
			if regions and not languages:
				region_language = get_common_language_from_regions(regions)
				if region_language:
					languages = {region_language}
			if not language_array_equal(languages, self.expected_languages):
				print(f'Oh no! {self.name} failed: Languages = {languages}, expected = {self.expected_languages}')

			if regions:
				tv_type = get_tv_system_from_regions(regions)
			else:
				tv_type = get_tv_system_from_filename_tags(tags)
			if tv_type != self.expected_tv_type:
				print(f'Oh no! {self.name} failed: TV type = {tv_type}, expected = {self.expected_tv_type}')
		except Exception as ex: #pylint: disable=broad-except
			print(f'Oh no! {self.name} failed: exception = {ex}')

tests = [
	Test("No-Intro filename with region", "Cool Game (Spain)", {'Spain'}, {'Spanish'}, TVSystem.PAL),
	Test("No-Intro filename with two regions", "Cool Game (Europe, Australia)", {'Europe', 'Australia'}, {'English'}, TVSystem.PAL),
	Test("No-Intro filename with two regions with different languages", "Cool Game (Japan, USA)", {'Japan', 'USA'}, None, TVSystem.NTSC),
	Test("No-Intro filename with region but also unrelated tag", "Cool Game (Japan) (Unl)", {'Japan'}, {'Japanese'}, TVSystem.NTSC),
	Test("No-Intro filename with explicit languages", "Cool Game (France) (En,Fr)", {'France'}, {'English', 'French'}, TVSystem.PAL),
	Test("No-Intro filename with only one explicit language", "Cool Game (Japan) (En)", {'Japan'}, {'English'}, TVSystem.NTSC),
	Test("Non-standard filename with explicit TV type", "Cool Game (NTSC)", None, None, TVSystem.NTSC),
	Test("TOSEC filename with nothing", "Cool Game (1992)(CoolSoft)", None, None, None),
	Test("TOSEC filename with explicit TV type", "Cool Game (1992)(CoolSoft)(NTSC)", None, None, TVSystem.NTSC),
	Test("TOSEC filename with region", "Cool Game (1992)(CoolSoft)(JP)", {'Japan'}, {'Japanese'}, TVSystem.NTSC),
	Test("TOSEC filename with two regions", "Cool Game (1992)(CoolSoft)(JP-US)", {'Japan', 'USA'}, None, TVSystem.NTSC),
	Test("TOSEC filename with two regions with same language", "Cool Game (1992)(CoolSoft)(EU-AU)", {'Europe', 'Australia'}, {'English'}, TVSystem.PAL),
	Test("TOSEC filename with language but no region", "Cool Game (1992)(CoolSoft)(pt)", None, {'Portuguese'}, None),
	Test("TOSEC filename with two languages but no region", "Cool Game (1992)(CoolSoft)(en-fr)", None, {'English', 'French'}, None),
	Test("TOSEC filename with region and language", "Cool Game (1992)(CoolSoft)(JP)(en)", {'Japan'}, {'English'}, TVSystem.NTSC),
	Test("TOSEC filename with region and two languages", "Cool Game (1992)(CoolSoft)(JP)(en-fr)", {'Japan'}, {'English', 'French'}, TVSystem.NTSC),
	Test("TOSEC filename with two regions and two languages", "Cool Game (1992)(CoolSoft)(JP-US)(en-ja)", {'Japan', 'USA'}, {'English', 'Japanese'}, TVSystem.NTSC),
	Test("Name of a region in name but not tags", "Cool Adventures in Japan (USA)", {'USA'}, {'English'}, TVSystem.NTSC),
]

for test in tests:
	test.run()
