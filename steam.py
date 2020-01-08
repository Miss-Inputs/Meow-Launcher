#!/usr/bin/env python3

import calendar
import datetime
import glob
import io
import os
import re
import time
import zipfile

import launchers
from common import junk_suffixes, remove_capital_article, title_case
from common_types import MediaType, SaveType
from config import main_config
from data.capitalized_words_in_names import capitalized_words
from data.steam_developer_overrides import developer_overrides
from data.steam_genre_ids import genre_ids
from data.steam_store_categories import store_categories
from info.region_info import get_language_by_english_name
from metadata import Metadata
from series_detect import chapter_matcher

try:
	from PIL import Image, IcoImagePlugin
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

try:
	#Have to import it like this, because the directory is inside another directory
	#Anyway it _should_ be here since I made it a submodule anyway, but like... y'know, just to be safe
	from steamfiles.steamfiles import acf, appinfo
	have_steamfiles = True
except ModuleNotFoundError:
	have_steamfiles = False

#TODO A lot of this is messy and needs refactoring and I will leave an annoying todo comment here for myself to be bothered by until I refactor it

class SteamState():
	class __SteamState():
		def __init__(self):
			self.steamdir = self.find_steam_dir()
			if self.is_steam_installed:
				try:
					with open(self.app_info_path, 'rb') as app_info_file:
						try:
							self.app_info = appinfo.load(app_info_file)
							self.app_info_available = True
						except ValueError:
							#This will be thrown by steamfiles.appinfo if the appinfo.vdf structure is different than expected, which apparently has happened in earlier versions of it, so I should probably be prepared for that
							self.app_info = None
							self.app_info_available = False
				except FileNotFoundError:
					self.app_info = None
					self.app_info_available = False
				try:
					with open(self.config_path) as config_file:
						self.config = acf.load(config_file)
						self.config_available = True
				except FileNotFoundError:
					self.config = None
					self.config_available = False
				try:
					with open(self.localization_path) as localization_file:
						self.localization = acf.load(localization_file)
						self.localization_available = True
				except FileNotFoundError:
					self.localization = None
					self.localization_available = False
			else:
				self.app_info = None
				self.app_info_available = False
				self.config = None
				self.config_available = False
				self.localization = None
				self.localization_available = None

		@property
		def app_info_path(self):
			return os.path.join(self.steamdir, 'appcache', 'appinfo.vdf')

		@property
		def config_path(self):
			return os.path.join(self.steamdir, 'config', 'config.vdf')

		@property
		def localization_path(self):
			return os.path.join(self.steamdir, 'appcache', 'localization.vdf')

		@property
		def icon_folder(self):
			return os.path.join(self.steamdir, 'steam', 'games')

		@property
		def is_steam_installed(self):
			return self.steamdir is not None

		@property
		def steam_library_list_path(self):
			return os.path.join(self.steamdir, 'steamapps', 'libraryfolders.vdf')

		@staticmethod
		def find_steam_dir():
			#Most likely the former will be present as a symlink to the latter, I don't know if weird people have ways of installing Steam to other directories
			possible_locations = ['~/.steam/steam', '~/.local/share/steam', '~/.local/share/Steam']

			for location in possible_locations:
				location = os.path.expanduser(location)

				if os.path.isdir(location):
					return location
				if os.path.islink(location):
					return os.path.realpath(location)

			return None

	__instance = None

	@staticmethod
	def getSteamState():
		if SteamState.__instance is None:
			SteamState.__instance = SteamState.__SteamState()
		return SteamState.__instance

steam_state = SteamState.getSteamState()

def is_steam_available():
	#If false, you won't be able to use this module
	return steam_state.is_steam_installed and have_steamfiles

def get_steam_library_folders():
	with open(steam_state.steam_library_list_path, 'rt') as steam_library_list_file:
		steam_library_list = acf.load(steam_library_list_file)
		library_folders = steam_library_list.get('LibraryFolders')
		if not library_folders:
			#Shouldn't happen unless Valve decides to mess with the format bigtime
			return [steam_state.steamdir]
		#Not sure I like the condition on k here, but I guess it'll work. The keys under LibraryFolders are TimeNextStatsReport and ContentStatsID (whatever those do), and then 1 2 3 4 for each library folder, but I dunno how reliable that is. Anyway, that should do the trick, I guess; if someone breaks something it's gonna break
		return [v for k, v in library_folders.items() if k.isdigit()] + [steam_state.steamdir]

