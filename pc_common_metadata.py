import os
import re

from common import title_case
from config.main_config import main_config
from data.name_cleanup.capitalized_words_in_names import capitalized_words
from series_detect import chapter_matcher

#Hmm, are other extensions going to work as icons in a file manager
icon_extensions = ('png', 'ico', 'xpm', 'svg')

def look_for_icon_next_to_file(path):
	#TODO: Use pefile etc to extract icon from path if it is an exe
	parent_folder = os.path.dirname(path)
	for f in os.listdir(parent_folder):
		for ext in icon_extensions:
			if f.lower() == os.path.splitext(os.path.basename(path))[0].lower() + os.path.extsep + ext:
				return os.path.join(parent_folder, f)

	return look_for_icon_in_folder(parent_folder, False)

def look_for_icon_in_folder(folder, look_for_any_ico=True):
	for f in os.listdir(folder):
		for ext in icon_extensions:
			if f.lower() == 'icon' + os.path.extsep + ext:
				return os.path.join(folder, f)
			if f.startswith('goggame-') and f.endswith(icon_extensions):
				return os.path.join(folder, f)
			if f == 'gfw_high.ico':
				#Some kind of older GOG icon? Except not in actual GOG games, just stuff that was distributed elsewhere I guess
				return os.path.join(folder, f)

	if look_for_any_ico:
		#Just get the first ico if we didn't find anything specific
		for f in os.listdir(folder):
			if f.lower().endswith('.ico'):
				return os.path.join(folder, f)
	return None

def try_detect_unity(folder):
	for f in os.listdir(folder):
		if not os.path.isdir(os.path.join(folder, f)):
			continue

		if f == 'Build':
			if os.path.isfile(os.path.join(folder, f, 'UnityLoader.js')):
				#Web version of Unity, there should be some .unityweb files here
				return True

		if f.endswith('_Data'):
			#This folder "blah_Data" seems to always go with an executable named "blah", "blah.exe" (on Windows), "blah.x86", "blah.x86_64"
			#appinfo.txt contains the publisher on line 1, and the name (which sometimes is formatted weirdly) on line 2
			if os.path.isfile(os.path.join(folder, f, 'Managed', 'UnityEngine.dll')):
				return True
	return False

def try_detect_ue4(folder):
	if os.path.isfile(os.path.basename(folder) + '.uproject'):
		return True

	engine_folder = os.path.join(folder, 'Engine') #I guess this is always there… dunno if anything is _always_ in there though (Binaries + Content?)
	if not os.path.isdir(engine_folder):
		return False
	
	if os.path.isfile(os.path.join(engine_folder, 'Binaries', 'Linux', 'UE4Game-Linux-Shipping')):
		return True
	if os.path.isfile(os.path.join(engine_folder, 'Binaries', 'Win64', 'UE4Game-Win64-Shipping.exe')):
		return True

	redist_folder = os.path.join(engine_folder, 'Extras', 'Redist')
	if os.path.isdir(redist_folder):
		for subdir in os.listdir(redist_folder):
			if not os.path.isdir(os.path.join(redist_folder, subdir)):
				continue
			#subdir will probably be something like "en-us" but that's a language so maybe not
			if os.path.isfile(os.path.join(redist_folder, subdir, 'UE4PrereqSetup_x64.exe')) or os.path.isfile(os.path.join(redist_folder, subdir, 'UE4PrereqSetup_x86.exe')):
				return True

	#Hmm…
	#Something like Blah/Binaries/Linux/Blah-Linux-Shipping
	project_name = None
	binaries_folder = None
	for subdir in os.listdir(folder):
		if subdir == 'Engine':
			continue
		if not os.path.isdir(os.path.join(folder, subdir)):
			continue
		for subsubdir in os.listdir(os.path.join(folder, subdir)):
			if subsubdir == 'Binaries':
				project_name = subdir
				binaries_folder = os.path.join(folder, subdir, subsubdir)
				break
		if binaries_folder:
			break

	if not binaries_folder or not os.path.isdir(binaries_folder):
		#Gonna assume probably not then
		return False

	if not os.path.isdir(os.path.join(folder, project_name, 'Content', 'Paks')):
		return False
	
	if os.path.isfile(os.path.join(binaries_folder, 'Linux', project_name + '-Linux-Shipping')) or os.path.isfile(os.path.join(binaries_folder, 'Linux', project_name)):
		#HMMMMMMMMMmmmmmm
		return True
	if os.path.isfile(os.path.join(binaries_folder, 'Win64', project_name + '-Win64-Shipping.exe')):
		return True	
	
	return False

