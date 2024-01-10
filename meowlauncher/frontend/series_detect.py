#!/usr/bin/env python3
import contextlib
import re
from collections.abc import Collection, Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from meowlauncher.config import main_config
from meowlauncher.data.series_detect.series_detect_overrides import series_overrides
from meowlauncher.output.desktop_files import info_section_name, section_prefix
from meowlauncher.util.desktop_files import get_desktop, get_field
from meowlauncher.util.name_utils import chapter_matcher, convert_roman_numerals_in_title
from meowlauncher.util.utils import convert_roman_numeral, remove_capital_article

if TYPE_CHECKING:
	from configparser import RawConfigParser

#The reason why we don't simply find this at the time of the launcher is so that we can try using the serieses present in other launchers that have been already generated as a hint for what serieses exist and hence what we should try and detect, or something like that I guess

SeriesWithSeriesIndex = tuple[str | None, int | str | None]

_probably_not_series_index_threshold = 20
#Assume that a number over this is probably not referring to the nth or higher entry in the series, but is probably just any old number that means something else
_probably_not_a_series_index = {'XXX', '007', 'DX', 'XL', 'V3'} #V3 shouldn't be detected as some weird mix of Roman and Arabic numerals anyway…
#These generally aren't entries in a series, and are just there at the end
_suffixes_not_part_of_series = ('64', 'Advance', '3D', 'DS')
#If these are appended to a series it's just part of that same series and not a new one, if that makes sense, see series_match

_series_matcher = re.compile(r'(?P<Series>.+?)\b\s+#?(?P<Number>\d{1,3}|[IVXLCDM]+?)\b(?:\s|$)')
#"Phase", "Disk" might also be chapter marker things?
_subtitle_splitter = re.compile(r'\s*(?:\s+-\s+|:\s+|\s+\/\s+)')
_blah_in_1_matcher = re.compile(r'.+\s+in\s+1')

def _get_name_chunks(name: str) -> Sequence[str]:
	#TODO: Rewrite this to use a nested comprehension, my head asplode
	name_chunks = tuple(_blah_in_1_matcher.sub('', chunk) for chunk in _subtitle_splitter.split(name))
	name_chunks = tuple(chunk for chunk in name_chunks if chunk)
	return name_chunks

def find_series_from_game_name(name: str) -> SeriesWithSeriesIndex:
	if name in series_overrides:
		return series_overrides[name]
	name_chunks = _get_name_chunks(name)
	if not name_chunks:
		return None, None
	name_chunk = name_chunks[0]
	series_match = _series_matcher.fullmatch(name_chunk)
	if series_match:
		series_name = series_match['Series']
		series_name.removeprefix('The ')
		series_name = remove_capital_article(series_name)
		number_match = series_match['Number']
		if number_match in _probably_not_a_series_index:
			return None, None

		try:
			number = int(number_match)
		except ValueError:
			try:
				number = convert_roman_numeral(number_match)
			except ValueError:
				#Not actually a roman numeral, chief
				return None, None

		if number > _probably_not_series_index_threshold:
			return None, None
		return chapter_matcher.sub('', series_name).rstrip(), number
	return None, None

def _does_series_match(name_to_match: str, existing_series: str) -> bool:
	name_to_match = name_to_match.removeprefix('The ').lower()
	existing_series = existing_series.lower()

	for suffix in _suffixes_not_part_of_series:
		name_to_match = name_to_match.removesuffix(f' {suffix}')

	#Might also want to remove punctuation

	return name_to_match == existing_series

def _find_series_name_by_subtitle(name: str, existing_serieses: Collection[str], force: bool=False) -> SeriesWithSeriesIndex:
	name_chunks = _get_name_chunks(name)
	if not name_chunks:
		return None, None
	name_chunk = name_chunks[0]

	match = next((existing for existing in existing_serieses if _does_series_match(name_chunk, existing)), None) if not force else name_chunk

	if match:
		series = remove_capital_article(match)
		index = name_chunks[1] if len(name_chunks) > 1 else '1'
		return series, index
	return None, None

def _get_usable_name(desktop: 'RawConfigParser') -> str:
	sort_name = get_field(desktop, 'Sort-Name')
	if sort_name:
		return sort_name
	#Note that this is before disambiguate.py, so we don't need to worry about using Ambiguous-Name from disambiguation section
	#Name _must_ exist in a .desktop file... although this is platform-specific, come to think of it, maybe I should put stuff in launchers.py to abstract getting name/exec/icon/etc
	name = get_field(desktop, 'Name', 'Desktop Entry')
	assert name, 'What the heck get_usable_name encountered a desktop with no name'
	return name

