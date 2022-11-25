from typing import TYPE_CHECKING, Any, Optional, Union, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.data.name_cleanup.libretro_database_company_name_cleanup import \
    company_name_overrides
from meowlauncher.games.common.generic_info import (
    add_generic_info_from_filename_tags, add_generic_software_info,
    find_equivalent_arcade_game)
from meowlauncher.games.common.libretro_database import (
    LibretroDatabaseType, parse_all_dats_for_system)
from meowlauncher.games.mame_common.mame_helpers import get_image
from meowlauncher.games.mame_common.mame_utils import image_config_keys
from meowlauncher.games.specific_behaviour.info_helpers import (
    arcade_machine_finders, custom_info_funcs, rom_file_info_funcs,
    software_info_funcs, static_info_funcs, filename_tag_info_funcs)
from meowlauncher.info import Date
from meowlauncher.util.detect_things_from_filename import \
    get_tv_system_from_filename_tags
from meowlauncher.util.region_info import (get_common_language_from_regions,
                                           get_tv_system_from_regions)
from meowlauncher.util.utils import (find_filename_tags_at_end, find_tags,
                                     junk_suffixes, remove_filename_tags)

from .rom import ROM, CompressedROM, FileROM, FolderROM, GCZFileROM

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.machine import Machine
	from meowlauncher.info import GameInfo

	from .rom_game import ROMGame
	
def _add_metadata_from_regions(metadata: 'GameInfo') -> None:
	if metadata.regions:
		if not metadata.languages:
			region_language = get_common_language_from_regions(metadata.regions)
			if region_language:
				metadata.languages = [region_language]

def _add_metadata_from_arcade(game: 'ROMGame', machine: 'Machine') -> None:
	if 'Icon' not in game.info.images:
		machine_icon = get_image(image_config_keys['Icon'], machine.basename)
		if machine_icon:
			game.info.images['Icon'] = machine_icon

	if machine.family_basename in {'monopoly', 'scrabble'}:
		#The arcade games Monopoly and Scrabble are some weird quiz games that have the licensed board games as a theme, whereas every Monopoly and Scrabble in the software list is not going to be that at all, and just a normal conversion of the board game like you expect, so all metadata except the icon isn't necessarily going to be accurate. I choose to hardcode these cases because they annoy me
		game.info.genre = 'Tabletop'
		game.info.subgenre = 'Board'
		return

	if not game.info.series:
		game.info.series = machine.series
	
	catlist = machine.organized_catlist
	if not catlist:
		return
	if not game.info.genre:
		game.info.genre = catlist.genre
	if not game.info.subgenre:
		game.info.subgenre = catlist.subgenre
	if not game.info.categories and catlist.category and catlist.definite_category:
		game.info.categories = [catlist.category]
	#Well, I guess not much else can be inferred here. Still, though!
	#TODO: Hell no there's not much else, get the history if it's not a bootleg, etc etc
		
def _add_alternate_names(rom: ROM, game_info: 'GameInfo') -> None:
	name, tags_at_end = find_tags(rom.name)
	
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
		game_info.add_alternate_name(alt_name)

def _add_metadata_from_libretro_database_entry(metadata: 'GameInfo', database: LibretroDatabaseType, key: Union[str, int]) -> bool:
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
			if description not in {database_entry.get('comment'), database_entry.get('name')}:
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

def _add_metadata_from_libretro_database(game: 'ROMGame') -> None:
	key: Union[str | None, int]
	if game.platform.dat_uses_serial:
		key = game.info.product_code
	elif isinstance(game.rom, FileROM):
		key = game.rom.crc32
	else:
		return

	if not key:
		return
		
	for dat_name in game.platform.dat_names:
		database = parse_all_dats_for_system(dat_name, game.platform.dat_uses_serial)
		if database:
			if game.platform.dat_uses_serial and ', ' in cast(str, key):
				for product_code in cast(str, key).split(', '):
					if _add_metadata_from_libretro_database_entry(game.info, database, product_code):
						break
			else:
				_add_metadata_from_libretro_database_entry(game.info, database, key)

def _autodetect_tv_type(game: 'ROMGame') -> None:
	if game.info.specific_info.get('TV Type'):
		return
	
	from_tags = get_tv_system_from_filename_tags(game.filename_tags)
	if from_tags:
		game.info.specific_info['TV Type'] = from_tags
		return
	
	from_region = get_tv_system_from_regions(game.info.regions)
	if from_region:
		game.info.specific_info['TV Type'] = from_region
		return

