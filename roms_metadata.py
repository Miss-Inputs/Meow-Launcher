import re
import calendar
import os

import region_detect
import platform_metadata
from mame_helpers import lookup_system_cpu, lookup_system_displays, get_mame_xml
from software_list_info import get_software_lists_by_names
from info import system_info

date_regex = re.compile(r'\((?P<year>[x\d]{4})\)|\((?P<year2>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\)|\((?P<day2>\d{2})\.(?P<month2>\d{2})\.(?P<year3>\d{4})\)')
revision_regex = re.compile(r'\(Rev ([A-Z\d]+?)\)')

cpu_overrides = {
	#Usually just look up system_info.systems, but this is here where they aren't in systems or there isn't a MAME driver so we can't get the CPU from there or where MAME gets it wrong because the CPU we want to return isn't considered the main CPU
	"32X": lookup_system_cpu('sega_32x_ntsc'),
	"FDS": lookup_system_cpu('fds'),
	"Game Boy Color": lookup_system_cpu('gbcolor'),
	"Mega CD": lookup_system_cpu('segacd_us'),
	"C64GS": lookup_system_cpu('c64gs'),
	'Satellaview': lookup_system_cpu('snes'),
	'Sufami Turbo': lookup_system_cpu('snes'),
	'Benesse Pocket Challenge V2': lookup_system_cpu('wswan'), #Should be about right
	'PlayChoice-10': lookup_system_cpu('nes'), #lookup_system_cpu('playch10') returns Zilog Z80, the N2A03 is the "cart" cpu
	'VS Unisystem': lookup_system_cpu('nes'),
}

display_overrides = {
	'FDS': lookup_system_displays('fds'),
	'Game Boy Color': lookup_system_displays('gbcolor'),
	'C64GS': lookup_system_displays('c64gs'),
	'Satellaview': lookup_system_displays('snes'),
	'Sufami Turbo': lookup_system_displays('snes'),
	'Benesse Pocket Challenge V2': lookup_system_displays('wswan'),
	'PlayChoice-10': lookup_system_displays('playch10'),
	'VS Unisystem': lookup_system_displays('nes'),
}

source_file_overrides = {
	#This won't happen often; if there's no MAME driver we should just leave the X-Source-File field blank by definition
	#Basically, this is when something in platform_metadata changes what game.metadata.platform is, which means we can no longer just look up that platform in system_info because it won't be in there
	"FDS": get_mame_xml('fds').find('machine').attrib['sourcefile'],
	"Game Boy Color": get_mame_xml('gbcolor').find('machine').attrib['sourcefile'],
	"C64GS": get_mame_xml('c64gs').find('machine').attrib['sourcefile'],
	'Satellaview': get_mame_xml('snes').find('machine').attrib['sourcefile'],
	'Sufami Turbo': get_mame_xml('snes').find('machine').attrib['sourcefile'],
	'PlayChoice-10': get_mame_xml('playch10').find('machine').attrib['sourcefile'],
	'VS Unisystem': 'vsnes.cpp', #All the VS Unisystem games are in there, but there's no specific BIOS or anything
}

def get_year_revision_from_filename_tags(game, tags):
	found_date = False
	found_revision = True
	if not game.metadata.revision:
		found_revision = False
	for tag in tags:
		date_match = date_regex.match(tag)
		revision_match = revision_regex.match(tag)
		if date_match:
			game.metadata.ignored_filename_tags.append(tag)
			if not found_date:
				#Fuck you and your stupid bullshit. If you hate reading this code direct your anger at Python devs and not me
				groupdict = date_match.groupdict()
				if not game.metadata.year:
					if groupdict['year']:
						game.metadata.year = date_match['year']
					elif groupdict['year2']:
						game.metadata.year = date_match['year2']
					elif groupdict['year3']:
						game.metadata.year = date_match['year3']

				if not game.metadata.month:
					if groupdict['month']:
						try:
							game.metadata.month = calendar.month_name[int(date_match['month'])]
						except (ValueError, IndexError):
							game.metadata.month = date_match['month']
					elif groupdict['month2']:
						try:
							game.metadata.month = calendar.month_name[int(date_match['month2'])]
						except (ValueError, IndexError):
							game.metadata.month = date_match['month2']

				if not game.metadata.day:
					if groupdict['day']:
						game.metadata.day = date_match['day']
					elif groupdict['day2']:
						game.metadata.day = date_match['day2']

				found_date = True
		if revision_match:
			game.metadata.ignored_filename_tags.append(tag)
			if not found_revision:
				game.metadata.revision = revision_match[1]
				found_revision = True

def get_metadata_from_tags(game):
	#Only fall back on filename-based detection of stuff if we weren't able to get it any other way. platform_metadata handlers take priority.
	tags = game.filename_tags

	get_year_revision_from_filename_tags(game, tags)

	if not game.metadata.regions:
		regions = region_detect.get_regions_from_filename_tags(tags, game.metadata.ignored_filename_tags)
		if regions:
			game.metadata.regions = regions

	if not game.metadata.languages:
		languages = region_detect.get_languages_from_filename_tags(tags, game.metadata.ignored_filename_tags)
		if languages:
			game.metadata.languages = languages
		elif game.metadata.regions:
			languages = region_detect.get_languages_from_regions(game.metadata.regions)
			if languages:
				game.metadata.languages = languages


	if not game.metadata.tv_type:
		if game.metadata.regions:
			game.metadata.tv_type = region_detect.get_tv_system_from_regions(game.metadata.regions)
		else:
			tv_type = region_detect.get_tv_system_from_filename_tags(tags, game.metadata.ignored_filename_tags)
			if tv_type:
				game.metadata.tv_type = tv_type

def add_device_hardware_metadata(game):
	mame_driver = system_info.get_mame_driver_by_system_name(game.metadata.platform)

	source_file = None
	if mame_driver:
		source_file = get_mame_xml(mame_driver).find('machine').attrib['sourcefile']
	elif game.metadata.platform in source_file_overrides:
		source_file = source_file_overrides[game.metadata.platform]
	if source_file:
		game.metadata.specific_info['Source-File'] = os.path.splitext(source_file)[0]

	if not game.metadata.cpu_info:
		cpu = None
		if game.metadata.platform in cpu_overrides:
			cpu = cpu_overrides[game.metadata.platform]
		else:
			if mame_driver:
				cpu = lookup_system_cpu(mame_driver)

		if cpu:
			game.metadata.cpu_info = cpu

	if not game.metadata.screen_info:
		displays = None
		if game.metadata.platform in display_overrides:
			displays = display_overrides[game.metadata.platform]
		else:
			if mame_driver:
				displays = lookup_system_displays(mame_driver)
		if displays:
			game.metadata.screen_info = displays

def add_metadata(game):
	game.metadata.extension = game.rom.extension

	system = system_info.get_system_by_name(game.metadata.platform)
	game.metadata.media_type = system.get_media_type(game.rom.extension)

	software_list_names = system_info.get_mame_software_list_names_by_system_name(game.metadata.platform)
	if software_list_names:
		game.software_lists = get_software_lists_by_names(software_list_names)

	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)

	add_device_hardware_metadata(game)

	get_metadata_from_tags(game)


def add_engine_metadata(game):
	game.metadata.extension = game.file.extension

	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)
