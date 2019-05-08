#!/usr/bin/env python3

import os
import configparser
import time
import datetime

from config import main_config
import launchers
import input_metadata
from metadata import Metadata
from common_types import SaveType, MediaType
from common import find_filename_tags
import region_detect

scumm_config_path = os.path.expanduser('~/.config/scummvm/scummvm.ini')
residualvm_config_path = os.path.expanduser('~/.config/residualvm/residualvm.ini')

def _get_vm_config(path):
	parser = configparser.ConfigParser()
	parser.optionxform = str
	parser.read(path)
	return parser

class ScummVMConfig():
	class __ScummVMConfig():
		def __init__(self):
			self.have_scummvm = os.path.isfile(scumm_config_path)
			self.have_residualvm = os.path.isfile(residualvm_config_path)

			self.scummvm_config = _get_vm_config(scumm_config_path)
			self.residualvm_config = _get_vm_config(residualvm_config_path)

	__instance = None

	@staticmethod
	def getScummVMConfig():
		if ScummVMConfig.__instance is None:
			ScummVMConfig.__instance = ScummVMConfig.__ScummVMConfig()
		return ScummVMConfig.__instance

vmconfig = ScummVMConfig.getScummVMConfig()

def have_something_vm():
	return vmconfig.have_scummvm or vmconfig.have_residualvm

def get_stuff_from_filename_tags(metadata, filename_tags):
	for filename_tag in filename_tags:
		#There's usually only one, though
		filename_tag = filename_tag.lstrip('(').rstrip(')')
		for piece in filename_tag.split('/'):
			language = region_detect.get_language_by_english_name(piece)
			if language:
				metadata.languages = [language]
				continue
			if piece == 'Demo':
				metadata.categories = ['Trials']
			if piece == 'CD':
				metadata.media_type = MediaType.OpticalDisc
			#Emulated platform: DOS, Windows, Macintosh, Apple II, etc. (could set platform to this if we really wanted, but I dunno)
			#Others: v0.0372 cd, 1.1, Masterpiece Edition, unknown version, VGA, EGA, Freeware 1.1, Freeware 1.0, Talkie
			#There doesn't seem to be any particular structure or order that I can tell (if there is though, that'd be cool)

class ScummVMGame():
	def __init__(self, name):
		self.name = name
		self.options = {}

	def _get_launch_params(self):
		return 'scummvm', ['-f', self.name]

	@staticmethod
	def _get_emulator_name():
		return 'ScummVM'

	def make_launcher(self):
		name = self.options.get('description', self.name)

		launch_params = launchers.LaunchParams(*self._get_launch_params())
		metadata = Metadata()
		metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it
		metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		metadata.emulator_name = self._get_emulator_name()

		get_stuff_from_filename_tags(metadata, find_filename_tags.findall(name))

		#Hmm, could use ResidualVM as the launcher type for ResidualVM games... but it's just a unique identifier type thing, so it should be fine
		launchers.make_launcher(launch_params, name, metadata, 'ScummVM', self.name)

class ResidualVMGame(ScummVMGame):
	@staticmethod
	def _get_emulator_name():
		return 'ResidualVM'

	def _get_launch_params(self):
		return 'residualvm', ['-f', self.name]

def no_longer_exists(game_id):
	if vmconfig.have_scummvm:
		exists_in_scummvm = game_id in vmconfig.scummvm_config.sections()
	else:
		exists_in_scummvm = False

	if vmconfig.have_residualvm:
		exists_in_residualvm = game_id in vmconfig.residualvm_config.sections()
	else:
		exists_in_residualvm = False
	return not (exists_in_scummvm or exists_in_residualvm)

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
	add_vm_games('ScummVM', scumm_config_path, vmconfig.scummvm_config, ScummVMGame)
	add_vm_games('ResidualVM', residualvm_config_path, vmconfig.residualvm_config, ResidualVMGame)

if __name__ == '__main__':
	add_scummvm_games()
