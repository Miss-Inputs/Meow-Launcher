import os

def look_for_icon(folder):
	for f in os.listdir(folder):
		if f.lower().endswith('.ico'):
			return os.path.join(folder, f)
		if f.lower() in ('icon.png', 'icon.xpm'):
			return os.path.join(folder, f)
	return None

def try_and_detect_engine_from_folder(folder):
	dir_entries = list(os.scandir(folder))
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]

	if 'renpy' in subdirs:
		return "Ren'Py"
	if 'data.dcp' in files:
		return 'Wintermute'
	if 'acsetup.cfg' in files:
		return 'Adventure Game Studio'
	if 'rpg_rt.exe' in files:
		return 'RPG Maker 2000/2003'
	if os.path.basename(folder).lower() + '.uproject' in files:
		return 'Unreal Engine 4'
	
	if any(f.endswith('.rgssad') for f in files):
		return 'RPG Maker XP/VX'
	if any(f.endswith('.cf') for f in files):
		if 'data.xp3' in files and 'plugin' in subdirs:
			return 'KiriKiri'

	#Hmm should I be refactoring these lines down here
	if os.path.isfile(os.path.join(folder, 'assets', 'game.unx')):
		return 'GameMaker'
	if 'adobe air' in subdirs or os.path.isdir(os.path.join(folder, 'runtimes', 'Adobe AIR')):
		return 'Adobe AIR'
	if os.path.isfile(os.path.join(folder, 'AIR', 'arh')):
		#"Adobe Redistribution Helper" but I dunno how reliable this detection is, to be honest, but it seems to be used sometimes; games like this seem to instead check for a system-wide AIR installation and try and install that if it's not there
		return 'Adobe AIR'
	if 'bin' in subdirs and 'platform' in subdirs:
		for f in os.listdir(folder):
			if os.path.isdir(os.path.join(folder, f)):
				if os.path.isfile(os.path.join(folder, f, 'gameinfo.txt')):
					return 'Source'
	for f in os.listdir(folder):
		#Sometimes UnityPlayer.dll is not always there I think
		if f.endswith('_Data'):
			#appinfo.txt contains the publisher on line 1, and the name (which sometimes is formatted weirdly) on line 2
			if os.path.isfile(os.path.join(folder, f, 'Managed', 'UnityEngine.dll')):
				return 'Unity'
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
