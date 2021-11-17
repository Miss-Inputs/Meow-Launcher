#!/usr/bin/env python3

import collections
import configparser
import datetime
import itertools
import sys
import time
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Optional, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.output.desktop_files import (id_section_name,
                                                   junk_section_name,
                                                   metadata_section_name)
from meowlauncher.util.desktop_files import get_array, get_desktop, get_field
from meowlauncher.util.name_utils import normalize_name

FormatFunction = Callable[[str, str], Optional[str]]
DesktopWithPath = tuple[Path, configparser.ConfigParser]

super_debug = '--super-debug' in sys.argv
disambiguity_section_name = 'X-Meow Launcher Disambiguity'

def update_name(desktop: DesktopWithPath, disambiguator: Optional[str], disambiguation_method: str):
	if not disambiguator:
		return
	desktop_entry = desktop[1]['Desktop Entry']
	if disambiguity_section_name not in desktop[1]:
		desktop[1].add_section(disambiguity_section_name)
	disambiguity_section = desktop[1][disambiguity_section_name]

	if super_debug:
		print('Disambiguating', desktop_entry['Name'], 'with', disambiguator, 'using', disambiguation_method)
	if 'Ambiguous-Name' not in disambiguity_section:
		disambiguity_section['Ambiguous-Name'] = desktop_entry['Name']

	if 'Disambiguator' not in disambiguity_section:
		disambiguity_section['Disambiguator'] = disambiguator
	else:
		disambiguity_section['Disambiguator'] += ';' + disambiguator
	if 'Disambiguation-Method' not in disambiguity_section:
		disambiguity_section['Disambiguation-Method'] = disambiguation_method
	else:
		disambiguity_section['Disambiguation-Method'] += ';' + disambiguation_method

	desktop_entry['Name'] += ' ' + disambiguator

	with desktop[0].open('wt', encoding='utf-8') as f:
		desktop[1].write(f)

def resolve_duplicates_by_metadata(group: Collection[DesktopWithPath], field: str, format_function: Optional[FormatFunction]=None, ignore_missing_values: bool=False, field_section: str=metadata_section_name):
	value_counter = collections.Counter(get_field(d[1], field, field_section) for d in group)
	for dup in group:
		field_value = get_field(dup[1], field, field_section)
		name = cast(str, get_field(dup[1], 'Name', 'Desktop Entry')) #Yeah nah like I said, this wouldn't be a valid .desktop if that were missing

		#See if this launcher is unique in this group (of launchers with the same
		#name) for its field.  If it's the only launcher for this field, we can
		#use Thing (Field) as the final display name to avoid ambiguity
		should_update = False
		if value_counter[field_value] == 1:
			if field_value != name and field_value is not None:
				#Avoid "Doom (Doom)" and "Blah (None)" and such; in those cases, just leave it as "Doom" or "Blah"
				#That's not an example that happens anymore but uhh you think of a better one
				should_update = True
		elif value_counter[field_value] == len(group):
			#Field is the same across the whole group.  Need to disambiguate some
			#other way
			pass
		elif field_value != name and field_value is not None:
			#Field is different, but still requires disambiguation.  That is to say,
			#there is something else with the same field in this group, but we still
			#need to append the field to disambiguate it from other stuff
			should_update = True

		if should_update and field_value:
			if ignore_missing_values:
				#In this case, check if the other values we're disambiguating against are all None
				#Because it looks weird that way in some cases to have just Cool Game and Cool Game (Thing)
				rest_of_counter = list({k for k in value_counter.keys() if k != field_value})
				if len(rest_of_counter) == 1 and rest_of_counter[0] is None:
					return

			original_name = get_field(dup[1], 'Ambiguous-Name', disambiguity_section_name)
			update_name(dup, format_function(field_value, original_name if original_name else name) if format_function else f'({field_value})', field)

