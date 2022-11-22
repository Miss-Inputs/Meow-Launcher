#!/usr/bin/env python3

import datetime
import json
import logging
import statistics
from collections.abc import Collection, Iterator, Mapping, MutableMapping
from functools import cached_property
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any

try:
	from steamfiles import appinfo
	have_steamfiles = True
except ModuleNotFoundError:
	have_steamfiles = False

from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.exceptions import (GameNotSupportedException,
                                     NotActuallyLaunchableGameException,
                                     NotLaunchableException)
from meowlauncher.game_source import GameSource
from meowlauncher.games.common.engine_detect import (
    try_and_detect_engine_from_folder, try_detect_engine_from_exe)
from meowlauncher.games.common.pc_common_info import add_info_for_raw_exe
from meowlauncher.games.steam.steam_game import (LauncherInfo, SteamGame,
                                                 SteamLauncher)
from meowlauncher.games.steam.steam_utils import (format_genre,
                                                  normalize_developer,
                                                  store_categories,
                                                  translate_language_list)
from meowlauncher.info import Date
from meowlauncher.util.desktop_files import has_been_done
from meowlauncher.util.name_utils import normalize_name_case
from meowlauncher.util.utils import remove_capital_article

if have_steamfiles or TYPE_CHECKING:
	#TODO: This isn't to avoid a circular import, it just assumes steamfiles can be imported because I can't be bothered doing "have_steamfiles" in there
	#Maybe this should just require steamfiles anyway…
	from meowlauncher.games.steam.steam_installation import (IconError,
	                                                         IconNotFoundError,
	                                                         SteamInstallation)
if TYPE_CHECKING:
	from meowlauncher.launcher import Launcher

logger = logging.getLogger(__name__)

class SteamState():
	"""Singleton for storing where Steam is installed and if it's installed or not
	If you have Steam installed twice in different locations somehow then that is your own problem, but I don't think that's really a thing that people do
	Hmmm… does this acutally need to be its own class?
	TODO: Yeah it does for now, until this module is rewritten to move stuff into SteamGame
	"""
	def __init__(self) -> None:
		self.steam_installation = None
		#Most likely the former will be present as a symlink to the latter, I don't know if weird distros install it any differently
		possible_locations = ('~/.local/share/Steam', '~/.local/share/steam', '~/.steam/steam')
		steam_path = None
		for str_location in possible_locations:
			location = Path(str_location).expanduser()

			if location.is_symlink():
				location = location.readlink()

			if location.is_dir():
				steam_path = location
				break
		
		if steam_path:
			self.steam_installation = SteamInstallation(Path(steam_path))

	@property
	def is_steam_installed(self) -> bool:
		return self.steam_installation is not None

	__instance = None

	def __new__(cls) -> 'SteamState':
		if cls.__instance is None:
			cls.__instance = object.__new__(cls)
		return cls.__instance

#TODO: Move more of this to SteamGame

