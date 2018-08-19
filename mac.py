#!/usr/bin/env python3

import sys
import os
import configparser

import config
import hfs
from info.emulator_info import mac_emulators
import dos_mac_common

debug = '--debug' in sys.argv

class MacApp(dos_mac_common.App):
	def additional_metadata(self, metadata):
		metadata.platform = 'Mac'

def make_mac_launchers():
	mac_config = config.get_system_config_by_name('Mac')
	if not mac_config:
		return

	game_list = dos_mac_common.init_game_list('mac')
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
		MacApp(path, config_name, game_config).make_launcher(mac_config, mac_emulators)

	if config.launchers_for_unknown_mac_apps:
		for unknown, _ in parser.items('Unknown'):
			MacApp(unknown, unknown.split(':')[-1], {}).make_launcher(mac_config, mac_emulators)

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
	dos_mac_common.scan_folders('Mac', config.mac_config_path, scan_mac_volume)

if __name__ == '__main__':
	os.makedirs(config.output_folder, exist_ok=True)
	if '--scan' in sys.argv:
		scan_mac_volumes()
	else:
		make_mac_launchers()