def try_detect_build(folder):
	files = [f.name.lower() for f in os.scandir(folder) if f.is_file()]
	if 'build.exe' in files and 'bsetup.exe' in files and 'editart.exe' in files:
		return True
	for f in os.listdir(folder):
		if f.lower() == 'build' and os.path.isdir(os.path.join(folder, f)):
			if try_detect_build(os.path.join(folder, f)):
				return True
	return False

def try_detect_ue3(folder):
	for f in os.listdir(folder):
		if (f != 'Game' and f.endswith('Game')) or f == 'P13':
			if os.path.isdir(os.path.join(folder, f)):
				if os.path.isfile(os.path.join(folder, f, 'CookedPC', 'Engine.u')):
					return True
				if os.path.isdir(os.path.join(folder, f, 'CookedPCConsole')) or os.path.isdir(os.path.join(folder, f, 'CookedPCConsole_FR')) or os.path.isdir(os.path.join(folder, f, 'CookedPCConsoleFinal')):
					return True
	return False

def try_detect_gamemaker(folder):
	if os.path.isfile(os.path.join(folder, 'audiogroup1.dat')) and os.path.isfile(os.path.join(folder, 'data.win')) and os.path.isfile(os.path.join(folder, 'options.ini')):
		#Hmmmmmmmmmmmmm probably
		#data.win generally has "FORM" magic? audiogroup1/2/3.dat and options.ini might not always be there but I wanna be more sure if I don't poke around in files
		return True
	
	#Linux ports are a bit different (assets folder seems to always be there? But game.unx is not always in there)
	assets_folder = os.path.join(folder, 'assets')
	if not os.path.isdir(assets_folder):
		return False
	#icon.png might be in here, usually seems to be

	#game.unx seems to also always have FORM magic
	if (os.path.isfile(os.path.join(folder, 'game.unx')) or os.path.isfile(os.path.join(assets_folder, 'game.unx'))) and os.path.isfile(os.path.join(assets_folder, 'options.ini')):
		return True

	return False

def try_detect_source(folder):
	have_bin = False
	have_platform = False
	game_folder = None
	for subdir in os.listdir(folder):
		if not os.path.isdir(os.path.join(folder, subdir)):
			continue

		if subdir == 'bin':
			have_bin = True
			continue
		if subdir == 'platform':
			have_platform = True
			continue
		#Looking for 'hl2', 'ep1', etc
		for f in os.listdir(os.path.join(folder, subdir)):
			if f == 'gameinfo.txt':
				#gameinfo.txt contains metadata but then this would probably only appear on games that are from Steam and we get all the metadata from there anyway
				#Also there might be more than one gameinfo.txt inside multiple subdirs in folder (like the Half-Life 2 install dir having all the episodes)
				game_folder = os.path.join(folder, subdir)
				break
	if have_bin and have_platform and game_folder:
		return True
	
	return False

def try_detect_adobe_air(folder):
	if os.path.isdir(os.path.join(folder, 'Adobe AIR')):
		return True
	if os.path.isdir(os.path.join(folder, 'runtimes', 'Adobe AIR')):
		return True
	
	if os.path.isfile(os.path.join(folder, 'AIR', 'arh')):
		#"Adobe Redistribution Helper" but I dunno how reliable this detection is, to be honest, but it seems to be used sometimes; games like this seem to instead check for a system-wide AIR installation and try and install that if it's not there
		return True

	metainf_dir = os.path.join(folder, 'META-INF', 'AIR')
	if os.path.isdir(metainf_dir):
		if os.path.isfile(os.path.join(metainf_dir, 'application.xml')) and os.path.isfile(os.path.join(metainf_dir, 'hash')):
			return True

	#file named "mimetype" might also exist with content of "application/vnd.adobe.air-application-installer-package+zip"

	return False