def process_launchers(game: 'SteamGame', launch: Mapping[bytes, Mapping[bytes, Any]]) -> None:
	launch_items: MutableMapping[str | None, list[LauncherInfo]] = {}
	#user_config = game.app_state.get('UserConfig')
	#installed_betakey = user_config.get('betakey') if user_config else None
	for launch_item in launch.values():
		#Key here is 0, 1, 2, n... which is a bit useless, it's really just a boneless list. Anyway, each of these values is another dict containing launch parameters, for each individual platform or configuration, e.g. Windows 32-bit, Windows 64-bit, MacOS, etc
		#If you wanted to do secret evil things: b'executable' = 'CoolGame.sh' b'arguments' (optional) = '--fullscreen --blah' b'description' = 'Cool Game'

		#Actually, sometimes the key doesn't start at 0, which is weird, but anyway it still doesn't really mean much, it just means we can't get the first item by getting key 0

		executable_name = launch_item.get(b'executable')
		exe: PurePath | None = None
		if executable_name:
			exe_name: str = executable_name.decode('utf-8', errors='backslashreplace')
			if exe_name.startswith('steam://open'):
				#None of that
				continue
			exe = PurePath(exe_name.replace('\\', '/'))
		
		args: str | None = None
		executable_arguments = launch_item.get(b'arguments')
		if executable_arguments:
			if isinstance(executable_arguments, appinfo.Integer):
				args = str(executable_arguments.data)
			else:
				args = executable_arguments.decode('utf-8', errors='backslashreplace')

		description = launch_item.get(b'description')
		launcher_description: str | None = None
		if description:
			launcher_description = description.decode('utf-8', errors='backslashreplace')

		launch_type = launch_item.get(b'type')
		launcher_type: str | None = None
		if launch_type:
			launcher_type = launch_type.decode('utf-8', errors='backslashreplace')
		
		platform = None
		launch_item_config = launch_item.get(b'config')
		if launch_item_config:
			oslist = launch_item_config.get(b'oslist', b'')
			if oslist:
				#I've never seen oslist be a list, but it is always a byte string, so maybe there's some game where it's multiple platforms comma separated
				platform = oslist.decode('utf-8', errors='backslashreplace')
				osarch = launch_item_config.get(b'osarch')
				if osarch:
					platform += '_' + (str(osarch.data) if isinstance(osarch, appinfo.Integer) else osarch.decode('utf-8', errors='backslashreplace'))
			#ownsdlc = integer, need this DLC for it to show up
			#betakey = launch_item_config.get(b'betakey')
			#if betakey and betakey != installed_betakey:
			#	continue
		launcher = LauncherInfo(exe, args, launcher_description, launcher_type, platform)
		launch_items.setdefault(platform, []).append(launcher)

	for platform, platform_launchers in launch_items.items():
		platform_launcher: LauncherInfo
		if len(platform_launchers) == 1:
			platform_launcher = platform_launchers[0]
		else:
			game.extra_launchers.setdefault(platform, [])
			game.extra_launchers[platform] += platform_launchers[1:]
			game.info.specific_info['Multiple Launchers?'] = True
			platform_launcher = platform_launchers[0]

		game.launchers[platform] = platform_launcher
				
def add_icon_from_common_section(game: 'SteamGame', common_section: Mapping[bytes, Any]) -> None:
	potential_icon_names = (b'linuxclienticon', b'clienticon', b'clienticns')
	#icon and logo have similar hashes, but don't seem to actually exist. logo_small seems to just be logo with a _thumb on the end
	#Damn I really thought clienttga was a thing too
	icon_exception = None
	found_an_icon = False
	potentially_has_icon = False

	for potential_icon_name in potential_icon_names:
		if potential_icon_name not in common_section:
			continue
		potentially_has_icon = True
		try:
			icon_hash = common_section[potential_icon_name].decode('utf-8')
		except UnicodeDecodeError:
			continue
		try:
			icon = game.steam_installation.look_for_icon(icon_hash)
		except IconError as icon_error:
			icon_exception = icon_error
			continue
		except IconNotFoundError:
			continue
		if icon:
			game.info.images['Icon'] = icon
			icon_exception = None
			found_an_icon = True
			break
	if main_config.warn_about_missing_icons:
		if icon_exception:
			logger.error(game, exc_info=icon_exception)
		elif potentially_has_icon and not found_an_icon:
			logger.debug('Could not find icon for %s', game)
		elif not potentially_has_icon:
			logger.debug('%s does not even have an icon', game)

def add_genre(game: 'SteamGame', common: Mapping[bytes, Any]) -> None:
	content_warning_ids = []
	primary_genre_id = common.get(b'primary_genre')
	#I think this has to do with the breadcrumb thing in the store at the top where it's like "All Games > Blah Games > Blah"
	#It is flawed in a few ways, as some things aren't really primary genres (Indie, Free to Play) and some are combinations (Action + RPG, Action + Adventure)
	if primary_genre_id:
		if primary_genre_id.data == 0:
			#Sometimes it's 0, even though the genre list is still there
			primary_genre_id = None
		elif primary_genre_id.data == 37:
			#'Free to Play' is not a genre
			primary_genre_id = None
		elif primary_genre_id.data >= 71:
			#While it is humourous that "Nudity" can appear as the primary genre for a game (Hentai Puzzle), this is not really what someone would sensibly want
			content_warning_ids.append(primary_genre_id.data)
			primary_genre_id = None
		else:
			primary_genre_id = primary_genre_id.data
	genre_id_list = common.get(b'genres')
	#This is definitely the thing in the sidebar on the store page

	additional_genre_ids = []
	if genre_id_list:
		for genre_id in genre_id_list.values():
			if not genre_id:
				continue
			if genre_id.data == primary_genre_id:
				continue
			if genre_id.data == 37:
				#'Free to Play' is not a genre
				continue
			if genre_id.data >= 71:
				if genre_id.data not in content_warning_ids:
					content_warning_ids.append(genre_id.data)
			elif genre_id.data not in additional_genre_ids:
				additional_genre_ids.append(genre_id.data)
	if additional_genre_ids and not primary_genre_id:
		primary_genre_id = additional_genre_ids.pop(0)

	if primary_genre_id:
		game.info.genre = format_genre(primary_genre_id)
	#TODO: Combine additional genres where appropriate (e.g. Action + Adventure, Massively Multiplayer + RPG)
	if additional_genre_ids:
		game.info.specific_info['Additional Genres'] = tuple(format_genre(id) for id in additional_genre_ids)
	if content_warning_ids:
		game.info.specific_info['Content Warnings'] = tuple(format_genre(id) for id in content_warning_ids)
	#"genre" doesn't look like a word anymore

