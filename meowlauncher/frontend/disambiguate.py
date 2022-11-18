#!/usr/bin/env python3

import collections
import datetime
import itertools
import logging
import time
from collections.abc import Callable, Collection, Iterable, MutableMapping
from pathlib import Path
from shutil import copymode
from typing import TYPE_CHECKING, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.output.desktop_files import (id_section_name,
                                               info_section_name,
                                               junk_section_name,
                                               section_prefix)
from meowlauncher.util.desktop_files import get_array, get_desktop, get_field
from meowlauncher.util.io_utils import ensure_unique_path, sanitize_name
from meowlauncher.util.name_utils import normalize_name
from meowlauncher.util.utils import NoNonsenseConfigParser

if TYPE_CHECKING:
	import configparser

logger = logging.getLogger(__name__)
FormatFunction = Callable[[str, str], str | None]
DesktopWithPath = tuple[Path, 'configparser.RawConfigParser']

disambiguity_section_name = section_prefix + 'Disambiguity'

def _update_name(desktop: DesktopWithPath, disambiguator: str | None, disambiguation_method: str) -> None:
	#TODO: Encapsulate accessing .desktop files better, this module shouldn't know about them
	if not disambiguator:
		return
	desktop_entry = desktop[1]['Desktop Entry']
	if disambiguity_section_name not in desktop[1]:
		desktop[1].add_section(disambiguity_section_name)
	disambiguity_section = desktop[1][disambiguity_section_name]

	logger.debug('Disambiguating %s with %s using %s', desktop_entry['Name'], disambiguator, disambiguation_method)
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

	new_path = ensure_unique_path(desktop[0].with_stem(sanitize_name(desktop_entry['Name'])))
	with new_path.open('wt', encoding='utf-8') as f:
		desktop[1].write(f)
	if new_path != desktop[0]:
		copymode(desktop[0], new_path)
		desktop[0].unlink()

def _resolve_duplicates_by_info(group: Collection[DesktopWithPath], field: str, format_function: FormatFunction | None=None, ignore_missing_values: bool=False, field_section: str=info_section_name) -> None:
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
				rest_of_counter = tuple({k for k in value_counter.keys() if k != field_value})
				if len(rest_of_counter) == 1 and rest_of_counter[0] is None:
					return

			original_name = get_field(dup[1], 'Ambiguous-Name', disambiguity_section_name)
			_update_name(dup, format_function(field_value, original_name if original_name else name) if format_function else f'({field_value})', field)

def _resolve_duplicates_by_filename_tags(group: Collection[DesktopWithPath]) -> None:
	for dup in group:
		the_rest = tuple(d for d in group if d[0] != dup[0])
		tags = get_array(dup[1], 'Filename-Tags', junk_section_name)

		differentiator_candidates = []

		rest_tags = tuple(get_array(rest[1], 'Filename-Tags', junk_section_name) for rest in the_rest)
		for tag in tags:
			if all(tag in rest_tag for rest_tag in rest_tags):
				continue
			if og_name := get_field(dup[1], 'Name', 'Desktop Entry'):
				if tag.lower() in og_name.lower():
					#Bit silly to add a tag that is already there from something else
					continue
			differentiator_candidates.append(tag)

		if differentiator_candidates:
			_update_name(dup, ' '.join(differentiator_candidates), 'tags')

def _resolve_duplicates_by_dev_status(group: Iterable[DesktopWithPath]) -> None:
	for dup in group:
		tags = get_array(dup[1], 'Filename-Tags', junk_section_name)

		for tag in tags:
			tag_matches = tag.lower().startswith(('(beta', '(sample)', '(proto', '(preview', '(pre-release', '(demo', '(multiboot demo)', '(shareware', '(taikenban'))
			if tag_matches:= tag_matches or (tag.lower().startswith('(alpha') and tag[6] == ' ' and tag[7:-1].isdigit()):
				_update_name(dup, '(' + tag[1:].title() if tag.islower() else tag, 'dev status')

def _resolve_duplicates_by_date(group: Collection[DesktopWithPath]) -> None:
	year_counter = collections.Counter(get_field(d[1], 'Year') for d in group)
	month_counter = collections.Counter(get_field(d[1], 'Month') for d in group)
	day_counter = collections.Counter(get_field(d[1], 'Day') for d in group)
	for dup in group:
		year = get_field(dup[1], 'Year')
		month = get_field(dup[1], 'Month')
		day = get_field(dup[1], 'Day')
		if year is None and month is None and day is None:
			continue

		disambiguator: MutableMapping[str, str | None] = {'Day': None, 'Month': None, 'Year': None}
		#TODO: Use a dataclass there
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
				if not year_disambig:
					return
				date_string = year_disambig

			_update_name(dup, '(' + date_string + ')', 'date')

