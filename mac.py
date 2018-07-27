#!/usr/bin/env python3

import sys
import os
import json
import urllib.request
import configparser

import launchers
import config
import hfs
from info.emulator_info import mac_emulators
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

class MacApp:
	def __init__(self, path, name, app_config):
		self.path = path
		self.name = name
		self.config = app_config

	def make_launcher(self, mac_config):
		metadata = Metadata()
		metadata.platform = 'Mac'
		#TODO Add input_info and whatnot

		if 'category' in self.config:
			metadata.categories = [self.config['category']]
	
		if 'genre' in self.config:
			metadata.genre = self.config['genre']
		if 'subgenre' in self.config:
			metadata.subgenre = self.config['subgenre']
		if 'adult' in self.config:
			metadata.nsfw = self.config['adult']
		if 'notes' in self.config:
			metadata.specific_info['Notes'] = self.config['notes']
		if 'compat_notes' in self.config:
			metadata.specific_info['Compatibility-Notes'] = self.config['compat_notes']
			print('Compatibility notes for', self.name, ':', self.config['compat_notes'])
		if 'requires_cd' in self.config:
			print(self.name, 'requires a CD in the drive. It will probably not work with this launcher at the moment')
			metadata.specific_info['Requires-CD'] = self.config['requires_cd']

		emulator_name = None
		command = None
		for emulator in mac_config.chosen_emulators:
			emulator_name = emulator
			command = mac_emulators[emulator].get_command_line(self, mac_config.other_config)
			if command:
				break

		if not command:
			return

		metadata.emulator_name = emulator_name
		launchers.make_launcher(command, self.name, metadata)

def make_mac_launchers():
	mac_config = config.get_system_config_by_name('Mac')
	if not mac_config:
		return

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
		MacApp(path, config_name, game_config).make_launcher(mac_config)

	if config.launchers_for_unknown_mac_apps:
		for unknown, _ in parser.items('Unknown'):
			MacApp(unknown, unknown.split(':')[-1], {}).make_launcher(mac_config)

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

	if 'Mac' not in config.system_configs:
		return
	mac_config = config.system_configs['Mac']

	game_list = init_game_list()
	#for mac_volume in config.mac_disk_images:
	for mac_volume in mac_config.paths:
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
