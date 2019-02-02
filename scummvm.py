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

scumm_config_path = os.path.expanduser('~/.config/scummvm/scummvm.ini')
residualvm_config_path = os.path.expanduser('~/.config/residualvm/residualvm.ini')

def _get_vm_config(path):
	parser = configparser.ConfigParser()
	parser.optionxform = str
	parser.read(path)
	return parser
scummvm_config = _get_vm_config(scumm_config_path)
residualvm_config = _get_vm_config(residualvm_config_path)

class ScummVMGame():
	def __init__(self, name):
		self.name = name
		self.options = {}

	def _get_command_line_template(self):
		return 'scummvm', ['-f', self.name]

	@staticmethod
	def _get_emulator_name():
		return 'ScummVM'

	def make_launcher(self):
		name = self.options.get('description', self.name)
		exe_name, exe_args = self._get_command_line_template()
		metadata = Metadata()
		metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it
		metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		metadata.emulator_name = self._get_emulator_name()

		#Hmm, could use ResidualVM as the launcher type for ResidualVM games... but it's just a unique identifier type thing, so it should be fine
		launchers.make_launcher(exe_name, exe_args, name, metadata, 'ScummVM', self.name)

class ResidualVMGame(ScummVMGame):
	@staticmethod
	def _get_emulator_name():
		return 'ResidualVM'

	def _get_command_line_template(self):
		return 'residualvm', ['-f', self.name]

def no_longer_exists(game_id):
	return game_id not in scummvm_config.sections() and game_id not in residualvm_config.sections()

def add_vm_games(name, config_path, vm_config, game_class):
	if not os.path.isfile(config_path):
		return

	time_started = time.perf_counter()

	for section in vm_config.sections():
		if section == name.lower():
			continue
		if not main_config.full_rescan:
			if launchers.has_been_done('ScummVM', section):
				continue

		game = game_class(section)
		for k, v in vm_config.items(section):
			game.options[k] = v
		game.make_launcher()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def add_scummvm_games():
	add_vm_games('ScummVM', scumm_config_path, scummvm_config, ScummVMGame)
	add_vm_games('ResidualVM', residualvm_config_path, residualvm_config, ResidualVMGame)

if __name__ == '__main__':
	add_scummvm_games()
