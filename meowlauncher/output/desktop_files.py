import itertools
from collections.abc import Collection
from enum import Enum, Flag
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.config.main_config import main_config
from meowlauncher.util.io_utils import (ensure_exist, ensure_unique_path,
                                        sanitize_name)
from meowlauncher.util.utils import (NoNonsenseConfigParser, clean_string,
                                     find_tags)
from meowlauncher.version import __version__

if TYPE_CHECKING:
	import configparser

	from meowlauncher.info import GameInfo
	from meowlauncher.launch_command import LaunchCommand
	from meowlauncher.launcher import Launcher

id_section_name = 'ID'
section_prefix = 'X-Meow Launcher '
info_section_name = 'Game Info'
junk_section_name = 'Junk'
image_section_name = 'Images'

def _write_field(desktop: 'configparser.RawConfigParser', section_name: str, key_name: str, value: Any) -> None:
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

def make_linux_desktop_for_launcher(launcher: 'Launcher', game_type: str) -> None:
	name = launcher.game.name

	name, filename_tags = find_tags(name)
	
	if launcher.runner.is_emulated:
		launcher.game.info.emulator_name = launcher.runner.name

	#TODO: Merge with make_linux_desktop once we get rid of make_launcher
	_make_linux_desktop(launcher.command, name, launcher.game.info, filename_tags, game_type, launcher.game_id)

def _make_linux_desktop(command: 'LaunchCommand', display_name: str, game_info: 'GameInfo', filename_tags: Collection[str], game_type: str, game_id: str) -> None:
	path = ensure_unique_path(Path(main_config.output_folder, sanitize_name(display_name, no_janky_chars=True) + '.desktop'))

	configwriter = NoNonsenseConfigParser()

	configwriter.add_section('Desktop Entry')
	desktop_entry = configwriter['Desktop Entry']

	#Necessary for this thing to even be recognized
	desktop_entry['Type'] = 'Application'
	desktop_entry['Encoding'] = 'UTF-8'

	desktop_entry['Name'] = clean_string(display_name)
	desktop_entry['Exec'] = command.make_linux_command_string()
	if command.working_directory:
		desktop_entry['Path'] = command.working_directory.as_posix()

	fields = game_info.to_launcher_fields()

	if filename_tags:
		fields[junk_section_name]['Filename Tags'] = filename_tags
	fields[junk_section_name]['Original Name'] = display_name #Will be most likely touched by disambiguate later

	fields[id_section_name] = {'Type': game_type, 'Unique ID': game_id, 'Version': __version__}
	
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
					image_path = this_image_folder.joinpath(path.stem + '.png')
					v.save(image_path, 'png', optimize=True, compress_level=9)
					#v = image_path
					_write_field(configwriter, section_name, k, image_path)
					continue

			_write_field(configwriter, section_name, k, v)

	if section_prefix + image_section_name in configwriter:
		image_section = configwriter[section_prefix + image_section_name]
		desktop_entry_icon = next((image_section[k] for k in itertools.chain({'Icon'}, main_config.other_images_to_use_as_icons) if k in image_section), None)
		if desktop_entry_icon:
			desktop_entry['Icon'] = desktop_entry_icon
		
	ensure_exist(path)
	with path.open('wt', encoding='utf-8') as f:
		configwriter.write(f)

	#Set executable, but also set everything else because whatever, partially because I can't remember what I would need to do to get the original mode and | it with executable
	path.chmod(0o7777)

def make_launcher(launch_params: 'LaunchCommand', name: str, game_info: 'GameInfo', id_type: str, unique_id: str) -> None:
	#TODO: Remove this, once it is no longer used - game sources should be using GameSource and whatever main class can call make_linux_desktop_for_launcher (which will have a better name) instead
	display_name, filename_tags = find_tags(name)

	#For very future use, this is where the underlying host platform is abstracted away. Right now we only run on Linux though so zzzzz
	_make_linux_desktop(launch_params, display_name, game_info, filename_tags, id_type, unique_id)