def get_steamplay_overrides():
	if not steam_state.config_available:
		return {}

	try:
		mapping = steam_state.config['InstallConfigStore']['Software']['Valve']['Steam']['CompatToolMapping']

		overrides = {}
		for k, v in mapping.items():
			overrides[k] = v.get('name')
		return overrides
	except KeyError:
		return {}

class SteamGame():
	def __init__(self, app_id, folder, app_state):
		self.app_id = app_id
		self.library_folder = folder
		self.app_state = app_state
		self.metadata = Metadata()

		self.launchers = {}
		self.extra_launchers = {}

	@property
	def name(self):
		name = self.app_state.get('name')
		if not name:
			name = '<unknown game {0}>'.format(self.app_id)
		name = fix_name(name)
		return name

	@property
	def appinfo(self):
		if steam_state.app_info_available:
			game_app_info = steam_state.app_info.get(self.app_id)
			if game_app_info is None:
				#Probably shouldn't happen if all is well and that game is supposed to be there
				if main_config.debug:
					print(self.name, self.app_id, 'does not have an entry in appinfo.vdf')
				return None

			#There are other keys here too but I dunno if they're terribly useful, just stuff about size and state and access token and bleh
			#last_update is a Unix timestamp for the last time the user updated the game
			sections = game_app_info.get('sections')
			if sections is None:
				if main_config.debug:
					print(self.name, self.app_id, 'does not have a sections key in appinfo.vdf')
				return None
			#This is the only key in sections, and from now on everything is a bytes instead of a str, seemingly
			app_info_section = sections.get(b'appinfo')
			if app_info_section is None:
				if main_config.debug:
					print(self.name, self.app_id, 'does not have a appinfo section in appinfo.vdf sections')
				return None
			return app_info_section
		return None

	def make_launcher(self):
		params = launchers.LaunchParams('steam', ['steam://rungameid/{0}'.format(self.app_id)])
		launchers.make_launcher(params, self.name, self.metadata, 'Steam', self.app_id)

class NotLaunchableError(Exception):
	pass

class IconError(Exception):
	pass

class IconNotFoundError(Exception):
	pass

def look_for_icon(icon_hash):
	icon_hash = icon_hash.lower()
	for icon_file in os.listdir(steam_state.icon_folder):
		icon_path = os.path.join(steam_state.icon_folder, icon_file)

		if icon_file.lower() in (icon_hash + '.ico', icon_hash + '.png', icon_hash + '.zip'):
			is_zip = zipfile.is_zipfile(icon_path)
			#Can't just rely on the extension because some zip files like to hide and pretend to be .ico files for some reason

			with open(icon_path, 'rb') as test:
				magic = test.read(4)
				if magic == b'Rar!':
					raise IconError('icon {0} is secretly a RAR file and cannot be opened'.format(icon_hash))

			if have_pillow and icon_file.endswith('.ico') and not is_zip:
				#.ico files can be a bit flaky with Tumbler thumbnails and some other image-reading stuff, so if we can convert them, that might be a good idea just in case (well, there definitely are some icons that don't thumbnail properly so yeah)
				try:
					image = Image.open(icon_path)
					return image
				except (ValueError, OSError) as ex:
					#Try and handle the "This is not one of the allowed sizes of this image" error caused by .ico files having incorrect headers which I guess happens more often than I would have thought otherwise
					#This is gonna get ugly
					with open(icon_path, 'rb') as f:
						try:
							#Use BytesIO here to prevent "seeking a closed file" errors, which is probably a sign that I don't actually know what I'm doing
							ico = IcoImagePlugin.IcoFile(io.BytesIO(f.read()))
							biggest_size = (0, 0)
							for size in ico.sizes():
								if size[0] > biggest_size[0] and size[1] > biggest_size[1]:
									biggest_size = size
							if biggest_size == (0, 0):
								raise IconError('.ico file {0} has no valid sizes'.format(icon_file))
							return ico.getimage(biggest_size)
						except SyntaxError as syntax_error:
							#Of all the errors it throws, it throws this one? Well, okay fine whatever
							raise IconError('.ico file {0} is not actually an .ico file at all'.format(icon_file)) from syntax_error

					#Guess it's still broken
					raise IconError('.ico file {0} has some annoying error: {1}'.format(icon_file, str(ex))) from ex

			if not is_zip:
				return icon_path

			with zipfile.ZipFile(icon_path, 'r') as zip_file:
				icon_files = []
				for zip_info in zip_file.infolist():
					if zip_info.is_dir():
						continue
					if zip_info.filename.startswith('__MACOSX'):
						#Yeah that happens with retail Linux games apparently
						continue
					if zip_info.filename.lower().endswith(('.ico', '.png')):
						icon_files.append(zip_info)

				#Get the biggest image file and assume that's the best icon we can have
				extracted_icon_file = sorted(icon_files, key=lambda zip_info: zip_info.file_size, reverse=True)[0]
				extracted_icon_folder = os.path.join(main_config.image_folder, 'Icon', 'extracted_from_zip', icon_hash)
				return zip_file.extract(extracted_icon_file, path=extracted_icon_folder)

	raise IconNotFoundError('{0} not found'.format(icon_hash))