def _add_series(desktop: 'RawConfigParser', path: Path, series: str | None, series_index: str | int | None=None) -> None:
	#TODO: Encapsulate this better
	info_section_with_prefix = section_prefix + info_section_name
	if info_section_with_prefix not in desktop:
		desktop.add_section(info_section_with_prefix)
	if series is not None:
		desktop[info_section_with_prefix]['Series'] = series
	if series_index is not None:
		desktop[info_section_with_prefix]['Series-Index'] = str(series_index)
	with path.open('wt', encoding='utf-8') as f:
		desktop.write(f)

def _detect_series(desktop: 'RawConfigParser', path: Path) -> None:
	name = _get_usable_name(desktop)
	series, series_index = find_series_from_game_name(name)
	if series:
		_add_series(desktop, path, series, series_index)

def _find_existing_serieses() -> Collection[str]:
	serieses = set()
	for path in main_config.output_folder.iterdir():
		desktop = get_desktop(path)

		series = get_field(desktop, 'Series')
		if series:
			serieses.add(series)

	return serieses

def _detect_series_by_subtitle(desktop: 'RawConfigParser', path: Path, existing: Collection[str]) -> None:
	name = _get_usable_name(desktop)
	series, index = _find_series_name_by_subtitle(name, existing)
	if series:
		_add_series(desktop, path, series, index)

def _force_add_series_with_index(desktop: 'RawConfigParser', path: Path, existing: Collection[str]) -> None:
	name = _get_usable_name(desktop)
	series, _ = _find_series_name_by_subtitle(name, existing, force=True)
	if series:
		_add_series(desktop, path, series)

def _get_series_from_whole_thing(series: str, whole_name: str) -> str:
	rest = whole_name.removeprefix(series).strip()
	rest = chapter_matcher.sub('', rest).strip()

	if rest:
		if rest not in _probably_not_a_series_index:
			#Don't convert things that aren't actually roman numerals
			with contextlib.suppress(ValueError):
				rest = str(convert_roman_numeral(rest))
			return convert_roman_numerals_in_title(rest)
		return rest
	
	return '1'

def _detect_series_index_for_things_with_series() -> None:
	for path in main_config.output_folder.iterdir():
		desktop = get_desktop(path)

		existing_series = get_field(desktop, 'Series')
		if not existing_series:
			continue

		if get_field(desktop, 'Series-Index'):
			continue

		name = _get_usable_name(desktop)
		name.removeprefix('The ')
		name_chunks = _get_name_chunks(name)
		if len(name_chunks) > 1:
			if name_chunks[0] == existing_series:
				series_index = name_chunks[1]
				series_index = chapter_matcher.sub('', series_index).strip()
				series_index = convert_roman_numerals_in_title(series_index)
				_add_series(desktop, path, None, series_index)
			elif name_chunks[0].startswith(existing_series):
				series_index = _get_series_from_whole_thing(existing_series, name_chunks[0].strip())
				_add_series(desktop, path, None, series_index)
			else:
				#This handles the case where it's like "Blah Bloo - Chapter Zabityzoo" but the series in Steam is listed as some abbreviation/alternate spelling of Blah Bloo so it doesn't get picked up otherwise
				chapter_index = None
				try:
					chapter_index = name.index('Ch.') + len('Ch.')
				except ValueError:
					chapter_matcherooni = chapter_matcher.search(name)
					if chapter_matcherooni:
						chapter_index = chapter_matcherooni.end()
				if chapter_index is not None:
					#Could also do just a word match starting from chapter_index I guess
					_add_series(desktop, path, None, convert_roman_numerals_in_title(name[chapter_index:].strip()))
		elif len(name_chunks) == 1:
			if name_chunks[0].startswith(existing_series):
				_add_series(desktop, path, None, _get_series_from_whole_thing(existing_series, name_chunks[0].strip()))

def _iter_existing_seriesless_launchers() -> Iterator[tuple['RawConfigParser', Path]]:
	for path in main_config.output_folder.iterdir():
		desktop = get_desktop(path)

		if get_field(desktop, 'Series'):
			#Don't need to do this if it already exists
			continue

		yield desktop, path

def detect_series_for_all_desktops() -> None:
	for desktop, path in _iter_existing_seriesless_launchers():
		_detect_series(desktop, path)
	existing = _find_existing_serieses()
	for desktop, path in _iter_existing_seriesless_launchers():
		_detect_series_by_subtitle(desktop, path, existing)

	for desktop, path in _iter_existing_seriesless_launchers():
		if get_field(desktop, 'Series-Index'):
			_force_add_series_with_index(desktop, path, existing)

	_detect_series_index_for_things_with_series()