def try_and_detect_engine_from_folder(folder):
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]

	#Godot = .pck with "GDPC" magic, but that requires poking inside files and I don't wanna do that just yet
	#XNA: Might have a "common redistributables" folder with an installer in it?

	#These are simple enough to detect with just one line…	
	if ('nw.pak' in files or 'nw_100_percent.pak' in files or 'nw_200_percent.pak' in files) and ('package.json' in files or 'package.nw' in files):
		#package.nw is a zip with package.json and other fun stuff in it, package.json might have metadata
		return 'NW.js'
	if 'fna.dll' in files:
		return 'FNA'
	if 'monogame.framework.dll' in files or 'monogame.framework.lite.dll' in files:
		return 'MonoGame'
	if 'renpy' in subdirs and 'game' in subdirs and 'lib' in subdirs:
		return "Ren'Py"
	if 'data.dcp' in files or 'data_sd.dcp' in files or 'data_hd.dcp' in files:
		#Hmm, hopefully there's no false positives here without actually looking inside the file
		return 'Wintermute'
	if 'acsetup.cfg' in files:
		#The better way to do this would be to look for 'Adventure Creator Game File' in dat or exe I guess (and then we can get game title from there), but also the effort way
		return 'Adventure Game Studio'
	if 'rpg_rt.exe' in files:
		#TODO: Get title from RPG_RT.ini section RPG_RT line GameTitle= (this is not always there though…)
		return 'RPG Maker 2000/2003'
	if 'logdir' in files and 'object' in files and 'picdir' in files and 'viewdir' in files and 'snddir' in files and 'vol.0' in files and 'words.tok' in files:
		#Apparently there can be .wag files?
		return 'AGI' #v2
	if ('visplayer' in files and any(f.endswith('.vis') for f in files)) or ('data.vis' in files): #.vis magic is "VIS3"?
		return 'Visionaire Studio'
	if any(f.endswith('.rgssad') for f in files):
		return 'RPG Maker XP/VX' #If mkxp.conf is there, uses mkxp replacement implementation
	if any(f.endswith('.rvproj2') for f in files):
		return 'RPG Maker VX Ace'
	if 'rgss102j.dll' in files or 'rgss102e.dll' in files:
		return 'RPG Maker XP'
	if any(f.endswith('.cf') for f in files):
		if 'data.xp3' in files and 'plugin' in subdirs:
			return 'KiriKiri'
	if os.path.isfile(os.path.join(folder, 'Build', 'Final', 'DefUnrealEd.ini')):
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if os.path.isfile(os.path.join(folder, 'Builds', 'Binaries', 'DefUnrealEd.ini')):
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if os.path.isfile(os.path.join(folder, 'System', 'Engine.u')):
		return 'Unreal Engine 1'
	if 'data.wolf' in files and 'config.exe' in files:
		#TODO: Also might have a Data folder with .wolf files inside it
		#Is GuruguruSMF4.dll always there? Doesn't seem to be part of the thing
		return 'Wolf RPG Editor'
	if 'game.dmanifest' in files and 'game.arcd' in files and 'game.arci' in files:
		return 'Defold'
	if 'libogremain.so' in files or 'ogremain.dll' in files:
		return 'OGRE'
	if os.path.isfile(os.path.join(folder, 'bin', 'libUnigine_x64.so')) or os.path.isfile(os.path.join(folder, 'bin', 'libUnigine_x86.so')) or os.path.isfile(os.path.join(folder, 'bin', 'Unigine_x86.dll')) or os.path.isfile(os.path.join(folder, 'bin', 'Unigine_x64.dll')):
		return 'Unigine'

	if try_detect_gamemaker(folder):
		return 'GameMaker'
	if try_detect_build(folder):
		return 'Build'
	if try_detect_ue3(folder):
		return 'Unreal Engine 3'
	if try_detect_ue4(folder):
		return 'Unreal Engine 4'
	if try_detect_unity(folder):
		return 'Unity'
	if try_detect_source(folder):
		return 'Source'
	if try_detect_adobe_air(folder):
		return 'Adobe AIR'

	return None