def translate_language_list(languages):
	langs = []
	for language_name, _ in languages.items():
		#value is an Integer object but it's always 1, I dunno what the 0 means, because it's like, if the language isn't there, it just wouldn't be in the dang list anyway
		language_name = language_name.decode('utf-8', errors='backslashreplace')
		if language_name == 'koreana': #I don't know what the a at the end is for, but Steam does that
			langs.append(get_language_by_english_name('Korean'))
		elif language_name == 'schinese': #Simplified Chinese
			langs.append(get_language_by_english_name('Chinese'))
		elif language_name == 'tchinese':
			langs.append(get_language_by_english_name('Traditional Chinese'))
		elif language_name == 'brazilian':
			langs.append(get_language_by_english_name('Brazilian Portugese'))
		elif language_name == 'latam':
			langs.append(get_language_by_english_name('Latin American Spanish'))
		else:
			language = get_language_by_english_name(language_name, case_insensitive=True)
			if language:
				langs.append(language)
			elif main_config.debug:
				print('Unknown language:', language_name)

	return langs

def normalize_developer(dev):
	dev = junk_suffixes.sub('', dev)
	dev = dev.strip()

	if dev in developer_overrides:
		return developer_overrides[dev]
	return dev

def _get_steamplay_appinfo_extended():
	steamplay_manifest_appid = 891390

	steamplay_appinfo = steam_state.app_info.get(steamplay_manifest_appid)
	if steamplay_appinfo is None:
		return None
	sections = steamplay_appinfo.get('sections')
	if sections is None:
		return None
	app_info_section = sections.get(b'appinfo')
	if app_info_section is None:
		return None
	return app_info_section.get(b'extended')

def get_steamplay_compat_tools():
	extended = _get_steamplay_appinfo_extended()
	if not extended:
		return {}
	compat_tools_list = extended.get(b'compat_tools')
	if not compat_tools_list:
		return {}

	tools = {}
	for k, v in compat_tools_list.items():
		#appid, from_oslist, to_oslist might be useful in some situation
		#This just maps "proton_37" to "Proton 3.7-8" etc
		display_name = v.get(b'display_name')
		if display_name:
			tools[k.decode('utf-8', errors='ignore')] = display_name.decode('utf-8', errors='ignore')
	return tools

def get_steamplay_whitelist():
	extended = _get_steamplay_appinfo_extended()
	if not extended:
		return {}
	app_mappings = extended.get(b'app_mappings')
	if not app_mappings:
		return {}

	apps = {}
	for k, v in app_mappings.items():
		#v has an "appid" key which seems pointless, but oh well
		#Only other keys are "config" which is "none" except for Google Earth VR so whatevs, "comment" which is the game name but might have inconsistent formatting, and "platform" which is only Linux
		tool = v.get(b'tool')
		if tool:
			apps[k.decode('utf-8', errors='ignore')] = tool.decode('utf-8', errors='ignore')
	return apps

def format_genre(genre_id):
	return genre_ids.get(genre_id, 'unknown {0}'.format(genre_id))

