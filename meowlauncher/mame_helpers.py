import copy
import functools
import os
import re
import subprocess
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from meowlauncher.config.main_config import main_config
from meowlauncher.common import junk_suffixes
from meowlauncher.common_paths import cache_dir
from meowlauncher.data.name_cleanup.mame_manufacturer_name_cleanup import (
    dont_remove_suffix, manufacturer_name_cleanup)

def consistentify_manufacturer(manufacturer: str) -> str:
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
def parse_mame_config_file(path: str) -> dict[str, str]:
	settings = {}

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

class MachineNotFoundException(Exception):
	#This shouldn't be thrown unless I'm an idiot, but that may well happen
	pass

class MAMENotInstalledException(Exception):
	#This should always end up being caught, because I shouldn't assume the user has stuff installed
	pass

class MameExecutable():
	def __init__(self, path: str='mame'):
		self.executable = path
		self.version = self.get_version()
		if self.version:
			#Do I really wanna be checking that this MAME exists inside the object that represents it? That doesn't entirely make sense to me
			self.is_installed = True
			self.xml_cache_path = os.path.join(cache_dir, self.version)
		else:
			self.is_installed = False
			self.xml_cache_path = None

		self._icons = None

	def get_version(self):
		#Note that there is a -version option in (as of this time of writing, upcoming) MAME 0.211, but might as well just use this, because it works on older versions
		try:
			version_proc = subprocess.run([self.executable, '-help'], stdout=subprocess.PIPE, universal_newlines=True, check=True)
		except FileNotFoundError:
			#Should happen if and only if MAME isn't installed
			return None

		return version_proc.stdout.splitlines()[0]

	
	def _real_iter_mame_entire_xml(self):
		print('New MAME version found: ' + self.get_version() + '; creating XML; this may take a while the first time it is run')
		os.makedirs(self.xml_cache_path, exist_ok=True)

		with subprocess.Popen([self.executable, '-listxml'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
			#I'm doing what the documentation tells me to not do and effectively using proc.stdout.read
			try:
				for _, element in ElementTree.iterparse(proc.stdout):
					if element.tag == 'machine':
						my_copy = copy.copy(element)
						machine_name = element.attrib['name']

						with open(os.path.join(self.xml_cache_path, machine_name + '.xml'), 'wb') as cache_file:
							cache_file.write(ElementTree.tostring(element))
						yield machine_name, my_copy
						element.clear()
			except ElementTree.ParseError as fuck:
				#Hmm, this doesn't show us where the error really is
				if main_config.debug:
					print('baaagh XML error in listxml', fuck)
		#Guard against the -listxml process being interrupted and screwing up everything
		Path(self.xml_cache_path, 'is_done').touch()

	def _cached_iter_mame_entire_xml(self):
		for cached_file in os.listdir(self.xml_cache_path):
			splitty = cached_file.rsplit('.', 1)
			if len(splitty) != 2:
				continue
			driver_name, ext = splitty
			if ext != 'xml':
				continue
			yield driver_name, ElementTree.parse(os.path.join(self.xml_cache_path, cached_file)).getroot()
			
	def iter_mame_entire_xml(self):
		if os.path.isfile(os.path.join(self.xml_cache_path, 'is_done')):
			yield from self._cached_iter_mame_entire_xml()
		else:
			yield from self._real_iter_mame_entire_xml()
		
	def get_mame_xml(self, driver: str):
		if not self.is_installed:
			raise MAMENotInstalledException('MAME not installed for get_mame_xml')

		cache_file_path = os.path.join(self.xml_cache_path, driver + '.xml')
		try:
			with open(cache_file_path, 'rb') as cache_file:
				return ElementTree.parse(cache_file).getroot()
		except FileNotFoundError:
			pass

		try:
			proc = subprocess.run([self.executable, '-listxml', driver], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
		except subprocess.CalledProcessError:
			raise MachineNotFoundException(driver)

		return ElementTree.fromstring(proc.stdout).find('machine')

	def listsource(self):
		if not self.is_installed:
			raise MAMENotInstalledException('MAME not installed for listsource')
		proc = subprocess.run([self.executable, '-listsource'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, check=True)
		#Return code should always be 0 so if it's not I dunno what to do about that and let's just panic instead
		for line in proc.stdout.splitlines():
			#Machine names and source files both shouldn't contain spaces, so this should be fine
			yield line.split()
	
	def verifysoftlist(self, software_list_name):
		#Unfortunately it seems we cannot verify an individual software, which would probably take less time
		proc = subprocess.run([self.executable, '-verifysoftlist', software_list_name], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
		#Don't check return code - it'll return 2 if one software in the list is bad

		available = []
		for line in proc.stdout.splitlines():
			#Bleh
			software_verify_matcher = re.compile(r'romset {0}:(.+) is (?:good|best available)$'.format(software_list_name))
			line_match = software_verify_matcher.match(line)
			if line_match:
				available.append(line_match[1])
		return available

	def verifyroms(self, basename):
		try:
			#Note to self: Stop wasting time thinking you can make this faster
			subprocess.run([self.executable, '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
			return True
		except subprocess.CalledProcessError:
			return False

	#Other frontend commands: listfull, listclones, listbrothers, listcrc, listroms, listsamples, verifysamples, romident, listdevices, listslots, listmedia, listsoftware, verifysoftware, getsoftlist

class DefaultMameExecutable():
	__instance = None

	@staticmethod
	def getDefaultMameExecutable():
		if DefaultMameExecutable.__instance is None:
			DefaultMameExecutable.__instance = MameExecutable()
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

def get_mame_core_config():
	conf = default_mame_configuration.core_config
	if conf:
		return conf
	raise MAMENotInstalledException('MAME not installed for get_mame_core_config')

def get_mame_ui_config():
	conf = default_mame_configuration.ui_config
	if conf:
		return conf
	raise MAMENotInstalledException('MAME not installed for get_mame_ui_config')

def have_mame():
	return default_mame_executable.is_installed and default_mame_configuration.is_configured

def iter_mame_entire_xml():
	yield from default_mame_executable.iter_mame_entire_xml()

def get_mame_xml(driver):
	return default_mame_executable.get_mame_xml(driver)

def list_by_source_file():
	return default_mame_executable.listsource()

def verify_software_list(software_list_name):
	return default_mame_executable.verifysoftlist(software_list_name)

@functools.lru_cache(maxsize=None)
def get_image(config_key, machine_or_list_name, software_name=None):
	return default_mame_configuration.get_image(config_key, machine_or_list_name, software_name)

def _tag_starts_with(tag, tag_list):
	if not tag:
		return False
	#Chips from devices are in the format device:thing
	tag = tag.split(':')[-1]

	for t in tag_list:
		if re.fullmatch('^' + re.escape(t) + r'(?:(?:_|\.)?\d+)?$', tag):
			return True
	return False

def find_cpus(machine_xml):
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

def verify_romset(basename):
	return default_mame_executable.verifyroms(basename)

def get_history_xml():
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

def get_histories():
	system_histories = {}
	software_histories = {}

	xml = get_history_xml()
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

def add_history(metadata, machine_or_softlist, software_name=None):
	if not hasattr(add_history, 'systems') or not hasattr(add_history, 'softwares'):
		add_history.systems, add_history.softwares = get_histories()

	if software_name:
		softlist = add_history.softwares.get(machine_or_softlist)
		if not softlist:
			return
		history = softlist.get(software_name)
	else:
		history = add_history.systems.get(machine_or_softlist)

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
