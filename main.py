import os

import config
import dos
import mac
import mame_machines
import roms
import scummvm
import steam
import remove_nonexistent_games
import disambiguate
import organize_folders

def main(mame_enabled, roms_enabled, dos_enabled, mac_enabled, scummvm_enabled, steam_enabled):
	if config.main_config.full_rescan:
		if os.path.isdir(config.main_config.output_folder):
			for f in os.listdir(config.main_config.output_folder):
				os.unlink(os.path.join(config.main_config.output_folder, f))
	os.makedirs(config.main_config.output_folder, exist_ok=True)

	if mame_enabled:
		mame_machines.process_arcade()
	if roms_enabled:
		roms.process_systems()
	if mac_enabled:
		mac.make_mac_launchers()
	if dos_enabled:
		dos.make_dos_launchers()
	if scummvm_enabled:
		scummvm.add_scummvm_games()
	if steam_enabled:
		steam.process_steam()

	if not config.main_config.full_rescan:
		remove_nonexistent_games.remove_nonexistent_games()

	disambiguate.disambiguate_names()

	if config.main_config.organize_folders:
		organize_folders.move_into_folders()
