#!/usr/bin/env python3

import sys
import os
import shlex
import json
import urllib.request
import configparser

import launchers
import config
import hfs
from metadata import Metadata

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
	width = 1920
	height = 1080
	if 'width' in game_config:
		width = game_config['width']
	if 'height' in game_config:
		height = game_config['height']
	#Can't do anything about colour depth at the moment (displaycolordepth is functional on some SDL1 builds, but not SDL2)
	#Or controls... but I swear I will find a way!!!!
	
	#If you're not using an SDL2 build of BasiliskII, you probably want to change dga to window! Well you really want to get an SDL2 build of BasiliskII, honestly
	actual_emulator_command = 'BasiliskII --screen dga/{0}/{1}'.format(width, height)
	inner_command = 'echo {0} > {1} && {2} && rm {1}'.format(shlex.quote(path), shlex.quote(autoboot_txt_path), actual_emulator_command)
	command = 'sh -c {0}'.format(shlex.quote(inner_command))
	
	metadata = Metadata()
	metadata.emulator_name = 'BasiliskII'
	metadata.platform = 'Mac'

	if 'category' in game_config:
		metadata.categories = [game_config['category']]
	
	if 'genre' in game_config:
		metadata.genre = game_config['genre']
	if 'subgenre' in game_config:
		metadata.subgenre = game_config['subgenre']
	if 'adult' in game_config:
		metadata.nsfw = game_config['adult']
	if 'notes' in game_config:
		metadata.specific_info['Notes'] = game_config['notes']
	if 'compat_notes' in game_config:
		metadata.specific_info['Compatibility-Notes'] = game_config['compat_notes']
		print('Compatibility notes for', path, ':', game_config['compat_notes'])
	if 'requires_cd' in game_config:
		print(path, 'requires a CD in the drive. It will probably not work with this launcher at the moment')
		metadata.specific_info['Requires-CD'] = game_config['requires_cd']
	
	launchers.make_launcher(command, game_name, metadata)

def make_mac_launchers():
	game_list = init_game_list()
	if not os.path.isfile(config.mac_config_path):
		#TODO: Perhaps notify user they have to do ./mac.py --scan to do the thing
		return

	parser = configparser.ConfigParser(delimiters=('='), allow_no_value=True)
	parser.optionxform = str
	parser.read(config.mac_config_path)

	for path, config_name in parser.items('Apps'):
		if config_name not in game_list:
			print('Oh no!', path, 'refers to', config_name, "but that isn't known")
			continue
		game_config = game_list[config_name]
		make_launcher(path, config_name, game_config)

	#TODO: Optionally, attempt to do unknown apps as well. I mean, we could.


def scan_app(app, game_list, unknown_games, found_games, ambiguous_games):
	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['creator_code'] == app['creator']]
	if not possible_games:
		unknown_games.append(app['path'])
	elif len(possible_games) == 1:
		found_games[app['path']] = possible_games[0][0]
	else:
		possible_games = [(game_name, game_config) for game_name, game_config in possible_games if game_config['app_name'] == app['name']]
		if not possible_games:
			unknown_games.append(app['path'])
		elif len(possible_games) == 1:
			found_games[app['path']] = possible_games[0][0]
		else:
			ambiguous_games[app['path']] = [game_name for game_name, game_config in possible_games]

def scan_mac_volume(path, game_list, unknown_games, found_games, ambiguous_games):
	for f in hfs.list_hfv(path):
		if f['file_type'] != 'APPL':
			continue
		scan_app(f, game_list, unknown_games, found_games, ambiguous_games)

def scan_mac_volumes():
	unknown_games = []
	found_games = {}
	ambiguous_games = {}

	game_list = init_game_list()
	for mac_volume in config.mac_disk_images:
		scan_mac_volume(mac_volume, game_list, unknown_games, found_games, ambiguous_games)

	configwriter = configparser.ConfigParser()
	configwriter.optionxform = str
	configwriter['Apps'] = {}
	configwriter['Ambiguous'] = {}
	configwriter['Unknown'] = {}
	for k, v in found_games.items():
		configwriter['Apps'][k] = v
	for k, v in ambiguous_games.items():
		configwriter['Ambiguous'][k] = ';'.join(v)
	for unknown in unknown_games:
		configwriter['Unknown'][unknown] = ''
	with open(config.mac_config_path, 'wt') as config_file:
		configwriter.write(config_file)
	
	print('Scan results have been written to', config.mac_config_path)
	print('Because not everything can be autodetected, some may be unrecognized')
	print('and you will have to configure them yourself, or may be one of several')
	print('apps and you will have to specify which is which, until I think of')
	print('a better way to do this.')

if __name__ == '__main__':
	os.makedirs(config.output_folder, exist_ok=True)
	if '--scan' in sys.argv:
		scan_mac_volumes()
	else:
		make_mac_launchers()
