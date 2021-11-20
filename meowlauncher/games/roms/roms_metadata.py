from typing import Any, Optional, Union, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.data.name_cleanup.libretro_database_company_name_cleanup import \
    company_name_overrides
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.common.libretro_database import (
    LibretroDatabaseType, parse_all_dats_for_system)
from meowlauncher.games.mame_common.machine import (Machine,
                                                    does_machine_match_game,
                                                    get_machine)
from meowlauncher.games.mame_common.mame_executable import \
    MachineNotFoundException
from meowlauncher.games.mame_common.mame_helpers import (
    default_mame_executable, get_image)
from meowlauncher.games.mame_common.mame_utils import image_config_keys
from meowlauncher.games.specific_behaviour.metadata import helpers
from meowlauncher.metadata import Date, Metadata
from meowlauncher.util.detect_things_from_filename import (
    get_date_from_filename_tags, get_languages_from_filename_tags,
    get_regions_from_filename_tags, get_revision_from_filename_tags,
    get_tv_system_from_filename_tags, get_version_from_filename_tags)
from meowlauncher.util.region_info import (get_language_from_regions,
                                           get_tv_system_from_regions)
from meowlauncher.util.utils import (find_filename_tags_at_end, junk_suffixes,
                                     load_list, remove_filename_tags)

from .rom import ROM, FileROM, FolderROM
from .rom_game import ROMGame

not_necessarily_equivalent_arcade_names = load_list(None, 'not_necessarily_equivalent_arcade_names')

def add_metadata_from_tags(game: ROMGame):
	#Only fall back on filename-based detection of stuff if we weren't able to get it any other way. platform_metadata handlers take priority.
	tags = game.filename_tags

	filename_date = get_date_from_filename_tags(tags)
	if filename_date:
		if filename_date.is_better_than(game.metadata.release_date):
			game.metadata.release_date = filename_date
	
	revision = get_revision_from_filename_tags(tags)
	if revision and 'Revision' not in game.metadata.specific_info:
		game.metadata.specific_info['Revision'] = revision

	version = get_version_from_filename_tags(tags)
	if version and 'Version' not in game.metadata.specific_info:
		game.metadata.specific_info['Version'] = version

	if not game.metadata.regions:
		regions = get_regions_from_filename_tags(tags)
		if regions:
			game.metadata.regions = regions

	if not game.metadata.languages:
		languages = get_languages_from_filename_tags(tags)
		if languages:
			game.metadata.languages = languages

def add_metadata_from_regions(metadata: Metadata):
	if metadata.regions:
		if not metadata.languages:
			region_language = get_language_from_regions(metadata.regions)
			if region_language:
				metadata.languages = [region_language]

def find_equivalent_arcade_game(game: ROMGame, basename: str) -> Optional[Machine]:
	#Just to be really strict: We will only get it if the name matches
	if basename in not_necessarily_equivalent_arcade_names:
		return None

	if not default_mame_executable:
		return None
	try:
		machine = get_machine(basename, default_mame_executable)
	except MachineNotFoundException:
		return None

	if machine.family in not_necessarily_equivalent_arcade_names:
		return None

	catlist = machine.catlist
	if catlist:
		if not catlist.is_arcade:
			#I think not, only video games can be video games
			#That comment made sense but y'know what I mean right
			#Do we really need to exclude mechanical/slot machines? This function used to, I dunno
			return None
	if '(bootleg of' in machine.name or '(bootleg?)' in machine.name:
		#This doesn't count
		return None
	if does_machine_match_game(game.rom.name, game.metadata.names.values(), machine):
		return machine
	return None

def add_metadata_from_arcade(game: ROMGame, machine: Machine):
	if 'Icon' not in game.metadata.images:
		machine_icon = get_image(image_config_keys['Icon'], machine.basename)
		if machine_icon:
			game.metadata.images['Icon'] = machine_icon

	if machine.family in {'monopoly', 'scrabble'}:
		#The arcade games Monopoly and Scrabble are some weird quiz games that have the licensed board games as a theme, whereas every Monopoly and Scrabble in the software list is not going to be that at all, and just a normal conversion of the board game like you expect, so all metadata except the icon isn't necessarily going to be accurate. I choose to hardcode these cases because they annoy me
		game.metadata.genre = 'Tabletop'
		game.metadata.subgenre = 'Board'
		return

	if not game.metadata.series:
		game.metadata.series = machine.series
	
	catlist = machine.organized_catlist
	if not catlist:
		return
	if not game.metadata.genre:
		game.metadata.genre = catlist.genre
	if not game.metadata.subgenre:
		game.metadata.subgenre = catlist.subgenre
	if not game.metadata.categories and catlist.category and catlist.definite_category:
		game.metadata.categories = [catlist.category]
	#Well, I guess not much else can be inferred here. Still, though!
		