def resolve_duplicates_by_filename_tags(group: Collection[DesktopWithPath]):
	for dup in group:
		the_rest = [d for d in group if d[0] != dup[0]]
		tags = get_array(dup[1], 'Filename-Tags', junk_section_name)

		differentiator_candidates = []

		rest_tags = [get_array(rest[1], 'Filename-Tags', junk_section_name) for rest in the_rest]
		for tag in tags:
			if all(tag in rest_tag for rest_tag in rest_tags):
				continue
			if og_name := get_field(dup[1], 'Name', 'Desktop Entry'):
				if tag.lower() in og_name.lower():
					#Bit silly to add a tag that is already there from something else
					continue
			differentiator_candidates.append(tag)

		if differentiator_candidates:
			update_name(dup, ' '.join(differentiator_candidates), 'tags')

def resolve_duplicates_by_dev_status(group: Collection[DesktopWithPath]):
	for dup in group:
		tags = get_array(dup[1], 'Filename-Tags', junk_section_name)

		for tag in tags:
			tag_matches = tag.lower().startswith(('(beta', '(sample)', '(proto', '(preview', '(pre-release', '(demo', '(multiboot demo)', '(shareware', '(taikenban'))
			if tag_matches:= tag_matches or (tag.lower().startswith('(alpha') and tag[6] == ' ' and tag[7:-1].isdigit()):
				update_name(dup, '(' + tag[1:].title() if tag.islower() else tag, 'dev status')

def resolve_duplicates_by_date(group: Collection[DesktopWithPath]):
	year_counter = collections.Counter(get_field(d[1], 'Year') for d in group)
	month_counter = collections.Counter(get_field(d[1], 'Month') for d in group)
	day_counter = collections.Counter(get_field(d[1], 'Day') for d in group)
	for dup in group:
		year = get_field(dup[1], 'Year')
		month = get_field(dup[1], 'Month')
		day = get_field(dup[1], 'Day')
		if year is None or (year is None and month is None and day is None):
			continue

		disambiguator: dict[str, Optional[str]] = {'Day': None, 'Month': None, 'Year': None}
		disambiguated = False
		if year_counter[year] != len(group):
			disambiguated = True
			if year is None:
				disambiguator['Year'] = '(No year)'
			else:
				disambiguator['Year'] = year

		if month_counter[month] != len(group):
			disambiguated = True
			if month is None:
				disambiguator['Month'] = '(No month)'
			else:
				disambiguator['Month'] = month

		if day_counter[day] != len(group):
			disambiguated = True
			if day is None:
				disambiguator['Day'] = '(No day)'
			else:
				disambiguator['Day'] = day

		if disambiguated:
			#Just having the day by itself would look weird, so put the year etc in always
			year_disambig = disambiguator['Year'] if disambiguator['Year'] is not None else year
			month_disambig = disambiguator['Month'] if disambiguator['Month'] is not None else month
			day_disambig = disambiguator['Day'] if disambiguator['Day'] is not None else day
			date_string: str
			if disambiguator['Month'] or disambiguator['Day']:
				date_string = f'{day_disambig} {month_disambig} {year_disambig}'
			else:
				if disambiguator['Year'] is None:
					continue
				date_string = year_disambig

			update_name(dup, '(' + date_string + ')', 'date')

def resolve_duplicates(group: Collection[DesktopWithPath], method: str, format_function: Optional[FormatFunction]=None, ignore_missing_values: bool=False, field_section: str=metadata_section_name):
	if method == 'tags':
		resolve_duplicates_by_filename_tags(group)
	elif method == 'dev-status':
		resolve_duplicates_by_dev_status(group)
	elif method == 'date':
		resolve_duplicates_by_date(group)
	else:
		resolve_duplicates_by_metadata(group, method, format_function, ignore_missing_values, field_section)

