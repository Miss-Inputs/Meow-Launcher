#!/usr/bin/env python3

import datetime
import sys
import time

import launchers
from common_types import EmulationStatus
from config.main_config import main_config
from data.machines_with_inbuilt_games import (bioses_with_inbuilt_games,
                                              machines_with_inbuilt_games)
from info import emulator_command_line_helpers
from mame_helpers import get_mame_xml, iter_mame_entire_xml, verify_romset
from mame_machine import Machine, get_machines_from_source_file
from mame_metadata import add_metadata, add_status


def is_actually_machine(machine):
	if machine.xml.attrib.get('runnable', 'yes') == 'no':
		return False

	if machine.xml.attrib.get('isbios', 'no') == 'yes': #Hmm, technically there's nothing stopping you launching these
		return False

	if machine.xml.attrib.get('isdevice', 'no') == 'yes':
		return False

	return True

def is_machine_launchable(machine):
	if machine.has_mandatory_slots:
		return False
	
	return True

def does_user_want_machine(machine):
	if main_config.exclude_non_arcade and machine.metadata.platform == 'Non-Arcade':
		return False
	if main_config.exclude_pinball and machine.metadata.platform == 'Pinball':
		return False
	if main_config.exclude_system_drivers and machine.is_system_driver:
		return False

	return True

def make_machine_launcher(machine):
	#pylint: disable=protected-access #It's my code and I say I'm allowed to do that
	if not machine._has_inited_metadata:
		machine._add_metadata_fields()

	slot_options = {}

	params = launchers.LaunchParams('mame', emulator_command_line_helpers.mame_base(machine.basename, slot_options=slot_options))
	#TODO: Let's put this in emulator_info, even if only MAME exists as the singular arcade emulator for now; and clean this up some more
	launchers.make_launcher(params, machine.name, machine.metadata, 'Arcade' if machine.metadata.platform == 'Arcade' else 'MAME', machine.basename)

def process_machine(machine):
	if machine.is_skeleton_driver:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up

		#We'll do this check _after_ verify_romset so we don't spam debug print for a bunch of skeleton drivers we don't have
		if main_config.debug:
			print('Skipping %s (%s, %s) as it is probably a skeleton driver' % (machine.name, machine.basename, machine.source_file))
		return

	add_metadata(machine)
	
	make_machine_launcher(machine)

def no_longer_exists(game_id):
	#This is used to determine what launchers to delete if not doing a full rescan
	return not verify_romset(game_id)

def process_machine_element(machine_element):
	machine = Machine(machine_element)
	if machine.source_file in main_config.skipped_source_files:
		return

	if not is_actually_machine(machine):
		return

	if not is_machine_launchable(machine):
		return

	if not does_user_want_machine(machine):
		return

	if main_config.exclude_non_working and machine.emulation_status == EmulationStatus.Broken and machine.basename not in main_config.non_working_whitelist:
		#This will need to be refactored if anything other than MAME is added
		#The code behind -listxml is of the opinion that protection = imperfect should result in a system being considered entirely broken, but I'm not so sure if that works out
		return

	if not verify_romset(machine.basename):
		#We do this as late as we can after checks to see if we want to actually add this machine or not, because it takes a while (in a loop of tens of thousands of machines), and hence if we can get out of having to do it we should
		#However this is a reminder to myself to stop trying to be clever (because I am not); we cannot assume -verifyroms would succeed if machine.romless is true because there might be a device which is not romless
		return

	process_machine(machine)

def process_inbuilt_game(machine_name, inbuilt_game, bios_name=None):
	if not verify_romset(machine_name):
		return

	machine_xml = get_mame_xml(machine_name)
	#MachineNotFoundException shouldn't happen because verify_romset already returned true? Probably
	machine = Machine(machine_xml, init_metadata=True)
	
	machine.metadata.platform = inbuilt_game[1]
	machine.metadata.categories = [inbuilt_game[2]]
	machine.metadata.genre = None #We don't actually know these and it's probably not accurate to call a game "Home Videogame Console" etc
	machine.metadata.subgenre = None #Could possibly add it ourselves to the inbuilt games list but that requires me knowing what I'm talking about when it comes to genres
	machine.metadata.developer = None #We also don't know this necessarily, but it does make sense that the publisher of a built-in game would be the publisher of the console it's built into
	machine.metadata.specific_info.pop('Number-of-Players') #This also doesn't necessarily match up, you can have a console that supports 2 players but the inbuilt game is for just one
	add_status(machine)

	args = emulator_command_line_helpers.mame_base(machine_name, bios=bios_name)
	launch_params = launchers.LaunchParams('mame', args) #I guess this should be refactored one day to allow for different MAME paths
	machine.metadata.emulator_name = 'MAME'

	unique_id = machine_name
	if bios_name:
		unique_id += ':' + bios_name
	launchers.make_launcher(launch_params, inbuilt_game[0], machine.metadata, 'Inbuilt game', unique_id)

def process_arcade():
	time_started = time.perf_counter()

	for machine_name, machine_element in iter_mame_entire_xml():
		if not main_config.full_rescan:
			if launchers.has_been_done('Arcade', machine_name):
				continue
			if launchers.has_been_done('MAME', machine_name):
				continue

		process_machine_element(machine_element)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Arcade/MAME machines finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

	time_started = time.perf_counter()

	for machine_name, inbuilt_game in machines_with_inbuilt_games.items():
		if not main_config.full_rescan:
			if launchers.has_been_done('Inbuilt game', machine_name):
				continue
		process_inbuilt_game(machine_name, inbuilt_game)
	for machine_and_bios_name, inbuilt_game in bioses_with_inbuilt_games.items():
		if not main_config.full_rescan:
			if launchers.has_been_done('Inbuilt game', machine_and_bios_name[0] + ':' + machine_and_bios_name[1]):
				continue
		process_inbuilt_game(machine_and_bios_name[0], inbuilt_game, machine_and_bios_name[1])

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Machines with inbuilt games finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main():
	if '--drivers' in sys.argv:
		arg_index = sys.argv.index('--drivers')
		if len(sys.argv) == 2:
			print('--drivers requires an argument')
			return

		driver_list = sys.argv[arg_index + 1].split(',')
		for driver_name in driver_list:
			process_machine_element(get_mame_xml(driver_name))
		return 
	if '--source-file' in sys.argv:
		arg_index = sys.argv.index('--source-file')
		if len(sys.argv) == 2:
			print('--source-file requires an argument')
			return

		source_file = sys.argv[arg_index + 1]
		for machine in get_machines_from_source_file(source_file):
			if not is_actually_machine(machine):
				continue
			if not is_machine_launchable(machine):
				continue
			if not verify_romset(machine.basename):
				continue
			process_machine(machine)
		return

	process_arcade()

if __name__ == '__main__':
	main()
