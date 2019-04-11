import re

import info.region_info as region_info

language_list_regex = re.compile(r'\(((?:[A-Z][a-z],)*(?:[A-Z][a-z]))\)')
translated_regex = re.compile(r'\[(?:tr |T-|T\+)([A-Z][a-z])(?: (?:by )?[^]]+)?\]')
tosec_language_regex = re.compile(r'\(([a-z][a-z])(?:-([a-z][a-z]))?\)')

def get_language_by_short_code(code):
	for language in region_info.languages:
		if language.short_code == code:
			return language

	return None

def get_language_by_english_name(name, case_insensitive=False):
	if case_insensitive:
		name = name.lower()
	for language in region_info.languages:
		if (language.english_name.lower() if case_insensitive else language.english_name) == name:
			return language

	return None

def get_region_by_name(name):
	for region in region_info.regions:
		if region.name == name:
			return region

	return None

def get_region_by_short_code(short_code):
	for region in region_info.regions:
		if region.short_code == short_code:
			return region

	return None

def get_languages_from_regions(regions):
	common_language = None
	#If all the regions here have the same language, we can infer the language of the game. Otherwise, we sorta can't
	#e.g. We know (USA, Australia) is English, but (Japan, USA) could be Japanese or English
	for region in regions:
		if not common_language:
			common_language = get_language_by_english_name(region.language)
		else:
			if region.language != common_language.english_name:
				return None

	return [common_language]

def get_languages_from_filename_tags(tags, ignored_tags=None):
	for tag in tags:
		#Lazy way to deal with hhug-style filenames, but it works
		#Can't really deal with (Unlicensed, Multi3) since that doesn't tell me what those 3 languages are
		if tag == '(Unlicensed, Chinese)':
			return [get_language_by_english_name('Chinese')]
		elif tag == '(Unlicensed, English)':
			return [get_language_by_english_name('English')]

		translation_match = translated_regex.match(tag)
		if translation_match:
			return [get_language_by_short_code(translation_match.group(1))]

		language_list_match = language_list_regex.match(tag)
		if language_list_match:
			good_tag = False
			languages = []

			language_list = language_list_match.group(1).split(',')
			for language_code in language_list:
				language = get_language_by_short_code(language_code)
				if language:
					good_tag = True
					languages.append(language)

			if good_tag and (ignored_tags is not None):
				ignored_tags.append(tag)

			return languages

		tosec_languages_match = tosec_language_regex.match(tag)
		if tosec_languages_match:
			first_language_code = tosec_languages_match[1].capitalize()
			first_language = get_language_by_short_code(first_language_code)
			if first_language:
				if tosec_languages_match[2]:
					second_language_code = tosec_languages_match[2].capitalize()
					second_language = get_language_by_short_code(second_language_code)
					if second_language:
						if ignored_tags is not None:
							ignored_tags.append(tag)

						return [first_language, second_language]
				else:
					if ignored_tags is not None:
						ignored_tags.append(tag)
					return [first_language]

	return None

is_tosec_region_list = re.compile(r'^[A-Z][A-Z]-[A-Z][A-Z]$')
def get_regions_from_filename_tags(tags, ignored_tags=None, loose=False):
	regions = []
	for tag in tags:
		if tag.startswith('['):
			continue
		tag = tag.lstrip('(').rstrip(')')
		if loose:
			tag_ignored_already = False
			for region in region_info.regions:
				if re.search(r'\b' + re.escape(region.name) + r'(?:\b|,|/)', tag):
					regions.append(region)
				if ignored_tags is not None and not tag_ignored_already:
					ignored_tags.append('(' + tag + ')')
					tag_ignored_already = True
			continue

		multiple_region_separator = None
		if ', ' in tag: #No-Intro style filename
			multiple_region_separator = ', '
		elif is_tosec_region_list.fullmatch(tag):
			multiple_region_separator = '-'

		if multiple_region_separator:
			good_tag = False
			multiple_regions = tag.split(multiple_region_separator)
			for region_name in multiple_regions:
				region = get_region_by_name(region_name)
				if region:
					good_tag = True
					regions.append(region)
				else:
					region = get_region_by_short_code(region_name)
					if region:
						good_tag = True
						regions.append(region)
			if good_tag and (ignored_tags is not None):
				ignored_tags.append('(' + tag + ')')
		else:
			region = get_region_by_name(tag)
			if region:
				if ignored_tags is not None:
					ignored_tags.append('(' + tag + ')')
				regions = [region]
			else:
				region = get_region_by_short_code(tag)
				if region:
					if ignored_tags is not None:
						ignored_tags.append('(' + tag + ')')
					regions.append(region)

	if regions and any(regions):
		return regions

	return None

def get_tv_system_from_regions(regions):
	tv_systems = {region.tv_system for region in regions if region.tv_system is not None}
	if not tv_systems:
		return None
	if len(tv_systems) == 1:
		return tv_systems.pop()

	#If there are multiple distinct systems, it must be agnostic (since we only have NTSC, PAL, and agnostic (both) for now)
	return region_info.TVSystem.Agnostic

def get_tv_system_from_filename_tags(tags, ignored_tags=None):
	#You should look for regions instead if you can. This just looks at the presence of (NTSC) or (PAL) directly (both No-Intro and TOSEC style filenames sometimes do this).
	for tag in tags:
		tag = tag.upper()
		if tag == '(NTSC)':
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return region_info.TVSystem.NTSC
		elif tag == '(PAL)':
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return region_info.TVSystem.PAL
		elif tag == '(NTSC-PAL)' or tag == '(PAL-NTSC)':
			if ignored_tags is not None:
				ignored_tags.append(tag)
			return region_info.TVSystem.Agnostic

	return None
