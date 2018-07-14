import sys
import os
import shlex
import json
import urllib.request

import launchers
import common
import config
import hfs

debug = '--debug' in sys.argv

def init_game_list():
	if not os.path.exists(config.mac_db_path):
		print("You don't have mac_db.json which is required for this to work. Let me get that for you.")
		#TODO: Is this the wrong way to do this? I think it most certainly is
		mac_db_url = 'https://raw.githubusercontent.com/Zowayix/computer-software-db/master/mac_db.json'
		with urllib.request.urlopen(mac_db_url) as mac_db_request:
			mac_db_data = mac_db_request.read().decode('utf-8')
		with open(config.mac_db_path, 'wt') as mac_db_local_file:
			mac_db_local_file.write(mac_db_data)
			game_list = json.loads(mac_db_data)
	else:
		with open(config.mac_db_path, 'rt') as mac_db_file:
			game_list = json.load(mac_db_file)

	for game_name, game in game_list.items():
		if 'parent' in game:
			parent_name = game['parent']
			if parent_name in game_list:
				parent = game_list[parent_name]
				for key in parent.keys():
					if key == "notes":
						if key in game:
							game_list[game_name][key] = parent[key] + ";" + game_list[game_name][key]
						else:
							game_list[game_name][key] = parent[key]
					elif key not in game:
						game_list[game_name][key] = parent[key]
			else:
				if debug:
					print('Oh no! {0} refers to undefined parent game {1}'.format(game_name, parent_name))

	return game_list

def make_launcher(path, game_name, game_config):
	#This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that.
	#Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	autoboot_txt_path = os.path.join(config.basilisk_ii_shared_folder, 'autoboot.txt')
	width = 1920 #TODO: Get desktop resolution
	height = 1080
	if 'width' in game_config:
		width = game_config['width']
	if 'height' in game_config:
		height = game_config['height']
	#Can't do anything about colour depth at the moment (displaycolordepth is functional on some SDL1 builds, but not SDL2)
	#Or controls... but I swear I will find a way!!!!
	
	#If you're not using an SDL2 build of BasiliskII, you probably want to change dga to window! Well you really want to get an SDL2 build of BasiliskII, honestly
	#TODO: Should put BasiliskII in emulator_info.py so it can get the command line from there
	actual_emulator_command = 'BasiliskII --screen dga/{0}/{1}'.format(width, height)
	inner_command = 'echo {0} > {1} && {2} && rm {1}'.format(shlex.quote(path), shlex.quote(autoboot_txt_path), actual_emulator_command)
	command = 'sh -c {0}'.format(shlex.quote(inner_command))
	display_name = common.remove_filename_tags(game_name)
	if 'category' in game_config:
		categories = [game_config['category']]
	else:
		categories = []
	
	metadata = {'Emulator': 'BasiliskII'}
	if 'genre' in game_config:
		metadata['Genre'] = game_config['genre']
	if 'subgenre' in game_config:
		metadata['Subgenre'] = game_config['subgenre']
	if 'adult' in game_config:
		metadata['NSFW'] = game_config['adult']
	if 'notes' in game_config:
		metadata['Notes'] = game_config['notes']
	if 'compat_notes' in game_config:
		metadata['Compat-Notes'] = game_config['compat_notes']
		print('Compatibility notes for', path, ':', game_config['compat_notes'])
	if 'requires_cd' in game_config:
		print(path, 'requires a CD in the drive. It will probably not work with this launcher at the moment')
		metadata['Requires-CD'] = game_config['requires_cd']
	
	#Extra metadata because we have nothing else to do with it right now
	#TODO: If arch == ppc, we shouldn't use BasiliskII, and either reject the app or use SheepShaver (as much as I don't wanna because of the vm.mmap_min_addr thing)
	for extra_metadata in ('min_players', 'max_players', 'emu_compat', 'controls', 'required_hardware', 'required_software', 'colours', 'colours_compat', 'resolution_compat', 'clone_of', 'runs_in_window'):
		if extra_metadata in game_config:
			metadata[extra_metadata] = game_config[extra_metadata]

	launchers.make_launcher('Mac', command, display_name, categories, metadata)

def do_mac_stuff():
	game_list = init_game_list()
	for mac_volume in config.mac_disk_images:
		create_launchers_from_mac_volume(mac_volume, game_list)

def create_launchers_from_mac_volume(path, game_list):
	for f in hfs.list_hfv(path):
		if f['file_type'] != 'APPL':
			continue
	
		#TODO: Should handle the case with other_app_names, so Blah 1.2 and Blah 1.3 that have the same creator code won't cause ambiguity here
		#This will require changing the structure of mac_db.json. As an example, Frog Xing 1.2 and Frog Xing 1.3 both have a creator code of QnFx which is unique, but they both end up with a launcher called "Frog Xing" and there's no way for disambiguate.py to handle that. What I'd need to do is change the name of Frog Xing's config to "Frog Xing (1.3)", and convert each item in other_app_names to an array so it's like ["Frog Xing 1.2", "Frog Xing (1.2)"] and then that'd work out. Or implement some parent/clone system, perhaps. In JSON. Somehow. Hmm. Hmmm..... HMM......
		possible_games = [(game_name, game) for game_name, game in game_list.items() if game['creator_code'] == f['creator']]
		if not possible_games:
			if debug:
				print('Unknown game, using default config:', f['path'])
			make_launcher(f['path'], f['name'], {})
		elif len(possible_games) == 1:
			make_launcher(f['path'], *possible_games[0])
		else:
			possible_games_by_name = [(game_name, game) for game_name, game in possible_games if game['app_name'] == f['name']]
			if not possible_games_by_name:
				if debug:
					print('Unknown game (but known creator code', f['creator'], ')', 'using default config:', f['path'])
				make_launcher(f['path'], f['name'], {})
			elif len(possible_games_by_name) == 1:
				make_launcher(f['path'], *possible_games_by_name[0])
			else:
				if debug:
					print(f['path'], 'could be', list(game_name for game_name, game in possible_games_by_name), 'using first one for now')
				make_launcher(f['path'], *possible_games_by_name[0])
