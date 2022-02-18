from collections.abc import Iterator, Sequence
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

from meowlauncher.config.main_config import main_config
from meowlauncher.output.desktop_files import (id_section_name,
                                               metadata_section_name,
                                               section_prefix)

standard_sections = {'Desktop Entry'}
def get_desktop(path: Path) -> ConfigParser:
	parser = ConfigParser(interpolation=None, delimiters='=', comment_prefixes='#')
	parser.optionxform = str #type: ignore[assignment]
	parser.read(path)
	return parser

def destkop_contains(desktop: ConfigParser, section: str=metadata_section_name) -> bool:
	if section not in standard_sections:
		section = section_prefix + section
	return section in desktop

def get_field(desktop: ConfigParser, name: str, section: str=metadata_section_name) -> Optional[str]:
	if section not in standard_sections:
		section = section_prefix + section

	if section not in desktop:
		return None

	entry = desktop[section]
	if name in entry:
		return entry[name]

	return None

def get_array(desktop: ConfigParser, name: str, section: str=metadata_section_name) -> Sequence[str]:
	field = get_field(desktop, name, section)
	if field is None:
		return ()

	return field.split(';')

#These might not belong here in the future, they deal with the output folder in particular rather than specifically .desktop files
def _iter_existing_launchers() -> Iterator[tuple[str, str]]:
	output_folder: Path = main_config.output_folder
	if not output_folder.is_file():
		return
	for path in output_folder.iterdir():
		existing_launcher = get_desktop(path)
		existing_type = get_field(existing_launcher, 'Type', id_section_name)
		existing_id = get_field(existing_launcher, 'Unique-ID', id_section_name)
		if not existing_type or not existing_id:
			#Not expected to happen but maybe there are desktops we don't expect in the output folder
			continue
		yield existing_type, existing_id

def has_been_done(game_type: str, game_id: str) -> bool:
	if not hasattr(has_been_done, 'existing_launchers'):
		has_been_done.existing_launchers = tuple(_iter_existing_launchers()) #type: ignore[attr-defined]

	return any(existing_type == game_type and existing_id == game_id for (existing_type, existing_id) in has_been_done.existing_launchers) #type: ignore[attr-defined]
