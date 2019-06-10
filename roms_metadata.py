import os

import detect_things_from_filename
import platform_metadata
from config import main_config
from info import region_info, system_info
from mame_helpers import (get_icons, get_mame_xml, have_mame,
                          lookup_system_cpus, lookup_system_displays)
from software_list_info import get_software_lists_by_names

mame_driver_overrides = {
	#Basically, this is when something in platform_metadata changes what game.metadata.platform is, which means we can no longer just look up that platform in system_info because it won't be in there
	'FDS': 'fds',
	'Game Boy Color': 'gbcolor',
	'Satellaview': 'gbcolor',
	'Sufami Turbo': 'gbcolor',
	'DSi': 'nds', #For now, there is an nds skeleton driver for us to get info from but not a DSi skeleton driver, so that's fine
	#It can also be set to New 3DS but that has no MAME driver anyway
}
if have_mame():
	cpu_overrides = {
		#Usually just look up system_info.systems, but this is here where they aren't in systems or there isn't a MAME driver so we can't get the CPU from there, or they're addons so things get weird
		'32X': lookup_system_cpus('sega_32x_ntsc'), #This ends up being weird and having 0 clock speed when looking at the device... but if we don't override things, it just has the 68000
		'Mega CD': lookup_system_cpus('segacd_us'),
		'Benesse Pocket Challenge V2': lookup_system_cpus('wswan'), #Should be the same; the BPCV2 is a different system but it is effectively a boneless WonderSwan
	}

	display_overrides = {
		'Benesse Pocket Challenge V2': lookup_system_displays('wswan'),
	}
else:
	cpu_overrides = {}
	display_overrides = {}

def get_metadata_from_tags(game):
	#Only fall back on filename-based detection of stuff if we weren't able to get it any other way. platform_metadata handlers take priority.
	tags = game.filename_tags

	is_nsfw_from_tags = detect_things_from_filename.determine_is_nsfw_from_filename(tags)
	if is_nsfw_from_tags:
		#There is no tag to detect that would determine nsfw = definitely false
		game.metadata.nsfw = True

	year, month, day = detect_things_from_filename.get_date_from_filename_tags(tags)
	if year and not game.metadata.year:
		game.metadata.year = year
	if month and not game.metadata.month:
		game.metadata.month = month
	if day and not game.metadata.day:
		game.metadata.day = day

	revision = detect_things_from_filename.get_revision_from_filename_tags(tags)
	if revision and 'Revision' not in game.metadata.specific_info:
		game.metadata.specific_info['Revision'] = revision

	version = detect_things_from_filename.get_version_from_filename_tags(tags)
	if version and 'Version' not in game.metadata.specific_info:
		game.metadata.specific_info['Version'] = version

	if not game.metadata.regions:
		regions = detect_things_from_filename.get_regions_from_filename_tags(tags)
		if regions:
			game.metadata.regions = regions

	if not game.metadata.languages:
		languages = detect_things_from_filename.get_languages_from_filename_tags(tags)
		if languages:
			game.metadata.languages = languages			

	if not game.metadata.tv_type:
		tv_type = detect_things_from_filename.get_tv_system_from_filename_tags(tags)
		if tv_type:
			game.metadata.tv_type = tv_type

def get_metadata_from_regions(game):
	if game.metadata.regions:
		if not game.metadata.languages:
			region_language = region_info.get_language_from_regions(game.metadata.regions)
			if region_language:
				game.metadata.languages = [region_language]
		if not game.metadata.tv_type:
			tv_type = region_info.get_tv_system_from_regions(game.metadata.regions)
			if tv_type:
				game.metadata.tv_type = tv_type

def add_device_hardware_metadata(game, mame_driver):
	source_file = None
	if have_mame():
		if mame_driver:
			source_file = get_mame_xml(mame_driver).attrib['sourcefile']
			#By definition, if we don't have a MAME driver, then Source-File shouldn't even be set
			if source_file:
				game.metadata.specific_info['Source-File'] = os.path.splitext(source_file)[0]

		if not game.metadata.cpu_info.is_inited:
			cpus = None
			if game.metadata.platform in cpu_overrides:
				cpus = cpu_overrides[game.metadata.platform]
			elif mame_driver:
				cpus = lookup_system_cpus(mame_driver)

			if cpus is not None:
				game.metadata.cpu_info.set_inited()
				for cpu in cpus:
					game.metadata.cpu_info.add_cpu(cpu)

		if not game.metadata.screen_info:
			displays = None
			if game.metadata.platform in display_overrides:
				displays = display_overrides[game.metadata.platform]
			elif mame_driver:
				displays = lookup_system_displays(mame_driver)

			if displays:
				game.metadata.screen_info = displays

mame_icons = get_icons()
def add_metadata(game):
	game.metadata.extension = game.rom.extension

	system = system_info.systems[game.metadata.platform]
	game.metadata.media_type = system.get_media_type(game.rom.extension)

	software_list_names = system.mame_software_lists
	if software_list_names:
		game.software_lists = get_software_lists_by_names(software_list_names)

	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)
	else:
		#For anything else, use this one to just get basic software list info.
		#This would only work for optical discs if they are in .chd format though. Also see MAME GitHub issue #2517, which makes a lot of newly created CHDs invalid with older softlists
		platform_metadata.generic_helper(game)

	mame_driver = None
	if game.metadata.mame_driver:
		mame_driver = game.metadata.mame_driver
	elif game.metadata.platform in mame_driver_overrides:
		mame_driver = mame_driver_overrides[game.metadata.platform]
	elif game.metadata.platform in system_info.systems:
		mame_driver = system_info.systems[game.metadata.platform].mame_driver
			
	add_device_hardware_metadata(game, mame_driver)
	if main_config.use_mame_system_icons:
		if mame_driver in mame_icons:
			game.icon = mame_icons[mame_driver]

	get_metadata_from_tags(game)
	get_metadata_from_regions(game)

def add_engine_metadata(game):
	game.metadata.extension = game.file.extension

	if game.metadata.platform in platform_metadata.helpers:
		platform_metadata.helpers[game.metadata.platform](game)
