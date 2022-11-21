#!/usr/bin/env python3

import datetime
import logging
import time
from collections.abc import Collection
from pathlib import Path
from typing import cast

from meowlauncher.config.main_config import main_config
from meowlauncher.games.gog import (DOSBoxGOGGame, GOGGame, GOGGameInfo,
                                    NormalGOGGame, ScummVMGOGGame,
                                    WindowsGOGGame)
from meowlauncher.util.desktop_files import has_been_done

logger = logging.getLogger(__name__)

def look_in_linux_gog_folder(folder: Path) -> GOGGame | None:
	gameinfo_path = folder.joinpath('gameinfo')
	if not gameinfo_path.is_file():
		return None
	gameinfo = GOGGameInfo(gameinfo_path)

	launch_script = folder.joinpath('start.sh')
	if not launch_script.is_file():
		return None

	#.mojosetup, uninstall-*.sh, docs are also here
	support_folder = folder.joinpath('support')
	if not support_folder.is_dir():
		return None

	if folder.joinpath('dosbox').is_dir():
		return DOSBoxGOGGame(folder, gameinfo, launch_script, support_folder)
	if folder.joinpath('scummvm').is_dir():
		return ScummVMGOGGame(folder, gameinfo, launch_script, support_folder)
	if folder.joinpath('game').is_dir():
		return NormalGOGGame(folder, gameinfo, launch_script, support_folder)

	return None

def look_in_windows_gog_folder(folder: Path) -> WindowsGOGGame | None:
	info_file: Path | None = None
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
	gog_folders = cast(Collection[Path], main_config.gog_folders)
	for gog_folder in gog_folders:
		if not gog_folder.is_dir():
			logger.warning('%s does not exist/is not a directory', gog_folder)
			continue

		for subfolder in gog_folder.iterdir():
			if not main_config.full_rescan:
				if has_been_done('GOG', str(subfolder)):
					continue
			if not subfolder.is_dir():
				continue
			if not (game := look_in_linux_gog_folder(subfolder)):
				logger.info('GOG subfolder does not have a GOG game (detection may have failed): %s', subfolder)
				continue

			game.add_info()
			game.make_launcher()

def do_windows_gog_games() -> None:
	windows_gog_folders = cast(Collection[Path], main_config.windows_gog_folders)
	for windows_gog_folder in windows_gog_folders:
		if not windows_gog_folder.is_dir():
			logger.warning('%s does not exist/is not a directory', windows_gog_folder)
			continue

		for subfolder in windows_gog_folder.iterdir():
			if not main_config.full_rescan:
				if has_been_done('GOG', str(subfolder)):
					continue
			if not subfolder.is_dir():
				continue
			if not (windows_game := look_in_windows_gog_folder(subfolder)):
				logger.info('GOG subfolder does not have a GOG game (detection may have failed): %s', subfolder)
				continue
			
			windows_game.add_info()
			windows_game.make_launchers()

def do_gog_games() -> None:
	time_started = time.perf_counter()

	do_linux_gog_games()

	#TODO: Should have is_wine_available helper function or whatever
	if main_config.wine_path.is_file():
		do_windows_gog_games()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('GOG finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