def add_alternate_names(rom: ROM, metadata: Metadata):
	tags_at_end = find_filename_tags_at_end(rom.name)
	name = remove_filename_tags(rom.name)

	#Unlikely that there would be an "aaa (bbb ~ ccc)" but still
	if ' ~ ' not in rom.name:
		return

	splits = name.split(' ~ ')
	primary_name = splits[0]
	alt_names = splits[1:]

	#This is which way around they are in No-Intro etc, but… no
	not_allowed_to_be_primary_name = {"Tony Hawk's Skateboarding", 'Senjou no Ookami II', 'G-Sonic', 'Chaotix', 'After Burner Complete'}
	if primary_name in not_allowed_to_be_primary_name:
		alt_names.append(primary_name)
		primary_name = alt_names.pop(0)
	if primary_name == 'Ax Battler - A Legend of Golden Axe':
		#I refuse to let "Golden Axe" be the alternate name when that's a completely different thing
		return
		
	primary_name_tags = find_filename_tags_at_end(primary_name)
	if tags_at_end:
		if not primary_name_tags:
			#This stuff in brackets was probably a part of the whole thing, not the last alternate name
			primary_name += ' ' + ' '.join(tags_at_end)
			alt_names[-1] = remove_filename_tags(alt_names[-1])
		else:
			#The name is something like "aaa (bbb) ~ ccc (ddd)" so the (ddd) here actually belongs to the ccc, not the whole thing (this wouldn't usually happen with any naming convention I know of, but I copypasta'd this code from mame_machine.py and I guess why not handle a possible thing happening while we're here)
			alt_names[-1] += ' ' + ' '.join(tags_at_end)

	#rom.name = primary_name #FIXME: That's a read only property, we shouldn't be changing the ROM's name logically speaking anyway; there should be a display_name type thing for Game
	for alt_name in alt_names:
		metadata.add_alternate_name(alt_name)

def add_metadata_from_libretro_database_entry(metadata: Metadata, database: LibretroDatabaseType, key: Union[str, int]):
	database_entry = cast(Optional[dict[str, Any]], database.get(key)) #TODO: Hmm what's the best way to do this - we don't want mypy complaining about all the different things GameValueType could be
	if database_entry:
		name = database_entry.get('comment', database_entry.get('name'))
		if name:
			metadata.add_alternate_name(name, 'Libretro Database Name')
		if 'serial' in database_entry and not metadata.product_code:
			metadata.product_code = database_entry['serial']
		#seems name = description = comment = usually just the name of the file from No-Intro/Redump, region we already know, enhancement_hw we already know (just SNES and Mega Drive)
		if 'description' in database_entry:
			description = database_entry['description']
			if description not in (database_entry.get('comment'), database_entry.get('name')):
				metadata.descriptions['Libretro Description'] = description


		date = Date()
		if 'releaseyear' in database_entry:
			date.year = database_entry['releaseyear']
		elif 'year' in database_entry:
			#Unusual but can happen apparently
			date.year = database_entry['year']
		if 'releasemonth' in database_entry:
			date.month = database_entry['releasemonth']
		if 'releaseday' in database_entry:
			date.day = database_entry['releaseday']
		if date.is_better_than(metadata.release_date):
			metadata.release_date = date

		if 'developer' in database_entry:
			developer = database_entry['developer']
			while junk_suffixes.search(developer):
				developer = junk_suffixes.sub('', developer)
			metadata.developer = company_name_overrides.get(developer, developer)
		if 'publisher' in database_entry:
			publisher = database_entry['publisher']
			while junk_suffixes.search(publisher):
				publisher = junk_suffixes.sub('', publisher)
			metadata.publisher = company_name_overrides.get(publisher, publisher)
		if 'manufacturer' in database_entry:
			publisher = database_entry['manufacturer']
			while junk_suffixes.search(publisher):
				publisher = junk_suffixes.sub('', publisher)
			metadata.publisher = company_name_overrides.get(publisher, publisher)


		if 'genre' in database_entry:
			genre = database_entry['genre']
			if '/' in genre:
				metadata.genre, metadata.subgenre = genre.split('/', 1)
			else:
				metadata.genre = genre
		if 'franchise' in database_entry:
			metadata.series = database_entry['franchise']
		if 'version' in database_entry:
			metadata.specific_info['Version'] = database_entry['version']

		if 'users' in database_entry:
			metadata.specific_info['Number of Players'] = database_entry['users']
		if 'homepage' in database_entry:
			metadata.documents['Homepage'] = database_entry['homepage']
		if 'patch' in database_entry:
			metadata.documents['Patch Homepage'] = database_entry['patch']
		if 'esrb_rating' in database_entry:
			metadata.specific_info['ESRB Rating'] = database_entry['esrb_rating']
		if 'bbfc_rating' in database_entry:
			metadata.specific_info['BBFC Rating'] = database_entry['bbfc_rating']
		if 'elspa_rating' in database_entry:
			metadata.specific_info['ELSPA Rating'] = database_entry['elspa_rating']
		if 'origin' in database_entry:
			metadata.specific_info['Development Origin'] = database_entry['origin']
		if 'edge_review' in database_entry:
			metadata.descriptions['EDGE Review'] = database_entry['edge_review']
		if 'edge_rating' in database_entry:
			metadata.specific_info['EDGE Rating'] = database_entry['edge_rating']
		if 'edge_issue' in database_entry:
			metadata.specific_info['EDGE Issue'] = database_entry['edge_issue']
		if 'famitsu_rating' in database_entry:
			metadata.specific_info['Famitsu Rating'] = database_entry['famitsu_rating']
		
		if database_entry.get('analog', 0) == 1:
			#This is PS1 specific
			metadata.specific_info['Uses Analog?'] = True
		if database_entry.get('rumble', 0) == 1:
			metadata.specific_info['Force Feedback?'] = True

		# for k, v in database_entry.items():
		# 	if k not in ('name', 'description', 'region', 'releaseyear', 'releasemonth', 'releaseday', 'genre', 'developer', 'serial', 'comment', 'franchise', 'version', 'homepage', 'patch', 'publisher', 'users', 'esrb_rating', 'origin', 'enhancement_hw', 'edge_review', 'edge_rating', 'edge_issue', 'famitsu_rating', 'analog', 'rumble'):
		# 		print('uwu', database_entry.get('comment'), k, v)
		return True
	return False

