import datetime
import os
import time

from meowlauncher.config.main_config import main_config
from meowlauncher.desktop_launchers import make_linux_desktop_for_launcher
from meowlauncher.game_sources import (game_sources, gog, itch_io,
                                       mame_machines, roms, steam)

from . import organize_folders, series_detect
from .disambiguate import disambiguate_names
from .remove_nonexistent_games import remove_nonexistent_games


def main(progress_function, mame_enabled=True, roms_enabled=True, steam_enabled=True, gog_enabled=True, itch_io_enabled=True):
	def call_progress_function(data, should_increment=True):
		if progress_function:
			progress_function(data, should_increment)

	call_progress_function('Creating output folder')

	if main_config.full_rescan:
		if os.path.isdir(main_config.output_folder):
			for f in os.listdir(main_config.output_folder):
				os.unlink(os.path.join(main_config.output_folder, f))
	os.makedirs(main_config.output_folder, exist_ok=True)

	for game_source in game_sources:
		#TODO: Should actually use blah_enabled in some way, or some equivalent basically
		time_started = time.perf_counter()
		count = 0
		
		call_progress_function('Adding ' + game_source.description)
		if not game_source.is_available:
			continue
		for launcher in game_source.get_launchers():
			count += 1
			make_linux_desktop_for_launcher(launcher)
		if main_config.print_times:
			time_ended = time.perf_counter()
			call_progress_function(f'{count} {game_source.description} finished in {str(datetime.timedelta(seconds=time_ended - time_started))}')

	if mame_enabled:
		call_progress_function('Adding MAME machines')
		mame_machines.process_arcade()
	if roms_enabled:
		call_progress_function('Adding ROMs')
		roms.process_platforms()
	if steam_enabled:
		call_progress_function('Adding Steam games')
		steam.process_steam()
	if gog_enabled:
		call_progress_function('Adding GOG games')
		gog.do_gog_games()
	if itch_io_enabled:
		call_progress_function('Adding itch.io games')
		itch_io.do_itch_io_games()

	if not main_config.full_rescan:
		call_progress_function('Removing games which no longer exist')
		remove_nonexistent_games()
	else:
		call_progress_function(None)

	if main_config.get_series_from_name:
		call_progress_function('Detecting series')
		series_detect.detect_series_for_all_desktops()
	else:
		call_progress_function(None)

	call_progress_function('Disambiguating names')
	disambiguate_names()

	if main_config.organize_folders:
		call_progress_function('Organizing into folders')
		organize_folders.move_into_folders()
	else:
		call_progress_function(None)