def process_launchers(game, launch):
	launch_items = {}
	user_config = game.app_state.get('UserConfig')
	installed_betakey = user_config.get('betakey') if user_config else None
	for launch_item in launch.values():
		#Key here is 0, 1, 2, n... which is a bit useless, it's really just a boneless list. Anyway, each of these values is another dict containing launch parameters, for each individual platform or configuration, e.g. Windows 32-bit, Windows 64-bit, MacOS, etc
		#If you wanted to do secret evil things: b'executable' = 'CoolGame.sh' b'arguments' (optional) = '--fullscreen --blah' b'description' = 'Cool Game'

		#Actually, sometimes the key doesn't start at 0, which is weird, but anyway it still doesn't really mean much, it just means we can't get the first item by getting key 0
		launcher = {'exe': None, 'args': None, 'description': None, 'type': None}
		executable_name = launch_item.get(b'executable')
		if executable_name:
			exe_name = executable_name.decode('utf-8', errors='backslashreplace')
			if exe_name.startswith('steam://open'):
				#None of that
				continue
			launcher['exe'] = exe_name
		
		executable_arguments = launch_item.get(b'arguments')
		if executable_arguments:
			if isinstance(executable_arguments, appinfo.Integer):
				launcher['args'] = str(executable_arguments.data)
			else:
				launcher['args'] = executable_arguments.decode('utf-8', errors='backslashreplace')

		description = launch_item.get(b'description')
		if description:
			launcher['description'] = description.decode('utf-8', errors='backslashreplace')

		launch_type = launch_item.get(b'type')
		if launch_type:
			launcher['type'] = launch_type.decode('utf-8', errors='backslashreplace')
		
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
			betakey = launch_item_config.get(b'betakey')
			if betakey and betakey != installed_betakey:
				continue
		if platform not in launch_items:
			launch_items[platform] = []
		launch_items[platform].append(launcher)

	for platform, platform_launchers in launch_items.items():
		platform_launcher = None
		if len(platform_launchers) == 1:
			platform_launcher = platform_launchers[0]
		else:
			if platform not in game.extra_launchers:
				game.extra_launchers[platform] = []
			game.extra_launchers[platform] += platform_launchers[1:]
			game.metadata.specific_info['Multiple-Launchers'] = True
			platform_launcher = platform_launchers[0]

		game.launchers[platform] = platform_launcher
				
def add_icon_from_common_section(game, common_section):
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
			icon = look_for_icon(icon_hash)
		except IconError as icon_error:
			icon_exception = icon_error
			continue
		except IconNotFoundError:
			continue
		if icon:
			game.metadata.images['Icon'] = icon
			icon_exception = None
			found_an_icon = True
			break
	if main_config.debug:
		if icon_exception:
			print(game.name, game.app_id, icon_exception)
		elif potentially_has_icon and not found_an_icon:
			print('Could not find icon for', game.name, game.app_id)
		elif not potentially_has_icon:
			print(game.name, game.app_id, 'does not even have an icon')

