import re
import calendar
import common

import region_detect
import platform_metadata
from mame_helpers import lookup_system_cpu, lookup_system_displays
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
	tags = common.find_filename_tags.findall(game.rom.name)

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
	if not game.metadata.cpu_info:
		cpu = None
		if game.metadata.platform in cpu_overrides:
			cpu = cpu_overrides[game.metadata.platform]			
		else:
			mame_driver = system_info.get_mame_driver_by_system_name(game.metadata.platform)
			if mame_driver:
				cpu = lookup_system_cpu(mame_driver)

		if cpu:
			game.metadata.cpu_info = cpu

	if not game.metadata.screen_info:
		displays = None
		if game.metadata.platform in display_overrides:
			displays = display_overrides[game.metadata.platform]
		else:	
			mame_driver = system_info.get_mame_driver_by_system_name(game.metadata.platform)
			if mame_driver:
				displays = lookup_system_displays(mame_driver)
		if displays:
			game.metadata.screen_info = displays

def add_metadata(game):
	game.metadata.extension = game.rom.extension
	
	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)

	add_device_hardware_metadata(game)
	
	get_metadata_from_tags(game)


def add_engine_metadata(game):
	game.metadata.extension = game.file.extension
	
	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)
