#!/usr/bin/env python3

import sys
import os

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
			if f_lowercase in (basename + '.ico', 'game.ico', 'icon.ico', 'icon.png') or (f_lowercase.startswith('goggame') and f_lowercase.endswith('.ico')):
				self.icon = os.path.join(base_dir, f)

def make_dos_launchers():
	dos_mac_common.make_launchers('DOS', config.dos_ini_path, DOSApp, dos_emulators)

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
				continue

			path = os.path.join(root, name)
			scan_app(path, name.lower(), game_list, unknown_games, found_games, ambiguous_games)

def scan_dos_folders():
	dos_mac_common.scan_folders('DOS', config.dos_ini_path, scan_dos_folder)

if __name__ == '__main__':
	if '--scan' in sys.argv:
		scan_dos_folders()
	else:
		make_dos_launchers()