def add_metadata_from_appinfo_common_section(game, common):
	add_icon_from_common_section(game, common)

	#oslist and osarch may come in handy (former is comma separated windows/macos/linux; latter is b'64' or purrsibly b'32'), osextended is sometimes like 'macos64'
	#eulas is a list, so it could be used to detect if game has third-party EULA
	#small_capsule and header_image refer to image files that don't seem to be there so I dunno
	#workshop_visible and community_hub_visible could also tell you stuff about if the game has a workshop and a... community hub
	#releasestate: 'released' might be to do with early access?
	#exfgls = exclude from game library sharing
	#b'requireskbmouse' and b'kbmousegame' are also things, but don't seem to be 1:1 with games that have controllersupport = none
	#name_localized has a dict with e.g. b'japanese' as the keys; will worry about that later...
	language_list = common.get(b'languages')
	if language_list:
		game.metadata.languages = translate_language_list(language_list)

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
		game.metadata.genre = format_genre(primary_genre_id)
	#TODO: Combine additional genres where appropriate (e.g. Action + Adventure, Massively Multiplayer + RPG)
	if additional_genre_ids:
		game.metadata.specific_info['Additional-Genres'] = [format_genre(id) for id in additional_genre_ids]
	if content_warning_ids:
		game.metadata.specific_info['Content-Warnings'] = [format_genre(id) for id in content_warning_ids]
	#"genre" doesn't look like a word anymore

	release_date = common.get(b'steam_release_date')
	#Seems that original_release_date is here sometimes, and original_release_date sometimes appears along with steam_release_date where a game was only put on Steam later than when it was actually released elsewhere
	if not release_date:
		release_date = common.get(b'original_release_date')
	if release_date:
		release_datetime = datetime.datetime.fromtimestamp(release_date.data)
		game.metadata.year = release_datetime.year
		game.metadata.month = calendar.month_name[release_datetime.month]
		game.metadata.day = release_datetime.day

	store_categories_list = common.get(b'category')
	if store_categories_list:
		#keys are category_X where X is some arbitrary ID, values are always Integer = 1
		#This is the thing where you go to the store sidebar and it's like "Single-player" "Multi-player" "Steam Achievements" etc"
		cats = [store_categories.get(key, key) for key in [key.decode('utf-8', errors='backslashreplace') for key in store_categories_list.keys()]]
		game.metadata.specific_info['Store-Categories'] = cats #meow
		game.metadata.specific_info['Has-Achievements'] = 'Steam Achievements' in cats
		game.metadata.specific_info['Has-Trading-Cards'] = 'Steam Trading Cards' in cats
		is_single_player_only = True
		for cat in cats:
			if 'multiplayer' in cat.lower() or 'multi-player' in cat.lower() or 'co-op' in cat.lower() or 'split screen' in cat.lower():
				is_single_player_only = False
				break
		if is_single_player_only:
			game.metadata.specific_info['Number-of-Players'] = 1
		

	category = common.get(b'type', b'Unknown').decode('utf-8', errors='backslashreplace')
	if category in ('game', 'Game'):
		#This makes the categories like how they are with DOS/Mac
		game.metadata.categories = ['Games']
	elif category in ('Tool', 'Application'):
		#Tool is for SDK/level editor/dedicated server/etc stuff, Application is for general purchased software
		game.metadata.categories = ['Applications']
	elif category == 'Demo':
		game.metadata.categories = ['Trials']
	else:
		game.metadata.categories = [category]

	has_adult_content = common.get(b'has_adult_content') #Integer object with data = 0 or 1, as most bools here seem to be
	game.metadata.nsfw = False if has_adult_content is None else bool(has_adult_content.data)

	only_vr = common.get(b'onlyvrsupport')
	vr_support = common.get(b'openvrsupport')
	if only_vr is not None and only_vr.data:
		game.metadata.specific_info['VR-Support'] = 'Required'
	elif vr_support is not None and vr_support.data:
		game.metadata.specific_info['VR-Support'] = 'Optional'

	metacritic_score = common.get(b'metacritic_score')
	if metacritic_score:
		#Well why not
		game.metadata.specific_info['Metacritic-Score'] = metacritic_score.data
	metacritic_url = common.get(b'metacritic_fullurl')
	if metacritic_url:
		game.metadata.specific_info['Metacritic-URL'] = metacritic_url.decode('utf8', errors='backslashreplace')

	review_score = common.get(b'review_score')
	#This is Steam's own review section, I guess?
	#This seems to be a number from 2 to 9 inclusive. Not sure what it means though
	#There is also review_score_bombs? What the heck
	if review_score:
		game.metadata.specific_info['Review-Score'] = review_score.data
	review_percentage = common.get(b'review_percentage')
	#Also seemingly related to Steam reviews, and there is also a review_percentage_bombs, but I still don't know exactly what this does
	if review_percentage:
		game.metadata.specific_info['Review-Percentage'] = review_percentage.data
	
	sortas = common.get(b'sortas')
	if sortas:
		game.metadata.specific_info['Sort-Name'] = sortas.decode('utf8', errors='backslashreplace')

	game.metadata.specific_info['Controlller-Support'] = common.get(b'controller_support', b'none').decode('utf-8', errors='backslashreplace')

	if steam_state.localization_available:
		store_tag_names = steam_state.localization['localization']['english']['store_tags']
		store_tag_ids_list = common.get(b'store_tags')
		if store_tag_ids_list:
			store_tags = [store_tag_names.get(id, id) for id in [str(value.data) for value in store_tag_ids_list.values()]]
			game.metadata.specific_info['Store-Tags'] = store_tags

	franchise_name = None
	associations = common.get(b'associations')

	if associations:
		associations_dict = {}
		for association in associations.values():
			#Can also get multiple developers/publishers this way (as can sometimes happen if a separate developer does the Linux port, for example)
			association_type_value = association.get(b'type')
			if isinstance(association_type_value, appinfo.Integer):
				association_type = str(association_type_value.data)
			else:
				association_type = association_type_value.decode('utf-8', errors='ignore')

			association_name_value = association.get(b'name')
			if isinstance(association_name_value, appinfo.Integer):
				association_name = str(association_name_value.data)
			else:
				association_name = association_name_value.decode('utf-8', errors='ignore')
				
			associations_dict[association_type] = association_name

		if 'franchise' in associations_dict:
			franchise_name = associations_dict['franchise']
			if franchise_name.lower().endswith(' franchise'):
				franchise_name = franchise_name[:-len(' franchise')]
			elif franchise_name.lower().endswith(' series'):
				franchise_name = franchise_name[:-len(' series')]
			if franchise_name.lower().startswith('the '):
				franchise_name = franchise_name[len('the '):]

			franchise_name = normalize_name_case(franchise_name)
			
			not_actual_franchises = ('Playism', 'Hentai', 'Coming-of-Age')
			if franchise_name.lower() not in {assoc.lower() for assoc_type, assoc in associations_dict.items() if assoc_type != 'franchise'} and franchise_name not in not_actual_franchises:
				#These franchises aren't the game series at all, they're just the developer/publisher etc used for marketing purposes on the store, and not relevant to what we want to use this field for
				game.metadata.series = remove_capital_article(franchise_name)
	
