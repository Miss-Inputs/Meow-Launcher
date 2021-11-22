import configparser
from collections.abc import Collection
from enum import Enum, Flag
from typing import TYPE_CHECKING, Any

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config.main_config import main_config
from meowlauncher.games.mame_common.machine import Machine
from meowlauncher.games.mame_common.software_list import Software, SoftwareList
from meowlauncher.util.io_utils import ensure_exist, pick_new_filename
from meowlauncher.util.utils import (clean_string, find_filename_tags_at_end,
                                     remove_filename_tags)

if TYPE_CHECKING:
	from meowlauncher.launch_command import LaunchCommand
	from meowlauncher.launcher import Launcher
	from meowlauncher.metadata import Metadata

section_prefix = 'X-Meow Launcher '
metadata_section_name = 'Metadata'
id_section_name = 'ID'
junk_section_name = 'Junk'
image_section_name = 'Images'

def _write_field(desktop: configparser.ConfigParser, section_name: str, key_name: str, value: Any):
	value_as_string: str
	
	if isinstance(value, Collection) and not isinstance(value, str):
		if not value:
			return
		value_as_string = ';'.join('None' if item is None else item.name if isinstance(item, Enum) else str(item) for item in value)
	elif isinstance(value, Enum):
		if value.name:
			value_as_string = value.name
		elif isinstance(value, Flag):
			value_as_string = str(value).replace('|', ';')
			value_as_string = value_as_string[value_as_string.find('.') + 1:]
	elif isinstance(value, Software):
		value_as_string = f'{value.name} ({value.description})'
	elif isinstance(value, SoftwareList):
		value_as_string = f'{value.name} ({value.description})'
	elif isinstance(value, Machine):
		value_as_string = f'{value.basename} ({value.name})'
	else:
		value_as_string = str(value)

	cleaned_key_name = key_name.replace('_', '-').replace(' ', '-').replace('?', '').replace('/', '')
	value_as_string = clean_string(value_as_string.strip(), True)

	section_writer = desktop[section_prefix + section_name]
	if '\n' in value_as_string or '\r' in value_as_string:
		for i, line in enumerate(value_as_string.splitlines()):
			section_writer[f'{cleaned_key_name}-Line-{i}'] = line
	else:
		section_writer[cleaned_key_name] = value_as_string

def make_linux_desktop_for_launcher(launcher: 'Launcher'):
	name = launcher.game.name

	filename_tags = find_filename_tags_at_end(name)
	name = remove_filename_tags(name)

	if launcher.runner.is_emulated:
		launcher.game.metadata.emulator_name = launcher.runner.name

	#TODO: Merge with make_linux_desktop once we get rid of make_launcher
	_make_linux_desktop(launcher.command, name, launcher.game.metadata, filename_tags, launcher.game_type, launcher.game_id)

def _make_linux_desktop(command: 'LaunchCommand', display_name: str, metadata: 'Metadata', filename_tags: Collection[str], game_type: str, game_id: str):
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
	desktop_entry['Exec'] = command.make_linux_command_string()
	if command.working_directory:
		desktop_entry['Path'] = command.working_directory

	fields = metadata.to_launcher_fields()

	if filename_tags:
		fields[junk_section_name]['Filename Tags'] = filename_tags
	fields[junk_section_name]['Original Name'] = display_name #Will be most likely touched by disambiguate later

	fields[id_section_name] = {}
	fields[id_section_name]['Type'] = game_type
	fields[id_section_name]['Unique ID'] = game_id

	for section_name, section in fields.items():
		if not section:
			continue
		configwriter.add_section(section_prefix + section_name)

		for k, v in section.items():
			if v is None:
				continue
			if have_pillow:
				if isinstance(v, Image.Image):
					this_image_folder = main_config.image_folder.joinpath(k)
					this_image_folder.mkdir(exist_ok=True, parents=True)
					image_path = this_image_folder.joinpath(filename + '.png')
					v.save(image_path, 'png')
					#v = image_path
					_write_field(configwriter, section_name, k, image_path)
					continue

			_write_field(configwriter, section_name, k, v)

	if section_prefix + image_section_name in configwriter:
		keys_to_try = ('Icon', ) + main_config.use_other_images_as_icons
		for k in keys_to_try:
			if k in configwriter[section_prefix + image_section_name]:
				desktop_entry['Icon'] = configwriter[section_prefix + image_section_name][k]
				break

	ensure_exist(path)
	with path.open('wt', encoding='utf-8') as f:
		configwriter.write(f)

	#Set executable, but also set everything else because whatever, partially because I can't remember what I would need to do to get the original mode and | it with executable
	path.chmod(0o7777)

def make_launcher(launch_params: 'LaunchCommand', name: str, metadata: 'Metadata', id_type: str, unique_id: str):
	#TODO: Remove this, once it is no longer used - game sources should be using GameSource and whatever main class can call make_linux_desktop_for_launcher (which will have a better name) instead
	display_name = remove_filename_tags(name)
	filename_tags = find_filename_tags_at_end(name)

	#For very future use, this is where the underlying host platform is abstracted away. Right now we only run on Linux though so zzzzz
	_make_linux_desktop(launch_params, display_name, metadata, filename_tags, id_type, unique_id)
