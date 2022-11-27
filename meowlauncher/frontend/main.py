import logging

from meowlauncher.config.main_config import main_config

from . import organize_folders, series_detect
from .add_games import add_games
from .disambiguate import disambiguate_names
from .remove_nonexistent_games import remove_nonexistent_games

logger = logging.getLogger(__name__)

def main() -> None:
	"""Recreates output folder if it doesn't exist, calls add_games and does the other things (disambiguate, series detect, etc). The logger here outputs progress messages so it may be useful to add a handler to it, for GUIs or if printed output might look nicer that way"""
	logger.info('Creating output folder')

	if main_config.full_rescan:
		if main_config.output_folder.is_dir():
			for f in main_config.output_folder.iterdir():
				#TODO: We should probably only do this if we know f is made by us, just in case someone wants to set output_folder to somewhere shared with other apps
				f.unlink()
	main_config.output_folder.mkdir(exist_ok=True, parents=True)

	add_games()

	if not main_config.full_rescan:
		logger.info('Removing games which no longer exist')
		remove_nonexistent_games()

	if main_config.get_series_from_name:
		logger.info('Detecting series')
		series_detect.detect_series_for_all_desktops()

	if main_config.disambiguate:
		logger.info('Disambiguating names')
		disambiguate_names()

	if main_config.organize_folders:
		logger.info('Organizing into folders')
		organize_folders.move_into_folders()

__doc__ = main.__doc__ or __name__
