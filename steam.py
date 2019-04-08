#!/usr/bin/env python

import os
import glob
import zipfile
import time
import datetime
import calendar

try:
	from PIL import Image
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

from config import main_config
from common import junk_suffixes, title_case, chapter_matcher, find_franchise_from_game_name
from common_types import MediaType, SaveType
import region_detect
import launchers
from metadata import Metadata

from data.steam_genre_ids import genre_ids
from data.steam_developer_overrides import developer_overrides
from data.steam_store_categories import store_categories

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
			else:
				self.app_info = None
				self.app_info_available = False
				self.config = None
				self.config_available = False
		@property
		def app_info_path(self):
			return os.path.join(self.steamdir, 'appcache', 'appinfo.vdf')

		@property
		def config_path(self):
			return os.path.join(self.steamdir, 'config', 'config.vdf')

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
			possible_locations = ['~/.steam/steam', '~/.local/share/steam']

			for location in possible_locations:
				location = os.path.expanduser(location)

				if os.path.isdir(location):
					return location
				elif os.path.islink(location):
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
			return []
		#Not sure I like the condition on k here, but I guess it'll work. The keys under LibraryFolders are TimeNextStatsReport and ContentStatsID (whatever those do), and then 1 2 3 4 for each library folder, but I dunno how reliable that is. Anyway, that should do the trick, I guess; if someone breaks something it's gonna break
		return [v for k, v in library_folders.items() if k.isdigit()]

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
	def __init__(self, app_id, name):
		self.app_id = app_id
		self.name = name
		self.metadata = Metadata()
		self.icon = None

		self.native_platforms = set()

	def make_launcher(self):
		#Could also use steam -appid {0} here, but like... I dunno if I should
		params = launchers.LaunchParams('xdg-open', ['steam://rungameid/{0}'.format(self.app_id)])
		launchers.make_launcher(params, self.name, self.metadata, 'Steam', self.app_id, self.icon)

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
					#.ico file is shitty and broken and has an invalid size in its own fucking header
					#OSError is also thrown too sometimes when it's not actually an .ico file
					raise IconError('.ico file {0} has some annoying error: {1}'.format(icon_hash, str(ex))) from ex

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
				extracted_icon_folder = os.path.join(main_config.image_folder, 'icons', 'extracted_from_zip', icon_hash)
				return zip_file.extract(extracted_icon_file, path=extracted_icon_folder)

	raise IconNotFoundError('{0} not found'.format(icon_hash))

def translate_language_list(languages):
	langs = []
	for language_name, _ in languages.items():
		#value is an Integer object but it's always 1, I dunno what the 0 means, because it's like, if the language isn't there, it just wouldn't be in the dang list anyway
		language_name = language_name.decode('utf-8', errors='backslashreplace')
		if language_name == 'koreana': #I don't know what the a at the end is for, but Steam does that
			langs.append(region_detect.get_language_by_english_name('Korean'))
		elif language_name == 'schinese': #Simplified Chinese
			langs.append(region_detect.get_language_by_english_name('Chinese'))
		elif language_name == 'tchinese':
			langs.append(region_detect.get_language_by_english_name('Traditional Chinese'))
		elif language_name == 'brazilian':
			langs.append(region_detect.get_language_by_english_name('Brazilian Portugese'))
		elif language_name == 'latam':
			langs.append(region_detect.get_language_by_english_name('Latin American Spanish'))
		else:
			language = region_detect.get_language_by_english_name(language_name, case_insensitive=True)
			if language:
				langs.append(language)
			elif main_config.debug:
				print('Unknown language:', language_name)

	return langs

def normalize_developer(dev):
	dev = junk_suffixes.sub('', dev)


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
	found_first_launcher = False
	for launch_item in launch.values():
		#Key here is 0, 1, 2, n... which is a bit useless, it's really just a boneless list. Anyway, each of these values is another dict containing launch parameters, for each individual platform or configuration, e.g. Windows 32-bit, Windows 64-bit, MacOS, etc
		#If you wanted to do secret evil things: b'executable' = 'CoolGame.sh' b'arguments' (optional) = '--fullscreen --blah' b'description' = 'Cool Game'

		#Actually, sometimes the key doesn't start at 0, which is weird, but anyway it still doesn't really mean much, it just means we can't get the first item by getting key 0
		if not found_first_launcher:
			#Look at the first launcher to see what we can tell about the game exe. Everything that is a DOS game packaged with DOSBox will have DOSBox for all launchers (from what I know so far), except for Duke Nukem 3D, which has a "launch OpenGL" and a "launch DOS" thing, and so because the first launcher is the OpenGL mode it won't be detected as a DOSBox wrapper and maybe that's correct
			executable_name = launch_item.get(b'executable')
			if executable_name:
				executable_basename = executable_name.decode('utf-8', errors='ignore')
				if '/' in executable_basename:
					executable_basename = executable_basename.split('/')[-1]
				elif '\\' in executable_basename:
					executable_basename = executable_basename.split('\\')[-1]
				if executable_basename.lower() in ('dosbox.exe', 'dosbox', 'dosbox.sh'):
					game.metadata.specific_info['Is-DOSBox-Wrapper'] = True
			executable_arguments = launch_item.get(b'arguments')
			if executable_arguments:
				if '-uplay_steam_mode' in executable_arguments.decode('utf-8', errors='ignore'):
					game.metadata.specific_info['Launcher'] = 'uPlay'
			#You can't detect that a game uses Origin that I can tell... dang
			found_first_launcher = True

		launch_item_config = launch_item.get(b'config')
		if launch_item_config:
			launch_item_oslist = launch_item_config.get(b'oslist', b'')
			if launch_item_oslist:
				#I've never seen oslist be a list, but it is always a byte string, so maybe there's some game where it's multiple platforms comma separated
				#(Other key: osarch = sometimes Integer with data = 32/64, or b'32' or b'64')
				game.native_platforms.add(launch_item_oslist.decode('utf-8', errors='ignore'))

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
			game.icon = icon
			icon_exception = None
			found_an_icon = True
			break
	if main_config.debug:
		if icon_exception:
			print(game.name, game.app_id, icon_exception)
		elif potentially_has_icon and not found_an_icon:
			print('Could not find icon for', game.name, game.app_id)

