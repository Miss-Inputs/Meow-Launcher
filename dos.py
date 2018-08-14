#!/usr/bin/env python3

import sys
import os
import configparser

import config
from info.emulator_info import dos_emulators
import common
import dos_mac_common

debug = '--debug' in sys.argv

class DOSApp(dos_mac_common.App):
	def additional_metadata(self, metadata):
		metadata.platform = 'DOS'
		basename, extension = os.path.splitext(self.path)
		metadata.extension = extension[1][1:].lower()
		basename = os.path.basename(basename).lower()
		base_dir = os.path.dirname(self.path)
		for f in os.listdir(base_dir):
			f_lowercase = f.lower()
			if f_lowercase in (basename + '.ico', 'game.ico', 'icon.ico') or (f_lowercase.startswith('goggame') and f_lowercase.endswith('.ico')):
				self.icon = os.path.join(base_dir, f)

def make_dos_launchers():
	dos_config = config.get_system_config_by_name('DOS')
	if not dos_config:
		return

	game_list = dos_mac_common.init_game_list('dos')
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
		DOSApp(path, config_name, game_config).make_launcher(dos_config, dos_emulators)

	if config.launchers_for_unknown_dos_apps:
		for unknown, _ in parser.items('Unknown'):
			DOSApp(unknown, unknown.split(':')[-1], {}).make_launcher(dos_config, dos_emulators)

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
		if common.starts_with_any(root + os.sep, config.ignored_directories):
			continue
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

	game_list = dos_mac_common.init_game_list('dos')
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
