#!/usr/bin/env python3

import os
import configparser
import time
import datetime

from config import main_config
import launchers
import input_metadata
from metadata import Metadata
from common_types import SaveType

config_path = os.path.expanduser('~/.config/scummvm/scummvm.ini')
def _get_scummvm_config():
	parser = configparser.ConfigParser()
	parser.optionxform = str
	parser.read(config_path)
	return parser
scummvm_config = _get_scummvm_config()

class ScummVMGame():
	def __init__(self, name):
		self.name = name
		self.options = {}

	def make_launcher(self):
		name = self.options.get('description', self.name)
		command = 'scummvm -f {0}'.format(self.name)
		metadata = Metadata()
		metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it
		metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		metadata.emulator_name = 'ScummVM'
		#TODO: publisher, categories, languages, nsfw, regions, subgenre, year... somehow
		#Others are left deliberately blank because they refer to emulators and not engines
		launchers.make_launcher(command, name, metadata, 'ScummVM', self.name)

def no_longer_exists(game_id):
	return game_id not in scummvm_config.sections()

def add_scummvm_games():
	if not os.path.isfile(config_path):
		return

	time_started = time.perf_counter()

	for section in scummvm_config.sections():
		if section == 'scummvm':
			continue
		if not main_config.full_rescan:
			if launchers.has_been_done('ScummVM', section):
				continue

		game = ScummVMGame(section)
		for k, v in scummvm_config.items(section):
			game.options[k] = v
		game.make_launcher()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('ScummVM finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


if __name__ == '__main__':
	add_scummvm_games()
