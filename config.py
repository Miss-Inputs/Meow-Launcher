import os
import configparser

from info import system_info, emulator_info

#TODO: Get this in a less hardcody cross-platform way.
config_dir = os.path.expanduser('~/.config/CrappyGameLauncher/')
config_path = os.path.join(config_dir, 'config.ini')
ignored_dirs_path = os.path.join(config_dir, 'ignored_directories.txt')
name_consistency_path = os.path.join(os.path.dirname(__file__), 'name_consistency.ini')
emulator_config_path = os.path.join(config_dir, 'emulators.ini')

class SystemConfig():
	def __init__(self, name, rom_dir, chosen_emulator, other_config=None):
		self.name = name
		self.rom_dir = rom_dir
		self.chosen_emulator = chosen_emulator
		self.other_config = {} if other_config is None else other_config

#Normally, we'd skip over anything that has software because that indicates it's a system you plug games into and not
#usable by itself.  But these are things that are really just standalone things, but they have an expansion for
#whatever reason and are actually fine
#cfa3000 is kinda fine but it counts as a BBC Micro so it counts as not fine, due to detecting this stuff by
#parent/clone family
okay_to_have_software = ['vii', 'snspell', 'tntell']

output_folder = None
organized_output_folder = None

basilisk_ii_shared_folder = None
mac_disk_images = []
mac_db_path = None

catlist_path = None
languages_path = None
skipped_source_files = None

ignored_directories = []
#For when I do a hecking disagreement about how names should be formatted, and if subtitles should be in the title or
#not.  This probably annoys purists, but I think it makes things less confusing at the end of the day
#TODO: Review the practicality of just changing normalize_name to remove all spaces and punctuation.  Would that cause
#any false positives at all?  Though there would still be use for this part here
name_replacement = []
#Add "The " in front of these things (but not if there's already "The " in front of them of course)
add_the = []
#Only check for this at the start of a thing
subtitle_removal = []

system_configs = []

def load_config():
	#TODO: Load overrides from command line
	parser = configparser.ConfigParser()
	parser.optionxform = str
	if not os.path.isfile(config_path):
		print('oh no')
		return
	parser.read(config_path)
	global output_folder, organized_output_folder, basilisk_ii_shared_folder, mac_disk_images, mac_db_path, catlist_path, languages_path, skipped_source_files

	output_folder = os.path.expanduser(parser['General']['output_folder'])
	organized_output_folder = os.path.expanduser(parser['General']['organized_output_folder'])
	
	basilisk_ii_shared_folder = os.path.expanduser(parser['Mac']['basilisk_ii_shared_folder'])
	mac_disk_images = [os.path.expanduser(path) for path in parser['Mac']['mac_disk_images'].split(';')]
	mac_db_path = os.path.expanduser(parser['Mac']['mac_db_path'])

	catlist_path = os.path.expanduser(parser['Arcade']['catlist_path'])
	languages_path = os.path.expanduser(parser['Arcade']['languages_path'])
	skipped_source_files = parser['Arcade']['skipped_source_files'].split(';')

def load_name_replacement():
	#Sometimes, we want to mess around with : being in the title, so that can't be a delimiter since it needs to appear inside "keys". I'd have to restructure the whole config file to not be an .ini at all otherwise. Hopefully, nothing will have an equals sign in the title.
	parser = configparser.ConfigParser(delimiters=('='), allow_no_value=True)
	parser.optionxform = str
	if not os.path.isfile(name_consistency_path):
		print('oh no')
		return
	parser.read(name_consistency_path)
	
	for k, v in parser['Name Replacement'].items():
		name_replacement.append((k, v))
	for k, v in parser['Add "The"'].items():
		add_the.append(k)
	for k, v in parser['Subtitle Removal'].items():
		subtitle_removal.append((k, v))

def load_emulator_configs():
	global system_configs

	parser = configparser.ConfigParser(delimiters=('='), allow_no_value=True)
	parser.optionxform = str
	if not os.path.isfile(emulator_config_path):
		print('oh no')
		return
	parser.read(emulator_config_path)

	for system in parser.sections():
		rom_dir = parser[system]['rom_dir']
		if not rom_dir:
			continue
		emulator = parser[system]['emulator']

		if emulator not in emulator_info.emulators:
			print('Warning! System {0} is configured to use {1} but that is not known as an emulator'.format(system, emulator))

		info = system_info.get_system_by_name(system)
		if info:
			if emulator not in info.emulators:
				print('Warning! System {0} is configured to use {1} which does not support {0}'.format(system, emulator))
		else:
			print('Warning! System {0} is configured but might not exist'.format(system))

		other_config = {k: v for k, v in parser[system].items() if k not in ('rom_dir', 'emulator')}

		system_configs.append(SystemConfig(system, rom_dir, emulator, other_config))
			
load_config()
with open(ignored_dirs_path, 'rt') as ignored_txt:
	ignored_directories = ignored_txt.read().splitlines()
load_name_replacement()
load_emulator_configs()
