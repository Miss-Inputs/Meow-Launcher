#!/usr/bin/env python3

import datetime
import os
import shutil
import sys
import time

import launchers
from config import main_config
from io_utils import sanitize_name

#This is sort of considered separate from the main launcher generator.
#Consider it to be its own kind of frontend, perhaps.
#This code sucks titty balls

def copy_to_folder(path, *dest_folder_components):
	dest_folder = os.path.join(*dest_folder_components)
	os.makedirs(dest_folder, exist_ok=True)
	shutil.copy(path, dest_folder)

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

def move_into_extra_subfolder(path, desktop, subfolder, keys):
	subsubfolder = []
	is_array = '*' in keys
	subsubfolders = []
	temp = []

	for key in keys.split(','):
		is_key_array = False
		is_key_bool = False
		element_subsubfolders = []
		if key.endswith('*'):
			is_key_array = True
			is_array = True
			key = key[:-1]
		elif key.endswith('?'):
			is_key_bool = True
			key = key[:-1]

		if is_key_array:
			get_function = launchers.get_array
			subsubfolders = []
		else:
			get_function = launchers.get_field

		if '/' in key:
			section, _, actual_key = key.partition('/')
			value = get_function(desktop, actual_key, section=section)
		else:
			value = get_function(desktop, key)
		if (not value) if is_key_array else (value is None):
			#Maybe a "allow missing values" thing would be a good idea like I used to have as that parameter
			return
		
		if is_key_bool:
			if value != 'False':
				subsubfolder.append('')
		else:
			if is_key_array:
				for element in value:
					element_subsubfolders.append(sanitize_name(element))
			else:
				subsubfolder.append(sanitize_name(value))
		if is_array:
			#I confused myself while writing this code, I hope it continues to just work and I don't have to touch it again
			#Okay, let's just note what I expect it to do, and then I can take a look at it later when I'm feeling more mentally sharp
			#- If there was a * anywhere, we're in array mode
			#- If this is an array key, make subfolders for each element in the array
			#	- i.e. if this is the first key: "Value 1", "Value 2"
			#	- if this is a key after a non-array key: "Blah - Value 1", "Blah - Value 2"
			#	- if this is a key after another array key: "Blah 1 - Value 1", "Blah 1 - Value 2", "Blah 2 - Value 1", "Blah 2 - Value 2"
			#- If it's not an array key but it's after an array key, add to each subfolder that would have been there
			#	- "Blah 1", "Blah 2" -> "Blah 1 - Value", "Blah 2 - Value"
			#- If any value out of the specified keys is missing, don't copy it to any folders, don't create a folder just called "Blah"
			#I feel like I'm overthinking this
			if is_key_array:
				if temp:
					for element_subsubfolder in element_subsubfolders:
						for t in temp[:]:
							for v in t:
								subsubfolders.append([v, element_subsubfolder])
				else:
					for element_subsubfolder in element_subsubfolders:
						subsubfolders.append([element_subsubfolder])
					temp = subsubfolders[:]
			else:
				if subsubfolders:
					for s in subsubfolders:
						s.append(' - '.join(subsubfolder))
					temp = subsubfolders[:]
				else:
					temp.append(subsubfolder)

	if is_array:
		for subsubfolder_name in subsubfolders:
			copy_to_folder(path, main_config.organized_output_folder, subfolder, ' - '.join([subsubfolder_name_component for subsubfolder_name_component in subsubfolder_name if subsubfolder_name_component]))
	else:
		if subsubfolder:
			copy_to_folder(path, main_config.organized_output_folder, subfolder, ' - '.join(subsubfolder))

def move_into_subfolders(path):
	desktop = launchers.get_desktop(path)
	platform = launchers.get_field(desktop, 'Platform')
	categories = launchers.get_array(desktop, 'Categories')
	languages = launchers.get_array(desktop, 'Languages')
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

	if year:
		copy_to_folder(path, main_config.organized_output_folder, 'By year', sanitize_name(year.replace('x', '?')))

	copy_to_folder(path, main_config.organized_output_folder, 'By platform and category', sanitize_name(platform) + ' - ' + sanitize_name(category))
	copy_to_folder(path, main_config.organized_output_folder, 'By category and platform', sanitize_name(category) + ' - ' + sanitize_name(platform))

	move_into_extra_subfolder(path, desktop, 'By genre', 'Genre')
	move_into_extra_subfolder(path, desktop, 'By subgenre', 'Genre,Subgenre')
	move_into_extra_subfolder(path, desktop, 'By developer', 'Developer')
	move_into_extra_subfolder(path, desktop, 'By publisher', 'Publisher')
	#move_into_extra_subfolder(path, desktop, 'By platform and category', 'Platform,Categories*') #We might just only care about first category...
	move_into_extra_subfolder(path, desktop, 'By platform and genre', 'Platform,Genre')
	move_into_extra_subfolder(path, desktop, 'Is NSFW', 'NSFW?')
	move_into_extra_subfolder(path, desktop, 'By series', 'Series')

	if len(languages) == 1:
		copy_to_folder(path, main_config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')

def move_into_folders():
	time_started = time.perf_counter()

	delete_existing_output_dir()
	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Removal of old organized folder finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

	time_started = time.perf_counter()

	for root, _, files in os.walk(main_config.output_folder):
		for f in files:
			if f.endswith('.desktop'):
				path = os.path.join(root, f)

				move_into_subfolders(path)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Folder organization finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main():
	if '--organize-folder' in sys.argv:
		time_started = time.perf_counter()

		arg_index = sys.argv.index('--organize-folder')
		key = sys.argv[arg_index + 1]
		if '--name' in sys.argv:
			name_arg_index = sys.argv.index('--name')
			name = sys.argv[name_arg_index + 1]
		else:
			name = 'By ' + key
		for root, _, files in os.walk(main_config.output_folder):
			for f in files:
				if f.endswith('.desktop'):
					path = os.path.join(root, f)
					desktop = launchers.get_desktop(path)
					move_into_extra_subfolder(path, desktop, sanitize_name(name, supersafe=True), key)
		if main_config.print_times:
			time_ended = time.perf_counter()
			print('Folder organization finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
		
	else:
		move_into_folders()

if __name__ == '__main__':
	main()
