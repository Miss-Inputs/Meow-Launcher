import logging
import time
from datetime import timedelta

from meowlauncher.config import main_config

from . import organize_folders, series_detect
from .add_games import add_games
from .disambiguate import disambiguate_names
from .remove_nonexistent_games import remove_nonexistent_games

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger('meowlauncher.frontend.progress')
time_logger = logging.getLogger('meowlauncher.frontend.time')

def main() -> None:
	"""Recreates output folder if it doesn't exist, calls add_games and does the other things (disambiguate, series detect, etc).
	Uses two loggers with non-standard names: meowlauncher.frontend.progress and meowlauncher.frontend.time, to report progress and time taken to do each component respectively, so you may want to set those to be formatted differently"""

	overall_time_started = time.perf_counter()

	progress_logger.info('Creating output folder')

	if main_config.full_rescan:
		if main_config.output_folder.is_dir():
			for f in main_config.output_folder.iterdir():
				#TODO: We should probably only do this if we know f is made by us, just in case someone wants to set output_folder to somewhere shared with other apps
				f.unlink()
	main_config.output_folder.mkdir(exist_ok=True, parents=True)

	add_games()

	if not main_config.full_rescan:
		progress_logger.info('Removing games which no longer exist')
		time_started = time.perf_counter()
		remove_nonexistent_games()
		time_logger.info('Removal of games which no longer exist finished in %s', timedelta(seconds=time.perf_counter() - time_started))

	if main_config.get_series_from_name:
		progress_logger.info('Detecting series')
		time_started = time.perf_counter()
		series_detect.detect_series_for_all_desktops()
		time_logger.info('Series detection by name finished in %s', timedelta(seconds=time.perf_counter() - time_started))

	if main_config.disambiguate:
		progress_logger.info('Disambiguating names')
		time_started = time.perf_counter()
		disambiguate_names()
		time_logger.info('Name disambiguation finished in %s', timedelta(seconds=time.perf_counter() - time_started))

	if main_config.organize_folders:
		progress_logger.info('Organizing into folders')
		time_started = time.perf_counter()
		organize_folders.move_into_folders()
		time_logger.info('Folder organization finished in %s', timedelta(seconds=time.perf_counter() - time_started))

	time_logger.info('Whole thing finished in %s', timedelta(seconds=time.perf_counter() - overall_time_started))
	
__doc__ = main.__doc__ or __name__
