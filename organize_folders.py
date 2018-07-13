import os
import shutil
import sys

import config
import launchers
import mame_machines

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

def lookup_system_cpu(driver_name):
	xml = mame_machines.get_mame_xml(driver_name)
	if not xml:
		return None
	machine = xml.find('machine')
	if not machine:
		return None

	main_cpu = mame_machines.find_main_cpu(machine)
	if main_cpu is not None: #"if main_cpu: doesn't work. Frig! Why not! Wanker! Sodding bollocks!
		return main_cpu.attrib['name']

	return None

console_cpus = {
	#TODO: Ideally, we'd put this in config.py along with the emulators, but I guess it's not really important
	#I look up things from MAME here (even when MAME doesn't really support the system and it's just a skeleton driver, as long as it knows the CPU) so the wording and naming and stuff is consistent with arcade games, which already have their CPU known
	"3DS": "ARM11",
	"32X": "Hitachi SH-2",
	"Amstrad GX4000": lookup_system_cpu('gx4000'),
	"APF-MP1000": lookup_system_cpu('apfm1000'),
	"Arcadia 2001": lookup_system_cpu('apfm1000'),
	"Astrocade": lookup_system_cpu('astrocde'),
	"Atari 8-bit": lookup_system_cpu('a800'),
	"Atari 2600": lookup_system_cpu('a2600'),
	"Atari 5200": lookup_system_cpu('a5200'),
	"Atari 7800": lookup_system_cpu('a7800'),
	"C64": lookup_system_cpu('c64'),
	"Casio PV-1000": lookup_system_cpu('pv1000'),
	"Casio PV-2000": lookup_system_cpu('pv2000'),
	"CD-i": lookup_system_cpu('cdimono1'),
	"Channel F": lookup_system_cpu('channelf'),
	"Colecovision": lookup_system_cpu('coleco'),
	"DS": 'ARM9',
	"Entex Adventure Vision": lookup_system_cpu('advision'),
	"Epoch Game Pocket Computer": lookup_system_cpu('gamepock'),
	"FDS": lookup_system_cpu('fds'),
	"Gamate": lookup_system_cpu('gamate'),
	"Game Boy": lookup_system_cpu('gameboy'),
	"Game Boy Color": lookup_system_cpu('gbcolor'),
	"GameCube": lookup_system_cpu('gcjp'),
	"Game Gear": lookup_system_cpu('gamegear'),
	"GBA": lookup_system_cpu('gba'),
	"Intellivision": lookup_system_cpu('intv'),
	"Lynx": lookup_system_cpu('lynx'),
	"Mac": lookup_system_cpu('macqd700'), #Correct for now, since we aren't emulating PPC games yet, nor are we falling back to earlier systems in case of really old games
	"Master System": lookup_system_cpu('sms'),
	"Mega CD": lookup_system_cpu('megacd'),
	"Mega Drive": lookup_system_cpu('megadriv'),
	"Mega Duck": lookup_system_cpu('megaduck'),
	"MSX": lookup_system_cpu('fsa1wsx'),
	"MSX2": lookup_system_cpu('fsa1wsx'),
	"N64": lookup_system_cpu('n64'),
	"Neo Geo CD": lookup_system_cpu('neocdz'),
	"Neo Geo Pocket": lookup_system_cpu('ngpc'),
	"NES": lookup_system_cpu('nes'),
	"PC Engine": lookup_system_cpu('pce'),
	"PC Engine CD": lookup_system_cpu('pce'),
	"PlayStation": lookup_system_cpu('psj'),
	"Pokemon Mini": lookup_system_cpu('pokemini'),
	"PS2": lookup_system_cpu('ps2'),
	"PSP": "Allegrex",
	"Satellaview": lookup_system_cpu('snes'),
	"Saturn": lookup_system_cpu('saturn'),
	"SG-1000": lookup_system_cpu('sg1000'),
	"Sharp X1": lookup_system_cpu('x1'),
	"Sharp X68000": lookup_system_cpu('x68000'),
	"SNES": lookup_system_cpu('snes'),
	"Sord M5": lookup_system_cpu('m5'),
	"Sufami Turbo": lookup_system_cpu('snes'),
	"Tomy Tutor": lookup_system_cpu('tutor'),
	"Vectrex": lookup_system_cpu('vectrex'),
	"VIC-10": lookup_system_cpu('vic10'),
	"VIC-20": lookup_system_cpu('vic20'),
	"Virtual Boy": lookup_system_cpu('vboy'),
	"Watara Supervision": lookup_system_cpu('svision'),
	"Wii": lookup_system_cpu('tvcapcom'), #Yes that's not a Wii, but it runs on Wii hardware, and a real Wii isn't even a skeleton driver yet. I really just don't feel like hardcoding things today
	"WonderSwan": lookup_system_cpu('wscolor'),
}

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


					#Would still be in this extra part
					main_input = launchers.get_field(desktop, 'X-Main-Input')
					main_cpu = launchers.get_field(desktop, 'X-Main-CPU')
					source_file = launchers.get_field(desktop, 'X-Source-File')
					family = launchers.get_field(desktop, 'X-Family')
					
					if main_input:
						copy_to_folder(path, config.organized_output_folder, 'By input method', sanitize_name(main_input))
					if main_cpu:
						copy_to_folder(path, config.organized_output_folder, 'By main CPU', sanitize_name(main_cpu))
					elif platform in console_cpus:
						copy_to_folder(path, config.organized_output_folder, 'By main CPU', sanitize_name(console_cpus[platform]))
					if source_file:
						copy_to_folder(path, config.organized_output_folder, 'By MAME source file', sanitize_name(source_file))
					if family:
						copy_to_folder(path, config.organized_output_folder, 'By parent-clone family', sanitize_name(family))
	