def add_info_from_appinfo_common_section(game: 'SteamGame', common: Mapping[bytes, Any]) -> None:
	if 'Icon' not in game.info.images:
		add_icon_from_common_section(game, common)

	#eulas is a list, so it could be used to detect if game has third-party EULA
	#small_capsule and header_image refer to image files that don't seem to be there so I dunno
	#workshop_visible and community_hub_visible could also tell you stuff about if the game has a workshop and a... community hub
	#releasestate: 'released' might be to do with early access?
	#exfgls = exclude from game library sharing
	#b'requireskbmouse' and b'kbmousegame' are also things, but don't seem to be 1:1 with games that have controllersupport = none

	oslist = common.get(b'oslist')
	if not main_config.use_steam_as_platform:
		#It's comma separated, but we can assume platform if there's only one (and sometimes config section doesn't do the thing)
		if oslist == b'windows':
			game.info.platform = 'Windows'
		if oslist == b'macos':
			game.info.platform = 'Mac'
		if oslist == b'linux':
			game.info.platform = 'Linux'
		
	#osarch is something like b'32' or b'64', osextended is sometimes 'macos64' etc

	app_retired_publisher_request = common.get(b'app_retired_publisher_request')
	if app_retired_publisher_request:
		game.info.specific_info['No Longer Purchasable'] = app_retired_publisher_request.data == 1
	#You can't know if a game's delisted entirely unless you go to the store API to find if that returns success or not, because the appinfo stuff is a cache and holds on to data that no longer exists

	language_list = common.get(b'languages')
	if language_list:
		game.info.languages = translate_language_list(language_list)
	else:
		supported_languages = common.get(b'supported_languages')
		if supported_languages:
			#Hmm… this one goes into more detail actually, you have not just "supported" but "full_audio" and "subtitles"
			#But for now let's just look at what else exists
			game.info.languages = translate_language_list(supported_languages)

	add_genre(game, common)

	steam_release_timestamp = common.get(b'steam_release_date')
	#Seems that original_release_date is here sometimes, and original_release_date sometimes appears along with steam_release_date where a game was only put on Steam later than when it was actually released elsewhere
	#Sometimes these are equal, or off by like one day (which is possibly timezone related)
	original_release_timestamp = common.get(b'original_release_date')

	release_date = original_release_timestamp
	if not release_date:
		release_date = steam_release_timestamp
	#Maybe I should put in an option to prefer Steam release date
		
	if release_date:
		release_datetime = datetime.datetime.fromtimestamp(release_date.data)
		game.info.release_date = Date(release_datetime.year, release_datetime.month, release_datetime.day)
	if original_release_timestamp and steam_release_timestamp:
		steam_release_datetime = datetime.datetime.fromtimestamp(steam_release_timestamp.data)
		game.info.specific_info['Steam Release Date'] = Date(steam_release_datetime.year, steam_release_datetime.month, steam_release_datetime.day)

	store_asset_mtime = common.get(b'store_asset_mtime')
	if store_asset_mtime:
		store_asset_timestamp = datetime.datetime.fromtimestamp(store_asset_mtime.data)
		game.info.specific_info['Store Asset Modification Time'] = Date(store_asset_timestamp.year, store_asset_timestamp.month, store_asset_timestamp.day)

	store_categories_list = common.get(b'category')
	if store_categories_list:
		#keys are category_X where X is some arbitrary ID, values are always Integer = 1
		#This is the thing where you go to the store sidebar and it's like "Single-player" "Multi-player" "Steam Achievements" etc"
		cats = {store_categories.get(key, key) for key in (key.decode('utf-8', errors='backslashreplace') for key in store_categories_list.keys())}
		game.info.specific_info['Store Categories'] = cats #meow
		game.info.specific_info['Has Achievements?'] = 'Steam Achievements' in cats
		game.info.specific_info['Has Trading Cards?'] = 'Steam Trading Cards' in cats
		is_single_player_only = True
		for cat in cats:
			if 'multiplayer' in cat.lower() or 'multi-player' in cat.lower() or 'co-op' in cat.lower() or 'split screen' in cat.lower():
				is_single_player_only = False
				break
		if is_single_player_only:
			game.info.specific_info['Number of Players'] = 1
		
	has_adult_content = common.get(b'has_adult_content') #Integer object with data = 0 or 1, as most bools here seem to be
	if has_adult_content:
		game.info.specific_info['Has Adult Content?'] = bool(has_adult_content.data)
	has_violence = common.get(b'has_adult_content_violence')
	if has_violence:
		game.info.specific_info['Has Violent Content?'] = bool(has_violence.data)
	has_sex = common.get(b'has_adult_content_sex') #uwu
	if has_sex:
		game.info.specific_info['Has Sexual Content?'] = bool(has_sex.data)
	
	only_vr = common.get(b'onlyvrsupport')
	vr_support = common.get(b'openvrsupport')
	if only_vr is not None and only_vr.data:
		game.info.specific_info['VR Support'] = 'Required'
	elif vr_support:
		#b'1'
		game.info.specific_info['VR Support'] = 'Optional'

	metacritic_score = common.get(b'metacritic_score')
	if metacritic_score:
		#Well why not
		game.info.specific_info['Metacritic Score'] = metacritic_score.data
	metacritic_url = common.get(b'metacritic_fullurl')
	if metacritic_url:
		game.info.documents['Metacritic Page'] = metacritic_url.decode('utf8', 'backslashreplace')
	metacritic_name = common.get(b'metacritic_name')
	if metacritic_name:
		game.info.add_alternate_name(metacritic_name.decode('utf8', 'backslashreplace'), 'Metacritic Name')

	review_score = common.get(b'review_score')
	#This is Steam's own review section, I guess?
	#This seems to be a number from 2 to 9 inclusive. Not sure what it means though
	#There is also review_score_bombs? What the heck
	if review_score:
		game.info.specific_info['Review Score'] = review_score.data
	review_percentage = common.get(b'review_percentage')
	#Also seemingly related to Steam reviews, and there is also a review_percentage_bombs, but I still don't know exactly what this does
	if review_percentage:
		game.info.specific_info['Review Percentage'] = review_percentage.data
	
	sortas = common.get(b'sortas')
	if sortas:
		game.info.specific_info['Sort Name'] = sortas.decode('utf8', errors='backslashreplace')

	game.info.specific_info['Controlller Support'] = common.get(b'controller_support', b'none').decode('utf-8', errors='backslashreplace')

	if game.steam_installation.localization:
		store_tag_names = game.steam_installation.localization['localization']['english']['store_tags']
		store_tag_ids_list = common.get(b'store_tags')
		if store_tag_ids_list:
			store_tags = {store_tag_names.get(id, id) for id in (str(value.data) for value in store_tag_ids_list.values())}
			game.info.specific_info['Store Tags'] = store_tags

	associations = common.get(b'associations')
	if associations:
		developers: dict[int, str] = {}
		publishers: dict[int, str] = {}
		franchises: dict[int, str] = {}
		for i, association in associations.items():
			association_type = association.get(b'type')
			association_name_bytes = association.get(b'name')
			if not association_type or not association_name_bytes:
				continue
			association_name = str(association_name_bytes.data) if isinstance(association_name_bytes, appinfo.Integer) else association_name_bytes.decode('utf-8', 'backslashreplace')
			if association_type ==  b'franchise':
				not_actual_franchises = {'Playism', 'Hentai', 'Coming-of-Age', 'Wolf RPG Editor', 'Winter Wolves Games', 'Team17 Digital', '&quot;caves rd&quot;', 'Jackbox Games', 'Franchise', 'PopCap'}
				if association_name in not_actual_franchises:
					continue
				association_name = association_name.removesuffix(' Franchise')
				association_name = association_name.removesuffix(' Series')
				association_name = remove_capital_article(association_name)
				association_name = normalize_name_case(association_name)				
				franchises[i] = association_name
				
			if association_type == b'developer':
				developers[i] = normalize_developer(association_name)
			if association_type == b'publisher' and association_name != 'none':
				publishers[i] = normalize_developer(association_name)

		game.info.series = [franchise for _, franchise in sorted(franchises.items()) if franchise not in publishers.values()]

		game.info.specific_info['Mac Developer'] = [dev.removesuffix(' (Mac)') for _, dev in sorted(developers.items()) if dev.endswith(' (Mac)')]
		game.info.specific_info['Linux Developer'] = [dev.removesuffix(' (Linux)') for _, dev in sorted(developers.items()) if dev.endswith(' (Linux)')]
		game.info.developer = [dev for _, dev in sorted(developers.items()) if not dev.endswith((' (Mac)', ' (Linux)'))]

		game.info.specific_info['Mac Publisher'] = [pub.removesuffix(' (Mac)') for _, pub in sorted(publishers.items()) if pub.endswith(' (Mac)')]
		game.info.specific_info['Linux Publisher'] = [pub.removesuffix(' (Linux)') for _, pub in sorted(publishers.items()) if pub.endswith(' (Linux)')]
		game.info.publisher = [game.info.developer[0] if pub == 'Self Published' and game.info.developer else pub for _, pub in sorted(publishers.items()) if not pub.endswith((' (Mac)', ' (Linux)'))]
			
