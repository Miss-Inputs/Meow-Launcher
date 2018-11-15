#!/usr/bin/env python3

import os
import shutil
import sys
import time
import datetime

from config import main_config, command_line_flags
import launchers

#This is sort of considered separate from the main launcher generator.
#Consider it to be its own kind of frontend, perhaps.
#This code sucks titty balls

def copy_to_folder(path, *dest_folder_components):
	dest_folder = os.path.join(*dest_folder_components)
	os.makedirs(dest_folder, exist_ok=True)
	shutil.copy(path, dest_folder)

def sanitize_name(s):
	#These must never be filenames or folder names!  Badbadbad!
	if not s:
		return 'Nothing'

	s = s.replace('/', '-')
	s = s.replace('\x00', ' ')
	if s == '.':
		return 'dot'
	if s == '..':
		return 'dotdot'
	return s

def delete_existing_output_dir():
	def rmdir_recursive(path):
		for f in os.listdir(path):
			file_path = os.path.join(path, f)
			if os.path.isdir(file_path):
				rmdir_recursive(file_path)
			else:
				os.unlink(file_path)
		try:
			os.rmdir(path)
		except FileNotFoundError:
			pass

	if os.path.isdir(main_config.organized_output_folder):
		for f in os.listdir(main_config.organized_output_folder):
			path = os.path.join(main_config.organized_output_folder, f)
			rmdir_recursive(path)
			#Only files here, no directories

extra_subfolders = {
	#These subfolders are enabled with an optional argument because most people wouldn't have any use for them (or would they? I'm just presuming they're of interest to people like me only)
	'By emulator used': ('Emulator', False),
	'By number of players': ('Number-of-Players', False),
	'By mapper': ('Mapper', False),
	'By save type': ('Save-Type', False),
	'By extension': ('Extension', False),
	'By media type': ('Media-Type', False),

	'By main CPU': ('Main-CPU', False),
	'By main CPU and clock speed': (['Main-CPU', 'Clock-Speed'], False),
	'By number of screens': ('Number-of-Screens', False),
	'By screen type': ('Screen-Type', False),


	'By MAME emulation status': ('MAME-Emulation-Status', False),
	'Has MAME software': ('MAME-Software-Name', True),
	'By MAME source file': ('Source-File', False),

	#Relevant for MAME machines only
	'By parent-clone family': ('Family', False),
	'By arcade system': ('Arcade-System', False),
	'Is mechanical': ('Is-Mechanical', True),
	'Has unemulated features': ('MAME-Unemulated-Features', True),
	'Dispenses tickets': ('Dispenses-Tickets', True),
	'No ROMs required': ('Romless', True),

	'Has icon': ('Icon', True),
	'Has force feedback': ('Force-Feedback', True),
	'Has RTC': ('Has-RTC', True),
	'Has product code': ('Product-Code', True),
	'Has notes': ('Notes', True),
}

def move_into_extra_subfolder(path, desktop, subfolder, key, is_boolean):
	if isinstance(key, list):
		values = []
		for component in key:
			component_value = launchers.get_field(desktop, component)
			if not component_value:
				return
			values.append(sanitize_name(component_value))
		value = ' - '.join(values)
	else:
		field_value = launchers.get_field(desktop, key)
		if not field_value:
			return
		value = sanitize_name(field_value)

	if is_boolean:
		if value != 'False':
			copy_to_folder(path, main_config.organized_output_folder, subfolder)
	else:
		copy_to_folder(path, main_config.organized_output_folder, subfolder, value)

def move_into_subfolders(path):
	desktop = launchers.get_desktop(path)
	platform = launchers.get_field(desktop, 'Platform')
	categories = launchers.get_array(desktop, 'Categories')
	languages = launchers.get_array(desktop, 'Languages')
	input_methods = launchers.get_array(desktop, 'Input-Methods')
	year = launchers.get_field(desktop, 'Year')

	if categories:
		category = categories[0]
	else:
		category = 'Uncategorized'

	copy_to_folder(path, main_config.organized_output_folder, 'By platform', sanitize_name(platform))
	copy_to_folder(path, main_config.organized_output_folder, 'By category', sanitize_name(category))

	if not languages:
		copy_to_folder(path, main_config.organized_output_folder, 'By language', 'Unknown')
	for language in languages:
		copy_to_folder(path, main_config.organized_output_folder, 'By language', sanitize_name(language))

	if not input_methods:
		copy_to_folder(path, main_config.organized_output_folder, 'By input method', 'Unknown')
	else:
		for input_method in input_methods:
			copy_to_folder(path, main_config.organized_output_folder, 'By input method', sanitize_name(input_method))

	if year:
		copy_to_folder(path, main_config.organized_output_folder, 'By year', sanitize_name(year.replace('x', '?')))

	copy_to_folder(path, main_config.organized_output_folder, 'By platform and category', sanitize_name(platform) + ' - ' + sanitize_name(category))

	move_into_extra_subfolder(path, desktop, 'By genre', 'Genre', False)
	move_into_extra_subfolder(path, desktop, 'By subgenre', ['Genre', 'Subgenre'], False)
	move_into_extra_subfolder(path, desktop, 'By developer', 'Developer', False)
	move_into_extra_subfolder(path, desktop, 'By publisher', 'Publisher', False)
	move_into_extra_subfolder(path, desktop, 'By platform and genre', ['Platform', 'Genre'], False)
	move_into_extra_subfolder(path, desktop, 'By platform and year', ['Platform', 'Year'], False)
	move_into_extra_subfolder(path, desktop, 'Is NSFW', 'NSFW', True)

	if '--extra-folders' in sys.argv:
		if len(languages) == 1:
			copy_to_folder(path, main_config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')

		filename_tags = launchers.get_array(desktop, 'Filename-Tags')
		for tag in filename_tags:
			copy_to_folder(path, main_config.organized_output_folder, 'By filename tag', sanitize_name(tag))

		for k, v in extra_subfolders.items():
			move_into_extra_subfolder(path, desktop, k, *v)

def move_into_folders():
	time_started = time.perf_counter()

	delete_existing_output_dir()
	if command_line_flags['print_times']:
		time_ended = time.perf_counter()
		print('Removal of old organized folder finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

	time_started = time.perf_counter()

	for root, _, files in os.walk(main_config.output_folder):
		for f in files:
			if f.endswith('.desktop'):
				path = os.path.join(root, f)

				move_into_subfolders(path)

	if command_line_flags['print_times']:
		time_ended = time.perf_counter()
		print('Folder organization finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	move_into_folders()
