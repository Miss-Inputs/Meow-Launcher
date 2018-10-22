import json
import os
import urllib.request
import sys
import configparser
import collections
import time
import datetime

from config import main_config, system_configs
from metadata import Metadata
from info.system_info import MediaType
from info.emulator_command_lines import EmulationNotSupportedException, NotARomException
import launchers

debug = '--debug' in sys.argv
print_times = '--print-times' in sys.argv


def init_game_list(platform):
	db_path = main_config.mac_db_path if platform == 'mac' else main_config.dos_db_path if platform == 'dos' else None

	if not os.path.exists(db_path):
		print("You don't have {0}_db.json which is required for this to work. Let me get that for you.".format(platform))
		#TODO: Is this the wrong way to do this? I think it most certainly is
		db_url = 'https://raw.githubusercontent.com/Zowayix/computer-software-db/master/{0}_db.json'.format(platform)
		with urllib.request.urlopen(db_url) as mac_db_request:
			db_data = mac_db_request.read().decode('utf-8')
		with open(db_path, 'wt') as db_local_file:
			db_local_file.write(db_data)
			game_list = json.loads(db_data)
	else:
		with open(db_path, 'rt') as db_file:
			game_list = json.load(db_file)

	for game_name, game in game_list.items():
		if 'parent' in game:
			parent_name = game['parent']
			if parent_name in game_list:
				parent = game_list[parent_name]
				for key in parent.keys():
					if key not in game:
						game_list[game_name][key] = parent[key]
			else:
				if debug:
					print('Oh no! {0} refers to undefined parent game {1}'.format(game_name, parent_name))

	return game_list

class App:
	def __init__(self, path, name, app_config):
		self.path = path
		self.name = name
		self.config = app_config
		self.icon = None

	def additional_metadata(self, metadata):
		pass

	def make_launcher(self, system_config, emulators):
		metadata = Metadata()
		#TODO Add input_info and whatnot
		self.additional_metadata(metadata)
		metadata.media_type = MediaType.Executable

		if 'developer' in self.config:
			metadata.developer = self.config['developer']
		if 'publisher' in self.config:
			metadata.publisher = self.config['publisher']
		elif 'developer' in self.config:
			metadata.publisher = self.config['developer']

		if 'year' in self.config:
			metadata.year = self.config['year']

		if 'category' in self.config:
			metadata.categories = [self.config['category']]

		if 'genre' in self.config:
			metadata.genre = self.config['genre']
		if 'subgenre' in self.config:
			metadata.subgenre = self.config['subgenre']
		if 'adult' in self.config:
			metadata.nsfw = self.config['adult']
		if 'notes' in self.config:
			metadata.specific_info['Notes'] = self.config['notes']
		if 'compat_notes' in self.config:
			metadata.specific_info['Compatibility-Notes'] = self.config['compat_notes']
			print('Compatibility notes for', self.name, ':', self.config['compat_notes'])
		if 'requires_cd' in self.config:
			print(self.name, 'requires a CD in the drive. It will probably not work with this launcher at the moment')
			metadata.specific_info['Requires-CD'] = self.config['requires_cd']

		emulator_name = None
		command = None
		exception_reason = None
		for emulator in system_config.chosen_emulators:
			emulator_name = emulator
			try:
				command = emulators[emulator].get_command_line(self, system_config.other_config)
				if command:
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not command:
			if debug:
				print(self.path, 'could not be launched by', system_config.chosen_emulators, 'because', exception_reason)
			return

		metadata.emulator_name = emulator_name
		launchers.make_launcher(command, self.name, metadata, {'Type': metadata.platform, 'Unique-ID': self.path}, icon=self.icon)

def scan_folders(platform, config_path, scan_function):
	unknown_games = []
	found_games = {}
	ambiguous_games = {}

	system_config = system_configs.configs[platform]
	if not system_config:
		return

	game_list = init_game_list(platform.lower())
	for folder in system_config.paths:
		scan_function(folder, game_list, unknown_games, found_games, ambiguous_games)

	configwriter = configparser.ConfigParser()
	configwriter.optionxform = str
	configwriter['Apps'] = {}
	configwriter['Ambiguous'] = {}
	configwriter['Unknown'] = {}
	for k in sorted(found_games.keys()):
		configwriter['Apps'][k] = found_games[k]
	for k in sorted(ambiguous_games.keys()):
		configwriter['Ambiguous'][k] = ';'.join(ambiguous_games[k])
	for unknown in sorted(unknown_games):
		configwriter['Unknown'][unknown] = ''
	with open(config_path, 'wt') as config_file:
		configwriter.write(config_file)

	found_counter = collections.Counter(found_games.values())
	for value in [value for value, count in found_counter.items() if count > 1]:
		print('Warning: {0} appears more than once: {1}'.format(value, [key for key, game_config_name in found_games.items() if value == game_config_name]))

	print('Scan results have been written to', config_path)
	print('Because not everything can be autodetected, some may be unrecognized')
	print('and you will have to configure them yourself, or may be one of several')
	print('apps and you will have to specify which is which, until I think of')
	print('a better way to do this.')

def make_launchers(system_config_name, config_path, app_class, emulator_list):
	system_config = system_configs.configs[system_config_name]
	if not system_config:
		return

	time_started = time.perf_counter()

	game_list = init_game_list(system_config_name.lower())
	if not os.path.isfile(config_path):
		#TODO: Perhaps notify user they have to do ./blah.py --scan to do the thing
		return

	parser = configparser.ConfigParser(delimiters=('='), allow_no_value=True)
	parser.optionxform = str
	parser.read(config_path)

	for path, config_name in parser.items('Apps'):
		if config_name not in game_list:
			print('Oh no!', path, 'refers to', config_name, "but that isn't known")
			continue
		game_config = game_list[config_name]
		app_class(path, config_name, game_config).make_launcher(system_config, emulator_list)

	do_unknown = main_config.launchers_for_unknown_dos_apps if system_config_name == 'DOS' else main_config.launchers_for_unknown_mac_apps if system_config_name == 'Mac' else False
	if do_unknown:
		for unknown, _ in parser.items('Unknown'):
			app_class(unknown, unknown.split(':')[-1], {}).make_launcher(system_config, emulator_list)

	if print_times:
		time_ended = time.perf_counter()
		print(system_config_name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))
