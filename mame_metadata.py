import configparser
import re
import sys

import config
import input_metadata
from info.system_info import MediaType
from metadata import EmulationStatus, CPUInfo, ScreenInfo, SaveType
from region_detect import get_language_by_english_name, get_regions_from_filename_tags
from common import find_filename_tags
from mame_helpers import find_main_cpu, consistentify_manufacturer

debug = '--debug' in sys.argv

mame_statuses = {
	'good': EmulationStatus.Good,
	'imperfect': EmulationStatus.Imperfect,
	'preliminary': EmulationStatus.Broken,
}

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
	elif machine.source_file == 'cps1' and '(CPS Changer, ' in machine.name:
		machine.metadata.platform = 'CPS Changer'
		machine.name = machine.name.replace('CPS Changer, ', '')
		machine.metadata.media_type = MediaType.Cartridge
	elif category == 'Game Console':
		machine.metadata.platform = 'Plug & Play'
		#Since we're skipping over stuff with software lists, anything that's still classified as a game console is a plug &
        #play system
	elif machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		machine.metadata.platform, _, machine.name = machine.name.partition(': ')
		if machine.metadata.platform in ('Select-A-Game', 'R-Zone'):
			machine.metadata.media_type = MediaType.Cartridge
	elif category == 'Misc.':
		machine.metadata.platform = machine.metadata.genre
	elif category == 'Handheld' and machine.metadata.genre == "Plug n' Play TV Game":
		machine.metadata.platform = "Plug & Play"
	elif category in ('Computer', 'Calculator', 'Handheld', 'Telephone'):
		#"Handheld" could also be a tabletop system which takes AC input, but since catlist.ini doesn't take that into account, I don't
		#really have a way of doing so either
		machine.metadata.platform = category
	elif machine.metadata.genre in ('Electromechanical', 'Slot Machine') and machine.metadata.subgenre == 'Reels':
		machine.metadata.platform = 'Pokies'
	elif machine.metadata.genre == 'Electromechanical' and machine.metadata.subgenre == 'Pinball':
		machine.metadata.platform = 'Pinball'
	elif machine.metadata.genre in ('Chess Machine', 'EPROM Programmer', 'Home Karaoke System'):
		machine.metadata.platform = machine.metadata.genre

#Some games have memory card slots, but they don't actually support saving, it's just that the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']
licensed_arcade_game_regex = re.compile(r'^(.+?) \((.+?) license\)$')
licensed_from_regex = re.compile(r'^(.+?) \(licensed from (.+?)\)$')

def add_save_type(machine):
	if machine.metadata.platform == 'Arcade':
		memory_cards = [device for device in machine.xml.findall('device') if device.find('instance') is not None and device.find('instance').attrib['name'] == 'memcard']
		machine.metadata.save_type = SaveType.MemoryCard if memory_cards and (machine.family not in not_actually_save_supported) else SaveType.Nothing
		#TODO: Some machines that aren't arcade systems might plausibly have something describable as SaveType.Cart or SaveType.Internal... anyway, I guess I'll burn that bridge when I see it

def add_manufacturer(machine):
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

def add_status(machine):
	driver = machine.xml.find('driver')
	#Overall status
	machine.metadata.specific_info['MAME-Emulation-Status'] = mame_statuses.get(driver.attrib['status'], EmulationStatus.Unknown)
	#I guess I gotta think of better names for this stuff
	machine.metadata.specific_info['MAME-Actual-Emulation-Status'] = mame_statuses.get(driver.attrib['emulation'], EmulationStatus.Unknown)

	unemulated_features = []
	for feature in machine.xml.findall('feature'):
		feature_type = feature.attrib['type']
		if 'status' in feature.attrib:
			feature_status = feature.attrib['status']
		elif 'overall' in feature.attrib:
			#wat?
			feature_status = feature.attrib['overall']
		else:
			continue

		if feature_status == 'unemulated':
			unemulated_features.append(feature_type)
		elif feature_type == 'graphics':
			machine.metadata.specific_info['MAME-Graphics-Status'] = mame_statuses.get(feature_status, EmulationStatus.Unknown)
		elif feature_type == 'sound':
			machine.metadata.specific_info['MAME-Sound-Status'] = mame_statuses.get(feature_status, EmulationStatus.Unknown)

	if unemulated_features:
		machine.metadata.specific_info['MAME-Unemulated-Features'] = unemulated_features

