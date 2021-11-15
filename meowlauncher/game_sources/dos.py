#!/usr/bin/env python3

import os

from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.dos import DOSApp
from meowlauncher.games.pc import AppLauncher

from . import pc

dos_config = platform_configs.get('DOS')

class DOS(pc.PCGameSource):
	def __init__(self) -> None:
		super().__init__('DOS', DOSApp, AppLauncher, dos_config)

	def no_longer_exists(self, game_id: str) -> bool:
		return not os.path.isfile(game_id)

#TODO Actually re-implement this, this is just old code and is only just there to refer to what logic I was using
# def scan_app(path, exe_name, game_list, unknown_games, found_games, ambiguous_games):
# 	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['app_name'].lower() == exe_name]
# 	if not possible_games:
# 		unknown_games.append(path)
# 	elif len(possible_games) == 1:
# 		found_games[path] = possible_games[0][0]
# 	else:
# 		ambiguous_games[path] = [game_name for game_name, game_config in possible_games]

# def scan_dos_folder(path, game_list, unknown_games, found_games, ambiguous_games):
# 	for root, _, files in os.walk(path):
# 		if common.starts_with_any(root + os.sep, main_config.ignored_directories):
# 			continue
# 		for name in files:
# 			ext = os.path.splitext(name)[1][1:].lower()
# 			if ext not in ('exe', 'com', 'bat'):
# 				continue

# 			path = os.path.join(root, name)
# 			scan_app(path, name.lower(), game_list, unknown_games, found_games, ambiguous_games)
