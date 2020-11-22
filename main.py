import os

import disambiguate
import dos
import gog
#import mac
import mame_machines
import organize_folders
import remove_nonexistent_games
import roms
import scummvm
import series_detect
import steam
from config.main_config import main_config

def main(progress_function, mame_enabled=True, roms_enabled=True, dos_enabled=True, mac_enabled=True, scummvm_enabled=True, steam_enabled=True, gog_enabled=True):
	def call_progress_function(data, should_increment=True):
		if progress_function:
			progress_function(data, should_increment)

	call_progress_function('Creating output folder')

	if main_config.full_rescan:
		if os.path.isdir(main_config.output_folder):
			for f in os.listdir(main_config.output_folder):
				os.unlink(os.path.join(main_config.output_folder, f))
	os.makedirs(main_config.output_folder, exist_ok=True)

	if mame_enabled:
		call_progress_function('Adding MAME machines')
		mame_machines.process_arcade()
	if roms_enabled:
		call_progress_function('Adding ROMs')
		roms.process_systems()
	#if mac_enabled:
	#	call_progress_function('Scanning Mac software')
	#	mac.make_mac_launchers()
	if dos_enabled:
		call_progress_function('Adding DOS software')
		dos.make_dos_launchers()
	if scummvm_enabled:
		call_progress_function('Adding ScummVM games')
		scummvm.add_scummvm_games()
	if steam_enabled:
		call_progress_function('Adding Steam games')
		steam.process_steam()
	if gog_enabled:
		call_progress_function('Adding GOG games')
		gog.do_gog_games()

	if not main_config.full_rescan:
		call_progress_function('Removing games which no longer exist')
		remove_nonexistent_games.remove_nonexistent_games()
	else:
		call_progress_function(None)

	if main_config.get_series_from_name:
		call_progress_function('Detecting series')
		series_detect.detect_series_for_all_desktops()
	else:
		call_progress_function(None)

	call_progress_function('Disambiguating names')
	disambiguate.disambiguate_names()

	if main_config.organize_folders:
		call_progress_function('Organizing into folders')
		organize_folders.move_into_folders()
	else:
		call_progress_function(None)
