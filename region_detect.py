import re

import region_info

language_list_regex = re.compile(r'\(((?:[A-Z][a-z],)*(?:[A-Z][a-z]))\)')
translated_regex = re.compile(r'\[(?:tr |T-|T\+)([A-Z][a-z])(?: (?:by )?[^]]+)?\]')

def get_language_by_short_code(code):
	for language in region_info.languages:
		if language.short_code == code:
			return language

	return None #TODO: Would it be better to throw an exception instead?

def get_language_by_english_name(name):
	for language in region_info.languages:
		if language.english_name == name:
			return language

	return None #TODO: Would it be better to throw an exception instead?

def get_region_by_name(name):
	for region in region_info.regions:
		if region.name == name:
			return region

	return None #TODO: Would it be better to throw exception and make callers use try/except?

def get_language_from_single_tag(tag):
	regions = []
	if ', ' in tag:
		multiple_region_names = tag.split(', ')
		for region_name in multiple_region_names:
			region = get_region_by_name(region_name)
			if not region:
				return None
			regions.append(region)
	else:
		region = get_region_by_name(tag)
		if not region:
			return None
		regions = [region]
		
	common_language = None
	#If all the regions here have the same language, we can infer the language of the game. Otherwise, we sorta can't
	#e.g. We know (USA, Australia) is English, but (Japan, USA) could be Japanese or English
	for region in regions:
		if not common_language:
			common_language = get_language_by_english_name(region.language)
		else:
			if region.language != common_language.english_name:
				return None

	return common_language

def get_languages_from_filename_tags(tags):
	#TODO: This could use some kinda unit testing thing, even the most basic and half-assed of unit tests

	if len(tags) == 1:
		#This will (probably) be the country the game was released in, so we might be able to infer the language from that
		#TODO: This won't work if it's like Cool Game (Japan) (Promo) or something like that... hmm, maybe detect common tags like (Promo) or (Unl) or [b] that have no bearing on region/language and ignore those?
		tag = tags[0].lstrip('(').rstrip(')')
		language = get_language_from_single_tag(tag)
		if language:
			return [language]

	for tag in tags:
		translation_match = translated_regex.match(tag)
		if translation_match:
			#TODO: Has there ever been a fan translation into multiple languages?
			return [get_language_by_short_code(translation_match.group(1))]

		language_list_match = language_list_regex.match(tag)
		if language_list_match:
			languages = []

			language_list = language_list_match.group(1).split(',')
			for language_code in language_list:
				language = get_language_by_short_code(language_code)
				if language:
					languages.append(language)
	
			return languages

	return None

def get_regions_from_filename_tags(tags):
	regions = []
	for tag in tags:
		if tag.startswith('['):
			continue
		tag = tag.lstrip('(').rstrip(')')

		if ', ' in tag:
			multiple_regions = tag.split(', ')
			for region_name in multiple_regions:
				region = get_region_by_name(region_name)
				if region:
					regions.append(region)
		else:
			region = get_region_by_name(tag)
			if region:
				regions = [region]

		if regions and any(regions):
			return regions

	return None

def get_tv_system_from_regions(regions):
	tv_systems = {region.tv_system for region in regions}
	if len(tv_systems) == 1:
		return tv_systems.pop()
	
	#If there are multiple distinct systems, it must be agnostic (since we only have NTSC, PAL, and agnostic (both) for now)
	return region_info.TVSystem.Agnostic

def get_tv_system_from_filename_tags(tags):
	#You should look for regions instead if you can. This just looks at the presence of (NTSC) or (PAL) directly (both No-Intro and TOSEC style filenames sometimes do this).
	for tag in tags:
		tag = tag.upper()
		if tag == '(NTSC)':
			return region_info.TVSystem.NTSC
		elif tag == '(PAL)':
			return region_info.TVSystem.PAL
		elif tag == '(NTSC-PAL)' or tag == '(PAL-NTSC)':
			return region_info.TVSystem.Agnostic

	return None
