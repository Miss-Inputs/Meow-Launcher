#!/usr/bin/env python3

#We will put stuff in here for now until one day we rewrite the whole CLI, to call only an individual game_scanner etc etc
#I sure do like to say "we" when it is just me

import sys

from meowlauncher import organize_folders
from meowlauncher.disambiguate import disambiguate_names
from meowlauncher.game_scanners import (dos, gog, itch_io, mac, mame_machines,
                                        mame_software, roms, scummvm, steam)
from meowlauncher.remove_nonexistent_games import remove_nonexistent_games
from meowlauncher.series_detect import detect_series_for_all_desktops


def main() -> None:
	if sys.argv[1] == 'roms':
		roms.main() #Hmm should this be having such a method
	elif sys.argv[1] == 'mame':
		mame_machines.main() #hmmmmm
	elif sys.argv[1] == 'dos':
		dos.make_dos_launchers()
	elif sys.argv[1] == 'gog':
		gog.do_gog_games()
	elif sys.argv[1] == 'itchio':
		itch_io.do_itch_io_games()
	elif sys.argv[1] == 'scummvm':
		scummvm.add_scummvm_games()
	elif sys.argv[1] == 'mac':
		mac.make_mac_launchers()
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
	

if __name__ == '__main__':
	main()