def add_info_from_appinfo_extended_section(game: 'SteamGame', extended: Mapping[bytes, Any]) -> None:
	if not game.info.developer:
		developer = extended.get(b'developer')
		if developer:
			if isinstance(developer, appinfo.Integer):
				#Cheeky buggers... the doujin developer 773 is represented by the actual integer value 773 here, for some reason
				game.info.developer = str(developer.data)
			else:
				game.info.developer = normalize_developer(developer.decode('utf-8', errors='backslashreplace'))
	if not game.info.publisher:
		publisher = extended.get(b'publisher')
		if publisher:
			if isinstance(publisher, appinfo.Integer):
				game.info.publisher = str(publisher.data)
			else:
				publisher = normalize_developer(publisher.decode('utf-8', errors='backslashreplace'))
				if publisher in {'none', 'Self Published'}:
					game.info.publisher = game.info.developer
				else:
					game.info.publisher = publisher

	homepage = extended.get(b'homepage')
	if homepage:
		game.info.documents['Homepage'] = homepage.decode('utf-8', errors='backslashreplace')
	developer_url = extended.get(b'developer_url')
	if developer_url:
		game.info.documents['Developer Homepage'] = developer_url.decode('utf-8', errors='backslashreplace')
	gamemanualurl = extended.get(b'gamemanualurl')
	if gamemanualurl:
		game.info.documents['Manual'] = gamemanualurl.decode('utf-8', errors='backslashreplace')

	isfreeapp = extended.get(b'isfreeapp')
	if isfreeapp:
		if isinstance(isfreeapp, bytes):
			#Why do you do this?
			game.info.specific_info['Is Free?'] = isfreeapp != b'0'
		elif isinstance(isfreeapp, appinfo.Integer):
			game.info.specific_info['Is Free?'] = isfreeapp.data != 0
	#icon is either blank or something like 'steam/games/icon_garrysmod' which doesn't exist so no icon for you (not that way)
	#order and noservers seem like they might mean something, but I dunno what
	#state = eStateAvailable verifies that it is indeed available (wait maybe it doesn't)
	#vrheadsetstreaming and listofdlc might be useful (the latter is a comma separated list of AppIDs for each DLC in existence for this game)
	#mustownapptopurchase: If present, appID of a game that you need to buy first (parent of DLC, or something like Source SDK Base for Garry's Mod, etc)
	#dependantonapp: Probably same sort of thing, like Half-Life: Opposing Force is dependent on original Half-Life

