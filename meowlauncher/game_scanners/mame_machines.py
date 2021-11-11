#!/usr/bin/env python3

import datetime
import sys
import time

from meowlauncher import desktop_launchers, launcher
from meowlauncher.common_types import EmulationStatus
from meowlauncher.config.main_config import main_config
from meowlauncher.data.machines_with_inbuilt_games import (
    bioses_with_inbuilt_games, machines_with_inbuilt_games)
from meowlauncher.games.mame.mame_game import MAMEGame
from meowlauncher.games.mame.mame_metadata import add_metadata, add_status
from meowlauncher.games.mame_common.machine import (
    Machine, get_machine, get_machines_from_source_file, iter_machines)
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.info import emulator_command_line_helpers
from meowlauncher.metadata import Metadata


def is_actually_machine(machine: Machine) -> bool:
	if machine.xml.attrib.get('isbios', 'no') == 'yes': #Hmm, technically there's nothing stopping you launching these
		return False

	if main_config.exclude_system_drivers and machine.is_system_driver:
		return False

	return True

def is_machine_launchable(machine: Machine) -> bool:
	if machine.xml.attrib.get('isdevice', 'no') == 'yes':
		return False

	if machine.xml.attrib.get('runnable', 'yes') == 'no':
		return False

	if machine.has_mandatory_slots:
		return False
	
	return True

def does_user_want_machine(game: MAMEGame) -> bool:
	if main_config.exclude_non_arcade and game.metadata.platform == 'Non-Arcade':
		return False
	if main_config.exclude_pinball and game.metadata.platform == 'Pinball':
		return False

	return True

def make_machine_launcher(game: MAMEGame):
	#pylint: disable=protected-access #It's my code and I say I'm allowed to do that

	params = launcher.LaunchCommand('mame', emulator_command_line_helpers.mame_base(game.machine.basename))
	#TODO: Let's put this in games.emulator, even if only MAME exists as the singular arcade emulator for now; and clean this up some more
	desktop_launchers.make_launcher(params, game.machine.name, game.metadata, 'Arcade' if game.metadata.platform == 'Arcade' else 'MAME', game.machine.basename)

def process_machine(machine: Machine):
	if machine.source_file in main_config.skipped_source_files:
		return

	if not is_actually_machine(machine):
		return

	if not is_machine_launchable(machine):
		return

	if main_config.exclude_non_working and machine.emulation_status == EmulationStatus.Broken and machine.basename not in main_config.non_working_whitelist:
		#This will need to be refactored if anything other than MAME is added
		#The code behind -listxml is of the opinion that protection = imperfect should result in a system being considered entirely broken, but I'm not so sure if that works out
		return

	game = MAMEGame(machine)
	if not does_user_want_machine(game):
		return

	if not default_mame_executable.verifyroms(machine.basename):
		#We do this as late as we can after checks to see if we want to actually add this machine or not, because it takes a while (in a loop of tens of thousands of machines), and hence if we can get out of having to do it we should
		#However this is a reminder to myself to stop trying to be clever (because I am not); we cannot assume -verifyroms would succeed if machine.romless is true because there might be a device which is not romless
		return

	if machine.is_probably_skeleton_driver:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up

		#We'll do this check _after_ verifyroms so we don't spam debug print for a bunch of skeleton drivers we don't have
		if main_config.debug:
			print('Skipping %s (%s, %s) as it is probably a skeleton driver' % (machine.name, machine.basename, machine.source_file))
		return

	add_metadata(game)
	
	make_machine_launcher(game)

def no_longer_exists(game_id: str):
	#This is used to determine what launchers to delete if not doing a full rescan
	return not default_mame_executable or not default_mame_executable.verifyroms(game_id)

def process_inbuilt_game(machine_name: str, inbuilt_game, bios_name=None) -> None:
	if not default_mame_executable.verifyroms(machine_name):
		return

	#TODO: This needs to be moved into a new subclass of EmulatedGame thank you
	#MachineNotFoundException shouldn't happen because verifyroms already returned true? Probably
	machine = get_machine(machine_name, default_mame_executable)
	
	metadata = Metadata()
	metadata.platform = inbuilt_game[1]
	metadata.categories = [inbuilt_game[2]]
	metadata.genre = None #We don't actually know these and it's probably not accurate to call a game "Home Videogame Console" etc
	metadata.subgenre = None #Could possibly add it ourselves to the inbuilt games list but that requires me knowing what I'm talking about when it comes to genres
	metadata.developer = None #We also don't know this necessarily, but it does make sense that the publisher of a built-in game would be the publisher of the console it's built into
	#metadata.specific_info.pop('Number-of-Players') #This also doesn't necessarily match up, you can have a console that supports 2 players but the inbuilt game is for just one
	add_status(machine, metadata)

	args = emulator_command_line_helpers.mame_base(machine_name, bios=bios_name)
	launch_params = launcher.LaunchCommand('mame', args) #I guess this should be refactored one day to allow for different MAME paths
	#machine.metadata.emulator_name = 'MAME'

	unique_id = machine_name
	if bios_name:
		unique_id += ':' + bios_name
	desktop_launchers.make_launcher(launch_params, inbuilt_game[0], metadata, 'Inbuilt game', unique_id)

def process_arcade() -> None:
	time_started = time.perf_counter()

	exe = default_mame_executable
	if not exe:
		raise NotImplementedError('Sorry I need to make it fail gracefully but not yet')

	for machine in iter_machines(exe):
		if not main_config.full_rescan:
			if desktop_launchers.has_been_done('Arcade', machine.basename):
				continue
			if desktop_launchers.has_been_done('MAME', machine.basename):
				continue

		process_machine(machine)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Arcade/MAME machines finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

	time_started = time.perf_counter()

	for machine_name, inbuilt_game in machines_with_inbuilt_games.items():
		if not main_config.full_rescan:
			if desktop_launchers.has_been_done('Inbuilt game', machine_name):
				continue
		process_inbuilt_game(machine_name, inbuilt_game)
	for machine_and_bios_name, inbuilt_game in bioses_with_inbuilt_games.items():
		if not main_config.full_rescan:
			if desktop_launchers.has_been_done('Inbuilt game', machine_and_bios_name[0] + ':' + machine_and_bios_name[1]):
				continue
		process_inbuilt_game(machine_and_bios_name[0], inbuilt_game, machine_and_bios_name[1])

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Machines with inbuilt games finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main() -> None:
	if '--drivers' in sys.argv:
		arg_index = sys.argv.index('--drivers')
		if len(sys.argv) == 2:
			print('--drivers requires an argument')
			return

		driver_list = sys.argv[arg_index + 1].split(',')
		for driver_name in driver_list:
			process_machine(get_machine(driver_name, default_mame_executable))
		return 
	if '--source-file' in sys.argv:
		arg_index = sys.argv.index('--source-file')
		if len(sys.argv) == 2:
			print('--source-file requires an argument')
			return

		source_file = sys.argv[arg_index + 1]
		for machine in get_machines_from_source_file(source_file, default_mame_executable):
			if not is_actually_machine(machine):
				continue
			if not is_machine_launchable(machine):
				continue
			if not default_mame_executable.verifyroms(machine.basename):
				continue
			process_machine(machine)
		return

	process_arcade()
