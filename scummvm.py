#!/usr/bin/env python3

import os
import configparser
import time
import datetime

from config import main_config
import launchers
import input_metadata
from metadata import Metadata, EmulationStatus
from common_types import SaveType, MediaType
from common import find_filename_tags
from info.region_info import get_language_by_english_name

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
	for tag in filename_tags:
		tag = tag.lstrip('(').rstrip(')')
		language = get_language_by_english_name(tag)
		if language:
			metadata.languages.append(language)
			continue

		if tag == 'English (US':
			#Didn't except there'd be nested parentheses... oh well
			metadata.languages.append(get_language_by_english_name('English'))

		if tag in ('Demo', 'Linux Demo', 'CD Demo'):
			metadata.categories = ['Trials']
		if tag == 'Non-Interactive Demo':
			#One day, I'll think of some kind of standard for the categories names, but until then I've decided everything non-interactive should be in Demos
			metadata.categories = ['Demos']
		if tag in ('CD', 'CD Demo', 'CD32', 'SegaCD', 'Sony PlayStation', 'Philips CD-i', '3DO') or tag.endswith(' cd'):
			#The latter shows up alongside a version number infrequently, e.g. "v0.0372 cd"
			metadata.media_type = MediaType.OpticalDisc
		if tag == 'NES':
			metadata.media_type = MediaType.Cartridge

		#Platforms: https://github.com/scummvm/scummvm/blob/master/common/platform.cpp, in the event I want to do something with that
		#Versions: v1.1, v1.00, anything matching v\d+\.\d+ I guess, 1.1, Freeware v1.1, Freeware v1.0
		#Others: final, VGA, EGA, Masterpiece Edition, Talkie, Latest version, unknown version
		
class ScummVMGame():
	def __init__(self, name):
		self.name = name
		self.icon = None
		self.options = {}

	def _get_launch_params(self):
		return 'scummvm', ['-f', self.name]

	@staticmethod
	def _get_emulator_name():
		return 'ScummVM'

	def make_launcher(self):
		name = self.options.get('description', self.name)
		name = name.replace('/', ') (') #Names are usually something like Cool Game (CD/DOS/English); we convert it to Cool Game (CD) (DOS) (English) to make it work better with disambiguate etc

		launch_params = launchers.LaunchParams(*self._get_launch_params())
		metadata = Metadata()
		metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it, but I guess to add that as input_info I'd have to know exactly how many buttons and sticks etc it uses
		metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		metadata.emulator_name = self._get_emulator_name()
		metadata.categories = ['Games'] #Safe to assume this by default
		if self.name.startswith('agi-fanmade'):
			metadata.categories = ['Homebrew']
		#metadata.nsfw is false by default, but in some ScummVM-supported games (e.g. Plumbers Don't Wear Ties) it would arguably be true; but there's not any way to detect that unless we just do "if game in [list_of_stuff_with_adult_content] then nsfw = true" 
		#genre/subgenre is _probably_ always point and click adventure, but maybe not? (Plumbers is arguably a visual novel (don't @ me), and there's something about some casino card games in the list of supported games)
		#Would be nice to set things like developer/publisher/year but can't really do that unfortunately
		#Let series and series_index be detected by series_detect
		gsl = self.options.get('gsl')
		#From what I can tell, this stands for "game support level"
		#From engines/game.h:
		#enum GameSupportLevel {
		#kStableGame = 0, // the game is fully supported
		#kTestingGame, // the game is not supposed to end up in releases yet but is ready for public testing
		#kUnstableGame // the game is not even ready for public testing yet
		#};
		if gsl == 'testing':
			metadata.specific_info['ScummVM-Status'] = EmulationStatus.Imperfect
		elif gsl == 'unstable':
			metadata.specific_info['ScummVM-Status'] = EmulationStatus.Broken
		else:
			metadata.specific_info['ScummVM-Status'] = EmulationStatus.Good
		#TODO: Should have option to skip anything with unstable and/or testing status

		path = self.options.get('path')
		if path and os.path.exists(path):
			for f in os.listdir(path):
				if f.lower().endswith('.ico'):
					self.icon = os.path.join(path, f)

		get_stuff_from_filename_tags(metadata, find_filename_tags.findall(name))

		#Hmm, could use ResidualVM as the launcher type for ResidualVM games... but it's just a unique identifier type thing, so it should be fine
		launchers.make_launcher(launch_params, name, metadata, 'ScummVM', self.name, self.icon)

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