def process_appinfo_config_section(game: 'SteamGame', app_info_section: Mapping[bytes, Any]) -> None:
	config_section = app_info_section.get(b'config')
	if config_section:
		#contenttype = 3 in some games but not all of them? nani
		launch = config_section.get(b'launch')
		#This key would actually tell us the executable and arguments used to actually launch the game. It's probably not a good idea to do that directly though, mostly because most games are DRM'd to Steam, so it's probably a good idea to go through the Steam client like we are now.
		#Anyway, we're going to use it a bit more responsibly
		if launch:
			process_launchers(game, launch)
		else:
			raise NotActuallyLaunchableGameException('No launch entries in config section')

def add_info_from_appinfo(game: 'SteamGame', app_info_section: Mapping[bytes, Any]) -> None:
	#Alright let's get to the fun stuff
	common = app_info_section.get(b'common')
	if common:
		add_info_from_appinfo_common_section(game, common)

	extended = app_info_section.get(b'extended')
	if extended:
		add_info_from_appinfo_extended_section(game, extended)

	localization = app_info_section.get(b'localization')
	if localization:
		if b'richpresence' in localization:
			#Keys of this are 'english' or presumably other languages and then 'tokens' and then it's a bunch of stuff
			game.info.specific_info['Rich Presence?'] = True

	if b'ufs' in app_info_section:
		game.info.save_type = SaveType.Cloud
	else:
		#I think it's a fair assumption that every game on Steam will have _some_ sort of save data (even if just settings and not progress) so until I'm proven wrong... whaddya gonna do
		game.info.save_type = SaveType.Internal

