#!/usr/bin/env python3

import collections
import datetime
import itertools
import logging
import time
from collections.abc import Callable, Collection, Iterable, MutableMapping
from pathlib import Path

from meowlauncher.config.main_config import main_config
from meowlauncher.output.desktop_files import (id_section_name,
                                               junk_section_name,
                                               section_prefix)
from meowlauncher.util.desktop_files import get_array, get_field
from meowlauncher.util.io_utils import ensure_unique_path, sanitize_name
from meowlauncher.util.name_utils import normalize_name
from meowlauncher.util.utils import NoNonsenseConfigParser

logger = logging.getLogger(__name__)
FormatFunction = Callable[[str, str], str | None]

class DesktopWithPath():
	"""This is not a read only class, this modifies self.parser when it is created, although it does not write to it until update is called
	TODO: Encapsulate accessing .desktop files better, this module shouldn't know about them (parser should be some kind of base class for output files)"""
	def __init__(self, path: Path) -> None:
		self.path = path
		self.parser = NoNonsenseConfigParser()
		self.parser.read(self.path)
		self.desktop_entry = self.parser['Desktop Entry']
		self.old_name = self.desktop_entry['Name']
		if disambiguity_section_name in self.parser:
			disambiguity_section = self.parser[disambiguity_section_name]
			self.new_name = disambiguity_section['Ambiguous-Name']
			disambiguity_section = self.parser[disambiguity_section_name]
			if 'Disambiguator' in disambiguity_section:
				del disambiguity_section['Disambiguator']
			if 'Disambiguation-Method' in disambiguity_section:
				del disambiguity_section['Disambiguation-Method']
			if 'Ambiguous-Name' in disambiguity_section:
				del disambiguity_section['Ambiguous-Name']
			del self.parser[disambiguity_section_name]
		else:
			self.new_name = self.old_name
		self.disambiguators: list[tuple[str, str]] = []

	def update_name(self) -> None:
		if not self.disambiguators:
			return
		self.parser.add_section(disambiguity_section_name)
		disambiguity_section = self.parser[disambiguity_section_name]
		disambiguity_section['Ambiguous-Name'] = self.old_name
		disambiguity_section['Disambiguation-Method'] = self.disambiguators[0][0]
		disambiguity_section['Disambiguator'] = self.disambiguators[0][1]
		
		if len(self.disambiguators) > 1:
			for disambiguation_method, disambiguator in self.disambiguators[1:]:
				disambiguity_section['Disambiguation-Method'] += ';' + disambiguation_method
				disambiguity_section['Disambiguator'] += ';' + disambiguator

		self.parser['Desktop Entry']['Name'] = self.new_name
		with self.path.open('wt', encoding='utf-8') as f:
			self.parser.write(f)
		new_path = self.path.with_stem(sanitize_name(self.new_name))
		self.path.rename(ensure_unique_path(new_path))

disambiguity_section_name = section_prefix + 'Disambiguity'

def _update_name(desktop: DesktopWithPath, disambiguator: str | None, disambiguation_method: str) -> None:
	if not disambiguator:
		return
	logger.debug('Disambiguating %s with %s using %s', desktop.old_name, disambiguator, disambiguation_method)
	desktop.new_name += f' {disambiguator}'
	desktop.disambiguators.append((disambiguation_method, disambiguator))

def _resolve_duplicates_by_info(group: Collection[DesktopWithPath], field: str, format_function: FormatFunction | None=None, ignore_missing_values: bool=False, field_getter: 'Callable[[DesktopWithPath], str | None] | None'=None) -> None:
	value_counter = collections.Counter(field_getter(d) if field_getter else get_field(d.parser, field) for d in group)
	for dup in group:
		field_value = field_getter(dup) if field_getter else get_field(dup.parser, field)
		name = dup.new_name

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

			_update_name(dup, format_function(field_value, dup.new_name) if format_function else f'({field_value})', field)

def _resolve_duplicates_by_filename_tags(group: Collection[DesktopWithPath]) -> None:
	for dup in group:
		the_rest = tuple(d for d in group if d.path != dup.path)
		tags = get_array(dup.parser, 'Filename-Tags', junk_section_name)

		differentiator_candidates = []

		rest_tags = tuple(get_array(rest.parser, 'Filename-Tags', junk_section_name) for rest in the_rest)
		for tag in tags:
			if all(tag in rest_tag for rest_tag in rest_tags):
				continue
			if any(tag.lower() == d[1].lower() for d in dup.disambiguators):
				#Bit silly to add a tag that is already there from something else
				continue
			differentiator_candidates.append(tag)

		if differentiator_candidates:
			_update_name(dup, ' '.join(differentiator_candidates), 'tags')

