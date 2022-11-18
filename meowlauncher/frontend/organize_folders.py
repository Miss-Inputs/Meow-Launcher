#!/usr/bin/env python3

import datetime
import os
import shutil
import sys
import time
from collections.abc import Callable, Collection
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.util.desktop_files import get_array, get_desktop, get_field
from meowlauncher.util.io_utils import sanitize_name

if TYPE_CHECKING:
	from configparser import RawConfigParser

__doc__ = """This is sort of considered separate from the main launcher generator.
Consider it to be its own kind of frontend, perhaps.
This code sucks titty balls, so it will probably all be thrown out the window and redone at some point"""

def copy_to_folder(path: Path, *dest_folder_components: str | Path) -> None:
	dest_folder = Path(*dest_folder_components)
	dest_folder.mkdir(exist_ok=True, parents=True)
	shutil.copy(path, dest_folder)

def delete_existing_output_dir() -> None:
	def rmdir_recursive(path: Path) -> None:
		for f in path.iterdir():
			if f.is_dir():
				rmdir_recursive(f)
			else:
				f.unlink()
		try:
			path.rmdir()
		except FileNotFoundError:
			pass

	if main_config.organized_output_folder.is_dir():
		for f in main_config.organized_output_folder.iterdir():
			rmdir_recursive(f)
			#Only files here, no directories

def _move_into_extra_subfolder(path: Path, desktop: 'RawConfigParser', subfolder: str, keys: str, missing_value: str | None=None) -> None:
	"""Aw jeez what the fuck? Nah what the fuck is this
	This is like the ugliest code I've ever written, or at the very least, the ugliest code in Meow Launcher"""
	subsubfolder = []
	is_array = '*' in keys
	subsubfolders: list[list[str]] = []
	temp: list[list[str]] = []

	for key in keys.split(','):
		is_key_array = False
		is_key_bool = False
		element_subsubfolders: list[str] = []
		if key.endswith('*'):
			is_key_array = True
			is_array = True
			key = key[:-1]
		elif key.endswith('?'):
			is_key_bool = True
			key = key[:-1]

		get_function: Callable[['RawConfigParser', str, str], Any]
		if is_key_array:
			get_function = get_array
			subsubfolders = []
		else:
			get_function = get_field

		if '/' in key:
			section, _, actual_key = key.partition('/')
			value = get_function(desktop, actual_key, section=section)
		else:
			value = get_function(desktop, key)
		if (not value) if is_key_array else (value is None):
			if missing_value:
				#TODO: This shouldn't apply for all keys, but then I'd have to extend the syntax
				value = missing_value
			else:
				return
		
		if is_key_bool:
			if value != 'False':
				subsubfolder.append('')
		elif is_key_array:
			element_subsubfolders += (sanitize_name(element) for element in cast(Collection[str], value))
		else:
			subsubfolder.append(sanitize_name(cast(str, value)))

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
			#FIXME: Yeah, none of that works
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
			elif subsubfolders:
				for s in subsubfolders:
					s.append(' - '.join(subsubfolder))
				temp = subsubfolders[:]
			else:
				temp.append(subsubfolder)

	if is_array:
		for subsubfolder_name in subsubfolders:
			folder_name = ' - '.join(subsubfolder_name_component for subsubfolder_name_component in subsubfolder_name if subsubfolder_name_component)
			if len(folder_name) > 200:
				folder_name = folder_name[:199] + '…'
			if folder_name:
				copy_to_folder(path, main_config.organized_output_folder, subfolder, sanitize_name(folder_name))
			else:
				copy_to_folder(path, main_config.organized_output_folder, subfolder)
	elif subsubfolder:
		folder_name = ' - '.join(subsubfolder)
		if len(folder_name) > 200:
			folder_name = folder_name[:199] + '…'
		if folder_name:
			copy_to_folder(path, main_config.organized_output_folder, subfolder, sanitize_name(folder_name))
		else:
			copy_to_folder(path, main_config.organized_output_folder, subfolder)

def _move_into_subfolders(path: Path) -> None:
	desktop = get_desktop(path)
	platform = get_field(desktop, 'Platform')
	categories = get_array(desktop, 'Categories')
	languages = get_array(desktop, 'Languages')
	year = get_field(desktop, 'Year')

	category = categories[0] if categories else 'Uncategorized'

	copy_to_folder(path, main_config.organized_output_folder, 'By platform', sanitize_name(platform))
	copy_to_folder(path, main_config.organized_output_folder, 'By category', sanitize_name(category))

	if not languages:
		copy_to_folder(path, main_config.organized_output_folder, 'By language', 'Unknown')
	for language in languages:
		copy_to_folder(path, main_config.organized_output_folder, 'By language', sanitize_name(language))

	if year:
		if len(year) > 4:
			year = year.removeprefix('?')
		copy_to_folder(path, main_config.organized_output_folder, 'By year', sanitize_name(year.replace('?', 'x')))

	copy_to_folder(path, main_config.organized_output_folder, 'By platform and category', sanitize_name(platform) + ' - ' + sanitize_name(category))
	copy_to_folder(path, main_config.organized_output_folder, 'By category and platform', sanitize_name(category) + ' - ' + sanitize_name(platform))

	_move_into_extra_subfolder(path, desktop, 'By genre', 'Genre')
	_move_into_extra_subfolder(path, desktop, 'By subgenre', 'Genre,Subgenre')
	_move_into_extra_subfolder(path, desktop, 'By developer', 'Developer')
	_move_into_extra_subfolder(path, desktop, 'By publisher', 'Publisher')
	#move_into_extra_subfolder(path, desktop, 'By platform and category', 'Platform,Categories*') #We might just only care about first category...
	_move_into_extra_subfolder(path, desktop, 'By platform and genre', 'Platform,Genre')
	_move_into_extra_subfolder(path, desktop, 'By series', 'Series')
	_move_into_extra_subfolder(path, desktop, 'By arcade system', 'Arcade-System')
	_move_into_extra_subfolder(path, desktop, 'By emulator', 'Emulator')
	_move_into_extra_subfolder(path, desktop, 'By engine', 'Engine')

	if len(languages) == 1:
		copy_to_folder(path, main_config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')

def move_into_folders() -> None:
	time_started = time.perf_counter()

	delete_existing_output_dir()
	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Removal of old organized folder finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

	time_started = time.perf_counter()

	for root, _, files in os.walk(main_config.output_folder):
		for f in files:
			path = Path(root, f)
			if path.suffix == '.desktop':
				_move_into_subfolders(path)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Folder organization finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main() -> None:
	if '--organize-folder' in sys.argv:
		time_started = time.perf_counter()

		arg_index = sys.argv.index('--organize-folder')
		key = sys.argv[arg_index + 1]
		if '--name' in sys.argv:
			name_arg_index = sys.argv.index('--name')
			name = sys.argv[name_arg_index + 1]
		else:
			name = 'By ' + key

		missing_value: str | None
		if '--missing-value' in sys.argv:
			missing_value_arg_index = sys.argv.index('--missing-value')
			missing_value = sys.argv[missing_value_arg_index + 1]
		else:
			missing_value = None

		for root, _, files in os.walk(main_config.output_folder):
			for f in files:
				path = Path(root, f)
				if path.suffix == '.desktop':
					desktop = get_desktop(path)
					_move_into_extra_subfolder(path, desktop, sanitize_name(name, safe_for_fat32=True), key, missing_value)
		if main_config.print_times:
			time_ended = time.perf_counter()
			print('Folder organization finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
		
	else:
		move_into_folders()
