#!/usr/bin/env python3
#I can't be stuffed figuring out if there's some fancy unit test thing that all the cool kids use so I'm just gonna do my own thing

from info.region_info import TVSystem, Region, Language
from region_detect import *
from common import find_filename_tags

def regions_equal(region, other_region):
	if region == other_region:
		return True

	if isinstance(region, Region) and not isinstance(other_region, Region):
		return region.name == other_region

	if isinstance(other_region, Region) and not isinstance(region, Region):
		return region == other_region.name

	return False

def region_array_equal(regions, other_regions):
	if regions == other_regions:
		return True

	if regions is None:
		return other_regions is None

	if other_regions is None:
		return regions is None

	length = len(regions)
	if len(other_regions) != length:
		return False

	for region, other_region in zip(regions, other_regions):
		if not regions_equal(region, other_region):
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

def language_array_equal(languages, other_languages):
	if languages == other_languages:
		return True

	if languages is None:
		return other_languages is None

	if other_languages is None:
		return languages is None

	length = len(languages)
	if len(other_languages) != length:
		return False

	for language, other_language in zip(languages, other_languages):
		if not languages_equal(language, other_language):
			return False

	return True


class Test():
	def __init__(self, name, filename, expected_regions, expected_languages, expected_tv_type):
		self.name = name
		self.filename = filename
		self.expected_regions = expected_regions
		self.expected_languages = expected_languages
		self.expected_tv_type = expected_tv_type

	def run(self):
		try:
			tags = find_filename_tags.findall(self.filename)

			regions = get_regions_from_filename_tags(tags)
			if not region_array_equal(regions, self.expected_regions):
				print('Oh no! {0} failed: Regions = {1}, expected = {2}'.format(self.name, regions, self.expected_regions))

			languages = get_languages_from_filename_tags(tags)
			if regions and not languages:
				languages = get_languages_from_regions(regions)
			if not language_array_equal(languages, self.expected_languages):
				print('Oh no! {0} failed: Languages = {1}, expected = {2}'.format(self.name, languages, self.expected_languages))

			if regions:
				tv_type = get_tv_system_from_regions(regions)
			else:
				tv_type = get_tv_system_from_filename_tags(tags)
			if tv_type != self.expected_tv_type:
				print('Oh no! {0} failed: TV type = {1}, expected = {2}'.format(self.name, tv_type, self.expected_tv_type))
		except Exception as ex: #pylint: disable=broad-except
			print('Oh no! {0} failed: exception = {1}'.format(self.name, ex))

tests = [
	Test("No-Intro filename with region", "Cool Game (Spain)", ['Spain'], ['Spanish'], TVSystem.PAL),
	Test("No-Intro filename with two regions", "Cool Game (Europe, Australia)", ['Europe', 'Australia'], ['English'], TVSystem.PAL),
	Test("No-Intro filename with two regions with different languages", "Cool Game (Japan, USA)", ['Japan', 'USA'], None, TVSystem.NTSC),
	Test("No-Intro filename with region but also unrelated tag", "Cool Game (Japan) (Unl)", ['Japan'], ['Japanese'], TVSystem.NTSC),
	Test("No-Intro filename with explicit languages", "Cool Game (Germany) (En,De)", ['Germany'], ['English', 'German'], TVSystem.PAL),
	Test("No-Intro filename with only one explicit language", "Cool Game (Japan) (En)", ['Japan'], ['English'], TVSystem.NTSC),
	Test("Non-standard filename with explicit TV type", "Cool Game (NTSC)", None, None, TVSystem.NTSC),
	Test("TOSEC filename with nothing", "Cool Game (1992)(CoolSoft)", None, None, None),
	Test("TOSEC filename with explicit TV type", "Cool Game (1992)(CoolSoft)(NTSC)", None, None, TVSystem.NTSC),
	Test("TOSEC filename with region", "Cool Game (1992)(CoolSoft)(JP)", ['Japan'], ['Japanese'], TVSystem.NTSC),
	Test("TOSEC filename with two regions", "Cool Game (1992)(CoolSoft)(JP-US)", ['Japan', 'USA'], None, TVSystem.NTSC),
	Test("TOSEC filename with two regions with same language", "Cool Game (1992)(CoolSoft)(EU-AU)", ['Europe', 'Australia'], ['English'], TVSystem.PAL),
	Test("TOSEC filename with language but no region", "Cool Game (1992)(CoolSoft)(pt)", None, ['Portugese'], None),
	Test("TOSEC filename with two languages but no region", "Cool Game (1992)(CoolSoft)(en-fr)", None, ['English', 'French'], None),
	Test("TOSEC filename with region and language", "Cool Game (1992)(CoolSoft)(JP)(en)", ['Japan'], ['English'], TVSystem.NTSC),
	Test("TOSEC filename with region and two languages", "Cool Game (1992)(CoolSoft)(JP)(en-fr)", ['Japan'], ['English', 'French'], TVSystem.NTSC),
	Test("TOSEC filename with two regions and two languages", "Cool Game (1992)(CoolSoft)(JP-US)(en-ja)", ['Japan', 'USA'], ['English', 'Japanese'], TVSystem.NTSC),
	Test("Name of a region in name but not tags", "Cool Adventures in Japan (USA)", ['USA'], ['English'], TVSystem.NTSC),
]

for test in tests:
	test.run()
