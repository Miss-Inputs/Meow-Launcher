#!/usr/bin/env python3

import os 
import configparser

import launchers
from metadata import Metadata, PlayerInput, InputType, SaveType

config_path = os.path.expanduser('~/.config/scummvm/scummvm.ini')

class ScummVMGame():
	def __init__(self, name):
		self.name = name
		self.options = {}

	def make_launcher(self):
		name = self.options.get('description', self.name)
		command = 'scummvm -f {0}'.format(self.name)
		metadata = Metadata()
		player = PlayerInput()
		player.inputs = [InputType.Mouse, InputType.Keyboard] #Can use gamepad if you enable it
		metadata.input_info.players.append(player)
		metadata.save_type = SaveType.Internal #Saves to your own dang computer so I guess that counts
		#TODO: publisher, categories, languages, nsfw, regions, subgenre, year... somehow
		#Others are left deliberately blank because they refer to emulators and not engines
		launchers.make_launcher(command, name, metadata, {'Game-ID': self.name})

def add_scummvm_games():
	if not os.path.isfile(config_path):
		return	

	parser = configparser.ConfigParser()
	parser.optionxform = str
	parser.read(config_path)
	
	for section in parser.sections():
		if section == 'scummvm':
			continue

		game = ScummVMGame(section)
		for k, v in parser.items(section):
			game.options[k] = v
		game.make_launcher()

if __name__ == '__main__':
	add_scummvm_games()
