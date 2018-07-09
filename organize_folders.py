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

def move_into_folders():
	delete_existing_output_dir()
	
	for root, dirs, files in os.walk(config.output_folder):
		for f in files:
			if f.endswith('.desktop'):
				path = os.path.join(root, f)
				copy_to_folder(path, config.organized_output_folder, 'Ungrouped')
			
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
			
				if '--extra-folders' in sys.argv:
					copy_to_folder(path, config.organized_output_folder, 'By platform and category', sanitize_name(platform) + ' - ' + sanitize_name(category))
					if len(languages) == 1 and languages[0] != 'English':
						copy_to_folder(path, config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')
				
					filename_tags = launchers.get_array(desktop, 'X-Filename-Tags')
					ext = launchers.get_field(desktop, 'X-Extension')
					for tag in filename_tags:
						copy_to_folder(path, config.organized_output_folder, 'By filename tag', sanitize_name(tag))
	
					if ext:
						copy_to_folder(path, config.organized_output_folder, 'By extension', sanitize_name(ext))
								
					#Wouldn't be in this extra part if I could generate these for more than
					#just arcade games
					genre = launchers.get_field(desktop, 'X-Genre')
					subgenre = launchers.get_field(desktop, 'X-Subgenre')
					author = launchers.get_field(desktop, 'X-Author')
					emulation_status = launchers.get_field(desktop, 'X-Emulation-Status')

					if genre:
						copy_to_folder(path, config.organized_output_folder, 'By genre', sanitize_name(genre))
					if genre and subgenre:
						copy_to_folder(path, config.organized_output_folder, 'By subgenre', sanitize_name(genre) + ' - ' + sanitize_name(subgenre))
					if author:
						copy_to_folder(path, config.organized_output_folder, 'By author', sanitize_name(author))
					if emulation_status:
						copy_to_folder(path, config.organized_output_folder, 'By emulation status', sanitize_name(emulation_status))
					
					#Would still be in this extra part
					main_input = launchers.get_field(desktop, 'X-Main-Input')
					main_cpu = launchers.get_field(desktop, 'X-Main-CPU')
					source_file = launchers.get_field(desktop, 'X-Source-File')
					family = launchers.get_field(desktop, 'X-Family')
					
					if main_input:
						copy_to_folder(path, config.organized_output_folder, 'By input method', sanitize_name(main_input))
					if main_cpu:
						copy_to_folder(path, config.organized_output_folder, 'By main CPU', sanitize_name(main_cpu))
					if source_file:
						copy_to_folder(path, config.organized_output_folder, 'By MAME source file', sanitize_name(source_file))
					if family:
						copy_to_folder(path, config.organized_output_folder, 'By parent-clone family', sanitize_name(family))
				

