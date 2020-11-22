#!/usr/bin/env python3

import os

import launchers
import pc_common_metadata
from common_types import MediaType
from config.main_config import main_config
from metadata import Metadata


class GOGGameInfo():
	def __init__(self, path):
		self.name = None
		self.version = None
		self.dev_version = None
		#Sometimes games only have those 3
		self.language = None
		self.gameid = None
		#GameID is duplicated, and then there's some other ID?
		with open(path, 'rt') as f:
			lines = f.read().splitlines()
			try:
				self.name = lines[0]
				self.version = lines[1]
				self.dev_version = lines[2]
				self.language = lines[3]
				self.gameid = lines[4]
			except IndexError:
				pass

class GOGGame():
	def __init__(self, game_folder, info, start_script, support_folder):
		self.folder = game_folder
		self.info = info
		self.start_script = start_script
		self.support_folder = support_folder #Is this necessary to pass as an argument? I guess not but I've already found it in look_in_linux_gog_folder
		
		self.name = pc_common_metadata.fix_name(self.info.name)
		self.metadata = Metadata()

	def add_metadata(self):
		icon = self.icon
		if icon:
			self.metadata.images['Icon'] = icon
		self.metadata.specific_info['Version'] = self.info.version
		self.metadata.specific_info['Dev-Version'] = self.info.dev_version
		#self.metadata.specific_info['Language-Code'] = self.info.language
		self.metadata.specific_info['GOG-ProductID'] = self.info.gameid

		self.metadata.platform = 'Linux' #TODO: Option to have this as "GOG"
		self.metadata.media_type = MediaType.Digital
		self.metadata.categories = ['Trials'] if self.is_demo else ['Games'] #There are movies on GOG but I'm not sure how they work, no software I think
		#Dang… everything else would require the API, I guess

	@property
	def icon(self):
		for icon_ext in pc_common_metadata.icon_extensions:
			icon_path = os.path.join(self.support_folder, 'icon' + os.extsep + icon_ext)
			if os.path.isfile(icon_path):
				return icon_path
		return None

	@property
	def is_demo(self):
		#The API doesn't even say this for a given product ID, we'll just have to figure it out ourselves
		if self.info.version and 'demo' in self.info.version.lower():
			return True
		if self.info.dev_version and 'demo' in self.info.dev_version.lower():
			return True
		for demo_suffix in pc_common_metadata.demo_suffixes:
			if '({0})'.format(demo_suffix.lower()) in self.name.lower():
				return True
		return False

	def make_launcher(self):
		params = launchers.LaunchParams(self.start_script, [])
		launchers.make_launcher(params, self.name, self.metadata, 'GOG', self.folder)

class NormalGOGGame(GOGGame):
	def add_metadata(self):
		super().add_metadata()
		engine = pc_common_metadata.try_and_detect_engine_from_folder(os.path.join(self.folder, 'game'))
		if engine:
			self.metadata.specific_info['Engine'] = engine

class DOSBoxGOGGame(GOGGame):
	#TODO: Let user use native DOSBox
	def add_metadata(self):
		super().add_metadata()
		self.metadata.specific_info['Wrapper'] = 'DOSBox'

class ScummVMGOGGame(GOGGame):
	#TODO: Let user use native ScummVM
	def add_metadata(self):
		super().add_metadata()
		self.metadata.specific_info['Wrapper'] = 'ScummVM'

#I think there can be Wine bundled with a game sometimes too?

def look_in_linux_gog_folder(folder):
	gameinfo_path = os.path.join(folder, 'gameinfo')
	if not os.path.isfile(gameinfo_path):
		return None
	gameinfo = GOGGameInfo(gameinfo_path)

	launch_script = os.path.join(folder, 'start.sh')
	if not os.path.isfile(launch_script):
		return None

	#.mojosetup, uninstall-*.sh, docs are also here
	support_folder = os.path.join(folder, 'support')
	if not os.path.isdir(support_folder):
		return None

	if os.path.isdir(os.path.join(folder, 'dosbox')):
		return DOSBoxGOGGame(folder, gameinfo, launch_script, support_folder)
	if os.path.isdir(os.path.join(folder, 'scummvm')):
		return ScummVMGOGGame(folder, gameinfo, launch_script, support_folder)
	if os.path.isdir(os.path.join(folder, 'game')):
		return NormalGOGGame(folder, gameinfo, launch_script, support_folder)

	return None

def do_gog_games():
	for gog_folder in main_config.gog_folders:
		for subfolder in os.listdir(gog_folder):
			path = os.path.join(gog_folder, subfolder)
			if not os.path.isdir(path):
				continue
			game = look_in_linux_gog_folder(path)
			if not game:
				if main_config.debug:
					print('GOG subfolder does not have a GOG game (detection may have failed)', path)

			game.add_metadata()
			game.make_launcher()

if __name__ == '__main__':
	do_gog_games()