def process_launcher(game: 'SteamGame', launcher: 'LauncherInfo') -> None:
	if not launcher.exe:
		return #I guess
	extension = launcher.exe.suffix[1:].lower()
	if extension:
		game.info.specific_info['Extension'] = extension
	#See what we can tell about the game exe. Everything that is a DOS game packaged with DOSBox will have DOSBox for all launchers (from what I know so far), except for Duke Nukem 3D, which has a "launch OpenGL" and a "launch DOS" thing, so.. hmm
	#You can't detect that a game uses Origin that I can tell... dang
	executable_basename = launcher.exe.name
	# if executable_basename:
	# 	if '/' in executable_basename:
	# 		executable_basename = executable_basename.split('/')[-1]
	# 	elif '\\' in executable_basename:
	# 		executable_basename = executable_basename.split('\\')[-1]
	game.info.specific_info['Executable Name'] = executable_basename
	launcher_full_path = game.install_dir.joinpath(launcher.exe)
	if launcher_full_path.is_file():
		add_info_for_raw_exe(launcher_full_path, game.info)
		#look_for_icon_for_file(launcher_full_path) would also be an option
		engine = try_detect_engine_from_exe(launcher_full_path, game.info)
		if not engine and launcher.exe.parent != game.install_dir and game.install_dir.is_dir():
			try_and_detect_engine_from_folder(game.install_dir, game.info)
		if engine:
			game.info.specific_info['Engine'] = engine

	if launcher.args and '-uplay_steam_mode' in launcher.args:
		game.info.specific_info['Launcher'] = 'uPlay'
	if not main_config.use_steam_as_platform:
		launcher_platform = launcher.platform
		if launcher_platform:
			if 'linux' in launcher_platform.lower():
				game.info.platform = 'Linux'
			elif 'win' in launcher_platform.lower():
				game.info.platform = 'Windows'
			elif 'mac' in launcher_platform.lower():
				#Why not
				game.info.platform = 'Mac'

def add_images(game: 'SteamGame') -> None:
	"""Adds images for @game from the library cache
	Do I wanna call header a banner? I dunno I guess I'm not for now
	The grid image is not always a cover/box art, but it'll make enough sense to call it that, as opposed to having lots of different keys in images
	#What the hell is a "hero"? oh well it's there, might as well chuck it in"""
	for image_filename, name in (('icon', 'Icon'), ('header', 'Header'), ('library_600x900', 'Cover'), ('library_hero', 'Hero'), ('logo', 'Logo')):
		if name in game.info.images:
			continue
		image_path = game.steam_installation.find_image(game.appid, image_filename)
		if image_path:
			game.info.images[name] = image_path

