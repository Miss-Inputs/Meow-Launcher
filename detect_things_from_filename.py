#!/usr/bin/env python3

import re

from info import region_info
#from info.region_info import get_language_by_english_name, get_language_by_short_code, get_region_by_name, get_region_by_short_code, regions, languages, TVSystem

nointro_language_list_regex = re.compile(r'\(((?:[A-Z][a-z],)*(?:[A-Z][a-z]))\)')
maybeintro_translated_regex = re.compile(r'\[(?:tr |T-|T\+)([A-Z][a-z])(?: (?:by )?[^]]+)?\]')
tosec_language_regex = re.compile(r'\(([a-z][a-z])(?:-([a-z][a-z]))?\)')

def get_languages_from_tags_directly(tags, ignored_tags=None):
	langs = []
	for tag in tags:
		for language in region_info.languages:
			if language.english_name in tag:
				langs.append(language) 
			elif language.native_name in tag:
				langs.append(language)

			if ignored_tags is not None:
				if tag in ('(' + language.english_name + ')', '(' + language.native_name + ')'):
					ignored_tags.append(tag)
	return langs

def get_nointro_language_list_from_filename_tags(tags, ignored_tags=None):
	for tag in tags:
		language_list_match = nointro_language_list_regex.match(tag)
		if language_list_match:
			good_tag = False
			langs = []

			language_list = language_list_match[1].split(',')
			for language_code in language_list:
				language = region_info.get_language_by_short_code(language_code)
				if language:
					good_tag = True
					langs.append(language)

			if good_tag and (ignored_tags is not None):
				ignored_tags.append(tag)

			return langs
	return None

def get_maybeintro_languages_from_filename_tags(tags, ignored_tags=None):
	for tag in tags:
		translation_match = maybeintro_translated_regex.match(tag)
		if translation_match:
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return [region_info.get_language_by_short_code(translation_match.group(1))]
	return None

def get_tosec_languages_from_filename_tags(tags, ignored_tags=None):
	for tag in tags:
		tosec_languages_match = tosec_language_regex.match(tag)
		if tosec_languages_match:
			first_language_code = tosec_languages_match[1].capitalize()
			first_language = region_info.get_language_by_short_code(first_language_code)
			if first_language:
				if tosec_languages_match[2]:
					second_language_code = tosec_languages_match[2].capitalize()
					second_language = region_info.get_language_by_short_code(second_language_code)
					if second_language:
						if ignored_tags is not None:
							ignored_tags.append(tag)

						return [first_language, second_language]
				else:
					if ignored_tags is not None:
						ignored_tags.append(tag)
					return [first_language]
	return None

def get_languages_from_filename_tags(tags, ignored_tags=None):
	langs = get_maybeintro_languages_from_filename_tags(tags, ignored_tags)
	if langs:
		return langs

	langs = get_nointro_language_list_from_filename_tags(tags, ignored_tags)
	if langs:
		return langs

	langs = get_tosec_languages_from_filename_tags(tags, ignored_tags)
	if langs:
		return langs

	langs = get_languages_from_tags_directly(tags, ignored_tags)
	if langs:
		return langs

	return None

def get_regions_from_filename_tags_strictly(tags, ignored_tags=None):
	#Only of the form (Region 1, Region 2) strictly
	for tag in tags:
		if not (tag.startswith('(') and tag.endswith(')')):
			continue
		tag = tag[1:-1]
		components = tag.split(', ')
		regions = [region_info.get_region_by_name(component) for component in components]
		if any([r is None for r in regions]):
			#This wasn't the tag we wanted
			continue

		if ignored_tags is not None:
			ignored_tags.append(tag)
		return regions
	return None

def get_regions_from_filename_tags_loosely(tags, ignored_tags=None):
	regions = []
	for tag in tags:
		for region in region_info.regions:
			if region.name in tag:
				regions.append(region)
		if re.search(r'\bUS(?:\b|,|/)', tag):
			regions.append(region_info.get_region_by_name('USA'))
			if ignored_tags is not None and not tag_ignored_already:
				ignored_tags.append('(' + tag + ')')
				tag_ignored_already = True
		if re.search(r'\bEuro(?:\b|,|/)', tag):
			regions.append(region_info.get_region_by_name('Europe'))
			if ignored_tags is not None and not tag_ignored_already:
				ignored_tags.append('(' + tag + ')')
				tag_ignored_already = True
	return regions

def get_tosec_region_list_from_filename_tags(tags, ignored_tags=None):
	#Only something like (JP-US)
	for tag in tags:
		if not (tag.startswith('(') and tag.endswith(')')):
			continue
		tag = tag[1:-1]
		components = tag.split('-')
		regions = [region_info.get_region_by_short_code(component) for component in components]
		if any([r is None for r in regions]):
			#This wasn't the tag we wanted
			continue

		if ignored_tags is not None:
			ignored_tags.append(tag)
		return regions
	return None

def get_regions_from_filename_tags(tags, ignored_tags=None, loose=False):
	if loose:
		regions = get_regions_from_filename_tags_loosely(tags, ignored_tags)
		if regions:
			return regions
	
	regions = get_regions_from_filename_tags_strictly(tags, ignored_tags)
	if regions:
		return regions

	regions = get_tosec_region_list_from_filename_tags(tags, ignored_tags)
	if regions:
		return regions

	return None

def get_tv_system_from_filename_tags(tags, ignored_tags=None):
	#You should look for regions instead if you can. This just looks at the presence of (NTSC) or (PAL) directly (both No-Intro and TOSEC style filenames sometimes do this).
	for tag in tags:
		tag = tag.upper()
		if tag == '(NTSC)':
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return region_info.TVSystem.NTSC
		if tag == '(PAL)':
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return region_info.TVSystem.PAL
		if tag in ('(NTSC-PAL)', '(PAL-NTSC)'):
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return region_info.TVSystem.Agnostic

	return None

def determine_is_nsfw_from_filename(tags):
	#TOSEC has been known to use these in the "extra data" or whatsitcalled field at the end to specify that a game is adults only
	nsfw_tags = {'[adult]', '[XXX]'}
	for nsfw_tag in nsfw_tags:
		if nsfw_tag in tags:
			return True
	return False
