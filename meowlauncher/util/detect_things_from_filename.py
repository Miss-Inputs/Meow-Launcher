#!/usr/bin/env python3

import re
from collections.abc import Sequence

from meowlauncher.info import Date

from . import region_info

#TODO: I dunno if this should be done as a big ol' regex, maybe just see if a comma-separated list all matches languages
_nointro_language_list_regex = re.compile(r'\(((?:[A-Z][a-z](?:-[A-Z][a-z]+)?,)*(?:[A-Z][a-z](?:-[A-Z][a-z]+)?))\)')
_maybeintro_translated_regex = re.compile(r'\[(?:tr |T-|T\+)([A-Z][a-z])(?: (?:by )?[^]]+)?\]')
_tosec_language_regex = re.compile(r'\(([a-z][a-z])(?:-([a-z][a-z]))?\)')

def get_languages_from_tags_directly(tags: Sequence[str]) -> Sequence[region_info.Language]:
	langs = []
	for tag in tags:
		for language in region_info.languages:
			if language.english_name in tag:
				langs.append(language) 
			elif language.native_name in tag:
				langs.append(language)

	return langs

def get_nointro_language_list_from_filename_tags(tags: Sequence[str]) -> Sequence[region_info.Language] | None:
	for tag in tags:
		if (language_list_match := _nointro_language_list_regex.match(tag)):
			langs = []

			language_list = language_list_match[1].split(',')
			for language_code in language_list:
				if language := region_info.get_language_by_short_code(language_code):
					langs.append(language)

			return langs
	return None

def get_maybeintro_languages_from_filename_tags(tags: Sequence[str]) -> region_info.Language | None:
	for tag in tags:
		if translation_match := _maybeintro_translated_regex.match(tag):
			lang = region_info.get_language_by_short_code(translation_match.group(1))
			if lang:
				return lang
	return None

_tosec_date_tag_regex = re.compile(r'\((-|[x\d]{4}(?:-\d{2}(?:-\d{2})?)?)\)')
def get_tosec_languages_from_filename_tags(tags: Sequence[str]) -> Sequence[region_info.Language] | None:
	found_year_tag = False
	found_publisher_tag = False

	for tag in tags:
		if not found_year_tag:
			if _tosec_date_tag_regex.match(tag):
				found_year_tag = True
				continue
		if found_year_tag and not found_publisher_tag:
			if tag.startswith('(') and tag.endswith(')'):
				found_publisher_tag = True
				continue

		tosec_languages_match = _tosec_language_regex.match(tag)
		if found_year_tag and found_publisher_tag and tosec_languages_match:
			first_language_code = tosec_languages_match[1].capitalize()
			first_language = region_info.get_language_by_short_code(first_language_code)
			if first_language:
				if tosec_languages_match[2]:
					second_language_code = tosec_languages_match[2].capitalize()
					second_language = region_info.get_language_by_short_code(second_language_code)
					if second_language:
						return [first_language, second_language]
				else:
					return [first_language]
	return None

def get_languages_from_filename_tags(tags: Sequence[str]) -> Sequence[region_info.Language] | None:
	lang = get_maybeintro_languages_from_filename_tags(tags)
	if lang:
		return [lang]

	langs = get_nointro_language_list_from_filename_tags(tags)
	if langs:
		return langs

	langs = get_tosec_languages_from_filename_tags(tags)
	if langs:
		return langs

	langs = get_languages_from_tags_directly(tags)
	if langs:
		return langs

	return None

def get_regions_from_filename_tags_strictly(tags: Sequence[str]) -> Sequence[region_info.Region] | None:
	"""Only of the form (Region 1, Region 2) strictly (e.g. as with No-Intro naming convention)"""
	for tag in tags:
		if not (tag.startswith('(') and tag.endswith(')')):
			continue
		tag = tag[1:-1]
		components = tag.split(', ')
		try:
			regions = tuple(region_info.regions_by_name[component] for component in components)
		except KeyError:
			#This wasn't the tag we wanted
			continue
		return regions
	return None

def get_regions_from_filename_tags_loosely(tags: Sequence[str]) -> Sequence[region_info.Region]:
	regions = []
	for tag in tags:
		for region in region_info.regions:
			if region.name in tag:
				regions.append(region)
		if re.search(r'\bUS(?:\b|,|/)', tag):
			regions.append(region_info.regions_by_name['USA'])
		if re.search(r'\bEuro(?:\b|,|/)', tag):
			regions.append(region_info.regions_by_name['Europe'])
	return regions