def add_info_from_cache_json(game: 'SteamGame', json_path: Path, is_single_user: bool) -> None:
	"""This does not always exist, it's there if you've looked at it in the Steam client and it's loaded some metadata, but like why the heck not
	Cool stuff in here:
	friends -> Has info on which of your friends played this game (I don't think we need to put that in here anywhere)
	associations > Duplicated from appinfo so we don't need that
	workshop -> If you downloaded any workshop stuff
	badge -> If you're into the badge collecting that stuff is in here
	usernews and gameactivity sound cool, but they're blank? Hmm"""
	j = json.loads(json_path.read_bytes())
	achievements = None
	achievement_map = None #What's this about…
	descriptions = None
	social_media = None
	for key, values in j:
		if key == 'achievements':
			achievements = values.get('data')
		elif key == 'achievementmap':
			achievement_map = json.loads(values.get('data'))
		elif key == 'descriptions':
			descriptions = values.get('data')
		elif key == 'socialmedia':
			social_media = values.get('data')

	if descriptions:
		game.info.descriptions['Snippet'] = descriptions.get('strSnippet')
		full_description = descriptions.get('strFullDescription')
		if full_description and not full_description.startswith('#app_'):
			game.info.descriptions['Full Description'] = full_description

	if social_media:
		social_media_types = {
			#https://github.com/SteamDatabase/SteamTracking/blob/master/Structs/enums.steamd#L916 (EExternalAccountType)
			0: 'None',
			1: 'Steam',
			2: 'Google',
			3: 'Facebook',
			4: 'Twitter',
			5: 'Twitch',
			6: 'YouTube',
			7: 'Facebook Page',
		}
		for social_medium in social_media:
			#strName is just the account's name on that platform I think?
			key = social_media_types.get(social_medium.get('eType'), f'Unknown Social Media {social_medium.get("eType")}')
			game.info.documents[key] = social_medium.get('strURL')

	if is_single_user and achievements:
		total_achievements = achievements.get('nTotal', 0)
		achieved = achievements.get('nAchieved', 0)

		if total_achievements:
			unachieved_list = {cheevo['strID']: cheevo for cheevo in achievements.get('vecUnachieved', ())}
			achieved_list = {cheevo['strID']: cheevo for cheevo in achievements.get('vecAchievedHidden', ()) + achievements.get('vecHighlight', ())}
			if achievement_map:
				for achievement_id, achievement_data in achievement_map[0][1]:
					if achievement_data.get('bAchieved'):
						achieved_list[achievement_id] = dict(achieved_list.get(achievement_id, {}), **achievement_data)
					else:
						unachieved_list[achievement_id] = dict(unachieved_list.get(achievement_id, {}), **achievement_data)
			
			if unachieved_list:
				unachieved_stats = (cheevo.get('flAchieved', 0) / 100 for cheevo in unachieved_list.values())
				unachieved_percent = statistics.median(unachieved_stats)
				game.info.specific_info['Median Global Unachieved Completion'] = f'{unachieved_percent:.0%}'
			if achieved_list:
				achievement_stats = (cheevo.get('flAchieved', 0) / 100 for cheevo in achieved_list.values())
				achieved_percent = statistics.median(achievement_stats)
				game.info.specific_info['Median Global Achieved Completion'] = f'{achieved_percent:.0%}'
	
			game.info.specific_info['Achievement Completion'] = f'{achieved / total_achievements:.0%}'

def add_info_from_user_cache(game: 'SteamGame') -> None:
	user_list = game.steam_installation.user_ids
	if not user_list:
		#Also, that should never happen (maybe if you just installed Steam and haven't logged in yet, but then what would you get out of this anyway?)
		return
	single_user = len(user_list) == 1
	#If there is more than one user here, then we don't want to look at user-specific info, because it might not be the one who's running Meow Launcher and so it might be wrong
	for user in user_list:
		user_cache_folder = game.steam_installation.get_user_library_cache_folder(user)
		path = user_cache_folder.joinpath(f'{game.appid}.json')
		if path.is_file():
			add_info_from_cache_json(game, path, single_user)

