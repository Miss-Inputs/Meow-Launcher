#!/usr/bin/env python3

import os

import pc
from config.system_config import system_configs
from info.emulator_info import mac_emulators

try:
	import machfs
	have_machfs = True
except ImportError:
	have_machfs = False

mac_config = system_configs.get('Mac')

def get_path(volume, path):
	#Skip the first part since that's the volume name and the tuple indexing for machfs.Volume doesn't work that way
	return volume[tuple(path.split(':')[1:])]

def does_exist(hfv_path, path):
	if not have_machfs:
		#I guess it might just be safer to assume it's still there
		return True
	v = machfs.Volume()
	try:
		with open(hfv_path, 'rb') as f:
		#Hmm, this could be slurping very large (maybe gigabyte(s)) files all at once
			v.read(f.read())
			try:
				get_path(v, path)
				return True
			except KeyError:
				return False
	except FileNotFoundError:
		return False

class MacApp(pc.App):
	def __init__(self, info):
		super().__init__(info)
		self.hfv_path = info['hfv_path']

	@property
	def is_valid(self):
		return does_exist(self.hfv_path, self.path)

	def get_fallback_name(self):
		return self.path.split(':')[-1]

	def additional_metadata(self):
		self.metadata.platform = 'Mac'

	def get_launcher_id(self):
		return self.hfv_path + '/' + self.path

def no_longer_exists(game_id):
	hfv_path, inner_path = game_id.split('/', 1)
	if not os.path.isfile(hfv_path):
		return True

	return not does_exist(hfv_path, inner_path)

def make_mac_launchers():
	if mac_config:
		if not mac_config.chosen_emulators:
			return
	pc.make_launchers('Mac', MacApp, mac_emulators, mac_config)

# def scan_app(hfv_path, app, game_list, unknown_games, found_games, ambiguous_games):
# 	overall_path = hfv_path + ':' + app['path']

# 	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['creator_code'] == app['creator']]
# 	if not possible_games:
# 		unknown_games.append(overall_path)
# 	elif len(possible_games) == 1:
# 		found_games[overall_path] = possible_games[0][0]
# 	else:
# 		possible_games = [(game_name, game_config) for game_name, game_config in possible_games if game_config['app_name'] == app['name']]
# 		if not possible_games:
# 			unknown_games.append(overall_path)
# 		elif len(possible_games) == 1:
# 			found_games[overall_path] = possible_games[0][0]
# 		else:
# 			ambiguous_games[overall_path] = [game_name for game_name, game_config in possible_games]

# def scan_mac_volume(path, game_list, unknown_games, found_games, ambiguous_games):
# 	for f in hfs.list_hfv(path):
# 		if f['file_type'] != 'APPL':
# 			continue
# 		scan_app(path, f, game_list, unknown_games, found_games, ambiguous_games)

# def scan_mac_volumes():
# 	pc.scan_folders('Mac', mac_ini_path, scan_mac_volume)

if __name__ == '__main__':
	# if '--scan' in sys.argv:
	# 	scan_mac_volumes()
	# else:
	# 	make_mac_launchers()
	make_mac_launchers()
