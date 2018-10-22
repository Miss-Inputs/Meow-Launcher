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

from config import main_config

debug = '--debug' in sys.argv
print_times = '--print-times' in sys.argv

overall_time_started = time.perf_counter()

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

disambiguate.disambiguate_names()

if '--organize-folders' in sys.argv:
	organize_folders.move_into_folders()

if print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
