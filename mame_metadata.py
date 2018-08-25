import configparser
import re
import sys

import config
from metadata import EmulationStatus, CPUInfo, ScreenInfo, PlayerInput, InputType, SaveType
from region_detect import get_language_by_english_name, get_regions_from_filename_tags
from common import find_filename_tags
from mame_helpers import find_main_cpu, consistentify_manufacturer

debug = '--debug' in sys.argv

def get_catlist():
	if not config.catlist_path:
		return None
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.catlist_path)
	return parser
	
def get_languages():
	if not config.languages_path:
		return None
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
	parser.optionxform = str
	parser.read(config.languages_path)
	return parser

catlist = get_catlist()
languages = get_languages()

def get_category(basename):
	cat = None
	if catlist:
		for section in catlist.sections():
			if basename in catlist[section]:
				cat = section
				break
	if not cat:
		return 'Unknown', 'Unknown', 'Unknown', False

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
	if not languages:
		return None

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
	elif machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		#Source file is hh_sm510 so we can't detect the Game & Watchiness of a handheld game from that
		machine.metadata.platform, _, machine.name = machine.name.partition(': ')
	elif category == 'Misc.':
		machine.metadata.platform = machine.metadata.genre
	elif category == 'Handheld' and machine.metadata.genre == "Plug n' Play TV Game":
		machine.metadata.platform = "Plug & Play"
	elif category in ('Computer', 'Calculator', 'Handheld'):
		#"Handheld" could also be a tabletop system which takes AC input, but since catlist.ini doesn't take that into account, I don't
		#really have a way of doing so either
		machine.metadata.platform = category
	elif machine.metadata.genre in ('Electromechanical', 'Slot Machine') and machine.metadata.subgenre == 'Reels':
		machine.metadata.platform = 'Pokies'
	elif machine.metadata.genre == 'Electromechanical' and machine.metadata.subgenre == 'Pinball':
		machine.metadata.platform = 'Pinball'
	elif machine.metadata.genre in ('Chess Machine', 'EPROM Programmer'):
		machine.metadata.platform = machine.metadata.genre

#Some games have memory card slots, but they don't actually support saving, it's just that the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']
licensed_arcade_game_regex = re.compile(r'^(.+?) \((.+?) license\)$')
licensed_from_regex = re.compile(r'^(.+?) \(licensed from (.+?)\)$')
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

	add_machine_platform(machine)
	
	if machine.metadata.platform == 'Arcade':
		memory_cards = [device for device in machine.xml.findall('device') if device.find('instance') is not None and device.find('instance').attrib['name'] == 'memcard']
		machine.metadata.save_type = SaveType.MemoryCard if memory_cards and (machine.family not in not_actually_save_supported) else SaveType.Nothing
		#TODO: Some machines that aren't arcade systems might plausibly have something describable as SaveType.Cart or SaveType.Internal... anyway, I guess I'll burn that bridge when I see it
	

	language = get_language(machine.basename)
	if language:
		machine.metadata.languages = [language]

	machine.metadata.regions = get_regions_from_filename_tags(find_filename_tags.findall(machine.name), loose=True)
	
	machine.metadata.emulator_name = 'MAME'
	machine.metadata.year = machine.xml.findtext('year')
	manufacturer = machine.xml.findtext('manufacturer')
	license_match = licensed_arcade_game_regex.fullmatch(manufacturer)
	licensed_from_match = licensed_from_regex.fullmatch(manufacturer)
	if license_match:
		developer = license_match[1]
		publisher = license_match[2]
	elif licensed_from_match:
		developer = manufacturer
		publisher = licensed_from_match[1]
		machine.metadata.specific_info['Licensed-From'] = licensed_from_match[2]
	else:
		if not manufacturer.startswith(('bootleg', 'hack')):
			#TODO: Not always correct in cases where manufacturer is formatted as "Developer / Publisher", but then it never was correct, so it's just less not correct, which is fine
			developer = manufacturer
		else:
			developer = None #It'd be the original not-bootleg game's developer but we can't get that programmatically
		publisher = manufacturer
	machine.metadata.developer = consistentify_manufacturer(developer)
	machine.metadata.publisher = consistentify_manufacturer(publisher)

	emulation_status = machine.xml.find('driver').attrib['status']
	if emulation_status == 'good':
		machine.metadata.specific_info['MAME-Emulation-Status'] = EmulationStatus.Good
	elif emulation_status == 'imperfect':
		machine.metadata.specific_info['MAME-Emulation-Status'] = EmulationStatus.Imperfect
	elif emulation_status == 'preliminary':
		machine.metadata.specific_info['MAME-Emulation-Status'] = EmulationStatus.Broken	

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
		