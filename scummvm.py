#!/usr/bin/env python3

import configparser
import datetime
import os
import subprocess
import time

import input_metadata
import launchers
from common_types import SaveType
from config.main_config import main_config
from info.region_info import get_language_by_short_code
from metadata import Metadata
from pc_common_metadata import look_for_icon_in_folder

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
			self.have_scummvm_config = os.path.isfile(scumm_config_path)
			self.have_residualvm_config = os.path.isfile(residualvm_config_path)

			self.have_scummvm_exe = True
			try:
				self.scummvm_engines = self.get_vm_engines('scummvm')
			except FileNotFoundError:
				self.have_scummvm_exe = False

			self.have_residualvm_exe = True
			try:
				self.residualvm_engines = self.get_vm_engines('residualvm')
			except FileNotFoundError:
				self.have_residualvm_exe = False

			self.scummvm_config = _get_vm_config(scumm_config_path)
			self.residualvm_config = _get_vm_config(residualvm_config_path)

		@staticmethod
		def get_vm_engines(exe_name):
			try:
				proc = subprocess.run([exe_name, '--list-engines'], stdout=subprocess.PIPE, check=True, universal_newlines=True)
				lines = proc.stdout.splitlines()[2:] #Ignore header and ----

				engines = {}
				for line in lines:
					#Engine ID shouldn't have spaces, I think
					engine_id, name = line.split(maxsplit=1)
					name = name.removeprefix(' [all games]')
					engines[engine_id] = name
				engines['agi'] = 'AGI' #Not this weird 'AGI v32qrrbvdsnuignedogsafgd' business
				return engines
			except subprocess.CalledProcessError:
				return []

		@property
		def have_scummvm(self):
			return self.have_scummvm_config and self.have_scummvm_exe
		
		@property
		def have_residualvm(self):
			return self.have_residualvm_config and self.have_residualvm_exe

	__instance = None

	@staticmethod
	def getScummVMConfig():
		if ScummVMConfig.__instance is None:
			ScummVMConfig.__instance = ScummVMConfig.__ScummVMConfig()
		return ScummVMConfig.__instance

vmconfig = ScummVMConfig.getScummVMConfig()

def have_something_vm():
	return vmconfig.have_scummvm or vmconfig.have_residualvm

def format_platform(platform):
	#https://github.com/scummvm/scummvm/blob/master/common/platform.cpp#L28
	return {
		#We'll use the same formatting as in system_info
		'2gs': 'Apple IIgs',
		'apple2': 'Apple II',
		'3do': '3DO',
		'acorn': 'Acorn Archimedes',
		'amiga': 'Amiga',
		'atari8': 'Atari 8-bit',
		'atari': 'Atari ST',
		'c64': 'C64',
		'pc': 'DOS',
		'pc98': 'PC-98',
		'wii': 'Wii',
		'coco3': 'Tandy CoCo',
		'fmtowns': 'FM Towns',
		'linux': 'Linux',
		'macintosh': 'Mac',
		'pce': 'PC Engine CD', #All the PC Engine games supported would be CDs, not cards
		'nes': 'NES',
		'segacd': 'Mega CD',
		'windows': 'Windows',
		'playstation': 'PlayStation',
		'playstation2': 'PS2',
		'xbox': 'Xbox',
		'cdi': 'CD-i',
		'ios': 'iOS',
		'os2': 'OS/2',
		'beos': 'BeOS',
		'ppc': 'PocketPC',
		'megadrive': 'Mega Drive',
		'saturn': 'Saturn',
	}.get(platform, platform)