class Steam(GameSource):
	def __init__(self) -> None:
		self._steam_installation: 'SteamInstallation | None' = None
		if not have_steamfiles:
			self._is_available = False
		else:
			steam_state = SteamState()
			self._is_available = steam_state.is_steam_installed
			self._steam_installation = steam_state.steam_installation	

	@property
	def name(self) -> str:
		return 'Steam'
	
	@property
	def is_available(self) -> bool:
		return self._is_available
	
	@cached_property
	def _all_installed_appids(self) -> Collection[int]:
		if not self._steam_installation:
			return []
		return {app_id for _, app_id, __ in self._steam_installation.iter_steam_installed_appids()}
	
	def no_longer_exists(self, game_id: str) -> bool:
		if not self._is_available:
			#Then don't touchy, no evidence anything was uninstalled
			return False
		try:
			return int(game_id) not in self._all_installed_appids
		except ValueError:
			return False
	
	def iter_launchers(self) -> Iterator['Launcher']:
		assert self._steam_installation, 'Please do not call iter_launchers if is_available is false'
		for folder, app_id, app_state in self._steam_installation.iter_steam_installed_appids():
			if not main_config.full_rescan:
				if has_been_done('Steam', str(app_id)):
					continue
			
			try:
				yield self.process_game(app_id, folder, app_state)
			except NotLaunchableException:
				logger.warning('%s %s is skipped', app_state.get('name', app_id), app_id, exc_info=True)
				continue

	def process_game(self, appid: int, folder: Path, app_state: Mapping[str, Any]) -> 'SteamLauncher':
		#We could actually just leave it here and create a thing with xdg-open steam://rungame/app_id, but where's the fun in that? Much more metadata than that
		assert self._steam_installation, 'process_game called without checking steam_state.is_steam_installed'
		game = SteamGame(appid, folder, app_state, self._steam_installation)
		if main_config.use_steam_as_platform:
			game.info.platform = 'Steam'
		else:
			#I guess we might assume it's Windows if there's no other info specifying the platform, this seems to happen with older games
			game.info.platform = 'Windows'

		appinfo_entry = game.appinfo
		if appinfo_entry:
			process_appinfo_config_section(game, appinfo_entry)

		steamplay_overrides = self._steam_installation.steamplay_overrides
		steamplay_whitelist = self._steam_installation.steamplay_whitelist
		appid_str = str(game.appid)


		if not game.launchers:
			raise NotActuallyLaunchableGameException('Game cannot be launched')

		launcher: LauncherInfo | None = next(iter(game.launchers.values())) #Hmm
		tools = self._steam_installation.steamplay_compat_tools
		override = False
		if appid_str in steamplay_overrides:
			#Specifically selected in the dropdown box
			override = True
			tool_id = steamplay_overrides[appid_str]
			if tool_id: #Would there be a situation in which this is none? Hmm I dunno
				tool = tools.get(tool_id, (None, tool_id, None, None))
				game.info.emulator_name = tool[1]
				if tool[2] in game.launchers:
					launcher = game.launchers[tool[2]]		
				game.info.specific_info['Steam Play Forced?'] = True
		if appid_str in steamplay_whitelist:
			if not override:
				tool_id = steamplay_whitelist[appid_str]
				tool = tools.get(tool_id, (None, tool_id, None, None))
				game.info.emulator_name = tool[1]
				if tool[2] in game.launchers:
					launcher = game.launchers[tool[2]]
			game.info.specific_info['Steam Play Whitelisted?'] = True
		elif 'linux' in game.launchers:
			launcher = game.launchers['linux']
		elif 'linux_64' in game.launchers:
			launcher = game.launchers['linux_64']
		elif 'linux_32' in game.launchers:
			launcher = game.launchers['linux_32']
		else:
			global_tool_id = steamplay_overrides.get('0')
			if global_tool_id:
				#game.metadata.emulator_name = tools.get(global_tool, (None,global_tool))[1]
				global_tool = tools.get(global_tool_id, (None, global_tool_id, None, None))
				game.info.emulator_name = global_tool[1]
				if global_tool[2] in game.launchers:
					launcher = game.launchers[global_tool[2]]
				#"tool" doesn't look like a word anymore help
				game.info.specific_info['Steam Play Whitelisted?'] = False
			else:
				#If global tool is not set; this game can't be launched and will instead say "Invalid platform"
				game.info.specific_info['No Valid Launchers?'] = True
				launcher = None
				if not main_config.force_create_launchers:
					raise GameNotSupportedException('Platform not supported and Steam Play not used')

		if launcher:
			process_launcher(game, launcher)
		#Potentially do something with game.extra_launchers... I dunno, really

		game.add_metadata()
		add_images(game)
		add_info_from_user_cache(game)
		
		#userdata/<user ID>/config/localconfig.vdf has last time played stats, so that's a thing I guess
		#userdata/<user ID>/7/remote/sharedconfig.vdf has tags/categories etc as well

		if appinfo_entry:
			add_info_from_appinfo(game, appinfo_entry)
		
		return SteamLauncher(game)