def add_metadata(machine):
	category, genre, subgenre, nsfw = get_category(machine.basename)
	machine.metadata.categories = [category] if category else ['Unknown']
	machine.metadata.genre = genre
	machine.metadata.subgenre = subgenre
	machine.metadata.nsfw = nsfw

	machine.metadata.specific_info['Is-Mechanical'] = machine.xml.attrib.get('ismechanical', 'no') == 'yes'

	main_cpu = find_main_cpu(machine.xml)
	if main_cpu is not None: #Why?
		machine.metadata.cpu_info = CPUInfo()
		machine.metadata.cpu_info.load_from_xml(main_cpu)

	machine.metadata.screen_info = ScreenInfo()
	displays = machine.xml.findall('display')
	machine.metadata.screen_info.load_from_xml_list(displays)

	machine.metadata.media_type = MediaType.Standalone

	add_machine_platform(machine)
	add_save_type(machine)

	language = get_language(machine.basename)
	if language:
		machine.metadata.languages = [language]

	machine.metadata.regions = get_regions_from_filename_tags(find_filename_tags.findall(machine.name), loose=True)

	machine.metadata.emulator_name = 'MAME'
	machine.metadata.year = machine.xml.findtext('year')
	add_manufacturer(machine)

	add_status(machine)


def add_input_info(machine):
	machine.metadata.input_info.set_known()
	input_element = machine.xml.find('input')
	if input_element is None:
		#Seems like this doesn't actually happen
		if debug:
			print('Oi m8', machine.basename, '/', machine.name, 'has no input')
		return

	if 'players' not in input_element.attrib:
		machine.metadata.specific_info['Probably-Skeleton-Driver'] = True
		return

	num_players = int(input_element.attrib['players'])
	if num_players == 0:
		machine.metadata.specific_info['Probably-Skeleton-Driver'] = True
		return

	machine.metadata.specific_info['Number-of-Players'] = num_players

	control_elements = input_element.findall('control')
	if not control_elements:
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in
		machine.metadata.input_info.add_option([input_metadata.Custom()])
		return

	input_option = input_metadata.InputOption()

	for control in control_elements:
		buttons = int(control.attrib.get('buttons', 0))

		if control.attrib.get('player', '1') != '1':
			#I care not for these "other people" and "social interaction" concepts
			#Anyway, this would only matter for stuff like Lucky & Wild, and... not sure what I'm gonna do about that, because we wanna avoid doubling up on input types where number of players > 1
			continue

		#Still kinda feel like this is messy but ehhh
		input_type = control.attrib['type']
		if input_type == 'only_buttons':
			normal_input = input_metadata.NormalInput()
			normal_input.face_buttons = buttons
			input_option.inputs.append(normal_input)
		elif input_type == 'joy':
			normal_input = input_metadata.NormalInput()
			normal_input.face_buttons = buttons
			normal_input.dpads = 1
			input_option.inputs.append(normal_input)
		elif input_type == 'doublejoy':
			normal_input = input_metadata.NormalInput()
			normal_input.face_buttons = buttons
			normal_input.dpads = 2
			input_option.inputs.append(normal_input)
		elif input_type == 'triplejoy':
			normal_input = input_metadata.NormalInput()
			normal_input.face_buttons = buttons
			normal_input.dpads = 3
			input_option.inputs.append(normal_input)
		elif input_type == 'paddle':
			if machine.metadata.genre == 'Driving':
				#Yeah this looks weird and hardcody and dodgy but am I wrong
				input_option.inputs.append(input_metadata.SteeringWheel())
			else:
				input_option.inputs.append(input_metadata.Paddle())
		elif input_type == 'stick':
			normal_input = input_metadata.NormalInput()
			normal_input.analog_sticks = 1
			normal_input.face_buttons = buttons
			input_option.inputs.append(normal_input)
		elif input_type == 'pedal':
			input_option.inputs.append(input_metadata.Pedal())
		elif input_type == 'lightgun':
			#TODO: See if we can be clever and detect if this is actually a touchscreen, like platform = handheld or something
			input_option.inputs.append(input_metadata.LightGun())
		elif input_type == 'positional':
			#What _is_ a positional exactly
			input_option.inputs.append(input_metadata.Positional())
		elif input_type == 'dial':
			input_option.inputs.append(input_metadata.Dial())
		elif input_type == 'trackball':
			input_option.inputs.append(input_metadata.Trackball())
		elif input_type == 'mouse':
			input_option.inputs.append(input_metadata.Mouse())
		elif input_type == 'keypad':
			input_option.inputs.append(input_metadata.Keypad())
		elif input_type == 'keyboard':
			input_option.inputs.append(input_metadata.Keyboard())
		elif input_type == 'mahjong':
			input_option.inputs.append(input_metadata.Mahjong())
		elif input_type == 'hanafuda':
			input_option.inputs.append(input_metadata.Hanafuda())
		elif input_type == 'gambling':
			input_option.inputs.append(input_metadata.Gambling())
		else:
			input_option.inputs.append(input_metadata.Custom())

		machine.metadata.input_info.input_options = [input_option]
