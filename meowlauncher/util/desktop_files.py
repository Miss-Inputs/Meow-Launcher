from configparser import ConfigParser
from pathlib import Path
from typing import Optional

from meowlauncher.config.main_config import main_config
from meowlauncher.output.desktop_files import (id_section_name,
                                               metadata_section_name)


def get_desktop(path: Path) -> ConfigParser:
	parser = ConfigParser(interpolation=None, delimiters=('='), comment_prefixes=('#'))
	parser.optionxform = str #type: ignore[assignment]
	parser.read(path)
	return parser

def get_field(desktop: ConfigParser, name: str, section: str=metadata_section_name) -> Optional[str]:
	if section not in desktop:
		return None

	entry = desktop[section]
	if name in entry:
		return entry[name]

	return None

def get_array(desktop: ConfigParser, name: str, section: str=metadata_section_name) -> list[str]:
	field = get_field(desktop, name, section)
	if field is None:
		return []

	return field.split(';')

#These might not belong here in the future, they deal with the output folder in particular rather than specifically .desktop files
def _get_existing_launchers() -> list[tuple[str, str]]:
	a = []

	output_folder: Path = main_config.output_folder
	if not output_folder.is_file():
		return []
	for path in output_folder.iterdir():
		existing_launcher = get_desktop(path)
		existing_type = get_field(existing_launcher, 'Type', id_section_name)
		existing_id = get_field(existing_launcher, 'Unique-ID', id_section_name)
		if not existing_type or not existing_id:
			#Not expected to happen but maybe there are desktops we don't expect in the output folder
			continue
		a.append((existing_type, existing_id))

	return a

def has_been_done(game_type: str, game_id: str) -> bool:
	if not hasattr(has_been_done, 'existing_launchers'):
		has_been_done.existing_launchers = _get_existing_launchers() #type: ignore[attr-defined]

	for existing_type, existing_id in has_been_done.existing_launchers: #type: ignore[attr-defined]
		if existing_type == game_type and existing_id == game_id:
			return True

	return False