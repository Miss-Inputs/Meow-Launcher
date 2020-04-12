#!/usr/bin/env python3

import configparser
import datetime
import os
import subprocess
import time

import detect_things_from_filename
import input_metadata
import launchers
from common import find_filename_tags
from common_types import MediaType, SaveType
from config import main_config
from metadata import EmulationStatus, Metadata

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
					if name.endswith(' [all games]'):
						name = name[:-12]
					engines[engine_id] = name
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

def get_platform_mediatype_from_tags(tags):
	if '(Apple II)' in tags:
		return 'Apple II', MediaType.Floppy
	if '(Apple IIgs)' in tags:
		return 'Apple IIgs', MediaType.Floppy
	if '(3DO)' in tags:
		return '3DO', MediaType.OpticalDisc
	if '(Acorn)' in tags:
		return 'Acorn Archimedes', MediaType.Floppy #Let the rest of the code detect if it's a CD
	if '(Amiga)' in tags:
		if '(CD32)' in tags:
			return 'Amiga CD32', MediaType.OpticalDisc
		return 'Amiga', MediaType.Floppy
	if '(Atari 8-bit)' in tags:
		return 'Atari 8-bit', MediaType.Floppy
	if '(Atari ST)' in tags:
		return 'Atari ST', MediaType.Floppy
	if '(Commodore 64)' in tags:
		return 'C64', MediaType.Floppy
	if '(DOS)' in tags:
		return 'DOS', None #Either floppy or executable I dunno mate
	if '(PC-98)' in tags:
		return 'PC-98', None
	if '(Nintendo Wii)' in tags:
		return 'Wii', MediaType.OpticalDisc #I think none of the ScummVM games are WiiWare, slap me if I am wrong
	if '(CoCo3)' in tags:
		return 'Tandy CoCo', MediaType.Floppy
	if '(FM-TOWNS)' in tags:
		return 'FM Towns', None
	if '(Linux)' in tags or '(Linux Demo)' in tags:
		return 'Linux', None #Could argue platform is blank here, but like… eh
	if '(Macintosh)' in tags:
		return 'Mac', None
	if '(PC-Engine)' in tags:
		return 'PC Engine CD', MediaType.OpticalDisc #Doesn't actually do PC Engine cards last time I checked, if this becomes wrong, then check for CD in tags or whatever
	if '(NES)' in tags:
		return 'NES', MediaType.Cartridge
	if '(SegaCD)' in tags:
		return 'Mega CD', MediaType.OpticalDisc
	if '(Windows)' in tags:
		return 'Windows', None
	if '(Sony PlayStation)' in tags:
		return 'PlayStation', MediaType.OpticalDisc
	if '(Philips CD-i)' in tags:
		return 'CD-i', MediaType.OpticalDisc
	if '(Apple iOS)' in tags:
		return 'iOS', MediaType.Digital
	if '(OS/2)' in tags:
		return 'OS/2', None
	if '(BeOS)' in tags:
		return 'BeOS', None
	if '(PocketPC)' in tags:
		return 'PocketPC', None

	return None, None

def get_stuff_from_filename_tags(metadata, name_tags):
	languages = detect_things_from_filename.get_languages_from_filename_tags(name_tags)
	if languages:
		#This will parse "English (US)" as "English" which is what we want really
		metadata.languages = languages
	year, _, _ = detect_things_from_filename.get_date_from_filename_tags(name_tags)
	#Would not expect month/day to ever be detected
	if year:
		metadata.year = year
	revision = detect_things_from_filename.get_revision_from_filename_tags(name_tags)
	if revision:
		metadata.specific_info['Revision'] = revision
	version = detect_things_from_filename.get_version_from_filename_tags(name_tags)
	if version:
		metadata.specific_info['Version'] = version

	platform, assumed_media_type = get_platform_mediatype_from_tags(name_tags)
	if platform and main_config.use_original_platform:
		metadata.platform = platform
	if assumed_media_type:
		metadata.media_type = assumed_media_type

	for tag in name_tags:
		tag = tag.lstrip('(').rstrip(')')

		if tag in ('Demo', 'Linux Demo', 'CD Demo'):
			metadata.categories = ['Trials']
		if tag == 'Non-Interactive Demo':
			#One day, I'll think of some kind of standard for the categories names, but until then I've decided everything non-interactive should be in Demos
			metadata.categories = ['Demos']
		if tag in ('CD', 'CD Demo') or tag.endswith(' cd'):
			#The latter shows up alongside a version number infrequently, e.g. "v0.0372 cd"
			metadata.media_type = MediaType.OpticalDisc
		if tag == '1.1':
			#Oddball version number tag
			metadata.specific_info['Version'] = 'v1.1'

		#Versions: Freeware v1.1, Freeware v1.0
		#Others: final, VGA, EGA, Masterpiece Edition, Talkie, Latest version, unknown version
		
class ScummVMGame():
	def __init__(self, name):
		#The [game-name] is also user-modifiable and shouldn't be relied on to mean anything, but it is used for scummvm to actually launch the game and can be trusted to be unique
		self.name = name
		self.options = {}

	@staticmethod
	def _engine_list_to_use():
		return vmconfig.scummvm_engines

	def _get_launch_params(self):
		return 'scummvm', ['-f', self.name]

	@staticmethod
	def _get_emulator_name():
		return 'ScummVM'

	def make_launcher(self):
		#Note that I actually shouldn't rely on this, because it can be changed by the user
		name = self.options.get('description', self.name)
		name = name.replace('/', ') (') #Names are usually something like Cool Game (CD/DOS/English); we convert it to Cool Game (CD) (DOS) (English) to make it work better with disambiguate etc

		launch_params = launchers.LaunchParams(*self._get_launch_params())
		metadata = Metadata()
		metadata.input_info.add_option([input_metadata.Mouse(), input_metadata.Keyboard()]) #Can use gamepad if you enable it, but I guess to add that as input_info I'd have to know exactly how many buttons and sticks etc it uses
		metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		metadata.emulator_name = self._get_emulator_name()
		metadata.categories = ['Games'] #Safe to assume this by default
		if self.options.get('gameid') == 'agi-fanmade':
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

		engine_id = self.options.get('engineid')
		metadata.specific_info['Engine'] = self._engine_list_to_use().get(engine_id)

		path = self.options.get('path')
		if path:
			if os.path.isdir(path):
				for f in os.listdir(path):
					if f.lower().endswith('.ico'):
						metadata.images['Icon'] = os.path.join(path, f)
						break
					if f.lower() in ('icon.png', 'icon.xpm'):
						metadata.images['Icon'] = os.path.join(path, f)
						break
			else:
				if main_config.debug:
					print('Aaaa!', self.name, path, 'does not exist')

		name_tags = find_filename_tags.findall(name)
		get_stuff_from_filename_tags(metadata, name_tags)

		#Hmm, could use ResidualVM as the launcher type for ResidualVM games... but it's just a unique identifier type thing, so it should be fine
		launchers.make_launcher(launch_params, name, metadata, 'ScummVM', self.name)

class ResidualVMGame(ScummVMGame):
	@staticmethod
	def _get_emulator_name():
		return 'ResidualVM'

	@staticmethod
	def _engine_list_to_use():
		return vmconfig.residualvm_engines

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
			#Skip the top section that just says [scummvm]/[residualvm]
			continue
		if section == 'cloud':
			#This is not a game either
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
