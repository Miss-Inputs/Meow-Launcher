#!/usr/bin/env python3

import datetime
import time
import os
import sys

import roms
import mame_machines
import disambiguate
import organize_folders
import mac
import scummvm
import dos
import remove_nonexistent_games

from config import main_config, command_line_flags

if '--refresh-config' in sys.argv:
	#TODO: Do this on first run... or is that a bad idea
	exit()

overall_time_started = time.perf_counter()

if command_line_flags['full_rescan']:
	if os.path.isdir(main_config.output_folder):
		for f in os.listdir(main_config.output_folder):
			os.unlink(os.path.join(main_config.output_folder, f))
os.makedirs(main_config.output_folder, exist_ok=True)

if '--no-arcade' not in sys.argv:
	mame_machines.process_arcade()

roms.process_systems()

mac.make_mac_launchers()
dos.make_dos_launchers()

scummvm.add_scummvm_games()

if not command_line_flags['full_rescan']:
	remove_nonexistent_games.remove_nonexistent_games()

disambiguate.disambiguate_names()

if '--organize-folders' in sys.argv:
	organize_folders.move_into_folders()

if command_line_flags['print_times']:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