def add_metadata_from_appinfo_common_section(game, common):
	add_icon_from_common_section(game, common)

	#oslist and osarch may come in handy (former is comma separated windows/macos/linux; latter is b'64' or purrsibly b'32')
	#eulas is a list, so it could be used to detect if game has third-party EULA
	#small_capsule and header_image refer to image files that don't seem to be there so I dunno
	#store_tags is a list of numeric IDs, they're the user-supplied tags on the store
	#workshop_visible and community_hub_visible could also tell you stuff about if the game has a workshop and a... community hub
	#releasestate: 'released' might be to do with early access?
	#exfgls = exclude from game library sharing
	#b'requireskbmouse' and b'kbmousegame' are also things, but don't seem to be 1:1 with games that have controllersupport = none
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
	sortas = common.get(b'sortas')
	if sortas:
		game.metadata.specific_info['Sort-Name'] = sortas.decode('utf8', errors='backslashreplace')

	game.metadata.specific_info['Controlller-Support'] = common.get(b'controller_support', b'none').decode('utf-8', errors='backslashreplace')

	franchise_name = None
	associations = common.get(b'associations')
	if associations:
		for association in associations.values():
			#Can also get multiple developers/publishers this way (as can sometimes happen if a separate developer does the Linux port, for example)
			if association.get(b'type') == b'franchise':
				franchise = association.get(b'name')
				if franchise:
					franchise_name = franchise.decode('utf-8', errors='backslashreplace')
					if franchise_name.endswith(' Franchise'):
						franchise_name = franchise_name[:-len(' Franchise')]
					elif franchise_name.endswith(' Series'):
						franchise_name = franchise_name[:-len(' Series')]
					if franchise_name == 'THE KING OF FIGHTERS':
						#So that it matches up with series.ini
						franchise_name = 'King of Fighters'
					if main_config.normalize_name_case and franchise_name.isupper():
						franchise_name = title_case(franchise_name)
					game.metadata.franchise = franchise_name

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
	#icon is either blank or something like 'steam/games/icon_garrysmod' which doesn't exist so no icon for you (not that way)
	#order and noservers seem like they might mean something, but I dunno what
	#state = eStateAvailable verifies that it is indeed available (wait maybe it doesn't)
	#vrheadsetstreaming and listofdlc might be useful (the latter is a comma separated list of AppIDs for each DLC in existence for this game)
	#mustownapptopurchase: If present, appID of a game that you need to buy first (parent of DLC, or something like Source SDK Base for Garry's Mod, etc)
	#dependantonapp: Probably same sort of thing, like Half-Life: Opposing Force is dependent on original Half-Life

def add_metadata_from_appinfo(game):
	game_app_info = steam_state.app_info.get(game.app_id)
	if game_app_info is None:
		#Probably shouldn't happen if all is well and that game is supposed to be there
		print('Not for', game.app_id)
		return

	#There are other keys here too but I dunno if they're terribly useful, just stuff about size and state and access token and bleh
	#last_update is a Unix timestamp for the last time the user updated the game
	sections = game_app_info.get('sections')
	if sections is None:
		print('No sections')
		return
	#This is the only key in sections, and from now on everything is a bytes instead of a str, seemingly
	app_info_section = sections.get(b'appinfo')
	if app_info_section is None:
		print('No appinfo')
		return

	#Alright let's get to the fun stuff
	common = app_info_section.get(b'common')
	if common:
		add_metadata_from_appinfo_common_section(game, common)

	extended = app_info_section.get(b'extended')
	if extended:
		add_metadata_from_appinfo_extended_section(game, extended)

	config = app_info_section.get(b'config')
	if config:
		#contenttype = 3 in some games but not all of them? nani
		launch = config.get(b'launch')
		#This key would actually tell us the executable and arguments used to actually launch the game. It's probably not a good idea to do that directly though, mostly because most games are DRM'd to Steam, so it's probably a good idea to go through the Steam client like we are now.
		#Anyway, we're going to use it a bit more responsibly
		if launch:
			process_launchers(game, launch)
		else:
			game.metadata.specific_info['No-Launchers'] = True

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

