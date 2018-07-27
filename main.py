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

debug = '--debug' in sys.argv

overall_time_started = time.perf_counter()

if os.path.isdir(config.output_folder):
	for f in os.listdir(config.output_folder):
		os.unlink(os.path.join(config.output_folder, f))
os.makedirs(config.output_folder, exist_ok=True)

if '--no-arcade' not in sys.argv:
	time_started = time.perf_counter()
	mame_machines.process_arcade()
	time_ended = time.perf_counter()
	print('Arcade finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

for system in config.system_configs:
	time_started = time.perf_counter()
	roms.process_system(system)
	time_ended = time.perf_counter()
	print(system.name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

#This is turned off by the default because it's a bit experimental which is a nice way of saying it's a bit shit, needs hfsutils and parses command line output and ughhhh that's a bit gross hey
if '--with-mac' in sys.argv:
	time_started = time.perf_counter()
	mac.make_mac_launchers()
	time_ended = time.perf_counter()
	print('Mac finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

time_started = time.perf_counter()
scummvm.add_scummvm_games()
time_ended = time.perf_counter()
print('ScummVM finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

time_started = time.perf_counter()
disambiguate.disambiguate_names()
time_ended = time.perf_counter()
print('Name disambiguation finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

if '--organize-folders' in sys.argv:
	time_started = time.perf_counter()
	organize_folders.move_into_folders()
	time_ended = time.perf_counter()
	print('Folder organization finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

overall_time_ended = time.perf_counter()
print('Whole thing finished in', str(datetime.timedelta(seconds=overall_time_ended - overall_time_started)))
