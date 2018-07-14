import os
import shutil
import sys

import config
import launchers
import mame_machines
import system_info

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

lookup_system_cpu_cache = {}
def lookup_system_cpu(driver_name):
	if driver_name in lookup_system_cpu_cache:
		return lookup_system_cpu_cache[driver_name]

	xml = mame_machines.get_mame_xml(driver_name)
	if not xml:
		lookup_system_cpu_cache[driver_name] = None
		return None
	machine = xml.find('machine')
	if not machine:
		lookup_system_cpu_cache[driver_name] = None
		return None

	main_cpu = mame_machines.find_main_cpu(machine)
	if main_cpu is not None: #"if main_cpu: doesn't work. Frig! Why not! Wanker! Sodding bollocks!
		main_cpu_name = main_cpu.attrib['name']
		lookup_system_cpu_cache[driver_name] = main_cpu_name
		return main_cpu_name

	return None

platform_cpu_list = {
	#Usually just look up system_info.systems, but this is here where they aren't in systems or there isn't a MAME driver so we can't get the CPU from there or where MAME gets it wrong because the CPU we want to return isn't considered the main CPU
	"3DS": "ARM11",
	"32X": "Hitachi SH-2",
	"DS": 'ARM9',
	"FDS": lookup_system_cpu('fds'),
	"Game Boy Color": lookup_system_cpu('gbcolor'),
	"Mac": lookup_system_cpu('macqd700'), 
	#Correct for now, since we aren't emulating PPC games yet, nor are we falling back to earlier systems in case of really old games
	"Mega CD": lookup_system_cpu('megacd'),
	#For this purpose it's correct but it technically isn't: This is returning the CPU from the Megadrive instead of the actual Mega CD's CPU, but they're both 68000 so it's fine to just get the name
	"PSP": "Allegrex",
	"Wii": "IBM PowerPC 603", 
}

def get_cpu_for_platform(platform):
	#I look up things from MAME here (even when MAME doesn't really support the system and it's just a skeleton driver, as long as it knows the CPU) so the wording and naming and stuff is consistent with arcade games, which already have their CPU known
	#TODO: This should be done when the launcher is generated (add X-Main-CPU), not when it's being sorted by this frontend specifically

	if platform in platform_cpu_list:
		return platform_cpu_list[platform]

	for system in system_info.systems:
		if platform == system.name:
			mame_driver = system.mame_driver
			if mame_driver:
				return lookup_system_cpu(mame_driver)

	return None

def move_into_folders():
	delete_existing_output_dir()
	
	for root, _, files in os.walk(config.output_folder):
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
					if len(languages) == 1:
						copy_to_folder(path, config.organized_output_folder, 'By language', sanitize_name(languages[0]) + ' only')
				
					filename_tags = launchers.get_array(desktop, 'X-Filename-Tags')
					ext = launchers.get_field(desktop, 'X-Extension')
					for tag in filename_tags:
						copy_to_folder(path, config.organized_output_folder, 'By filename tag', sanitize_name(tag))
	
					if ext:
						copy_to_folder(path, config.organized_output_folder, 'By extension', sanitize_name(ext))
								
					#Wouldn't be in this extra part if I could generate these for every platform
					genre = launchers.get_field(desktop, 'X-Genre')
					subgenre = launchers.get_field(desktop, 'X-Subgenre')
					author = launchers.get_field(desktop, 'X-Author')
					emulation_status = launchers.get_field(desktop, 'X-Emulation-Status')
					is_nsfw = launchers.get_field(desktop, "X-NSFW") == 'True'
					clone_of = launchers.get_field(desktop, "X-clone-of")
					emulator = launchers.get_field(desktop, "X-Emulator")

					if genre:
						copy_to_folder(path, config.organized_output_folder, 'By genre', sanitize_name(genre))
					if genre and subgenre:
						copy_to_folder(path, config.organized_output_folder, 'By subgenre', sanitize_name(genre) + ' - ' + sanitize_name(subgenre))
					if author:
						copy_to_folder(path, config.organized_output_folder, 'By author', sanitize_name(author))
					if emulation_status:
						copy_to_folder(path, config.organized_output_folder, 'By emulation status', sanitize_name(emulation_status))
					if is_nsfw:
						copy_to_folder(path, config.organized_output_folder, 'NSFW')
					if clone_of:
						copy_to_folder(path, config.organized_output_folder, 'Clone of', sanitize_name(clone_of))
					if emulator:
						copy_to_folder(path, config.organized_output_folder, 'By emulator used', sanitize_name(emulator))

					#Would still be in this extra part
					main_input = launchers.get_field(desktop, 'X-Main-Input')
					main_cpu = launchers.get_field(desktop, 'X-Main-CPU')
					source_file = launchers.get_field(desktop, 'X-Source-File')
					family = launchers.get_field(desktop, 'X-Family')
					
					if main_input:
						copy_to_folder(path, config.organized_output_folder, 'By input method', sanitize_name(main_input))
					if main_cpu:
						copy_to_folder(path, config.organized_output_folder, 'By main CPU', sanitize_name(main_cpu))
					else:
						cpu = get_cpu_for_platform(platform)
						if cpu:
							copy_to_folder(path, config.organized_output_folder, 'By main CPU', sanitize_name(cpu))
					if source_file:
						copy_to_folder(path, config.organized_output_folder, 'By MAME source file', sanitize_name(source_file))
					if family:
						copy_to_folder(path, config.organized_output_folder, 'By parent-clone family', sanitize_name(family))
	