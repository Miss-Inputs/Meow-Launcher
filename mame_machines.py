#!/usr/bin/env python3

import subprocess
import configparser
import os
import sys
import re

import config
import launchers
from info import emulator_info
from metadata import Metadata, EmulationStatus, CPUInfo, ScreenInfo, PlayerInput, InputType, SaveType
from region_detect import get_language_by_english_name

from mame_helpers import get_mame_xml, find_main_cpu

debug = '--debug' in sys.argv

icon_line_regex = re.compile(r'^icons_directory\s+(.+)$')
def get_icon_directories():
	ui_config_path = os.path.expanduser('~/.mame/ui.ini')
	if not os.path.isfile(ui_config_path):
		return None

	with open(ui_config_path, 'rt') as ui_config:
		for line in ui_config.readlines():
			icon_line_match = icon_line_regex.match(line)
			if icon_line_match:
				#I ain't about that relative path life fam
				return [dir for dir in icon_line_match[1].split(';') if dir.startswith('/')]

	return None

icon_directories = get_icon_directories()

def load_icons():
	d = {}
	for icon_directory in icon_directories:
		if os.path.isdir(icon_directory):
			for icon_file in os.listdir(icon_directory):
				name, ext = os.path.splitext(icon_file)
				if ext == '.ico':
					d[name] = os.path.join(icon_directory, icon_file)
	
	return d
icons = load_icons()

class Machine():
	def __init__(self, xml):
		self.xml = xml
		self.basename = xml.attrib['name']
		self.family = xml.attrib['cloneof'] if 'cloneof' in xml.attrib else self.basename
		self.name = xml.findtext('description')
		self.metadata = Metadata()

		self.source_file = os.path.splitext(xml.attrib['sourcefile'])[0]
		self.metadata.specific_info['Source-File'] = self.source_file

	def make_launcher(self):
		icon = None
		if icons:
			icon = icons.get(self.basename)
			if not icon:
				icon = icons.get(self.family)

		command_line = emulator_info.make_mame_command_line(self.basename)
		launchers.make_launcher(command_line, self.name, self.metadata, icon)

def mame_verifyroms(basename):
	#FIXME Okay this is way too fuckin' slow
	try:
		subprocess.run(['mame', '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
		return True
	except subprocess.CalledProcessError:
		return False	

def get_catlist():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.catlist_path)
	return parser
	
def get_languages():
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.languages_path)
	return parser

catlist = get_catlist()
languages = get_languages()

def get_category(basename):
	cat = None
	for section in catlist.sections():
		if basename in catlist[section]:
			cat = section
			break
	if not cat:
		return 'Unknown', 'Unknown', 'Unknown', 'Unknown'

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_nsfw = False
		if subgenre.endswith('* Mature *'):
			is_nsfw = True
			subgenre = subgenre[:-10]
		
		return category, genre, subgenre, is_nsfw
	
	category, _, genre = cat.partition(' / ')
	return category, genre, None, False
		
def get_language(basename):
	lang = None
	for section in languages.sections():
		if basename in languages[section]:
			lang = section
			break
			
	return get_language_by_english_name(lang)

def add_machine_platform(machine):
	machine.metadata.platform = 'Arcade'
	category = machine.metadata.categories[0]

	if machine.source_file == 'megatech':
		machine.metadata.platform = 'Mega-Tech'
	elif machine.source_file == 'megaplay':
		machine.metadata.platform = 'Mega-Play'
	elif machine.source_file == 'playch10':
		machine.metadata.platform = 'PlayChoice-10'
	elif machine.source_file == 'nss':
		machine.metadata.platform = 'Nintendo Super System'
	elif category == 'Game Console':
		machine.metadata.platform = 'Plug & Play' 
		#Since we're skipping over stuff with software lists, anything that's still classified as a game console is a plug &
        #play system
	elif category == 'Handheld':
		machine.metadata.platform = 'Handheld' 
		#Could also be a tabletop system which takes AC input, but since catlist.ini doesn't take that into account, I don't
		#really have a way of doing so either
		if machine.name.startswith('Game & Watch: '):
			#Source file is hh_sm510 so we can't detect the Game & Watchiness of a handheld game from that
			machine.metadata.platform, _, machine.name = machine.name.partition(': ')
	elif category == 'Misc.':
		machine.metadata.platform = machine.metadata.genre
	elif category == 'Computer':
		machine.metadata.platform = 'Computer'
	elif machine.metadata.genre in ('Electromechanical', 'Slot Machine') and machine.metadata.subgenre == 'Reels':
		machine.metadata.platform = 'Pokies'
	elif machine.metadata.genre == 'Electromechanical' and machine.metadata.subgenre == 'Pinball':
		machine.metadata.platform = 'Pinball'

