import re
import xml.etree.ElementTree as ElementTree
from typing import Iterable, Optional

from meowlauncher.data.name_cleanup.mame_manufacturer_name_cleanup import (
    dont_remove_suffix, manufacturer_name_cleanup)
from meowlauncher.util.utils import junk_suffixes


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

image_config_keys = {
	'Cabinet': 'cabinets_directory',
	'Control Panel': 'cpanels_directory',
	'PCB': 'pcbs_directory',
	'Flyer': 'flyers_directory',
	'Title Screen': 'titles_directory',
	'End Screen': 'ends_directory',
	'Marquee': 'marquees_directory',
	'Artwork Preview': 'artwork_preview_directory',
	'Boss Screen': 'bosses_directory',
	'Logo Screen': 'logos_directory',
	'Score Screen': 'scores_directory',
	'Versus Screen': 'versus_directory',
	'Game Over Screen': 'gameover_directory',
	'How To Screen': 'howto_directory',
	'Select Screen': 'select_directory',
	'Icon': 'icons_directory',
	'Cover': 'covers_directory', #Software only
}

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
