from collections.abc import Callable

from meowlauncher.config.main_config import main_config

from . import organize_folders, series_detect
from .disambiguate import disambiguate_names
from .remove_nonexistent_games import remove_nonexistent_games


def main(progress_function: Callable[..., None]=print):
	progress_function('Creating output folder')

	if main_config.full_rescan:
		if main_config.output_folder.is_dir():
			for f in main_config.output_folder.iterdir():
				#TODO: We should probably only do this if we know f is made by us, just in case someone wants to set output_folder to somewhere shared with other apps
				f.unlink()
	main_config.output_folder.mkdir(exist_ok=True, parents=True)

	if not main_config.full_rescan:
		progress_function('Removing games which no longer exist')
		remove_nonexistent_games()

	if main_config.get_series_from_name:
		progress_function('Detecting series')
		series_detect.detect_series_for_all_desktops()

	progress_function('Disambiguating names')
	disambiguate_names()

	if main_config.organize_folders:
		progress_function('Organizing into folders')
		organize_folders.move_into_folders()
