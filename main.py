#!/usr/bin/env python3

import datetime
import time
import os
import sys

import config
import roms
import mame_machines

#TODO Add X-Ambiguous-Name and X-Disambiguator fields (or something named a bit better)
#TODO: For floppy based systems that use MAME (well, currently using MAME for all computers) and have more than one floppy drive, for multi-disk games insert all the disks of the game all at once. I _think_ that works anyway, at least where number_of_disks <= number_of_drives which seems to be the case most of the time. This would be tricky though - I guess I'd assume disk 1 is the boot disk, and other disks are not, and build command lines programmatically. Even if I don't do this, maybe I should only create a launcher for disk 1?


debug = False

overall_time_started = time.perf_counter()

if os.path.isdir(config.output_folder):
	#shutil.rmtree(output_folder)
	for f in os.listdir(config.output_folder):
		os.unlink(os.path.join(config.output_folder, f))
os.makedirs(config.output_folder, exist_ok=True)

if '--debug' in sys.argv:
	debug = True

if '--no-arcade' not in sys.argv:
	time_started = time.perf_counter()
	mame_machines.process_arcade(debug)
	time_ended = time.perf_counter()
	print('Arcade finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

for emulator in config.emulator_configs:
	time_started = time.perf_counter()
	roms.process_emulator(emulator, debug)
	time_ended = time.perf_counter()
	print(emulator['name'], 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


overall_time_ended = time.perf_counter()
print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
