import os

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
		if f.endswith('_Data'):
			#This folder will probably be named after an executable in the folder? Maybe
			#appinfo.txt contains the publisher on line 1, and the name (which sometimes is formatted weirdly) on line 2
			if os.path.isfile(os.path.join(folder, f, 'Managed', 'UnityEngine.dll')):
				return True
	return False


def try_and_detect_engine_from_folder(folder):
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]

	#These are simple enough to detect with just one line…
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

	if os.path.basename(folder).lower() + '.uproject' in files:
		return 'Unreal Engine 4'
	if any(f.endswith('.rgssad') for f in files):
		return 'RPG Maker XP/VX'
	if any(f.endswith('.cf') for f in files):
		if 'data.xp3' in files and 'plugin' in subdirs:
			return 'KiriKiri'

	#Hmm should I be refactoring these lines down here
	if os.path.isfile(os.path.join(folder, 'assets', 'game.unx')):
		#game.win on Windows… that's too false-positivey for me
		return 'GameMaker'
	if 'adobe air' in subdirs or os.path.isdir(os.path.join(folder, 'runtimes', 'Adobe AIR')):
		return 'Adobe AIR'
	if os.path.isfile(os.path.join(folder, 'AIR', 'arh')):
		#"Adobe Redistribution Helper" but I dunno how reliable this detection is, to be honest, but it seems to be used sometimes; games like this seem to instead check for a system-wide AIR installation and try and install that if it's not there
		return 'Adobe AIR'
	if 'bin' in subdirs and 'platform' in subdirs:
		for f in os.listdir(folder):
			if os.path.isdir(os.path.join(folder, f)): #'hl2', 'ep1', etc
				if os.path.isfile(os.path.join(folder, f, 'gameinfo.txt')):
					#gameinfo.txt contains metadata but then this would probably only appear on games that are from Steam and we get all the metadata from there anyway
					return 'Source'
	if try_detect_unity(folder):
		return 'Unity'
	for f in os.listdir(folder):
		if (f != 'Game' and f.endswith('Game')) or f == 'P13':
			if os.path.isdir(os.path.join(folder, f)):
				if os.path.isfile(os.path.join(folder, f, 'CookedPC', 'Engine.u')):
					return 'Unreal Engine 3'
				if os.path.isdir(os.path.join(folder, f, 'CookedPCConsole')) or os.path.isdir(os.path.join(folder, f, 'CookedPCConsole_FR')) or os.path.isdir(os.path.join(folder, f, 'CookedPCConsoleFinal')):
					return 'Unreal Engine 3'

	maybe_ue4_stuff_path = os.path.join(folder, 'Engine', 'Extras', 'Redist', 'en-us')
	if os.path.isdir(maybe_ue4_stuff_path):
		if os.path.isfile(os.path.join(maybe_ue4_stuff_path, 'UE4PrereqSetup_x64.exe')) or os.path.isfile(os.path.join(maybe_ue4_stuff_path, 'UE4PrereqSetup_x86.exe')):
			return 'Unreal Engine 4'

	if os.path.isfile(os.path.join(folder, 'Build', 'Final', 'DefUnrealEd.ini')):
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if os.path.isfile(os.path.join(folder, 'Builds', 'Binaries', 'DefUnrealEd.ini')):
		return 'Unreal Engine 2' #Possibly 2.5 specifically
	if os.path.isfile(os.path.join(folder, 'System', 'Engine.u')):
		return 'Unreal Engine 1'
	
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

def check_for_interesting_things_in_folder(folder, metadata):
	#Let's check for things existing because we can (there's not really any other reason to do this, it's just fun)
	#Not sure if any of these are in lowercase? Or they might be in a different directory
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]
	
	if 'libdiscord-rpc.so' in files or 'discord-rpc.dll' in files:
		metadata.specific_info['Discord-Rich-Presence'] = True
	if 'dosbox' in subdirs or any(f.startswith('dosbox') for f in files):
		metadata.specific_info['Wrapper'] = 'DOSBox'

	if any(f.startswith('scummvm_') for f in subdirs) or any(f.startswith('scummvm') for f in files):
		metadata.specific_info['Wrapper'] = 'ScummVM'

	if os.path.isfile(os.path.join(folder, 'support', 'UplayInstaller.exe')):
		metadata.specific_info['Launcher'] = 'uPlay'
