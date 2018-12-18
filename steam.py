import os
import glob
import zipfile
import time
import datetime

try:
	#Have to import it like this, because the directory is inside another directory
	#Anyway it _should_ be here since I made it a submodule anyway, but like... y'know, just to be safe
	from steamfiles.steamfiles import acf, appinfo
	have_steamfiles = True
except ModuleNotFoundError:
	have_steamfiles = False

from config import main_config
from common import junk_suffixes
from common_types import MediaType, SaveType
import region_detect
import launchers
from metadata import Metadata

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
			else:
				self.app_info = None
				self.app_info_available = False

		@property
		def app_info_path(self):
			return os.path.join(self.steamdir, 'appcache', 'appinfo.vdf')

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
			#TODO: There must be a better way to find out where it is, instead of just guessing and checking...
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

class SteamGame():
	def __init__(self, app_id, name):
		self.app_id = app_id
		self.name = name
		self.metadata = Metadata()
		self.icon = None

	def make_launcher(self):
		#Could also use steam -appid {0} here, but like... I dunno if I should
		command = 'xdg-open steam://rungameid/{0}'.format(self.app_id)
		launchers.make_launcher(command, self.name, self.metadata, 'Steam', self.app_id, self.icon)

def look_for_icon(icon_hash):
	icon_hash = icon_hash.lower()
	for icon_file in os.listdir(steam_state.icon_folder):
		icon_path = os.path.join(steam_state.icon_folder, icon_file)

		if icon_file.lower() in (icon_hash + '.ico', icon_hash + '.png', icon_hash + '.zip'):
			if not zipfile.is_zipfile(icon_path):
				#Can't just rely on the extension because some zip files like to hide and pretend to be .ico files for some reason
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
				extracted_icon_folder = os.path.join(main_config.icon_folder, 'extracted_from_zip', icon_hash)
				return zip_file.extract(extracted_icon_file, path=extracted_icon_folder)

	return None

def translate_language_list(languages):
	langs = []
	for language_name, _ in languages.items():
		#value is an Integer object but it's always 1, I dunno what the 0 means, because it's like, if the language isn't there, it just wouldn't be in the dang list anyway
		language_name = language_name.decode('utf-8', errors='backslashreplace')
		#'latam' might be Latin American Spanish? Not sure
		if language_name == 'koreana':
			#Not sure what the difference is there with normal Korean
			langs.append(region_detect.get_language_by_english_name('Korean'))
		elif language_name == 'schinese':
			#Simplified Chinese, which I probably shouldn't call just Chinese
			langs.append(region_detect.get_language_by_english_name('Chinese'))
		elif language_name == 'tchinese':
			langs.append(region_detect.get_language_by_english_name('Traditional Chinese'))
		elif language_name == 'brazilian':
			langs.append(region_detect.get_language_by_english_name('Brazilian Portugese'))
		else:
			language = region_detect.get_language_by_english_name(language_name, case_insensitive=True)
			if language:
				langs.append(language)
			elif main_config.debug:
				print('Unknown language:', language_name)

	return langs