#Some games have memory card slots, but they don't actually support saving, it's just that the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']

def add_metadata(machine):
	category, genre, subgenre, nsfw = get_category(machine.basename)
	machine.metadata.categories = [category] if category else ['Unknown']
	machine.metadata.genre = genre
	machine.metadata.subgenre = subgenre
	machine.metadata.nsfw = nsfw

	main_cpu = find_main_cpu(machine.xml)
	if main_cpu is not None: #Why?
		machine.metadata.cpu_info = CPUInfo()
		machine.metadata.cpu_info.load_from_xml(main_cpu)

	machine.metadata.screen_info = ScreenInfo()
	displays = machine.xml.findall('display')
	machine.metadata.screen_info.load_from_xml_list(displays)
	
	memory_cards = [device for device in machine.xml.findall('device') if device.find('instance') is not None and device.find('instance').attrib['name'] == 'memcard']
	machine.metadata.save_type = SaveType.MemoryCard if memory_cards and (machine.family not in not_actually_save_supported) else SaveType.Nothing
	#TODO: Some machines that aren't arcade systems might plausibly have something describable as SaveType.Cart or SaveType.Internal... anyway, I guess I'll burn that bridge when I see it
	
	add_machine_platform(machine)

	language = get_language(machine.basename)
	if language:
		machine.metadata.languages = [language]
	
	machine.metadata.emulator_name = 'MAME'
	machine.metadata.year = machine.xml.findtext('year')
	machine.metadata.author = machine.xml.findtext('manufacturer')
	
	emulation_status = machine.xml.find('driver').attrib['status']
	if emulation_status == 'good':
		machine.metadata.emulation_status = EmulationStatus.Good
	elif emulation_status == 'imperfect':
		machine.metadata.emulation_status = EmulationStatus.Imperfect
	elif emulation_status == 'preliminary':
		machine.metadata.emulation_status = EmulationStatus.Broken	

