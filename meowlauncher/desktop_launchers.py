import configparser
import os
import re
from collections.abc import Mapping
from enum import Enum, Flag
from pathlib import Path
from typing import Any, Optional

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config.main_config import main_config
from meowlauncher.launch_command import LaunchCommand
from meowlauncher.launcher import Launcher
from meowlauncher.metadata import Metadata
from meowlauncher.util.io_utils import ensure_exist, pick_new_filename
from meowlauncher.util.utils import (clean_string, find_filename_tags_at_end,
                                     remove_filename_tags)

metadata_section_name = 'X-Meow Launcher Metadata'
id_section_name = 'X-Meow Launcher ID'
junk_section_name = 'X-Meow Launcher Junk'
image_section_name = 'X-Meow Launcher Images'
name_section_name = 'X-Meow Launcher Names'
document_section_name = 'X-Meow Launcher Documents'
description_section_name = 'X-Meow Launcher Descriptions'

def get_desktop(path: Path) -> configparser.ConfigParser:
	parser = configparser.ConfigParser(interpolation=None, delimiters=('='), comment_prefixes=('#'))
	parser.optionxform = str #type: ignore[assignment]
	parser.read(path)
	return parser

def get_field(desktop: configparser.ConfigParser, name: str, section: str=metadata_section_name) -> Optional[str]:
	if section not in desktop:
		return None

	entry = desktop[section]
	if name in entry:
		return entry[name]

	return None

def get_array(desktop: configparser.ConfigParser, name: str, section: str=metadata_section_name) -> list[str]:
	field = get_field(desktop, name, section)
	if field is None:
		return []

	return field.split(';')

def make_linux_desktop_for_launcher(launcher: Launcher):
	name = launcher.game.name

	filename_tags = find_filename_tags_at_end(name)
	name = remove_filename_tags(name)

	fields = launcher.info_fields
	
	if launcher.runner.is_emulated:
		fields[metadata_section_name]['Emulator'] = launcher.runner.name

	if filename_tags:
		fields[junk_section_name]['Filename-Tags'] = filename_tags
	fields[junk_section_name]['Original-Name'] = name

	fields[id_section_name] = {}
	fields[id_section_name]['Type'] = launcher.game_type
	fields[id_section_name]['Unique-ID'] = launcher.game_id

	make_linux_desktop(launcher.get_launch_command(), name, fields)

def make_linux_desktop(launcher: LaunchCommand, display_name: str, fields: Mapping[str, Mapping[str, Any]]=None):
	#TODO: Remove this version, replace with above
	filename = pick_new_filename(main_config.output_folder, display_name, 'desktop')
	
	path = main_config.output_folder.joinpath(filename)

	configwriter = configparser.ConfigParser(interpolation=None)
	configwriter.optionxform = str #type: ignore[assignment]

	configwriter.add_section('Desktop Entry')
	desktop_entry = configwriter['Desktop Entry']

	#Necessary for this thing to even be recognized
	desktop_entry['Type'] = 'Application'
	desktop_entry['Encoding'] = 'UTF-8'

	desktop_entry['Name'] = clean_string(display_name)
	desktop_entry['Exec'] = launcher.make_linux_command_string()
	if launcher.working_directory:
		desktop_entry['Path'] = launcher.working_directory

	if fields:
		for section_name, section in fields.items():
			if not section:
				continue
			configwriter.add_section(section_name)
			section_writer = configwriter[section_name]

			for k, v in section.items():
				if v is None:
					continue

				use_image_object = False
				value_as_string: str
				if have_pillow:
					if isinstance(v, Image.Image):
						use_image_object = True
						this_image_folder = main_config.image_folder.joinpath(k)
						this_image_folder.mkdir(exist_ok=True, parents=True)
						image_path = this_image_folder.joinpath(filename + '.png')
						v.save(image_path, 'png')
						value_as_string = str(image_path)

				if isinstance(v, list):
					if not v:
						continue
					value_as_string = ';'.join(['None' if item is None else item.name if isinstance(item, Enum) else str(item) for item in v])
				elif isinstance(v, Enum):
					if v.name:
						value_as_string = v.name
					elif isinstance(v, Flag):
						value_as_string = str(v).replace('|', ';')
						value_as_string = value_as_string[value_as_string.find('.') + 1:]

				elif not use_image_object:
					value_as_string = str(v)

				value_as_string = clean_string(value_as_string)
				section_writer[k.replace('_', '-')] = value_as_string

	if image_section_name in configwriter:
		keys_to_try = ['Icon'] + main_config.use_other_images_as_icons
		for k in keys_to_try:
			if k in configwriter[image_section_name]:
				desktop_entry['Icon'] = configwriter[image_section_name][k]
				break

	ensure_exist(path)
	with open(path, 'wt', encoding='utf-8') as f:
		configwriter.write(f)

	#Set executable, but also set everything else because whatever
	os.chmod(path, 0o7777)


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


split_brackets = re.compile(r' (?=\()')
def make_launcher(launch_params: LaunchCommand, name: str, metadata: Metadata, id_type: str, unique_id: str):
	#TODO: Remove this, once it is no longer used
	display_name = remove_filename_tags(name)
	filename_tags = find_filename_tags_at_end(name)

	fields = metadata.to_launcher_fields()

	if filename_tags:
		fields[junk_section_name]['Filename-Tags'] = filename_tags
	fields[junk_section_name]['Original-Name'] = name

	fields[id_section_name] = {}
	fields[id_section_name]['Type'] = id_type
	fields[id_section_name]['Unique-ID'] = unique_id

	#For very future use, this is where the underlying host platform is abstracted away. Right now we only run on Linux though so zzzzz
	make_linux_desktop(launch_params, display_name, fields)
