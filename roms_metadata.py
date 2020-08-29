import config.main_config
import detect_things_from_filename
import platform_metadata
from data.not_necessarily_equivalent_arcade_names import \
    not_necessarily_equivalent_arcade_names
from info import region_info, system_info
from mame_helpers import (MachineNotFoundException, MAMENotInstalledException,
                          get_icons, get_mame_xml)
from mame_machine import Machine, does_machine_match_game, does_machine_match_name
from software_list_info import get_software_lists_by_names

conf = config.main_config.main_config

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
	if (year and ('x' not in str(year)) and ('?' not in str(year))) and (game.metadata.year and ('x' in str(game.metadata.year) or '?' in str(game.metadata.year))):
		#Maybe when I am sober this line can be rewritten to be more good
		#TODO Actually it should be more like (if platform_metadata/software list year/month/day is partially unknown, but tag year/month/day is all known, use latter)
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

def find_equivalent_arcade_game(game, basename):
	#Just to be really strict: We will only get it if the name matches
	if basename in not_necessarily_equivalent_arcade_names:
		return None

	try:
		machine_xml = get_mame_xml(basename)
	except (MachineNotFoundException, MAMENotInstalledException):
		return None
	machine = Machine(machine_xml, init_metadata=True)

	if machine.family in not_necessarily_equivalent_arcade_names:
		return None

	if machine.metadata.platform != 'Arcade' or machine.is_mechanical or machine.metadata.genre == 'Slot Machine':
		#I think not, only video games can be video games
		#That comment made sense but y'know what I mean right
		return None
	if '(bootleg of' in machine.name or '(bootleg?)' in machine.name:
		#This doesn't count
		return None
	software_name = game.metadata.specific_info.get('MAME-Software-Full-Name')
	if software_name:
		#TODO: This shouldn't be needed, MAME-Software-Full-Name should be part of names
		if does_machine_match_name(software_name, machine):
			return machine
	if does_machine_match_game(game.rom.name, game.metadata, machine):
		return machine
	return None

def add_metadata_from_arcade(game, machine):
	if 'Icon' not in game.metadata.images:
		game.metadata.images['Icon'] = machine.icon

	if machine.family in ('monopoly', 'scrabble'):
		#The arcade games Monopoly and Scrabble are some weird quiz games that have the licensed board games as a theme, whereas every Monopoly and Scrabble in the software list is not going to be that at all, and just a normal conversion of the board game like you expect, so all metadata except the icon isn't necessarily going to be accurate. I choose to hardcode these cases because they annoy me
		game.metadata.genre = 'Tabletop'
		game.metadata.subgenre = 'Board'
		return

	if not game.metadata.genre:
		game.metadata.genre = machine.metadata.genre
	if not game.metadata.subgenre:
		game.metadata.subgenre = machine.metadata.subgenre
	if not game.metadata.categories and 'Arcade' not in machine.metadata.categories:
		game.metadata.categories = machine.metadata.categories
	if machine.metadata.nsfw:
		game.metadata.nsfw = True
	if not game.metadata.series:
		game.metadata.series = machine.metadata.series
	#Well, I guess not much else can be inferred here. Still, though!
		
def add_metadata(game):
	game.metadata.extension = game.rom.extension

	game.metadata.media_type = game.system.get_media_type(game.rom.extension)

	software_list_names = game.system.mame_software_lists
	if software_list_names:
		game.software_lists = get_software_lists_by_names(software_list_names)

	if game.system_name in platform_metadata.helpers:
		platform_metadata.helpers[game.system_name](game)
	else:
		#For anything else, use this one to just get basic software list info.
		#This would only work for optical discs if they are in .chd format though. Also see MAME GitHub issue #2517, which makes a lot of newly created CHDs invalid with older softlists
		platform_metadata.generic_helper(game)

	mame_driver = None
	if game.metadata.mame_driver:
		mame_driver = game.metadata.mame_driver
	elif game.system_name in system_info.systems:
		mame_driver = system_info.systems[game.system_name].mame_driver
				
	equivalent_arcade = game.metadata.specific_info.get('Equivalent-Arcade')
	if not equivalent_arcade and conf.find_equivalent_arcade_games:
		software_name = game.metadata.specific_info.get('MAME-Software-Name')
		parent_name = game.metadata.specific_info.get('MAME-Software-Parent')
		if software_name:
			equivalent_arcade = find_equivalent_arcade_game(game, software_name)
			if not equivalent_arcade and parent_name:
				equivalent_arcade = find_equivalent_arcade_game(game, parent_name)
			if equivalent_arcade:
				game.metadata.specific_info['Equivalent-Arcade'] = equivalent_arcade
	
	if equivalent_arcade:
		add_metadata_from_arcade(game, equivalent_arcade)
	if 'Icon' not in game.metadata.images:
		if conf.use_mame_system_icons:
			try:
				mame_icons = add_metadata.mame_icons
			except AttributeError:
				mame_icons = add_metadata.mame_icons = get_icons()

			if mame_driver in mame_icons:
				game.metadata.images['Icon'] = mame_icons[mame_driver]

	get_metadata_from_tags(game)
	get_metadata_from_regions(game)
