#!/usr/bin/env python3

import datetime
import os
import time
from pathlib import Path
from typing import Optional

from meowlauncher import desktop_launchers
from meowlauncher.config.main_config import main_config
from meowlauncher.games.gog import (DOSBoxGOGGame, GOGGame, GOGGameInfo,
                                    NormalGOGGame, ScummVMGOGGame,
                                    WindowsGOGGame)


def look_in_linux_gog_folder(folder: Path) -> Optional[GOGGame]:
	gameinfo_path = folder.joinpath('gameinfo')
	if not gameinfo_path.is_file():
		return None
	gameinfo = GOGGameInfo(gameinfo_path)

	launch_script = folder.joinpath('start.sh')
	if not os.path.isfile(launch_script):
		return None

	#.mojosetup, uninstall-*.sh, docs are also here
	support_folder = folder.joinpath('support')
	if not os.path.isdir(support_folder):
		return None

	if os.path.isdir(folder.joinpath('dosbox')):
		return DOSBoxGOGGame(folder, gameinfo, launch_script, support_folder)
	if os.path.isdir(folder.joinpath('scummvm')):
		return ScummVMGOGGame(folder, gameinfo, launch_script, support_folder)
	if os.path.isdir(folder.joinpath('game')):
		return NormalGOGGame(folder, gameinfo, launch_script, support_folder)

	return None

def look_in_windows_gog_folder(folder: Path) -> Optional[WindowsGOGGame]:
	info_file: Optional[Path] = None
	game_id: str
	for file in folder.iterdir():
		if file.name.startswith('goggame-') and file.suffix == '.info':
			info_file = file
			game_id = file.name[8:-5]
			break
		#Other files that may exist: goggame-<gameid>.dll, goggame-<gameid>.hashdb (Galaxy related?), goggame-<gameid>.ico, goglog.ini, goggame-galaxyFileList.ini, goggame.sdb, unins000.exe, unins000.dat, unins000.msg
	if not info_file:
		#There are actually instances where this isn't here: Bonus content items (Prisoner of Ice UK version, SOTC Floppy version, etc) but I don't really know what to do with those right now to be quite honest, I guess I could look for "Launch <blah>.lnk" and extract which game to launch from there? But that's weird
		return None
	return WindowsGOGGame(folder, info_file, game_id)

def do_linux_gog_games() -> None:
	for gog_folder in main_config.gog_folders:
		if not os.path.isdir(gog_folder):
			if main_config.debug:
				print(gog_folder, 'does not exist/is not a directory')
			continue

		for subfolder in os.scandir(gog_folder):
			if not main_config.full_rescan:
				if desktop_launchers.has_been_done('GOG', subfolder.path):
					continue
			if not subfolder.is_dir():
				continue
			if not (game := look_in_linux_gog_folder(subfolder.path)):
				if main_config.debug:
					print('GOG subfolder does not have a GOG game (detection may have failed)', subfolder.path)
				continue

			game.add_metadata()
			game.make_launcher()

def do_windows_gog_games() -> None:
	for windows_gog_folder in main_config.windows_gog_folders:
		if not os.path.isdir(windows_gog_folder):
			if main_config.debug:
				print(windows_gog_folder, 'does not exist/is not a directory')
			continue

		for subfolder in os.scandir(windows_gog_folder):
			if not main_config.full_rescan:
				if desktop_launchers.has_been_done('GOG', subfolder.path):
					continue
			if not subfolder.is_dir():
				continue
			if not (windows_game := look_in_windows_gog_folder(subfolder.path)):
				if main_config.debug:
					print('GOG subfolder does not have a GOG game (detection may have failed)', subfolder.path)
				continue
			
			windows_game.add_metadata()
			windows_game.make_launchers()

def do_gog_games() -> None:
	time_started = time.perf_counter()

	if os.path.isfile(main_config.wine_path) or not main_config.wine_path.startswith('/'):
		do_windows_gog_games()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('GOG finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