def fix_name(name):
	name = name.replace('™', '')
	name = name.replace('®', '')
	if main_config.normalize_name_case:
		name_to_test_for_upper = chapter_matcher.sub('', name)
		if name_to_test_for_upper.lower().endswith(' demo'):
			#Hmm maybe I should make this a more complexy regex to catch " - Demo" as well, and maybe that could reused for other similar stuff down the line
			name_to_test_for_upper = name_to_test_for_upper[:-5]

		if name_to_test_for_upper.isupper():
			name = title_case(name, words_to_ignore_case=['GOTY', 'XL', 'VR', 'XCOM', 'VVVVVV', 'RPG', 'HD'])
	return name

def process_game(app_id, name=None):
	if not name:
		name = '<unknown game {0}>'.format(app_id)
	name = fix_name(name)

	#We could actually just leave it here and create a thing with xdg-open steam://rungame/app_id, but where's the fun in that? Much more metadata than that
	try:
		app_id = int(app_id)
	except ValueError:
		if main_config.debug:
			print('Should not happen:', app_id, name, 'is not numeric')
		return

	game = SteamGame(app_id, name)
	game.metadata.platform = 'Steam'
	game.metadata.specific_info['Steam-AppID'] = app_id
	game.metadata.media_type = MediaType.Digital

	if steam_state.app_info_available:
		add_metadata_from_appinfo(game)

	if not game.metadata.franchise:
		sort_name = game.metadata.specific_info.get('Sort-Name', game.name)
		franchise = find_franchise_from_game_name(sort_name)
		if franchise:
			game.metadata.franchise = franchise

	steamplay_overrides = get_steamplay_overrides()
	steamplay_whitelist = get_steamplay_whitelist()
	appid_str = str(game.app_id)
	if appid_str in steamplay_overrides:
		#Natively ported game, but forced to use Proton/etc for reasons
		tool = steamplay_overrides[appid_str]
		game.metadata.emulator_name = get_steamplay_compat_tools().get(tool, tool)
		game.metadata.specific_info['Steam-Play-Forced'] = True
	elif appid_str in steamplay_whitelist:
		tool = steamplay_whitelist[appid_str]
		game.metadata.emulator_name = get_steamplay_compat_tools().get(tool, tool)
		game.metadata.specific_info['Steam-Play-Whitelisted'] = True
	elif 'linux' not in game.native_platforms:
		global_tool = steamplay_overrides.get('0')
		if global_tool:
			game.metadata.emulator_name = get_steamplay_compat_tools().get(global_tool, global_tool)
			game.metadata.specific_info['Steam-Play-Whitelisted'] = False
		else:
			#If global tool is not set; this game can't be launched and will instead say "Invalid platform"
			game.metadata.specific_info['No-Launchers'] = True

	#userdata/<user ID>/config/localconfig.vdf has last time played stats, so that's a thing I guess
	#userdata/<user ID>/7/remote/sharedconfig.vdf has tags/categories etc as well

	#Other metadata that we can't or won't fill in:
	#cpu_info, screen_info, extension: Irrelevant (not going to do something silly like use the current user's CPU/monitor specs)
	#product_code: Not really a thing
	#regions: World or user's region? Hmm, maybe not entirely relevant with PC games
	#revision: Irrelevant since software versions aren't always linear numbers?
	#tv_type could be Agnostic, but it's like... I dunno if I'd consider it to be relevant
	if game.metadata.specific_info.get('No-Launchers', False) and not main_config.force_create_launchers:
		return

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
				continue

			yield app_id, app_state

no_longer_exists_cached_appids = None

def no_longer_exists(appid):
	if not is_steam_available():
		#I guess if you uninstalled Steam then you're not gonna play any Steam games, huh
		return False

	global no_longer_exists_cached_appids
	if no_longer_exists_cached_appids is None:
		no_longer_exists_cached_appids = [id for id, state in iter_steam_installed_appids()]

	return appid not in no_longer_exists_cached_appids

def process_steam():
	if not is_steam_available:
		return

	time_started = time.perf_counter()

	for app_id, app_state in iter_steam_installed_appids():
		if not main_config.full_rescan:
			if launchers.has_been_done('Steam', app_id):
				continue

		name = app_state.get('name')
		#installdir is the subfolder of library_folder/steamapps/common where the game is actually located, if that's ever useful
		#UserConfig might be interesting... normally it just has a key 'language' which is set to 'english' etc, sometimes duplicating name and app_id as 'gameid' for no reason, but also has things like 'lowviolence': '1' inside Left 4 Dead 2 for example (because I'm Australian I guess), so... well, I just think that's kinda neat, although probably not useful for our purposes here; also for TF2 it has 'betakey': 'prerelease' so I guess that has to do with opt-in beta programs
		#Anyway I don't think we need any of that for now
		process_game(app_id, name)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Steam finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	process_steam()
