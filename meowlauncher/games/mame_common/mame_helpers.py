import functools
import os
import re
import xml.etree.ElementTree as ElementTree
from typing import Iterable, Optional

from meowlauncher.data.name_cleanup.mame_manufacturer_name_cleanup import (
    dont_remove_suffix, manufacturer_name_cleanup)
from meowlauncher.metadata import Metadata
from meowlauncher.util.utils import junk_suffixes

from .mame_executable import MAMEExecutable, MAMENotInstalledException


def consistentify_manufacturer(manufacturer: Optional[str]) -> Optional[str]:
	if not manufacturer:
		return None
	if manufacturer not in dont_remove_suffix:
		while junk_suffixes.search(manufacturer):
			manufacturer = junk_suffixes.sub('', manufacturer)
	manufacturer = manufacturer.strip()
	if manufacturer[-1] == '?':
		return manufacturer_name_cleanup.get(manufacturer[:-1], manufacturer[:-1]) + '?'
	return manufacturer_name_cleanup.get(manufacturer, manufacturer)

mame_config_comment = re.compile(r'#.+$')
mame_config_line = re.compile(r'^(?P<key>\w+)\s+(?P<value>.+)$')
semicolon_not_after_quotes = re.compile(r'(?!");')
def parse_mame_config_file(path: str) -> dict[str, list[str]]:
	settings: dict[str, list[str]] = {}

	with open(path, 'rt') as f:
		for line in f.readlines():
			line = mame_config_comment.sub('', line)
			line = line.strip()

			if not line:
				continue

			match = mame_config_line.match(line)
			if match:
				key = match['key']
				values = semicolon_not_after_quotes.split(match['value'])
				settings[key] = []
				for value in values:
					if value[0] == '"' and value[-1] == '"':
						value = value[1:-1]
					settings[key].append(value)
	return settings

class DefaultMameExecutable():
	__instance = None

	@staticmethod
	def getDefaultMameExecutable():
		if DefaultMameExecutable.__instance is None:
			try:
				DefaultMameExecutable.__instance = MAMEExecutable()
			except MAMENotInstalledException:
				return None
		return DefaultMameExecutable.__instance

image_config_keys = {
	'Cabinet': 'cabinets_directory',
	'Control-Panel': 'cpanels_directory',
	'PCB': 'pcbs_directory',
	'Flyer': 'flyers_directory',
	'Title-Screen': 'titles_directory',
	'End-Screen': 'ends_directory',
	'Marquee': 'marquees_directory',
	'Artwork-Preview': 'artwork_preview_directory',
	'Boss-Screen': 'bosses_directory',
	'Logo-Screen': 'logos_directory',
	'Score-Screen': 'scores_directory',
	'Versus-Screen': 'versus_directory',
	'Game-Over-Screen': 'gameover_directory',
	'How-To-Screen': 'howto_directory',
	'Select-Screen': 'select_directory',
	'Icon': 'icons_directory',
	'Cover': 'covers_directory', #Software only
}
image_types = ('ico', 'png', 'jpg', 'bmp')

class MameConfiguration():
	def __init__(self, core_config_path=None, ui_config_path=None):
		self.is_configured = True

		if not core_config_path:
			core_config_path = os.path.expanduser('~/.mame/mame.ini')
		try:
			self.core_config = parse_mame_config_file(core_config_path)
		except FileNotFoundError:
			self.is_configured = False
			self.core_config = None

		if not ui_config_path:
			ui_config_path = os.path.expanduser('~/.mame/ui.ini')
		try:
			self.ui_config = parse_mame_config_file(ui_config_path)
		except FileNotFoundError:
			self.is_configured = False
			self.ui_config = None

		self._icons = None

	def get_image(self, config_key, machine_or_list_name, software_name=None):
		for directory in self.ui_config.get(config_key, []):
			basename = os.path.join(directory, machine_or_list_name)
			if software_name:
				basename = os.path.join(basename, software_name)
			for ext in image_types:
				path = basename + os.path.extsep + ext
				if os.path.isfile(path):
					return path
		return None

class DefaultMameConfiguration():
	__instance = None

	@staticmethod
	def getDefaultMameConfiguration():
		if DefaultMameConfiguration.__instance is None:
			DefaultMameConfiguration.__instance = MameConfiguration(None)
		return DefaultMameConfiguration.__instance	

default_mame_executable = DefaultMameExecutable.getDefaultMameExecutable()
default_mame_configuration = DefaultMameConfiguration.getDefaultMameConfiguration()

def get_mame_core_config() -> dict[str, list[str]]:
	conf = default_mame_configuration.core_config
	if conf:
		return conf
	raise MAMENotInstalledException('MAME not installed for get_mame_core_config')

def get_mame_ui_config():
	conf = default_mame_configuration.ui_config
	if conf:
		return conf
	raise MAMENotInstalledException('MAME not installed for get_mame_ui_config')

def have_mame() -> bool:
	return bool(default_mame_executable) and default_mame_configuration.is_configured

def iter_mame_entire_xml() -> Iterable[tuple[str, ElementTree.Element]]:
	yield from default_mame_executable.iter_mame_entire_xml()

def get_mame_xml(driver: str) -> ElementTree.Element:
	return default_mame_executable.get_mame_xml(driver)

def list_by_source_file() -> Iterable[list[str]]:
	yield from default_mame_executable.listsource()

def verify_software_list(software_list_name: str) -> list[str]:
	return default_mame_executable.verifysoftlist(software_list_name)

@functools.lru_cache(maxsize=None)
def get_image(config_key, machine_or_list_name, software_name=None):
	return default_mame_configuration.get_image(config_key, machine_or_list_name, software_name)

def _tag_starts_with(tag, tag_list: Iterable[str]) -> bool:
	if not tag:
		return False
	#Chips from devices are in the format device:thing
	tag = tag.split(':')[-1]

	for t in tag_list:
		if re.fullmatch('^' + re.escape(t) + r'(?:(?:_|\.)?\d+)?$', tag):
			return True
	return False

def find_cpus(machine_xml: ElementTree.Element) -> list[ElementTree.Element]:
	cpu_xmls = [chip for chip in machine_xml.findall('chip') if chip.attrib.get('type') == 'cpu']
	if not cpu_xmls:
		return []

	#audio_cpu_tags = ('audio_cpu', 'audiocpu', 'soundcpu', 'sndcpu', 'sound_cpu', 'genesis_snd_z80', 'pokey', 'audio', 'sounddsp', 'soundcpu_b', 'speechcpu')
	#cpu_xmls = [cpu for cpu in cpu_xmls if not _tag_starts_with(cpu.attrib.get('tag'), audio_cpu_tags)]

	#Skip microcontrollers etc
	#Do I really want to though? I can't even remember what I was doing any of this for
	microcontrollers = ('mcu', 'iomcu', 'dma', 'dma8237', 'iop_dma', 'dmac', 'i8237', 'i8257', 'i8741')
	device_controllers = ('fdccpu', 'dial_mcu_left', 'dial_mcu_right', 'adbmicro', 'printer_mcu', 'keyboard_mcu', 'keyb_mcu', 'motorcpu', 'drivecpu', 'z80fd', 'm3commcpu', 'mie')
	controller_tags = microcontrollers + device_controllers + ('prot', 'iop', 'iocpu', 'cia')
	cpu_xmls = [cpu for cpu in cpu_xmls if not _tag_starts_with(cpu.attrib.get('tag'), controller_tags)]
	
	return cpu_xmls

def verify_romset(basename: str) -> bool:
	return default_mame_executable.verifyroms(basename)

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
