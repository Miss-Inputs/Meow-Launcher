#!/usr/bin/env python3

#TODO: Eventually this wouldn't be needed - you would just have a --game-sources argument in cli_main.py and you can have one or many
#Until then this will duplicate code from there so I am sorry

import datetime
import sys
import time

from meowlauncher import organize_folders
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.desktop_launchers import make_linux_desktop_for_launcher
from meowlauncher.disambiguate import disambiguate_names
from meowlauncher.game_sources import (game_sources, gog, itch_io,
                                       mame_machines, mame_software, roms,
                                       scummvm, steam)
from meowlauncher.games.mame_common.machine import (
    get_machine, get_machines_from_source_file)
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.remove_nonexistent_games import remove_nonexistent_games
from meowlauncher.series_detect import detect_series_for_all_desktops


def process_roms_args() -> None:
	if len(sys.argv) >= 2 and '--platforms' in sys.argv:
		arg_index = sys.argv.index('--platforms')
		if len(sys.argv) == 2:
			print('--platforms requires an argument')
			return

		platform_list = sys.argv[arg_index + 1].split(',')
		for platform_name in platform_list:
			roms.process_platform(platform_configs[platform_name])
		return

	roms.process_platforms()

def process_mame_args() -> None:
	if '--drivers' in sys.argv:
		arg_index = sys.argv.index('--drivers')
		if len(sys.argv) == 2:
			print('--drivers requires an argument')
			return

		driver_list = sys.argv[arg_index + 1].split(',')
		for driver_name in driver_list:
			mame_machines.process_machine(get_machine(driver_name, default_mame_executable))
		return 
	if '--source-file' in sys.argv:
		arg_index = sys.argv.index('--source-file')
		if len(sys.argv) == 2:
			print('--source-file requires an argument')
			return

		source_file = sys.argv[arg_index + 1]
		for machine in get_machines_from_source_file(source_file, default_mame_executable):
			if not mame_machines.is_actually_machine(machine):
				continue
			if not mame_machines.is_machine_launchable(machine):
				continue
			if not default_mame_executable.verifyroms(machine.basename):
				continue
			mame_machines.process_machine(machine)
		return

	mame_machines.process_arcade()

def main() -> None:
	if sys.argv[1] == 'roms':
		process_roms_args()
	elif sys.argv[1] == 'mame':
		process_mame_args()
	elif sys.argv[1] == 'gog':
		gog.do_gog_games()
	elif sys.argv[1] == 'itchio':
		itch_io.do_itch_io_games()
	elif sys.argv[1] == 'scummvm':
		scummvm.add_scummvm_games()
	elif sys.argv[1] == 'mame_software':
		mame_software.add_mame_software()
	elif sys.argv[1] == 'steam':
		steam.process_steam()
	
	elif sys.argv[1] == 'series_detect':
		detect_series_for_all_desktops()
	elif sys.argv[1] == 'remove_nonexistent_games':
		remove_nonexistent_games()
	elif sys.argv[1] == 'disambiguate':
		disambiguate_names()
	elif sys.argv[1] == 'organize_folders':
		#This one's a bit jank and I should clean it up I guess
		organize_folders.main()
	else:
		for game_source in game_sources:
			if sys.argv[1] in {game_source.name, game_source.name.lower()}:
				time_started = time.perf_counter()
				count = 0
				
				print('Adding ' + game_source.description)
				if not game_source.is_available:
					continue
				for launcher in game_source.get_launchers():
					count += 1
					make_linux_desktop_for_launcher(launcher)
				time_ended = time.perf_counter()
				print(f'Added {count} {game_source.description} in {str(datetime.timedelta(seconds=time_ended - time_started))}')
				break
		else:
			print('Unknown game source', sys.argv[1])

if __name__ == '__main__':
	main()