def add_metadata_from_appinfo_extended_section(game, extended):
	developer = extended.get(b'developer')
	if developer:
		if isinstance(developer, appinfo.Integer):
			#Cheeky buggers... the doujin developer 773 is represented by the actual integer value 773 here, for some reason
			game.metadata.developer = str(developer.data)
		else:
			game.metadata.developer = normalize_developer(developer.decode('utf-8', errors='backslashreplace'))
	publisher = extended.get(b'publisher')
	if publisher:
		if isinstance(publisher, appinfo.Integer):
			game.metadata.publisher = str(publisher.data)
		else:
			publisher = normalize_developer(publisher.decode('utf-8', errors='backslashreplace'))
			if publisher in ('none', 'Self Published'):
				game.metadata.publisher = game.metadata.developer
			else:
				game.metadata.publisher = publisher

	homepage = extended.get(b'homepage')
	if homepage:
		game.metadata.specific_info['URL'] = homepage.decode('utf-8', errors='backslashreplace')
	developer_url = extended.get(b'developer_url')
	if developer_url:
		game.metadata.specific_info['Author-URL'] = developer_url.decode('utf-8', errors='backslashreplace')
	gamemanualurl = extended.get(b'gamemanualurl')
	if gamemanualurl:
		game.metadata.specific_info['Manual-URL'] = gamemanualurl.decode('utf-8', errors='backslashreplace')

	isfreeapp = extended.get(b'isfreeapp')
	if isfreeapp:
		if isinstance(isfreeapp, bytes):
			#Why do you do this?
			game.metadata.specific_info['Is-Free'] = isfreeapp != b'0'
		elif isinstance(isfreeapp, appinfo.Integer):
			game.metadata.specific_info['Is-Free'] = isfreeapp.data != 0
	#icon is either blank or something like 'steam/games/icon_garrysmod' which doesn't exist so no icon for you (not that way)
	#order and noservers seem like they might mean something, but I dunno what
	#state = eStateAvailable verifies that it is indeed available (wait maybe it doesn't)
	#vrheadsetstreaming and listofdlc might be useful (the latter is a comma separated list of AppIDs for each DLC in existence for this game)
	#mustownapptopurchase: If present, appID of a game that you need to buy first (parent of DLC, or something like Source SDK Base for Garry's Mod, etc)
	#dependantonapp: Probably same sort of thing, like Half-Life: Opposing Force is dependent on original Half-Life

def process_appinfo_config_section(game, app_info_section):
	config = app_info_section.get(b'config')
	if config:
		#contenttype = 3 in some games but not all of them? nani
		launch = config.get(b'launch')
		#This key would actually tell us the executable and arguments used to actually launch the game. It's probably not a good idea to do that directly though, mostly because most games are DRM'd to Steam, so it's probably a good idea to go through the Steam client like we are now.
		#Anyway, we're going to use it a bit more responsibly
		if launch:
			process_launchers(game, launch)
		else:
			raise NotLaunchableError('No launch entries in config section')

def add_metadata_from_appinfo(game, app_info_section):
	#Alright let's get to the fun stuff
	common = app_info_section.get(b'common')
	if common:
		add_metadata_from_appinfo_common_section(game, common)

	extended = app_info_section.get(b'extended')
	if extended:
		add_metadata_from_appinfo_extended_section(game, extended)

	localization = app_info_section.get(b'localization')
	if localization:
		if b'richpresence' in localization:
			#Keys of this are 'english' or presumably other languages and then 'tokens' and then it's a bunch of stuff
			game.metadata.specific_info['Rich-Presence'] = True

	if b'ufs' in app_info_section:
		game.metadata.save_type = SaveType.Cloud
	else:
		#I think it's a fair assumption that every game on Steam will have _some_ sort of save data (even if just settings and not progress) so until I'm proven wrong... whaddya gonna do
		game.metadata.save_type = SaveType.Internal