def detect_engine_recursively(folder):
	engine = try_and_detect_engine_from_folder(folder)
	if engine:
		return engine

	for subdir in os.listdir(folder):
		path = os.path.join(folder, subdir)
		if os.path.isdir(path):
			engine = try_and_detect_engine_from_folder(path)
			if engine:
				return engine

	return None

def check_for_interesting_things_in_folder(folder, metadata, find_wrappers=False):
	#Let's check for things existing because we can (there's not really any other reason to do this, it's just fun)
	#Not sure if any of these are in lowercase? Or they might be in a different directory
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]
	
	if 'libdiscord-rpc.so' in files or 'discord-rpc.dll' in files:
		metadata.specific_info['Discord-Rich-Presence'] = True

	if find_wrappers:
		#This is only really relevant for Steam etc
		if 'dosbox' in subdirs or any(f.startswith('dosbox') for f in files):
			metadata.specific_info['Wrapper'] = 'DOSBox'

		if any(f.startswith('scummvm_') for f in subdirs) or any(f.startswith('scummvm') for f in files):
			metadata.specific_info['Wrapper'] = 'ScummVM'

		if os.path.isfile(os.path.join(folder, 'support', 'UplayInstaller.exe')):
			metadata.specific_info['Launcher'] = 'uPlay'

fluff_editions = ['GOTY', 'Game of the Year', 'Definitive', 'Enhanced', 'Special', 'Ultimate', 'Premium', 'Gold', 'Extended', 'Super Turbo Championship', 'Digital', 'Megaton', 'Deluxe', 'Masterpiece']
demo_suffixes = ['Demo', 'Playable Teaser']
name_suffixes = demo_suffixes + ['Beta', 'GOTY', "Director's Cut", 'Unstable', 'Complete', 'Complete Collection', "Developer's Cut"] + [e + ' Edition' for e in fluff_editions]
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

why = re.compile(r' -(?=\w)') #This bothers me
def fix_name(name):
	name = name.replace('™', '')
	name = name.replace('®', '')
	name = name.replace(' : ', ': ') #Oi mate what kinda punctuation is this
	name = name.replace('[diary]', 'diary') #Stop that
	name = name.replace('(VI)', 'VI') #Why is Tomb Raider: The Angel of Darkness like this
	name = why.sub(' - ', name)

	if name.startswith('ARCADE GAME SERIES'):
		#This is slightly subjective as to whether or not one should do this, but I believe it should
		name = name[20:] + ' (ARCADE GAME SERIES)'

	name_to_test_for_upper = chapter_matcher.sub('', name)
	name_to_test_for_upper = name_suffix_matcher.sub('', name_to_test_for_upper)
	name = normalize_name_case(name, name_to_test_for_upper)
		
	#Hmm... this is primarily so series_detect and disambiguate work well, it may be worthwhile putting them back afterwards (put them in some kind of field similar to Filename-Tags but disambiguate always adds them in); depending on how important it is to have "GOTY" or "Definitive Edition" etc in the name if not ambiguous
	name = name_suffix_matcher.sub(r' (\1)', name)
	return name

tool_names = ('settings', 'setup', 'config', 'dedicated server', 'editor')
def is_probably_related_tool(name):
	lower = name.lower()
	return any(tool_name in lower for tool_name in tool_names)

mode_names = ('safe mode', 'play windowed')
def is_probably_different_mode(name):
	lower = name.lower()
	return any(mode_name in lower for mode_name in mode_names)