def fix_duplicate_names(method: str, format_function: Optional[FormatFunction]=None, ignore_missing_values: bool=False, field_section: str=metadata_section_name):
	files = [(path, get_desktop(path)) for path in main_config.output_folder.iterdir()]
	if method == 'dev-status':
		resolve_duplicates_by_dev_status(files)
		return

	#TODO: Handle this null check properly, it _should_ be impossible for Desktop Entry to not exist in a .desktop file, but that doesn't stop some joker putting them in there
	#Why did I call the variable "f"? Oh well
	keyfunc: Callable[[DesktopWithPath], str] = (lambda f: cast(str, get_field(f[1], 'Name', 'Desktop Entry')).lower()) \
		if method == 'check' \
		else (lambda f: normalize_name(cast(str, get_field(f[1], 'Name', 'Desktop Entry')), care_about_numerals=True))
	files.sort(key=keyfunc)
	duplicates: dict[str, list[DesktopWithPath]] = {}
	for key, group in itertools.groupby(files, key=keyfunc):
		g = list(group)
		if len(g) > 1:
			duplicates[key] = g

	for k, v in duplicates.items():
		if method == 'check':
			print('Duplicate name still remains: ', k, [(d[1][junk_section_name].get('Original-Name', '<no Original-Name>') if junk_section_name in d[1] else '<no junk section>') for d in v])
		else:
			resolve_duplicates(v, method, format_function, ignore_missing_values, field_section)

def revision_disambiguate(rev: str, _) -> Optional[str]:
	if rev == '0':
		return None

	if rev.isdigit() and len(rev) == 1:
		return '(Rev ' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[int(rev) - 1] + ')'

	return f'(Rev {rev})'

def arcade_system_disambiguate(arcade_system: Optional[str], name: str) -> Optional[str]:
	if arcade_system == name + ' Hardware':
		#Avoid "Cool Game (Cool Game Hardware)" where there exists a "Cool Game (Interesting Alternate Hardware)"
		return None
	return f'({arcade_system})'

def reambiguate() -> None:
	#This seems counter-intuitive, but if we're not doing a full rescan, we want to do this before disambiguating again or else it gets weird
	output_folder = main_config.output_folder
	for path in output_folder.iterdir():
		desktop = configparser.ConfigParser(interpolation=None)
		desktop.optionxform = str #type: ignore[assignment]
		desktop.read(path)
		desktop_entry = desktop['Desktop Entry']
		if disambiguity_section_name not in desktop:
			#If name wasn't ambiguous to begin with, we don't need to worry about it
			continue

		disambiguity_section = desktop[disambiguity_section_name]
		if 'Disambiguator' in disambiguity_section:
			del disambiguity_section['Disambiguator']
		if 'Disambiguation-Method' in disambiguity_section:
			del disambiguity_section['Disambiguation-Method']
		if 'Ambiguous-Name' in disambiguity_section:
			desktop_entry['Name'] = disambiguity_section['Ambiguous-Name']
			del disambiguity_section['Ambiguous-Name']
		del desktop[disambiguity_section_name]

		with path.open('wt', encoding='utf-8') as f:
			desktop.write(f)

def disambiguate_names() -> None:
	time_started = time.perf_counter()

	if not main_config.full_rescan:
		reambiguate()

	fix_duplicate_names('Platform')
	fix_duplicate_names('Type', field_section=id_section_name)
	fix_duplicate_names('dev-status')
	if not main_config.simple_disambiguate:
		fix_duplicate_names('Arcade-System', arcade_system_disambiguate)
		fix_duplicate_names('Media-Type', ignore_missing_values=True)
		fix_duplicate_names('Is-Colour', lambda is_colour, _: None if is_colour in {False, 'No'} else '(Colour)')
		fix_duplicate_names('Regions', lambda regions, _: f"({regions.replace(';', ', ') if regions else None})", ignore_missing_values=True)
		fix_duplicate_names('Region-Code')
		fix_duplicate_names('TV-Type', ignore_missing_values=True)
		fix_duplicate_names('Version')
		fix_duplicate_names('Revision', revision_disambiguate)
		fix_duplicate_names('Languages', lambda languages, _: f"({languages.replace(';', ', ')})", ignore_missing_values=True)
		#fix_duplicate_names('date', ignore_missing_values=True)
		fix_duplicate_names('Publisher', ignore_missing_values=True)
		fix_duplicate_names('Developer', ignore_missing_values=True)
	fix_duplicate_names('tags')
	fix_duplicate_names('Extension', '(.{0})'.format, ignore_missing_values=True) #pylint: disable=consider-using-f-string #I want the bound method actually
	fix_duplicate_names('Executable-Name', ignore_missing_values=True)
	if main_config.debug:
		fix_duplicate_names('check')

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Name disambiguation finished in', str(datetime.timedelta(seconds=time_ended - time_started)))