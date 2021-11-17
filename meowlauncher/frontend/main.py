import datetime
import time
from collections.abc import Callable
from typing import Optional

from meowlauncher.config.main_config import main_config
from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.game_sources import game_sources, gog, itch_io, steam
from meowlauncher.output.desktop_files import make_linux_desktop_for_launcher

from . import organize_folders, series_detect
from .disambiguate import disambiguate_names
from .remove_nonexistent_games import remove_nonexistent_games


def add_games(source: GameSource, progress_function: Callable[..., None]=print) -> int:
	time_started = time.perf_counter()
	count = 0
	
	print('Adding ' + source.description)
	if isinstance(source, CompoundGameSource):
		for subsource in source.sources:
			count += add_games(subsource)
	else:
		for launcher in source.get_launchers():
			count += 1
			make_linux_desktop_for_launcher(launcher)
	time_ended = time.perf_counter()
	time_taken = datetime.timedelta(seconds=time_ended - time_started)
	if count:
		progress_function(f'Added {count} {source.description} in {str(time_taken)} ({time_taken.total_seconds() / count} secs per game)')
	else:
		progress_function(f'Did not add any {source.description}')
	return count

def main(progress_function: Optional[Callable[..., None]], steam_enabled=True, gog_enabled=True, itch_io_enabled=True):
	def call_progress_function(data, should_increment=True):
		if progress_function:
			progress_function(data, should_increment)

	call_progress_function('Creating output folder')

	if main_config.full_rescan:
		if main_config.output_folder.is_dir():
			for f in main_config.output_folder.iterdir():
				#TODO: We should probably only do this if we know f is made by us, just in case someone wants to set output_folder to somewhere shared with other apps
				f.unlink()
	main_config.output_folder.mkdir(exist_ok=True)

	for game_source in game_sources:
		if not game_source.is_available:
			continue
		add_games(game_source, call_progress_function)
		#TODO: Should actually use blah_enabled in some way, or some equivalent basically
		
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
