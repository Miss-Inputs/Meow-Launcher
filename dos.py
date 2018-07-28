#!/usr/bin/env python3

import sys
import os
import json
import urllib.request
import configparser

import launchers
import config
from info.emulator_info import dos_emulators
from metadata import Metadata

debug = '--debug' in sys.argv

def init_game_list():
	if not os.path.exists(config.dos_db_path):
		print("You don't have dos_db.json which is required for this to work. Let me get that for you.")
		#TODO: Is this the wrong way to do this? I think it most certainly is
		dos_db_url = 'https://raw.githubusercontent.com/Zowayix/computer-software-db/master/dos_db.json'
		with urllib.request.urlopen(dos_db_url) as dos_db_request:
			dos_db_data = dos_db_request.read().decode('utf-8')
		with open(config.dos_db_path, 'wt') as dos_db_local_file:
			dos_db_local_file.write(dos_db_data)
			game_list = json.loads(dos_db_data)
	else:
		with open(config.dos_db_path, 'rt') as dos_db_file:
			game_list = json.load(dos_db_file)

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

class DOSApp:
	def __init__(self, path, name, app_config):
		self.path = path
		self.name = name
		self.config = app_config

	def make_launcher(self, dos_config):
		metadata = Metadata()
		metadata.platform = 'DOS'
			
		if 'publisher' in self.config:
			metadata.author = self.config['publisher']
		elif 'developer' in self.config:
			metadata.author = self.config['developer']
		if 'year' in self.config:
			metadata.year = self.config['year']

		metadata.extension = os.path.splitext(self.path)[1][1:].lower()

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
		for emulator in dos_config.chosen_emulators:
			emulator_name = emulator
			command = dos_emulators[emulator].get_command_line(self, dos_config.other_config)
			if command:
				break

		if not command:
			return

		metadata.emulator_name = emulator_name
		launchers.make_launcher(command, self.name, metadata)

def make_dos_launchers():
	dos_config = config.get_system_config_by_name('DOS')
	if not dos_config:
		return

	game_list = init_game_list()
	if not os.path.isfile(config.dos_config_path):
		#TODO: Perhaps notify user they have to do ./dos.py --scan to do the thing
		return

	parser = configparser.ConfigParser(delimiters=('='), allow_no_value=True)
	parser.optionxform = str
	parser.read(config.dos_config_path)

	for path, config_name in parser.items('Apps'):
		if config_name not in game_list:
			print('Oh no!', path, 'refers to', config_name, "but that isn't known")
			continue
		game_config = game_list[config_name]
		DOSApp(path, config_name, game_config).make_launcher(dos_config)

	if config.launchers_for_unknown_dos_apps:
		for unknown, _ in parser.items('Unknown'):
			DOSApp(unknown, unknown.split(':')[-1], {}).make_launcher(dos_config)

def scan_app(path, exe_name, game_list, unknown_games, found_games, ambiguous_games):
	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['app_name'].lower() == exe_name]
	if not possible_games:
		unknown_games.append(path)
	elif len(possible_games) == 1:
		found_games[path] = possible_games[0][0]
	else:
		ambiguous_games[path] = [game_name for game_name, game_config in possible_games]

def scan_dos_folder(path, game_list, unknown_games, found_games, ambiguous_games):
	for root, _, files in os.walk(path):
		for name in files:
			ext = os.path.splitext(name)[1][1:].lower()
			if ext not in ('exe', 'com', 'bat'):
				#TODO: Should there be any other extensions that I forgot existed?
				continue

			path = os.path.join(root, name)
			scan_app(path, name.lower(), game_list, unknown_games, found_games, ambiguous_games)

def scan_dos_folders():
	unknown_games = []
	found_games = {}
	ambiguous_games = {}

	dos_config = config.get_system_config_by_name('DOS')
	if not dos_config:
		return

	game_list = init_game_list()
	for dos_folder in dos_config.paths:
		scan_dos_folder(dos_folder, game_list, unknown_games, found_games, ambiguous_games)

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
	with open(config.dos_config_path, 'wt') as config_file:
		configwriter.write(config_file)
	
	print('Scan results have been written to', config.dos_config_path)
	print('Because not everything can be autodetected, some may be unrecognized')
	print('and you will have to configure them yourself, or may be one of several')
	print('apps and you will have to specify which is which, until I think of')
	print('a better way to do this.')

if __name__ == '__main__':
	os.makedirs(config.output_folder, exist_ok=True)
	if '--scan' in sys.argv:
		scan_dos_folders()
	else:
		make_dos_launchers()
