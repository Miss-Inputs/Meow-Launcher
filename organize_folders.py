#!/usr/bin/env python3

import os
import shutil
import sys

import config
import launchers

#This is sort of considered separate from the main launcher generator.
#Consider it to be its own kind of frontend, perhaps.
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
	
	if os.path.isdir(config.organized_output_folder):
		for f in os.listdir(config.organized_output_folder):
			path = os.path.join(config.organized_output_folder, f)
			rmdir_recursive(path)
			#Only files here, no directories

more_subfolders = {
	#These subfolders are enabled by an optional argument, because the information is unavailable for all platforms. Otherwise it would be there
	'By genre': 'X-Genre',
	'By subgenre': ['X-Genre', 'X-Subgenre'],
	'By author': 'X-Author',
	'By platform and genre': ['X-Platform', 'X-Genre'],
	'By platform and year': ['X-Platform', 'X-Year'],
	'Is NSFW': 'X-NSFW',
}

extra_subfolders = {
#These subfolders are enabled with an optional argument because most people wouldn't have any use for them (or would they? I'm just presuming they're of interest to people like me only)
	'By emulation status': 'X-Emulation-Status',
	'By emulator used': 'X-Emulator',
	'By input method': 'X-Input-Methods',
	'By number of players': 'X-Number-of-Players',
	'By number of buttons': 'X-Number-of-Buttons',
	'By main CPU': 'X-Main-CPU',
	'By clock speed': 'X-Clock-Speed',
	'By main CPU and clock speed': ['X-Main-CPU', 'X-Clock-Speed'],
	'By screen resolution': 'X-Screen-Resolution',
	'By refresh rate': 'X-Refresh-Rate',
	'By screen resolution and refresh rate': ['X-Screen-Resolution', 'X-Refresh-Rate'],
	'By aspect ratio': 'X-Aspect-Ratio',
	'By number of screens': 'X-Number-of-Screens',
	'By screen type': 'X-Screen-Type',
	'By screen tag': 'X-Screen-Tag',
	'By MAME source file': 'X-Source-File',
	'By parent-clone family': 'X-Family',
	'By mapper': 'X-Mapper',
	'By save type': 'X-Save-Type',
	'By TV type': 'X-TV-Type',
	'By extension': 'X-Extension',
	'By cart type': 'X-Cart-Type',
	'By expansion chip': 'X-Expansion-Chip',
	'By regions': 'X-Regions',
	'By genre and input method': ['X-Genre', 'X-Input-Methods'],
	'Has header': 'X-Headered',
	'Has force feedback': 'X-Force-Feedback',
}

def move_into_extra_subfolder(path, desktop, subfolder, key):
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

	if subfolder.startswith(('Is', 'Has')):
		if value != 'False':
			copy_to_folder(path, config.organized_output_folder, subfolder)
	else:
		copy_to_folder(path, config.organized_output_folder, subfolder, value)

def move_into_subfolders(path):
	desktop = launchers.convert_desktop(path)
	platform = launchers.get_field(desktop, 'X-Platform')
	categories = launchers.get_array(desktop, 'X-Categories')
	languages = launchers.get_array(desktop, 'X-Languages')
	year = launchers.get_field(desktop, 'X-Year')

	if categories:
		category = categories[0]
	else:
		category = 'Uncategorized'

	#TODO What do we do when there's no platform...  there should be, though
	copy_to_folder(path, config.organized_output_folder, 'By platform', sanitize_name(platform))
	copy_to_folder(path, config.organized_output_folder, 'By category', sanitize_name(category))
	if not languages:
		copy_to_folder(path, config.organized_output_folder, 'By language', 'Unknown')
	for language in languages:
		copy_to_folder(path, config.organized_output_folder, 'By language', sanitize_name(language))
	if year:
		copy_to_folder(path, config.organized_output_folder, 'By year', sanitize_name(year.replace('x', '?')))
			
	copy_to_folder(path, config.organized_output_folder, 'By platform and category', sanitize_name(platform) + ' - ' + sanitize_name(category))

	if '--more-folders' in sys.argv:
		for k, v in more_subfolders.items():
			move_into_extra_subfolder(path, desktop, k, v)

	if '--extra-folders' in sys.argv:
		if len(languages) == 1:
			copy_to_folder(path, config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')
				
		filename_tags = launchers.get_array(desktop, 'X-Filename-Tags')
		for tag in filename_tags:
			copy_to_folder(path, config.organized_output_folder, 'By filename tag', sanitize_name(tag))
					
		for k, v in extra_subfolders.items():
			move_into_extra_subfolder(path, desktop, k, v)

def move_into_folders():
	delete_existing_output_dir()
	
	for root, _, files in os.walk(config.output_folder):
		for f in files:
			if f.endswith('.desktop'):
				path = os.path.join(root, f)
				copy_to_folder(path, config.organized_output_folder, 'Ungrouped')
			
				move_into_subfolders(path)

if __name__ == '__main__':
	move_into_folders()