def _resolve_duplicates_by_dev_status(group: Iterable[DesktopWithPath]) -> None:
	for dup in group:
		tags = get_array(dup.parser, 'Filename-Tags', junk_section_name)
		for tag in tags:
			tag_matches = tag.lower().startswith(('(beta', '(sample)', '(proto', '(preview', '(pre-release', '(demo', '(multiboot demo)', '(shareware', '(taikenban'))
			if tag_matches:= tag_matches or (tag.lower().startswith('(alpha') and tag[6] == ' ' and tag[7:-1].isdigit()):
				_update_name(dup, '(' + tag[1:].title() if tag.islower() else tag, 'dev status')

def _resolve_duplicates_by_date(group: Collection[DesktopWithPath]) -> None:
	year_counter = collections.Counter(get_field(d.parser, 'Year') for d in group)
	month_counter = collections.Counter(get_field(d.parser, 'Month') for d in group)
	day_counter = collections.Counter(get_field(d.parser, 'Day') for d in group)
	for dup in group:
		year = get_field(dup.parser, 'Year')
		month = get_field(dup.parser, 'Month')
		day = get_field(dup.parser, 'Day')
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

def _resolve_duplicates(group: Collection[DesktopWithPath], method: str, format_function: FormatFunction | None=None, ignore_missing_values: bool=False, field_getter: 'Callable[[DesktopWithPath], str | None] | None'=None) -> None:
	if method == 'tags':
		_resolve_duplicates_by_filename_tags(group)
	elif method == 'dev-status':
		_resolve_duplicates_by_dev_status(group)
	elif method == 'date':
		_resolve_duplicates_by_date(group)
	else:
		_resolve_duplicates_by_info(group, method, format_function, ignore_missing_values, field_getter)

def _fix_duplicate_names(desktops: Collection[DesktopWithPath], method: str, format_function: FormatFunction | None=None, ignore_missing_values: bool=False, field_getter: 'Callable[[DesktopWithPath], str | None] | None'=None) -> None:
	if method == 'dev-status':
		_resolve_duplicates_by_dev_status(desktops)
		return

	keyfunc: Callable[[DesktopWithPath], str] = (lambda d: d.new_name.lower()) if method == 'check' else (lambda d: normalize_name(d.new_name, care_about_numerals=True))
	duplicates: dict[str, Collection[DesktopWithPath]] = {}
	#Group into desktops that all have the same name
	#Keep doing this with each call to this/with each disambiguation method, until at the end we have disambiguated things as much as possible
	for key, group in itertools.groupby(sorted(desktops, key=keyfunc), key=keyfunc):
		g = tuple(group)
		if len(g) > 1:
			duplicates[key] = g

	for k, v in duplicates.items():
		if method == 'check':
			logger.debug('Duplicate name still remains: %s %s', k, list(d.new_name for d in v))
		else:
			_resolve_duplicates(v, method, format_function, ignore_missing_values, field_getter)

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

def _platform_type_disambiguate(d: DesktopWithPath) -> str | None:
	typey = get_field(d.parser, 'Type', id_section_name)
	return get_field(d.parser, 'Platform') if typey == 'ROMs' else typey
		
def disambiguate_names() -> None:
	time_started = time.perf_counter()

	desktops = [DesktopWithPath(path) for path in main_config.output_folder.iterdir()]
	
	_fix_duplicate_names(desktops, 'Platform/Type', field_getter=_platform_type_disambiguate)
	_fix_duplicate_names(desktops, 'dev-status')
	if not main_config.simple_disambiguate:
		_fix_duplicate_names(desktops, 'Arcade-System', _arcade_system_disambiguate)
		_fix_duplicate_names(desktops, 'Media-Type', ignore_missing_values=True)
		_fix_duplicate_names(desktops, 'Is-Colour', lambda is_colour, _: None if is_colour in {False, 'No'} else '(Colour)')
		_fix_duplicate_names(desktops, 'Regions', lambda regions, _: f"({regions.replace(';', ', ') if regions else None})", ignore_missing_values=True)
		_fix_duplicate_names(desktops, 'Region-Code')
		_fix_duplicate_names(desktops, 'TV-Type', ignore_missing_values=True)
		_fix_duplicate_names(desktops, 'Version')
		_fix_duplicate_names(desktops, 'Revision', _revision_disambiguate)
		_fix_duplicate_names(desktops, 'Languages', lambda languages, _: f"({languages.replace(';', ', ')})", ignore_missing_values=True)
		#fix_duplicate_names('date', ignore_missing_values=True)
		_fix_duplicate_names(desktops, 'Publisher', ignore_missing_values=True)
		_fix_duplicate_names(desktops, 'Developer', ignore_missing_values=True)
	_fix_duplicate_names(desktops, 'tags')
	_fix_duplicate_names(desktops, 'Platform') #If Platform/Type doesn't do it, this would pick up platforms for ScummVM/Steam/whatever
	_fix_duplicate_names(desktops, 'Extension', '(.{0})'.format, ignore_missing_values=True) #pylint: disable=consider-using-f-string #I want the bound method actually
	_fix_duplicate_names(desktops, 'Executable-Name', ignore_missing_values=True)

	for desktop in desktops:
		desktop.update_name()
	_fix_duplicate_names(desktops, 'check')

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Name disambiguation finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
