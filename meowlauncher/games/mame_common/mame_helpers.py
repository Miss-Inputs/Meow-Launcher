#Use this file for handy shortcuts with the default MAME config/executable
import functools
import re
import xml.etree.ElementTree as ElementTree
from typing import Iterable, Optional

from .mame_configuration import MAMEConfiguration
from .mame_executable import MAMEExecutable, MAMENotInstalledException

class DefaultMameExecutable():
	__instance = None
	__missing = False

	@staticmethod
	def getDefaultMameExecutable():
		if DefaultMameExecutable.__instance is None and not DefaultMameExecutable.__missing:
			try:
				DefaultMameExecutable.__instance = MAMEExecutable()
			except MAMENotInstalledException:
				DefaultMameExecutable.__missing = True
				return None
		return DefaultMameExecutable.__instance

class DefaultMameConfiguration():
	__instance = None
	__missing = False

	@staticmethod
	def getDefaultMameConfiguration():
		if DefaultMameConfiguration.__instance is None and not DefaultMameConfiguration.__missing:
			try:
				DefaultMameConfiguration.__instance = MAMEConfiguration()
			except FileNotFoundError:
				DefaultMameConfiguration.__missing = True
				return None
		return DefaultMameConfiguration.__instance	

default_mame_executable = DefaultMameExecutable.getDefaultMameExecutable()
default_mame_configuration = DefaultMameConfiguration.getDefaultMameConfiguration()

def get_mame_core_config() -> dict[str, list[str]]:
	conf = default_mame_configuration.core_config
	if conf:
		return conf
	raise MAMENotInstalledException('MAME not installed for get_mame_core_config')

def get_mame_ui_config() -> dict[str, list[str]]:
	conf = default_mame_configuration.ui_config
	if conf:
		return conf
	raise MAMENotInstalledException('MAME not installed for get_mame_ui_config')

def have_mame() -> bool:
	return bool(default_mame_executable) and bool(default_mame_configuration)

def iter_mame_entire_xml() -> Iterable[tuple[str, ElementTree.Element]]:
	yield from default_mame_executable.iter_mame_entire_xml()

def get_mame_xml(driver: str) -> ElementTree.Element:
	return default_mame_executable.get_mame_xml(driver)

def list_by_source_file() -> Iterable[list[str]]:
	yield from default_mame_executable.listsource()

def verify_software_list(software_list_name: str) -> list[str]:
	return default_mame_executable.verifysoftlist(software_list_name)

@functools.cache
def get_image(config_key: str, machine_or_list_name: str, software_name: Optional[str]=None) -> Optional[str]:
	return default_mame_configuration.get_image(config_key, machine_or_list_name, software_name)

def _tag_starts_with(tag: Optional[str], tag_list: Iterable[str]) -> bool:
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