def add_input_info(machine):
	#TODO: Yeah, yeah... should actually have a setter on the class
	machine.metadata.input_info._known = True
	input_element = machine.xml.find('input')
	if input_element is None:
		#Seems like this doesn't actually happen
		if debug:
			print('Oi m8', machine.basename, '/', machine.name, 'has no input')
		return

	if 'players' not in input_element.attrib:
		return

	num_players = int(input_element.attrib['players'])
	if num_players == 0:
		return

	if machine.metadata.platform == 'Arcade':
		#We shouldn't assume this, but let's assume that all arcade games have one coin slot and one start button, although that's not necessarily the case anyway.
		#If it's some other kind of system, feels like I'm assuming nothing at all
		machine.metadata.input_info.console_buttons += 2
	
	for i in range(num_players):
		machine.metadata.input_info.players.append(PlayerInput())

	control_elements = input_element.findall('control')
	if not control_elements:
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in
		for i in range(num_players):
			machine.metadata.input_info.players[i].inputs = [InputType.Custom]
		return

	for control in control_elements:
		player_num = 1
		#The player number isn't really specified if there's only one, so assume player 1 by default
		if 'player' in control.attrib:
			player_num = int(control.attrib['player'])
		player = machine.metadata.input_info.players[player_num - 1]

		buttons = 0
		if 'buttons' in control.attrib:
			buttons = int(control.attrib['buttons'])

		#TODO: This very much needs some refactoring, I just can't really brain think at the moment
		input_type = control.attrib['type']
		if input_type == 'only_buttons':
			player.buttons += buttons
		elif input_type == 'joy':
			player.buttons += buttons
			player.inputs.append(InputType.Digital)
		elif input_type == 'doublejoy':
			player.buttons += buttons
			player.inputs += [InputType.Digital] * 2
		elif input_type == 'triplejoy':
			player.buttons += buttons
			player.inputs += [InputType.Digital] * 3
		elif input_type == 'paddle':
			player.buttons += buttons
			if machine.metadata.genre == 'Driving':
				#Yeah this looks weird and hardcody and dodgy but am I wrong
				player.inputs.append(InputType.SteeringWheel)
			else:
				player.inputs.append(InputType.Paddle)
		elif input_type == 'stick':
			player.buttons += buttons
			player.inputs.append(InputType.Analog)
		elif input_type == 'pedal':
			player.buttons += buttons
			player.inputs.append(InputType.Pedal)
		elif input_type == 'lightgun':
			player.buttons += buttons
			#TODO: See if we can be clever and detect if this is actually a touchscreen, like platform = handheld or something
			player.inputs.append(InputType.LightGun)
		elif input_type == 'positional':
			player.buttons += buttons
			#What _is_ a positional exactly
			player.inputs.append(InputType.Positional)
		elif input_type == 'dial':
			player.buttons += buttons
			player.inputs.append(InputType.Dial)
		elif input_type == 'trackball':
			player.buttons += buttons
			player.inputs.append(InputType.Trackball)
		elif input_type == 'mouse':
			player.buttons += buttons
			player.inputs.append(InputType.Mouse)
		elif input_type == 'keypad':
			player.inputs.append(InputType.Keypad)
		elif input_type == 'keyboard':
			player.inputs.append(InputType.Keyboard)
		elif input_type == 'mahjong':
			player.inputs.append(InputType.Mahjong)
		elif input_type == 'hanafuda':
			player.inputs.append(InputType.Hanafuda)
		elif input_type == 'gambling':
			player.buttons += buttons
			player.inputs.append(InputType.Gambling)
		else:
			player.buttons += buttons
			player.inputs.append(InputType.Custom)
		
	
def should_process_machine(machine):
	if machine.xml.attrib['runnable'] == 'no':
		return False

	if machine.xml.attrib['isbios'] == 'yes':
		return False

	if machine.xml.attrib['isdevice'] == 'yes':
		return False

	return True

def process_machine(machine):
	if not should_process_machine(machine):
		return
		
	if not (machine.xml.find('softwarelist') is None) and machine.family not in config.okay_to_have_software:
		return

	machine.metadata.specific_info['Family'] = machine.family

	add_metadata(machine)
	add_input_info(machine)
	if not machine.metadata.input_info.players:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
		if debug:
			print('Skipping %s (%s) as it has no controls' % (machine.basename, machine.name))
		return

	machine.make_launcher()
		
def get_mame_drivers():
	drivers = []

	process = subprocess.run(['mame', '-listsource'], stdout=subprocess.PIPE, universal_newlines=True)
	status = process.returncode
	output = process.stdout
	if status != 0:
		print('Shit')
		return []

	for line in output.splitlines():
		try:		
			driver, source_file = line.split(None, 1)
			drivers.append((driver, os.path.splitext(source_file)[0]))
		except ValueError:
			print('For fucks sake ' + line)
			continue	

	return drivers

def process_arcade():
	#Fuck iterparse by the way, if you stumble across this script and think "oh you should use iterparse instead of this
	#kludge!" you are wrong
	#(Okay, if you want an attempt at a reason why: I've tried it, and MAME's machine elements are actually more
	#complicated and seemingly refer to other machine elements that are displayed alongside the main one with an
	#individual -listxml)
	#Could it be faster to use -verifyroms globally and parse the output somehow and then get individual XML from
	#successful results?

	for driver, source_file in get_mame_drivers():
		if source_file in config.skipped_source_files:
			continue

		#You probably think this is why it's slow, right?  You think "Oh, that's silly, you're verifying every single romset
		#in existence before just getting the XML", that's what you're thinking, right?  Well, I am doing that, but as it
		#turns out if I do the verification inside process_machine it takes a whole lot longer.  I don't fully understand why
		#but I'll have you know I actually profiled it
		if not mame_verifyroms(driver):
			continue

		xml = get_mame_xml(driver)
		if xml is None:
			continue
		process_machine(Machine(xml.find('machine')))

if __name__ == '__main__':
	os.makedirs(config.output_folder, exist_ok=True)
	process_arcade()