def _add_platform_specific_metadata(game: 'ROMGame') -> None:
	software = None
	
	custom_info_func = custom_info_funcs.get(game.platform.name)
	if custom_info_func:
		custom_info_func(game)
		software = game.info.specific_info.get('MAME Software') #This shouldn't be here
	else:
		#For anything else, use this one to just get basic software list info.
		#This would only work for optical discs if they are in .chd format though. Also see MAME GitHub issue #2517, which makes a lot of newly created CHDs invalid with older softlists
		static_info_func = static_info_funcs.get(game.platform.name)
		if static_info_func:
			static_info_func(game.info)

		#We should always run rom_file_info_func before software_info_func if it's there, as that means we can get our product code/alt names and then use get_software_by_name and get_software_by_product_code
		if isinstance(game.rom, FileROM):
			#TODO: This is where we would call subroms if that's relevant
			#TODO: Hmm, how would we do that, actually, with m3u and .cue and related
			rom_file_info_func = rom_file_info_funcs.get(game.platform.name)
			if rom_file_info_func:
				rom_file_info_func(game.rom, game.info)

		filename_tag_func = filename_tag_info_funcs.get(game.platform.name)
		if filename_tag_func:
			filename_tag_func(game.filename_tags, game.info)

		try:
			software = game.get_software_list_entry()
		except NotImplementedError:
			pass
		if software:
			software_info_func = software_info_funcs.get(game.platform.name)
			if software_info_func:
				software_info_func(software, game.info)
			else:
				add_generic_software_info(software, game.info)

	arcade_equivalent_finder = arcade_machine_finders.get(game.platform.name)
	#TODO: This could just go in ROMGame, potentially, if that doesn't cause a circular import by importing arcade_machine_finders?
	equivalent_arcade = None
	if arcade_equivalent_finder:
		if software:
			equivalent_arcade = arcade_equivalent_finder(software.description)
			if not equivalent_arcade and software.parent_name:
				software_parent = software.parent
				assert software_parent, 'This is impossible, software.parent_name is set but software list has no parent'
				equivalent_arcade = arcade_equivalent_finder(software_parent.description)
		if not equivalent_arcade:
			equivalent_arcade = arcade_equivalent_finder(game.name)
	
	if not equivalent_arcade and main_config.find_equivalent_arcade_games:
		if software:
			equivalent_arcade = find_equivalent_arcade_game(game.name, game.info.names.values(), software)
			
	if equivalent_arcade:
		game.info.specific_info['Equivalent Arcade'] = equivalent_arcade
	
def add_info(game: 'ROMGame') -> None:
	_add_alternate_names(game.rom, game.info)
	#I guess if game.subroms was ever used you would loop through each one (I swear I will do the thing one day)

	if game.rom.is_folder:
		game.info.media_type = cast(FolderROM, game.rom).media_type
	else:
		game.info.specific_info['Extension'] = game.rom.extension
		game.info.media_type = game.platform.get_media_type(cast(FileROM, game.rom))

	game.info.specific_info['Size'] = game.rom.size
	if isinstance(game.rom, (CompressedROM, GCZFileROM)):
		game.info.specific_info['Compressed Size'] = game.rom.compressed_size

	_add_platform_specific_metadata(game)
				
	equivalent_arcade = game.info.specific_info.get('Equivalent Arcade')
	if not equivalent_arcade and main_config.find_equivalent_arcade_games:
		software = game.info.specific_info.get('MAME Software')
		if software:
			equivalent_arcade = find_equivalent_arcade_game(game.name, game.info.names.values(), software)
			if equivalent_arcade:
				game.info.specific_info['Equivalent Arcade'] = equivalent_arcade
	
	if equivalent_arcade:
		_add_metadata_from_arcade(game, equivalent_arcade)

	#Only fall back on filename-based detection of stuff if we weren't able to get it any other way. platform_metadata handlers take priority, but then regions come after this because we probably want to detect the regions from filename, and _then_ get other things from that
	add_generic_info_from_filename_tags(game.filename_tags, game.info)
	_add_metadata_from_regions(game.info)

	if game.platform.dat_names:
		_add_metadata_from_libretro_database(game)
	if game.platform.autodetect_tv_type:
		_autodetect_tv_type(game)