def normalize_developer(dev):
	dev = junk_suffixes.sub('', dev)

	overrides = {
		#Different spellings/formattings of the same company, but we like being consistent with all the other modules and I also just disagree with yelling I guess
		'ALICE IN DISSONANCE': 'Alice in Dissonance',
		'BANDAI NAMCO Entertainment': 'Bandai Namco',
		'GATO STUDIO': 'Gato Studio', #Also seen as "Gato Salvaje", although that doesn't transate exactly to the English name
		'SEGA': 'Sega',
		'QUICKTEQUILA': 'Quicktequila',
		'YAGER': 'Yager Development',

		#These could be sorta like different brands of the same company, but I'm gonna go with the opinion that they should be treated as the same company. But this section could be like... subjective I guess
		'Microsoft Studios': 'Microsoft',
		'Team17 Digital': 'Team17',
		'Two Tribes Publishing': 'Two Tribes',

		#Why
		'Image &amp; Form Games': 'Image & Form Games',
	}
	if dev in overrides:
		return overrides[dev]
	return dev

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
		print('No appiunfo')
		return

	#Alright let's get to the fun stuff
	common = app_info_section.get(b'common')
	if common:
		potential_icon_names = (b'linuxclienticon', b'clienticon', b'clienttga', b'clienticns', b'icon', b'logo', b'logo_small')
		for potential_icon_name in potential_icon_names:
			if potential_icon_name not in common:
				continue
			try:
				icon_hash = common[potential_icon_name].decode('utf-8')
			except UnicodeDecodeError:
				continue
			icon = look_for_icon(icon_hash)
			if icon:
				game.icon = icon
				break

		#oslist and osarch may come in handy (former is comma separated windows/macos/linux; latter is b'64' or purrsibly b'32')
		#openvrsupport, controllervr, othervrsupport, othervrsupport_rift_13 could have something to do with games that support VR
		#eulas is a list, so it could be used to detect if game has third-party EULA
		#small_capsule and header_image refer to image files that don't seem to be there so I dunno
		#store_tags would be useful for genre if they weren't all '9': Integer(size = 32, data = 4182) and I have no idea what a 4182 means and if it requires connecting to the dang web then nah thanks
		#workshop_visible and community_hub_visible could also tell you stuff about if the game has a workshop and a... community hub
		#releasestate: 'released' might be to do with early access?
		#exfgls = exclude from game library sharing
		#b'requireskbmouse' and b'kbmousegame' are also things, but don't seem to be 1:1 with games that have controllersupport = none
		language_list = common.get(b'languages')
		if language_list:
			game.metadata.languages = translate_language_list(language_list)

		category = common.get(b'type', b'Unknown').decode('utf-8', errors='backslashreplace')
		if category in ('game', 'Game'):
			#This makes the categories like how they are with DOS/Mac
			game.metadata.categories = ['Games']
		elif category == 'Tool':
			game.metadata.categories = ['Applications']
		elif category == 'Demo':
			game.metadata.categories = ['Trials']
		else:
			game.metadata.categories = [category]

		has_adult_content = common.get(b'has_adult_content') #Integer object with data = 0 or 1, as most bools here seem to be
		game.metadata.nsfw = False if has_adult_content is None else bool(has_adult_content.data)

		metacritic_score = common.get(b'metacritic_score')
		if metacritic_score:
			#Well why not
			game.metadata.specific_info['Metacritic-Score'] = metacritic_score.data

		game.metadata.specific_info['Metacritic-URL'] = common.get(b'metacritic_fullurl', b'').decode('utf8', errors='backslashreplace')
		game.metadata.specific_info['Sort-Name'] = common.get(b'sortas', b'').decode('utf8', errors='backslashreplace')

		#TODO: Probably can't do input_info with this, but maybe use EmulationStatus enum to do Good (full) Imperfect (partial) Broken (none)
		game.metadata.specific_info['Controlller-Support'] = common.get(b'controller_support', b'none').decode('utf-8', errors='backslashreplace')

	extended = app_info_section.get(b'extended')
	if extended:
		developer = extended.get(b'developer')
		if developer:
			game.metadata.developer = normalize_developer(developer.decode('utf-8', errors='backslashreplace'))
		publisher = extended.get(b'publisher')
		if publisher:
			game.metadata.publisher = normalize_developer(publisher.decode('utf-8', errors='backslashreplace'))

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

	config = app_info_section.get(b'config')
	if config:
		#contenttype = 3 in some games but not all of them? nani
		launch = config.get(b'launch')
		#This key would actually tell us the executable and arguments used to actually launch the game. It's probably not a good idea to do that directly though, mostly because some games are DRM'd to Steam, so it's probably a good idea to go through the Steam client like we are now.
		#Although I guess that would allow us to detect if a game is just a wrapper for going through another launcher, like Origin or uPlay or whatevs, but yeah
		#Anyway, we're going to use it a bit more responsibly
		if launch:
			#Should always exist if the game can be launched, but I'm just going to null check every single thing in my life from now on to avoid the pain
			have_linux_launcher = False
			for launch_item in launch.values():
				#Key here is 0, 1, 2, n... which is a bit useless, it's really just a boneless list. Anyway, each of these values is another dict containing launch parameters, for each individual platform or configuration, e.g. Windows 32-bit, Windows 64-bit, MacOS, etc
				#If you wanted to do secret evil things: b'executable' = 'CoolGame.sh' b'arguments' (optional) = '--fullscreen --blah' b'description' = 'Cool Game'
				launch_item_config = launch_item.get(b'config')
				if launch_item_config:
					if b'linux' in launch_item_config.get(b'oslist', b''):
						#I've never seen oslist be a list, but it is always a byte string, so maybe there's some game where it's multiple platforms comma separated
						#(Other key: osarch = sometimes Integer with data = 32/64, or b'32' or b'64')
						have_linux_launcher = True
			if not have_linux_launcher:
				game.metadata.specific_info['Uses-Steam-Play'] = True

	localization = app_info_section.get(b'localization')
	if localization:
		if b'richpresence' in localization:
			#I think this is correct
			#(Keys of this are 'english' or presumably other languages and then 'tokens' and then it's a bunch of stuff)
			game.metadata.specific_info['Discord-Rich-Presence'] = True

	if b'ufs' in app_info_section:
		game.metadata.save_type = SaveType.Cloud
	#As for how to tell the difference between SaveType.Internal and SaveType.Nothing... is there even a game on Steam that doesn't save at all?

def process_game(app_id, name=None):
	if not name:
		name = '<unknown game {0}>'.format(app_id)
	name = name.replace('™', '')
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

	#userdata/<user ID>/config/localconfig.vdf has last time played stats, so that's a thing I guess
	#userdata/<user ID>/7/remote/sharedconfig.vdf has tags/categories etc as well

	#Other metadata that we can't or won't fill in:
	#Month, day, year (ooh surely we can have this from somewhere)
	#cpu_info, emulator_name, screen_info, extension: Irrelevant (not going to do something silly like use the current user's CPU/monitor specs)
	#genre, subgenre: From shop tags, or we could use user's tags if they wanted
	#product_code: Not really a thing
	#regions: World or user's region? Hmm, maybe not entirely relevant with PC games
	#revision: Irrelevant since software versions aren't always linear numbers?
	#save_type: Internal (or cloud) or nothing, though I doubt there's much these days with no saving of progress at all
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
		#StateFlags probably has something to do with whether it's actually currently installed or not, seems to be just 4, maybe other values indicate it's in the middle of downloading or stuff like that
		#UserConfig might be interesting... normally it just has a key 'language' which is set to 'english' etc, sometimes duplicating name and app_id as 'gameid' for no reason, but also has things like 'lowviolence': '1' inside Left 4 Dead 2 for example (because I'm Australian I guess), so... well, I just think that's kinda neat, although probably not useful for our purposes here; also for TF2 it has 'betakey': 'prerelease' so I guess that has to do with opt-in beta programs
		#Anyway I don't think we need any of that for now
		process_game(app_id, name)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Steam finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	process_steam()
