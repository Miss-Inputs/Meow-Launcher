import re
from collections.abc import Collection, Iterator, Sequence
from xml.etree import ElementTree

from meowlauncher.data.name_cleanup.mame_manufacturer_name_cleanup import (
	dont_remove_suffix,
	manufacturer_name_cleanup,
)
from meowlauncher.util.utils import junk_suffixes


def consistentify_manufacturer(manufacturer: str | None) -> str | None:
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
	'Cover': 'covers_directory',  # Software only
}


def _tag_starts_with(tag: str | None, tag_list: Collection[str]) -> bool:
	if not tag:
		return False
	# Chips from devices are in the format device:thing
	tag = tag.split(':')[-1]

	return any(re.fullmatch('^' + re.escape(t) + r'(?:(?:_|\.)?\d+)?$', tag) for t in tag_list)


def iter_cpus(machine_xml: ElementTree.Element) -> Iterator[ElementTree.Element]:
	for chip_xml in machine_xml.iter('chip'):
		if chip_xml.attrib.get('type') != 'cpu':
			continue

		# audio_cpu_tags = ('audio_cpu', 'audiocpu', 'soundcpu', 'sndcpu', 'sound_cpu', 'genesis_snd_z80', 'pokey', 'audio', 'sounddsp', 'soundcpu_b', 'speechcpu')
		# cpu_xmls = [cpu for cpu in cpu_xmls if not _tag_starts_with(cpu.attrib.get('tag'), audio_cpu_tags)]

		# Skip microcontrollers etc
		# Do I really want to though? I can't even remember what I was doing any of this for
		microcontrollers = {
			'mcu',
			'iomcu',
			'dma',
			'dma8237',
			'iop_dma',
			'dmac',
			'i8237',
			'i8257',
			'i8741',
		}
		device_controllers = {
			'fdccpu',
			'dial_mcu_left',
			'dial_mcu_right',
			'adbmicro',
			'printer_mcu',
			'keyboard_mcu',
			'keyb_mcu',
			'motorcpu',
			'drivecpu',
			'z80fd',
			'm3commcpu',
			'mie',
		}
		controller_tags = microcontrollers.union(device_controllers).union(
			{'prot', 'iop', 'iocpu', 'cia'}
		)
		if _tag_starts_with(chip_xml.attrib.get('tag'), controller_tags):
			continue
		yield chip_xml


def untangle_manufacturer(
	arcade_system: str | None, manufacturers: Sequence[str]
) -> tuple[str, str]:
	developer = manufacturers[0]
	publisher = manufacturers[1]
	if manufacturers[0] == 'bootleg':
		developer = publisher = manufacturers[1]
	elif manufacturers[1] == 'bootleg':
		developer = publisher = manufacturers[0]
	elif 'JAKKS Pacific' in manufacturers:
		# Needs to be a better way of what I'm saying, surely. I'm tired, so I can't boolean logic properly. It's just like… if the manufacturer is X / Y or Y / X, then the developer is X, and the publisher is Y
		# Anyway, we at least know that JAKKS Pacific is always the publisher in this scenario, so that cleans up the plug & play games a bit
		developer = manufacturers[0] if manufacturers[1] == 'JAKKS Pacific' else manufacturers[1]
		publisher = manufacturers[1] if manufacturers[1] == 'JAKKS Pacific' else manufacturers[0]
	elif (
		'Sega' in manufacturers
		and arcade_system
		and ('Sega' in arcade_system or 'Naomi' in arcade_system)
	):
		# It would also be safe to assume Sega is not going to get someone else to be the publisher on their own hardware, I think; so in this case (manufacturer: Blah / Sega) we can probably say Blah is the developer and Sega is the publisher
		# I really really hope I'm not wrong about this assumption, but I want to make it
		developer = manufacturers[0] if manufacturers[1] == 'Sega' else manufacturers[1]
		publisher = manufacturers[1] if manufacturers[1] == 'Sega' else manufacturers[0]
	elif 'Capcom' in manufacturers and arcade_system and ('Capcom' in arcade_system):
		# Gonna make the same assumption here...
		developer = manufacturers[0] if manufacturers[1] == 'Capcom' else manufacturers[1]
		publisher = manufacturers[1] if manufacturers[1] == 'Capcom' else manufacturers[0]
	elif 'Namco' in manufacturers and arcade_system and ('Namco' in arcade_system):
		# And here, too
		developer = manufacturers[0] if manufacturers[1] == 'Namco' else manufacturers[1]
		publisher = manufacturers[1] if manufacturers[1] == 'Namco' else manufacturers[0]
	elif 'Sammy' in manufacturers and arcade_system and arcade_system == 'Atomiswave':
		developer = manufacturers[0] if manufacturers[1] == 'Sammy' else manufacturers[1]
		publisher = manufacturers[1] if manufacturers[1] == 'Sammy' else manufacturers[0]
	return developer, publisher