fluff_editions = ['GOTY', 'Game of the Year', 'Definitive', 'Enhanced', 'Special', 'Ultimate', 'Premium', 'Gold', 'Extended', 'Super Turbo Championship']
name_suffixes = ['Demo', 'Beta', 'GOTY', "Director's Cut", 'Unstable', 'Complete', 'Complete Collection', "Developer's Cut"] + [e + ' Edition' for e in fluff_editions]
name_suffix_matcher = re.compile(r'(?: | - |: )?(?:The )?(' + '|'.join(name_suffixes) + ')$', re.RegexFlag.IGNORECASE)
def normalize_name_case(name, name_to_test_for_upper=None):
	if not name_to_test_for_upper:
		name_to_test_for_upper = name

	if main_config.normalize_name_case == 1:
		if name_to_test_for_upper.isupper():
			return title_case(name, words_to_ignore_case=capitalized_words)
		return name
	if main_config.normalize_name_case == 2:
		if name_to_test_for_upper.isupper():
			return title_case(name, words_to_ignore_case=capitalized_words)

		#Assume minimum word length of 4 to avoid acronyms, although those should be in capitalized_words I guess
		return re.sub(r"[\w'-]{4,}", lambda match: title_case(match[0], words_to_ignore_case=capitalized_words) if match[0].isupper() else match[0], name)
	if main_config.normalize_name_case == 3:
		return title_case(name, words_to_ignore_case=capitalized_words)
	
	return name

def fix_name(name):
	name = name.replace('™', '')
	name = name.replace('®', '')
	name = name.replace(' : ', ': ') #Oi mate what kinda punctuation is this
	name = name.replace('[diary]', 'diary') #Stop that
	name = name.replace('(VI)', 'VI') #Why is Tomb Raider: The Angel of Darkness like this

	if name.startswith('ARCADE GAME SERIES'):
		#This is slightly subjective as to whether or not one should do this, but I believe it should
		name = name[20:] + ' (Arcade Game Series)'

	name_to_test_for_upper = chapter_matcher.sub('', name)
	name_to_test_for_upper = name_suffix_matcher.sub('', name_to_test_for_upper)
	name = normalize_name_case(name, name_to_test_for_upper)
		
	#Hmm... this is primarily so series_detect and disambiguate work well, it may be worthwhile putting them back afterwards (put them in some kind of field similar to Filename-Tags but disambiguate always adds them in); depending on how important it is to have "GOTY" or "Definitive Edition" etc in the name if not ambiguous
	name = name_suffix_matcher.sub(r' (\1)', name)
	return name

def process_launcher(game, launcher):
	game.metadata.extension = os.path.splitext(launcher['exe'])[-1][1:].lower()
	#See what we can tell about the game exe. Everything that is a DOS game packaged with DOSBox will have DOSBox for all launchers (from what I know so far), except for Duke Nukem 3D, which has a "launch OpenGL" and a "launch DOS" thing, so.. hmm
	#You can't detect that a game uses Origin that I can tell... dang
	executable_basename = launcher['exe']
	if executable_basename:
		if '/' in executable_basename:
			executable_basename = executable_basename.split('/')[-1]
		elif '\\' in executable_basename:
			executable_basename = executable_basename.split('\\')[-1]
		game.metadata.specific_info['Executable-Name'] = executable_basename

	if executable_basename:
		if executable_basename.lower() in ('dosbox.exe', 'dosbox', 'dosbox.sh'):
			game.metadata.specific_info['Wrapper'] = 'DOSBox'
		elif executable_basename.lower() in ('scummvm.exe', 'scummvm', 'scummvm.sh'):
			game.metadata.specific_info['Wrapper'] = 'ScummVM'
	
	if launcher['args'] and '-uplay_steam_mode' in launcher['args']:
		game.metadata.specific_info['Launcher'] = 'uPlay'

