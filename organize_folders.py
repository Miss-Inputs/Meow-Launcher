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
	if os.path.isdir(config.organized_output_folder):
		for f in os.listdir(config.organized_output_folder):
			path = os.path.join(config.organized_output_folder, f)
			if os.path.isdir(path):
				shutil.rmtree(path, ignore_errors=True)
			else:
				os.unlink(path)

extra_subfolders = {
	'By genre': 'X-Genre',
	'By subgenre': ['X-Genre', 'X-Subgenre'],
	'By author': 'X-Author',
	'By emulation status': 'X-Emulation-Status',
	'Is NSFW': 'X-NSFW',
	'By emulator used': 'X-Emulator',
	'By input method': 'X-Input-Method',
	'By main CPU': 'X-Main-CPU',
	'By MAME source file': 'X-Source-File',
	'By parent-clone family': 'X-Family',
	'By mapper': 'X-Mapper',
	'By save type': 'X-Save-Type',
	'By TV type': 'X-TV-Type',
	'By extension': 'X-Extension',
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

	if '--extra-folders' in sys.argv:
		if len(languages) == 1:
			copy_to_folder(path, config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')
				
		filename_tags = launchers.get_array(desktop, 'X-Filename-Tags')
		for tag in filename_tags:
			copy_to_folder(path, config.organized_output_folder, 'By filename tag', sanitize_name(tag))
					
		for k, v in extra_subfolders.items():
			move_into_extra_subfolder(path, desktop, k, v)

		#ext = launchers.get_field(desktop, 'X-Extension')	
		#if ext:
		#	copy_to_folder(path, config.organized_output_folder, 'By extension', sanitize_name(ext))
								
		#Wouldn't be in this extra part if I could generate these for every platform
		#genre = launchers.get_field(desktop, 'X-Genre')
		#subgenre = launchers.get_field(desktop, 'X-Subgenre')
		#author = launchers.get_field(desktop, 'X-Author')
		#emulation_status = launchers.get_field(desktop, 'X-Emulation-Status')
		#is_nsfw = launchers.get_field(desktop, "X-NSFW") == 'True'
		#clone_of = launchers.get_field(desktop, "X-clone-of")
		#emulator = launchers.get_field(desktop, "X-Emulator")

		#if genre:
		#	copy_to_folder(path, config.organized_output_folder, 'By genre', sanitize_name(genre))
		#if genre and subgenre:
		#	copy_to_folder(path, config.organized_output_folder, 'By subgenre', sanitize_name(genre) + ' - ' + sanitize_name(subgenre))
		#if author:
		#	copy_to_folder(path, config.organized_output_folder, 'By author', sanitize_name(author))
		#if emulation_status:
		#	copy_to_folder(path, config.organized_output_folder, 'By emulation status', sanitize_name(emulation_status))
		#if is_nsfw:
		#	copy_to_folder(path, config.organized_output_folder, 'NSFW')
		#if clone_of:
		#	copy_to_folder(path, config.organized_output_folder, 'Clone of', sanitize_name(clone_of))
		#if emulator:
		#	copy_to_folder(path, config.organized_output_folder, 'By emulator used', sanitize_name(emulator))

		#Would still be in this extra part
		#main_input = launchers.get_field(desktop, 'X-Input-Method')
		#main_cpu = launchers.get_field(desktop, 'X-Main-CPU')
		#source_file = launchers.get_field(desktop, 'X-Source-File')
		#family = launchers.get_field(desktop, 'X-Family')
					
		#if main_input:
		#	copy_to_folder(path, config.organized_output_folder, 'By input method', sanitize_name(main_input))
		#if main_cpu:
		#	copy_to_folder(path, config.organized_output_folder, 'By main CPU', sanitize_name(main_cpu))
		#if source_file:
		#	copy_to_folder(path, config.organized_output_folder, 'By MAME source file', sanitize_name(source_file))
		#if family:
		#	copy_to_folder(path, config.organized_output_folder, 'By parent-clone family', sanitize_name(family))

def move_into_folders():
	delete_existing_output_dir()
	
	for root, _, files in os.walk(config.output_folder):
		for f in files:
			if f.endswith('.desktop'):
				path = os.path.join(root, f)
				copy_to_folder(path, config.organized_output_folder, 'Ungrouped')
			
				move_into_subfolders(path)