def _resolve_duplicates(group: Collection[DesktopWithPath], method: str, format_function: FormatFunction | None=None, ignore_missing_values: bool=False, field_section: str=info_section_name) -> None:
	if method == 'tags':
		_resolve_duplicates_by_filename_tags(group)
	elif method == 'dev-status':
		_resolve_duplicates_by_dev_status(group)
	elif method == 'date':
		_resolve_duplicates_by_date(group)
	else:
		_resolve_duplicates_by_info(group, method, format_function, ignore_missing_values, field_section)

def _fix_duplicate_names(method: str, format_function: FormatFunction | None=None, ignore_missing_values: bool=False, field_section: str=info_section_name) -> None:
	files = ((path, get_desktop(path)) for path in main_config.output_folder.iterdir())
	if method == 'dev-status':
		_resolve_duplicates_by_dev_status(files)
		return

	#TODO: Handle this null check properly, it _should_ be impossible for Desktop Entry to not exist in a .desktop file, but that doesn't stop some joker putting them in there
	#Why did I call the variable "f"? Oh well
	keyfunc: Callable[[DesktopWithPath], str] = (lambda f: cast(str, get_field(f[1], 'Name', 'Desktop Entry')).lower()) \
		if method == 'check' \
		else (lambda f: normalize_name(cast(str, get_field(f[1], 'Name', 'Desktop Entry')), care_about_numerals=True))
	duplicates = {}
	#TODO: Is using keyfunc twice there really needed? Is that how that works?
	for key, group in itertools.groupby(sorted(files, key=keyfunc), key=keyfunc):
		g = tuple(group)
		if len(g) > 1:
			duplicates[key] = g

	for k, v in duplicates.items():
		if method == 'check':
			print('Duplicate name still remains: ', k, tuple(get_field(d[1], 'Original-Name', junk_section_name) for d in v))
		else:
			_resolve_duplicates(v, method, format_function, ignore_missing_values, field_section)

def _revision_disambiguate(rev: str, _) -> str | None:
	if rev == '0':
		return None

	if rev.isdigit() and len(rev) == 1:
		return '(Rev ' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[int(rev) - 1] + ')'

	return f'(Rev {rev})'

def _arcade_system_disambiguate(arcade_system: str | None, name: str) -> str | None:
	if arcade_system == name + ' Hardware':
		#Avoid "Cool Game (Cool Game Hardware)" where there exists a "Cool Game (Interesting Alternate Hardware)"
		return None
	return f'({arcade_system})'

def _reambiguate() -> None:
	#This seems counter-intuitive, but if we're not doing a full rescan, we want to do this before disambiguating again or else it gets weird
	output_folder = main_config.output_folder
	for path in output_folder.iterdir():
		desktop = NoNonsenseConfigParser()
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
		_reambiguate()

	_fix_duplicate_names('Platform')
	_fix_duplicate_names('Type', field_section=id_section_name)
	_fix_duplicate_names('dev-status')
	if not main_config.simple_disambiguate:
		_fix_duplicate_names('Arcade-System', _arcade_system_disambiguate)
		_fix_duplicate_names('Media-Type', ignore_missing_values=True)
		_fix_duplicate_names('Is-Colour', lambda is_colour, _: None if is_colour in {False, 'No'} else '(Colour)')
		_fix_duplicate_names('Regions', lambda regions, _: f"({regions.replace(';', ', ') if regions else None})", ignore_missing_values=True)
		_fix_duplicate_names('Region-Code')
		_fix_duplicate_names('TV-Type', ignore_missing_values=True)
		_fix_duplicate_names('Version')
		_fix_duplicate_names('Revision', _revision_disambiguate)
		_fix_duplicate_names('Languages', lambda languages, _: f"({languages.replace(';', ', ')})", ignore_missing_values=True)
		#fix_duplicate_names('date', ignore_missing_values=True)
		_fix_duplicate_names('Publisher', ignore_missing_values=True)
		_fix_duplicate_names('Developer', ignore_missing_values=True)
	_fix_duplicate_names('tags')
	_fix_duplicate_names('Extension', '(.{0})'.format, ignore_missing_values=True) #pylint: disable=consider-using-f-string #I want the bound method actually
	_fix_duplicate_names('Executable-Name', ignore_missing_values=True)
	_fix_duplicate_names('check')

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Name disambiguation finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