def process_game(app_id, folder, app_state):
	#installdir is the subfolder of library_folder/steamapps/common where the game is actually located, if that's ever useful
	#UserConfig might be interesting... normally it just has a key 'language' which is set to 'english' etc, sometimes duplicating name and app_id as 'gameid' for no reason, but also has things like 'lowviolence': '1' inside Left 4 Dead 2 for example (because I'm Australian I guess), so... well, I just think that's kinda neat, although probably not useful for our purposes here; also for TF2 it has 'betakey': 'prerelease' so I guess that has to do with opt-in beta programs

	#We could actually just leave it here and create a thing with xdg-open steam://rungame/app_id, but where's the fun in that? Much more metadata than that
	try:
		app_id = int(app_id)
	except ValueError:
		if main_config.debug:
			print('Should not happen:', app_id, app_state.get('name'), 'is not numeric')
		return

	game = SteamGame(app_id, folder, app_state)
	game.metadata.platform = 'Steam'
	lowviolence = app_state.get('UserConfig', {}).get('lowviolence')
	if lowviolence:
		game.metadata.specific_info['Low-Violence'] = lowviolence == '1'
	game.metadata.specific_info['Steam-AppID'] = app_id
	game.metadata.specific_info['Library-Folder'] = folder
	game.metadata.media_type = MediaType.Digital

	appinfo_entry = game.appinfo
	if appinfo_entry:
		process_appinfo_config_section(game, appinfo_entry)

	steamplay_overrides = get_steamplay_overrides()
	steamplay_whitelist = get_steamplay_whitelist()
	appid_str = str(game.app_id)

	if not game.launchers:
		raise NotLaunchableError('Game cannot be launched')
	else:
		launcher = list(game.launchers.values())[0]
		if appid_str in steamplay_overrides:
			#Natively ported game, but forced to use Proton/etc for reasons
			tool = steamplay_overrides[appid_str]
			game.metadata.emulator_name = get_steamplay_compat_tools().get(tool, tool)
			game.metadata.specific_info['Steam-Play-Forced'] = True
		elif appid_str in steamplay_whitelist:
			tool = steamplay_whitelist[appid_str]
			game.metadata.emulator_name = get_steamplay_compat_tools().get(tool, tool)
			game.metadata.specific_info['Steam-Play-Whitelisted'] = True
		elif 'linux' in game.launchers:
			launcher = game.launchers['linux']
		elif 'linux_64' in game.launchers:
			launcher = game.launchers['linux_64']
		elif 'linux_32' in game.launchers:
			launcher = game.launchers['linux_32']
		else:
			global_tool = steamplay_overrides.get('0')
			if global_tool:
				game.metadata.emulator_name = get_steamplay_compat_tools().get(global_tool, global_tool)
				game.metadata.specific_info['Steam-Play-Whitelisted'] = False
			else:
				#If global tool is not set; this game can't be launched and will instead say "Invalid platform"
				game.metadata.specific_info['No-Valid-Launchers'] = True
		process_launcher(game, launcher)
		#Potentially do something with game.extra_launchers... I dunno, really

	#userdata/<user ID>/config/localconfig.vdf has last time played stats, so that's a thing I guess
	#userdata/<user ID>/7/remote/sharedconfig.vdf has tags/categories etc as well

	if game.metadata.specific_info.get('No-Valid-Launchers', False) and not main_config.force_create_launchers:
		raise NotLaunchableError('Platform not supported and Steam Play not used')

	if appinfo_entry:
		add_metadata_from_appinfo(game, appinfo_entry)
	#Other metadata that we can't or won't fill in:
	#cpu_info, screen_info, extension: Irrelevant (not going to do something silly like use the current user's CPU/monitor specs)
	#product_code: Not really a thing
	#regions: World or user's region? Hmm, maybe not entirely relevant with PC games
	#revision: Irrelevant since software versions aren't always linear numbers?
	#tv_type could be Agnostic, but it's like... I dunno if I'd consider it to be relevant
	
	game.make_launcher()

def iter_steam_installed_appids():
	for library_folder in get_steam_library_folders():
		acf_files = glob.glob(os.path.join(library_folder, 'steamapps', '*.acf'))
		for acf_file_path in acf_files:
			#Technically I could try and parse it without steamfiles, but that would be irresponsible, so I shouldn't do that
			with open(acf_file_path, 'rt') as acf_file:
				app_manifest = acf.load(acf_file)
			app_state = app_manifest.get('AppState')
			if not app_state:
				#Should only happen if .acf is junk (or format changes dramatically), there's no other keys than AppState
				continue

			app_id = app_state.get('appid')
			if app_id is None:
				#Yeah we need that
				continue

			#https://github.com/lutris/lutris/blob/master/docs/steam.rst
			try:
				state_flags = int(app_state.get('StateFlags'))
				if not state_flags:
					continue
			except ValueError:
				continue

			#Only yield fully installed games
			if (state_flags & 4) == 0:
				if main_config.debug:
					print('Skipping', app_state.get('name'), app_id, 'as it is not actually installed (StateFlags =', state_flags, ')')
				continue

			yield library_folder, app_id, app_state

no_longer_exists_cached_appids = None

def no_longer_exists(appid):
	if not is_steam_available():
		#I guess if you uninstalled Steam then you're not gonna play any Steam games, huh
		return False

	global no_longer_exists_cached_appids
	if no_longer_exists_cached_appids is None:
		no_longer_exists_cached_appids = [id for folder, id, state in iter_steam_installed_appids()]

	return appid not in no_longer_exists_cached_appids

def process_steam():
	if not is_steam_available():
		return

	time_started = time.perf_counter()

	for folder, app_id, app_state in iter_steam_installed_appids():
		if not main_config.full_rescan:
			if launchers.has_been_done('Steam', app_id):
				continue

		try:
			process_game(app_id, folder, app_state)
		except NotLaunchableError as ex:
			if main_config.debug:
				print(app_state.get('name', app_id), app_id, 'is skipped because', ex)
			continue

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Steam finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	process_steam()
