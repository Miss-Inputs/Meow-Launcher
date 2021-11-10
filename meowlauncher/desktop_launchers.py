import configparser
from typing import Any, Optional
import os
from pathlib import Path
from enum import Enum, Flag
import re

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config.main_config import main_config
from meowlauncher.util.utils import (find_filename_tags_at_end,
                                     remove_filename_tags, clean_string)
from meowlauncher.util.io_utils import pick_new_filename, ensure_exist				
from meowlauncher.launcher import LaunchCommand

metadata_section_name = 'X-Meow Launcher Metadata'
id_section_name = 'X-Meow Launcher ID'
junk_section_name = 'X-Meow Launcher Junk'
image_section_name = 'X-Meow Launcher Images'
name_section_name = 'X-Meow Launcher Names'
document_section_name = 'X-Meow Launcher Documents'
description_section_name = 'X-Meow Launcher Descriptions'

def get_desktop(path: str) -> configparser.ConfigParser:
	parser = configparser.ConfigParser(interpolation=None, delimiters=('='), comment_prefixes=('#'))
	parser.optionxform = str #type: ignore
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

def make_linux_desktop(launch_command: LaunchCommand, display_name: str, fields: dict[str, dict[str, Any]]=None):
	filename = pick_new_filename(main_config.output_folder, display_name, 'desktop')
	
	path = os.path.join(main_config.output_folder, filename)

	configwriter = configparser.ConfigParser(interpolation=None)
	configwriter.optionxform = str #type: ignore

	configwriter.add_section('Desktop Entry')
	desktop_entry = configwriter['Desktop Entry']

	#Necessary for this thing to even be recognized
	desktop_entry['Type'] = 'Application'
	desktop_entry['Encoding'] = 'UTF-8'

	desktop_entry['Name'] = clean_string(display_name)
	desktop_entry['Exec'] = launch_command.make_linux_command_string()
	if launch_command.working_directory:
		desktop_entry['Path'] = launch_command.working_directory

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
						this_image_folder = os.path.join(main_config.image_folder, k)
						Path(this_image_folder).mkdir(exist_ok=True, parents=True)
						image_path = os.path.join(this_image_folder, filename + '.png')
						v.save(image_path, 'png')
						value_as_string = image_path

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
	with open(path, 'wt') as f:
		configwriter.write(f)

	#Set executable, but also set everything else because whatever
	os.chmod(path, 0o7777)


#These might not belong here in the future, they deal with the output folder in particular rather than specifically .desktop files
def _get_existing_launchers():
	a = []

	output_folder = main_config.output_folder
	if not os.path.isdir(output_folder):
		return []
	for name in os.listdir(output_folder):
		path = os.path.join(output_folder, name)

		existing_launcher = get_desktop(path)
		existing_type = get_field(existing_launcher, 'Type', id_section_name)
		existing_id = get_field(existing_launcher, 'Unique-ID', id_section_name)
		a.append((existing_type, existing_id))

	return a

def has_been_done(game_type, game_id):
	if not hasattr(has_been_done, 'existing_launchers'):
		has_been_done.existing_launchers = _get_existing_launchers()

	for existing_type, existing_id in has_been_done.existing_launchers:
		if existing_type == game_type and existing_id == game_id:
			return True

	return False


split_brackets = re.compile(r' (?=\()')
def make_launcher(launch_params, name, metadata, id_type, unique_id):
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
