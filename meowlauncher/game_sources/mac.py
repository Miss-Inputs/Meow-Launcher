#!/usr/bin/env python3

from pathlib import Path

from meowlauncher.data.emulators import mac_emulators
from meowlauncher.games.mac import (MacApp, MacLauncher, PathInsideHFS,
                                    does_exist)
from meowlauncher.manually_specified_game_source import \
    ManuallySpecifiedGameSource


class Mac(ManuallySpecifiedGameSource[MacApp]):
	"""GameSource for Classic Mac games, installed to a disk image and paths inside that disk image specified manually, or with a CD and a path to run that game from the CD image."""
	def __init__(self) -> None:
		super().__init__('Mac', MacApp, MacLauncher, mac_emulators)

	def no_longer_exists(self, game_id: str) -> bool:
		hfv_path_str, inner_path_str = game_id.rsplit('/', 1)
		hfv_path = Path(hfv_path_str)
		inner_path = PathInsideHFS(inner_path_str)
		if not hfv_path.is_file():
			return True

		return not does_exist(hfv_path, inner_path)

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
