import configparser
import os
import re
from collections.abc import Iterable
from enum import Enum, Flag
from typing import TYPE_CHECKING

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config.main_config import main_config
from meowlauncher.util.io_utils import ensure_exist, pick_new_filename
from meowlauncher.util.utils import (clean_string, find_filename_tags_at_end,
                                     remove_filename_tags)

if TYPE_CHECKING:
	from meowlauncher.launcher import Launcher
	from meowlauncher.metadata import Metadata
	from meowlauncher.launch_command import LaunchCommand

metadata_section_name = 'Metadata'
id_section_name = 'ID'
junk_section_name = 'Junk'
image_section_name = 'Images'

def make_linux_desktop_for_launcher(launcher: 'Launcher'):
	name = launcher.game.name

	filename_tags = find_filename_tags_at_end(name)
	name = remove_filename_tags(name)

	if launcher.runner.is_emulated:
		launcher.game.metadata.emulator_name = launcher.runner.name

	_make_linux_desktop(launcher.get_launch_command(), name, launcher.game.metadata, filename_tags, launcher.game_type, launcher.game_id)

def _make_linux_desktop(launcher: 'LaunchCommand', display_name: str, metadata: 'Metadata', filename_tags: Iterable[str], game_type, game_id):
	#TODO: Merge with above once we get rid of make_launcher
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

	fields = metadata.to_launcher_fields()

	if filename_tags:
		fields[junk_section_name]['Filename Tags'] = filename_tags
	fields[junk_section_name]['Original Name'] = display_name

	fields[id_section_name] = {}
	fields[id_section_name]['Type'] = game_type
	fields[id_section_name]['Unique ID'] = game_id

	for section_name, section in fields.items():
		if not section:
			continue
		configwriter.add_section('X-Meow Launcher ' + section_name)
		section_writer = configwriter['X-Meow Launcher ' + section_name]

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
			section_writer[k.replace('_', '-').replace(' ', '-').replace('?', '').replace('/', '')] = value_as_string

	if 'X-Meow Launcher ' + image_section_name in configwriter:
		keys_to_try = ['Icon'] + main_config.use_other_images_as_icons
		for k in keys_to_try:
			if k in configwriter['X-Meow Launcher ' + image_section_name]:
				desktop_entry['Icon'] = configwriter['X-Meow Launcher ' + image_section_name][k]
				break

	ensure_exist(path)
	with open(path, 'wt', encoding='utf-8') as f:
		configwriter.write(f)

	#Set executable, but also set everything else because whatever
	os.chmod(path, 0o7777)

split_brackets = re.compile(r' (?=\()')
def make_launcher(launch_params: 'LaunchCommand', name: str, metadata: 'Metadata', id_type: str, unique_id: str):
	#TODO: Remove this, once it is no longer used - game sources should be using GameSource and whatever main class can call make_linux_desktop_for_launcher (which will have a better name) instead
	display_name = remove_filename_tags(name)
	filename_tags = find_filename_tags_at_end(name)

	#For very future use, this is where the underlying host platform is abstracted away. Right now we only run on Linux though so zzzzz
	_make_linux_desktop(launch_params, display_name, metadata, filename_tags, id_type, unique_id)