def add_metadata_from_libretro_database(game: ROMGame):
	key: Union[Optional[str], int]
	if game.platform.dat_uses_serial:
		key = game.metadata.product_code
	elif isinstance(game.rom, FileROM):
		key = game.rom.crc32
	else:
		return

	if key:
		for dat_name in game.platform.dat_names:
			database = parse_all_dats_for_system(dat_name, game.platform.dat_uses_serial)
			if database:
				if game.platform.dat_uses_serial and ', ' in cast(str, key):
					for product_code in cast(str, key).split(', '):
						if add_metadata_from_libretro_database_entry(game.metadata, database, product_code):
							break
				else:
					add_metadata_from_libretro_database_entry(game.metadata, database, key)

def autodetect_tv_type(game: ROMGame):
	if game.metadata.specific_info.get('TV Type'):
		return
	
	from_tags = get_tv_system_from_filename_tags(game.filename_tags)
	if from_tags:
		game.metadata.specific_info['TV Type'] = from_tags
		return
	
	from_region = get_tv_system_from_regions(game.metadata.regions)
	if from_region:
		game.metadata.specific_info['TV Type'] = from_region
		return

def add_metadata(game: ROMGame):
	add_alternate_names(game.rom, game.metadata)
	#I guess if game.subroms was ever used you would loop through each one (I swear I will do the thing one day)

	if game.rom.is_folder:
		game.metadata.media_type = cast(FolderROM, game.rom).media_type
	else:
		game.metadata.specific_info['Extension'] = game.rom.extension
		game.metadata.media_type = game.platform.get_media_type(cast(FileROM, game.rom))

	if game.platform.name in helpers:
		helpers[game.platform.name](game)
	else:
		#For anything else, use this one to just get basic software list info.
		#This would only work for optical discs if they are in .chd format though. Also see MAME GitHub issue #2517, which makes a lot of newly created CHDs invalid with older softlists
		
		try:
			software = game.get_software_list_entry()
			if software:
				add_generic_software_info(software, game.metadata)
		except NotImplementedError:
			pass

				
	equivalent_arcade = game.metadata.specific_info.get('Equivalent Arcade')
	if not equivalent_arcade and main_config.find_equivalent_arcade_games:
		software_name = game.metadata.specific_info.get('MAME Software Name')
		parent_name = game.metadata.specific_info.get('MAME Software Parent')
		if software_name:
			equivalent_arcade = find_equivalent_arcade_game(game, software_name)
			if not equivalent_arcade and parent_name:
				equivalent_arcade = find_equivalent_arcade_game(game, parent_name)
			if equivalent_arcade:
				game.metadata.specific_info['Equivalent Arcade'] = equivalent_arcade
	
	if equivalent_arcade:
		add_metadata_from_arcade(game, equivalent_arcade)

	add_metadata_from_tags(game)
	add_metadata_from_regions(game.metadata)

	if game.platform.dat_names:
		add_metadata_from_libretro_database(game)
	if game.platform.autodetect_tv_type:
		autodetect_tv_type(game)
