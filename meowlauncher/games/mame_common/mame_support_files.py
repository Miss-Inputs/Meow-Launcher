import functools
import os
import xml.etree.ElementTree as ElementTree
from typing import Optional

from meowlauncher.metadata import Metadata
from meowlauncher.util.region_info import (Language,
                                           get_language_by_english_name)

from .mame_helpers import get_mame_ui_config

#TODO: Ideally this shouldn't require a MAMEConfiguration, and you should be able to manually specify the paths to things (in case you have some other arcade emulator or sources of arcade things but not MAME)

def get_history_xml() -> Optional[ElementTree.ElementTree]:
	dat_paths = get_mame_ui_config().get('historypath')
	if not dat_paths:
		return None
	for dat_path in dat_paths:
		historypath = os.path.join(dat_path, 'history.xml')
		#Yeah soz not gonna bother parsing the old history format
		try:
			return ElementTree.parse(historypath)
		except FileNotFoundError:
			continue
	return None

def get_histories() -> tuple[dict[str, Optional[str]], dict[str, dict[str, Optional[str]]]]:
	system_histories: dict[str, Optional[str]] = {}
	software_histories: dict[str, dict[str, Optional[str]]] = {}

	xml = get_history_xml()
	if not xml:
		return {}, {}
	for entry in xml.findall('entry'):
		text = entry.findtext('text')

		systems = entry.find('systems')
		if systems is not None:
			for system in systems.findall('system'):
				system_histories[system.attrib['name']] = text
		softwares = entry.find('software')
		if softwares is not None:
			for item in softwares.findall('item'):
				if item.attrib['list'] not in software_histories:
					software_histories[item.attrib['list']] = {}
				software_histories[item.attrib['list']][item.attrib['name']] = text
	return system_histories, software_histories

def add_history(metadata: Metadata, machine_or_softlist: str, software_name: Optional[str]=None) -> None:
	if not hasattr(add_history, 'systems') or not hasattr(add_history, 'softwares'):
		add_history.systems, add_history.softwares = get_histories() #type: ignore[attr-defined]

	if software_name:
		softlist = add_history.softwares.get(machine_or_softlist) #type: ignore[attr-defined]
		if not softlist:
			return
		history = softlist.get(software_name)
	else:
		history = add_history.systems.get(machine_or_softlist) #type: ignore[attr-defined]

	#history = get_history(machine_or_softlist, software_name)
	if not history:
		return

	#Line 0 is always the "Arcade video game published 999 years ago" stuff… actually it is not always there
	#Line 2 is always copyright
	#Line 1 and 3 are blank lines
	lines = [line.strip() for line in history.strip().splitlines()]
	description_start = 0
	if '(c)' in lines[0]:
		description_start = 2
	if '(c)' in lines[2]:
		description_start = 4

	cast_start = None
	technical_start = None
	trivia_start = None
	updates_start = None
	scoring_start = None
	tips_and_tricks_start = None
	series_start = None
	staff_start = None
	ports_start = None
	end_line = len(lines) - 1
	for i, line in enumerate(lines):
		if line in ('- CAST OF CHARACTERS -', '- CAST OF ELEMENTS -'):
			#I think they are the same thing but only one will appear
			cast_start = i
		elif line == '- TECHNICAL -':
			technical_start = i
		elif line == '- TRIVIA -':
			trivia_start = i
		elif line == '- UPDATES -':
			updates_start = i
		elif line == '- SCORING -':
			scoring_start = i
		elif line == '- TIPS AND TRICKS -':
			tips_and_tricks_start = i
		elif line == '- SERIES -':
			series_start = i
		elif line == '- STAFF -':
			staff_start = i
		elif line == '- PORTS -':
			ports_start = i
		elif line == '- CONTRIBUTE -':
			end_line = i #We don't care about things after this
		#elif len(line) > 4 and line.startswith('-') and line.endswith('-') and line[2:-2].isupper():
		#	print('Hmm', machine_or_softlist, software_name, 'has a new section', line)
	
	sections = [description_start, cast_start, technical_start, trivia_start, updates_start, scoring_start, tips_and_tricks_start, series_start, staff_start, ports_start, end_line]
	description_end = next(section for section in sections[1:] if section)
	if description_end - 1 > description_start:
		description = '\n'.join(lines[description_start:description_end])
		if 'Description' in metadata.descriptions:
			metadata.descriptions['History-Description'] = description
		else:
			metadata.descriptions['Description'] = description
	
	if technical_start:
		technical_end = next(section for section in sections[3:] if section)
		technical = '\n'.join(lines[technical_start + 1: technical_end])
		metadata.descriptions['Technical'] = technical
	if trivia_start:
		trivia_end = next(section for section in sections[4:] if section)
		trivia = '\n'.join(lines[trivia_start + 1: trivia_end])
		metadata.descriptions['Trivia'] = trivia
	if tips_and_tricks_start:
		tips_and_tricks_end = next(section for section in sections[7:] if section)
		tips_and_tricks = '\n'.join(lines[tips_and_tricks_start + 1: tips_and_tricks_end])
		metadata.descriptions['Tips-And-Tricks'] = tips_and_tricks
	if updates_start:
		updates_end = next(section for section in sections[5:] if section)
		updates = '\n'.join(lines[updates_start + 1: updates_end])
		metadata.descriptions['Updates'] = updates

def get_mame_categories_folders() -> list[str]:
	ui_config = get_mame_ui_config()
	return ui_config.get('categorypath', [])

@functools.cache
def get_mame_folder(name: str) -> dict[str, list[str]]:
	category_folders = get_mame_categories_folders()
	if not category_folders:
		return {}

	d: dict[str, list[str]] = {}
	for folder in category_folders:
		cat_path = os.path.join(folder, name + '.ini')
		try:
			with open(cat_path, 'rt') as f:
				current_section = None
				for line in f:
					line = line.strip()
					#Don't need to worry about FOLDER_SETTINGS or ROOT_FOLDER sections though I guess this code is gonna put them in there
					if line.startswith(';'):
						continue
					if line.startswith('['):
						current_section = line[1:-1]
					elif current_section:
						if current_section not in d:
							d[current_section] = []
						d[current_section].append(line)
						
		except FileNotFoundError:
			pass
	return d

@functools.cache
def get_machine_folder(basename: str, folder_name: str) -> Optional[list[str]]:
	folder = get_mame_folder(folder_name)
	if not folder:
		return None
	return [section for section, names in folder.items() if basename in names]

def get_category(basename: str) -> tuple[Optional[str], str, str, bool]:
	#I don't really like this function, returning 4 values at once feels like I'm doing something wrong
	cats = get_machine_folder(basename, 'catlist')
	#It would theoretically be possible for a machine to appear twice, but catlist doesn't do that I think
	if not cats:
		return 'Unknown', 'Unknown', 'Unknown', False
	cat = cats[0]

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_mature = False
		if subgenre.endswith('* Mature *'):
			is_mature = True
			subgenre = subgenre.removesuffix('* Mature *')
		genre.removeprefix('TTL * ')
		
		return category, genre, subgenre, is_mature

	genre, _, subgenre = cat.partition(' / ')
	return None, genre, subgenre, False

def get_languages(basename: str) -> Optional[list[Language]]:
	langs = get_machine_folder(basename, 'languages')
	if not langs:
		return None

	return [get_language_by_english_name(lang) for lang in langs]
