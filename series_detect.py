#!/usr/bin/env python3
import datetime
import os
import re
import time

from config import main_config
import launchers

#These already have a cromulent database of what is in a series and what isn't, or could, so we shouldn't detect it from name
#DOS/Mac _should_, but doesn't yet, so we won't skip it for now, but we will one day
#ignored_types = ('MAME machine', 'DOS', 'Mac')
ignored_types = ('MAME machine')

#Should probably go in data folder, probably
series_overrides = {
	#These names are too clever for my code to work properly, so I'll do them manually
	'Killer 7': (None, None),
}
probably_not_series_index_threshold = 20
#Assume that a number over this is probably not referring to the nth or higher entry in the series, but is probably just any old number that means something else
probably_not_a_series_index = ('XXX', '007')
#These generally aren't entries in a series, and are just there at the end

series_matcher = re.compile(r'(?P<Series>.+?)\b\s+#?(?P<Number>\d{1,3}|[IVX]+?)\b(?:\s|$)')
chapter_matcher = re.compile(r'\b(?:Chapter|Vol|Volume|Episode|Part)\b(?:\.)?', flags=re.RegexFlag.IGNORECASE)
#"Phase", "Version", "Disk" might also be chapter marker things?
subtitle_splitter = re.compile(r'\s*(?:\s+-\s+|:\s+|\/)')
#"&" and "and" and "+" might also go in here?
blah_in_1_matcher = re.compile(r'.+\s+in\s+1')
#TODO: "Whee! 2" should > "Whee!" but returns None instead

def get_name_chunks(name):
	name_chunks = subtitle_splitter.split(name, maxsplit=1)
	name_chunks = [blah_in_1_matcher.sub('', chunk) for chunk in name_chunks]
	name_chunks = [chunk for chunk in name_chunks if chunk]
	return name_chunks

def find_series_from_game_name(name):
	if name in series_overrides:
		return series_overrides[name]
	else:
		#TODO: Because we're doing fullmatch, should take out "Complete Edition" or "GOTY Edition" or "Demo" or whatever at the end, particularly affects Steam stuff that doesn't have things in brackets
		name_chunks = get_name_chunks(name)
		if not name_chunks:
			return None, None
		name_chunk = name_chunks[0]
		series_match = series_matcher.fullmatch(name_chunk)
		if series_match:
			series_name = series_match['Series']
			if series_name.lower().startswith('the '):
				series_name = series_name[len('the '):]
			number = series_match['Number']
			try:
				if int(number) > probably_not_series_index_threshold:
					#TODO Convert roman numerals too
					return None, None
			except ValueError:
				pass
			if number in probably_not_a_series_index:
				return None, None
			return chapter_matcher.sub('', series_name).rstrip(), number
	return None, None

def find_series_name_by_subtitle(name, existing_serieses):
	name_chunks = get_name_chunks(name)
	if not name_chunks:
		return None
	name_chunk = name_chunks[0]
	if name_chunk in existing_serieses:
		return name_chunk
	#TODO: Should we normalize it via similar stuff to disambiguate.normalize_name or nah?
	return None

def get_usable_name(desktop):
	sort_name = launchers.get_field(desktop, 'Sort-Name')
	if sort_name:
		return sort_name
	#Note that this is before disambiguate.py, so we don't need to worry about using Ambiguous-Name from disambiguation section
	#Name _must_ exist in a .desktop file... although this is platform-specific, come to think of it, maybe I should put stuff in launchers.py to abstract getting name/exec/icon/etc
	return launchers.get_field(desktop, 'Name', 'Desktop Entry')

def add_series(desktop, path, series, series_index=None):
	if launchers.metadata_section_name not in desktop:
		desktop.add_section(launchers.metadata_section_name)
	desktop[launchers.metadata_section_name]['Series'] = series
	if series_index is not None:
		desktop[launchers.metadata_section_name]['Series-Index'] = series_index
	with open(path, 'wt') as f:
		desktop.write(f)

def detect_series(desktop, path):
	name = get_usable_name(desktop)
	series, series_index = find_series_from_game_name(name)
	if series:
		add_series(desktop, path, series, series_index)

def find_existing_serieses():
	serieses = set()
	for name in os.listdir(main_config.output_folder):
		path = os.path.join(main_config.output_folder, name)
		desktop = launchers.get_desktop(path)

		series = launchers.get_field(desktop, 'Series')
		if series:
			serieses.add(series)
	return serieses

def detect_series_by_subtitle(desktop, path, existing):
	name = get_usable_name(desktop)
	series = find_series_name_by_subtitle(name, existing)
	if series:
		add_series(desktop, path, series)

def get_existing_seriesless_launchers():
	for name in os.listdir(main_config.output_folder):
		path = os.path.join(main_config.output_folder, name)
		desktop = launchers.get_desktop(path)

		if launchers.get_field(desktop, 'Type', launchers.id_section_name) in ignored_types:
			continue

		if launchers.get_field(desktop, 'Series'):
			#Don't need to do this if it already exists
			continue

		yield desktop, path

def detect_series_for_all_desktops():
	time_started = time.perf_counter()

	for desktop, path in get_existing_seriesless_launchers():
		detect_series(desktop, path)
	existing = find_existing_serieses()
	for desktop, path in get_existing_seriesless_launchers():
		detect_series_by_subtitle(desktop, path, existing)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Name disambiguation finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

if __name__ == '__main__':
	detect_series_for_all_desktops()
