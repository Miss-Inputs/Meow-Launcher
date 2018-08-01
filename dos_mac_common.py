import json
import os
import urllib.request
import sys

import config
from metadata import Metadata
import launchers

debug = '--debug' in sys.argv

def init_game_list(platform):
	db_path = config.mac_db_path if platform == 'mac' else config.dos_db_path if platform == 'dos' else None

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
					if key == "notes":
						if key in game:
							game_list[game_name][key] = parent[key] + ";" + game_list[game_name][key]
						else:
							game_list[game_name][key] = parent[key]
					elif key not in game:
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

	def additional_metadata(self, metadata):
		pass

	def make_launcher(self, system_config, emulators):
		metadata = Metadata()
		#TODO Add input_info and whatnot
		self.additional_metadata(metadata)

		if 'publisher' in self.config:
			metadata.publisher = self.config['publisher']
		if 'developer' in self.config:
			metadata.developer = self.config['developer']
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
		for emulator in system_config.chosen_emulators:
			emulator_name = emulator
			command = emulators[emulator].get_command_line(self, system_config.other_config)
			if command:
				break

		if not command:
			return

		metadata.emulator_name = emulator_name
		launchers.make_launcher(command, self.name, metadata, {'Path': self.path})
