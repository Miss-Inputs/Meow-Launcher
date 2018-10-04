#!/usr/bin/env python3

import datetime
import time
import os
import sys

import config
import roms
import mame_machines
import disambiguate
import organize_folders
import mac
import scummvm
import dos

debug = '--debug' in sys.argv
print_times = '--print-times' in sys.argv

overall_time_started = time.perf_counter()

if os.path.isdir(config.output_folder):
	for f in os.listdir(config.output_folder):
		os.unlink(os.path.join(config.output_folder, f))
os.makedirs(config.output_folder, exist_ok=True)

if '--no-arcade' not in sys.argv:
	mame_machines.process_arcade()

for system in config.system_configs:
	roms.process_system(system)

mac.make_mac_launchers()
dos.make_dos_launchers()

scummvm.add_scummvm_games()

disambiguate.disambiguate_names()

if '--organize-folders' in sys.argv:
	organize_folders.move_into_folders()

if print_times:
	overall_time_ended = time.perf_counter()
	print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