def get_tosec_region_list_from_filename_tags(tags: Sequence[str]) -> Sequence[region_info.Region] | None:
	"""Only something like (JP-US), as specified in TOSEC naming convention"""
	found_year_tag = False
	found_publisher_tag = False

	for tag in tags:
		if not found_year_tag:
			if _tosec_date_tag_regex.match(tag):
				found_year_tag = True
				continue
		if found_year_tag and not found_publisher_tag:
			if tag.startswith('(') and tag.endswith(')'):
				found_publisher_tag = True
				continue

		if not found_year_tag and not found_publisher_tag:
			continue
		if not (tag.startswith('(') and tag.endswith(')')):
			continue
		tag = tag[1:-1]
		components = tag.split('-')
		try:
			regions = tuple(region_info.regions_by_short_code[component] for component in components)
		except KeyError:
			#This wasn't the tag we wanted
			continue

		return regions
	return None

def get_regions_from_filename_tags(tags: Sequence[str], loose: bool=False) -> Sequence[region_info.Region] | None:
	regions: Sequence[region_info.Region] | None
	if loose:
		regions = get_regions_from_filename_tags_loosely(tags)
		if regions:
			return regions
	
	regions = get_regions_from_filename_tags_strictly(tags)
	if regions:
		return regions

	regions = get_tosec_region_list_from_filename_tags(tags)
	if regions:
		return regions

	return None

def get_tv_system_from_filename_tags(tags: Sequence[str]) -> region_info.TVSystem | None:
	"""You should look for regions instead if you can. This just looks at the presence of (NTSC) or (PAL) directly (both No-Intro and TOSEC style filenames sometimes do this), as well as some other things that might happen"""
	for tag in tags:
		tag = tag.upper()
		if tag in {'(NTSC)', '[F NTSC]'}:
			return region_info.TVSystem.NTSC
		if tag in {'(PAL)', '[F PAL]', '[PAL only]', '(PAL 50)', '(PAL50)'}:
			return region_info.TVSystem.PAL
		if tag in {'(NTSC-PAL)', '(PAL-NTSC)'}:
			return region_info.TVSystem.Agnostic
		#TODO: PAL60 should be noted too
	return None

_date_regex = re.compile(r'\((?P<year>[x\d]{4})\)|\((?P<year2>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\)|\((?P<day2>\d{2})\.(?P<month2>\d{2})\.(?P<year3>\d{4})\)')
def get_date_from_filename_tags(tags: Sequence[str]) -> Date | None:
	for tag in tags:
		if (date_match := _date_regex.match(tag)):
			groupdict = date_match.groupdict()
			#I _hate_ this. There's no way I can find to make this code not suck titty balls
			_year = groupdict.get('year')
			_year2 = groupdict.get('year2')
			_year3 = groupdict.get('year3')
			year = _year if _year else (_year2 if _year2 else _year3)
			_month = groupdict.get('month')
			_month2 = groupdict.get('month2')

			month_match = _month if _month else _month2
			_day = groupdict.get('day') 
			_day2 = groupdict.get('day2') 
			day = _day if _day else _day2
			return Date(year, month_match, day)
	return None

_revision_regex = re.compile(r'\([Rr]ev(?:ision)? ([A-Z\d]+?)\)')
def get_revision_from_filename_tags(tags: Sequence[str]) -> str | None:
	for tag in tags:
		revision_match = _revision_regex.match(tag)
		if revision_match:
			return revision_match[1]
	return None

_version_regex = re.compile(r'\(([vV]\d+(?:\.\w+)?)\)') #Very loose match, I know, but sometimes versions have stuff on the end like v1.2b or whatever and I don't wanna overcomplicate things
_version_number_regex = re.compile(r'\((?:version|ver|ver\.)\s+([\d.]+)[^)]*\)') #This one is a bit more specific and shows up in MAME machine names sometimes
def get_version_from_filename_tags(tags: Sequence[str]) -> str | None:
	for tag in tags:
		version_match = _version_regex.match(tag)
		if version_match:
			return version_match[1].lower()
		version_number_match = _version_number_regex.match(tag)
		if version_number_match:
			return 'v' + version_number_match[1]
	return None

def get_license_from_filename_tags(tags: Sequence[str]) -> str | None:
	if '(CW)' in tags or '(CW-R)' in tags:
		return 'Cardware'
	if '(FW)' in tags:
		return 'Freeware'
	if '(GW)' in tags or '(GW-R)' in tags:
		return 'Giftware'
	if '(LW)' in tags:
		#The hell is licenseware, TOSEC?
		return 'Licenseware'
	if '(PD)' in tags:
		return 'Public Domain'
	if '(SW)' in tags or '(SW-R)' in tags or '(Shareware)' in tags:
		return 'Shareware'
	
	#TOSEC does put more at the end, but they haven't updated the naming standards document in a while I guess
	if '(MIT)' in tags:
		return 'MIT'
	for tag in tags:
		if tag.startswith('(GPL'):
			return tag[1:-1]
		if tag.startswith('(CC BY-'):
			return tag[1:-1]
	
	return None
