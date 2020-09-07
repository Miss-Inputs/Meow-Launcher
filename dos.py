#!/usr/bin/env python3

import os

import config.main_config
import config.system_config
import launchers
import pc
from common_types import EmulationNotSupportedException, NotARomException
from info.emulator_info import dos_emulators
from pc_common_metadata import look_for_icon_next_to_file

conf = config.main_config.main_config
system_configs = config.system_config.system_configs
dos_config = system_configs.get('DOS')

class DOSApp(pc.App):
	def additional_metadata(self):
		self.metadata.platform = 'DOS'
		_, extension = os.path.splitext(self.path)
		self.metadata.extension = extension[1:].lower()
		try:
			icon = look_for_icon_next_to_file(self.path)
			if icon:
				self.metadata.images['Icon'] = icon
		except FileNotFoundError as fnfe:
			if conf.debug:
				print('Oh no!', self.name, fnfe)

	def make_launcher(self):
		emulator_name = None
		params = None
		exception_reason = None
		for emulator in dos_config.chosen_emulators:
			emulator_name = emulator
			try:
				params = dos_emulators[emulator].get_launch_params(self, dos_config.options)
				if params:
					break
			except (EmulationNotSupportedException, NotARomException) as ex:
				exception_reason = ex

		if not params:
			if conf.debug:
				print(self.path, 'could not be launched by', dos_config.chosen_emulators, 'because', exception_reason)
			return

		self.metadata.emulator_name = emulator_name
		launchers.make_launcher(params, self.name, self.metadata, 'DOS', self.path)

def make_dos_launchers():
	if dos_config:
		if not dos_config.chosen_emulators:
			return
		pc.make_launchers('DOS', DOSApp)

# def scan_app(path, exe_name, game_list, unknown_games, found_games, ambiguous_games):
# 	possible_games = [(game_name, game_config) for game_name, game_config in game_list.items() if game_config['app_name'].lower() == exe_name]
# 	if not possible_games:
# 		unknown_games.append(path)
# 	elif len(possible_games) == 1:
# 		found_games[path] = possible_games[0][0]
# 	else:
# 		ambiguous_games[path] = [game_name for game_name, game_config in possible_games]

# def scan_dos_folder(path, game_list, unknown_games, found_games, ambiguous_games):
# 	for root, _, files in os.walk(path):
# 		if common.starts_with_any(root + os.sep, conf.ignored_directories):
# 			continue
# 		for name in files:
# 			ext = os.path.splitext(name)[1][1:].lower()
# 			if ext not in ('exe', 'com', 'bat'):
# 				continue

# 			path = os.path.join(root, name)
# 			scan_app(path, name.lower(), game_list, unknown_games, found_games, ambiguous_games)

if __name__ == '__main__':
	make_dos_launchers()