class ScummVMGame():
	def __init__(self, name, vm_config):
		#The [game-name] is also user-modifiable and shouldn't be relied on to mean anything, but it is used for scummvm to actually launch the game and can be trusted to be unique
		self.name = name
		self.options = {}
		for k, v in vm_config.items(name):
			self.options[k] = v

		self.metadata = Metadata()
		self.add_metadata()

	@staticmethod
	def _engine_list_to_use():
		return vmconfig.scummvm_engines

	def _get_launch_params(self):
		return launchers.LaunchParams('scummvm', ['-f', self.name])

	@staticmethod
	def _get_emulator_name():
		return 'ScummVM'

	def add_metadata(self):
		self.metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it, but I guess to add that as input_info I'd have to know exactly how many buttons and sticks etc it uses
		self.metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		self.metadata.emulator_name = self._get_emulator_name()
		self.metadata.categories = ['Games'] #Safe to assume this by default
		if self.options.get('gameid') == 'agi-fanmade':
			self.metadata.categories = ['Homebrew']
		#genre/subgenre is _probably_ always point and click adventure, but maybe not? (Plumbers is arguably a visual novel (don't @ me), and there's something about some casino card games in the list of supported games)
		#Would be nice to set things like developer/publisher/year but can't really do that unfortunately
		#Let series and series_index be detected by series_detect
		
		engine_id = self.options.get('engineid')
		self.metadata.specific_info['Engine'] = self._engine_list_to_use().get(engine_id)
		extra = self.options.get('extra')
		if extra:
			self.metadata.specific_info['Version'] = extra #Hmm, I guess that'd be how we should use this properly…
			if 'demo' in extra.lower():
				#Keeping the category names consistent with everything else here, though people might like to call it "Demos" or whatever instead and technically there's no reason why we can't do that and this should be an option and I will put this ramble here to remind myself to make it an option eventually
				self.metadata.categories = ['Trials']
		
		if main_config.use_original_platform:
			platform = self.options.get('platform')
			if platform:
				self.metadata.platform = format_platform(platform)
			if platform == 'amiga' and extra == 'CD32':
				self.metadata.platform = 'Amiga CD32'
		
		language_code = self.options.get('language')
		if language_code:
			if language_code == 'br':
				language = get_language_by_short_code('Pt-Br')
			elif language_code == 'se':
				#…That's the region code for Sweden, not the language code for Swedish, so that's odd but that's how it ends up being
				language = get_language_by_short_code('Sv')
			else:
				language = get_language_by_short_code(language_code, case_insensitive=True)
			if language:
				self.metadata.languages = [language]

		path = self.options.get('path')
		if path:
			if os.path.isdir(path):
				icon = look_for_icon_in_folder(path)
				if icon:
					self.metadata.images['Icon'] = icon
			else:
				if main_config.debug:
					print('Aaaa!', self.name, path, 'does not exist')
		else:
			if main_config.debug:
				print('Wait what?', self.name, 'has no path')
		#Everything else is gonna be an actual option

	def make_launcher(self):
		name = self.options.get('description', self.name)
		name = name.replace('/', ') (') #Names are usually something like Cool Game (CD/DOS/English); we convert it to Cool Game (CD) (DOS) (English) to make it work better with disambiguate etc

		#Hmm, could use ResidualVM as the launcher type for ResidualVM games... but it's just a unique identifier type thing, so it should be fine
		launchers.make_launcher(self._get_launch_params(), name, self.metadata, 'ScummVM', self.name)

class ResidualVMGame(ScummVMGame):
	@staticmethod
	def _get_emulator_name():
		return 'ResidualVM'

	@staticmethod
	def _engine_list_to_use():
		return vmconfig.residualvm_engines

	def _get_launch_params(self):
		return launchers.LaunchParams('residualvm', ['-f', self.name])

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
			#Skip the top section that just says [scummvm]/[residualvm]
			continue
		if section == 'cloud':
			#This is not a game either
			continue
		if not main_config.full_rescan:
			if launchers.has_been_done('ScummVM', section):
				continue

		game = game_class(section, vm_config)
		game.make_launcher()

	if main_config.print_times:
		time_ended = time.perf_counter()
		print(name, 'finished in', str(datetime.timedelta(seconds=time_ended - time_started)))


def add_scummvm_games():
	if vmconfig.have_scummvm_exe:
		add_vm_games('ScummVM', scumm_config_path, vmconfig.scummvm_config, ScummVMGame)
	if vmconfig.have_residualvm_exe:
		add_vm_games('ResidualVM', residualvm_config_path, vmconfig.residualvm_config, ResidualVMGame)

if __name__ == '__main__':
	add_scummvm_games()
