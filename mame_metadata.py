import configparser
import functools
import os

import detect_things_from_filename
import input_metadata
from common import find_filename_tags, pluralize
from common_types import MediaType, SaveType
from config import main_config
from info.region_info import (get_language_by_english_name,
                              get_language_from_regions)
from mame_helpers import find_cpus, get_mame_ui_config
from metadata import CPU, EmulationStatus, ScreenInfo

#Maybe I just want to put all this back into mame_machines... it's only used there

mame_statuses = {
	'good': EmulationStatus.Good,
	'imperfect': EmulationStatus.Imperfect,
	'preliminary': EmulationStatus.Broken,
}

def get_mame_categories_folders():
	ui_config = get_mame_ui_config()
	return ui_config.get('categorypath')

@functools.lru_cache(maxsize=None)
def get_mame_folder(name):
	mame_categories_folders = get_mame_categories_folders()
	if not mame_categories_folders:
		return None
	
	#TODO: strict=False is there to prevent DuplicateOptionError, but it seems like this should indicate to me that configparser might not actually be the best tool for the job, maybe just write a custom thing to do it?
	parser = configparser.ConfigParser(interpolation=None, allow_no_value=True, strict=False)
	parser.optionxform = str
		
	for folder in mame_categories_folders:
		category_file_path = os.path.join(folder, name + '.ini')

		#This won't fail if category_file_path doesn't exist, so I guess it's fine
		parser.read(category_file_path)
	
	return parser

def get_machine_folder(basename, folder_name):
	folder = get_mame_folder(folder_name)

	sections = []
	for section in folder.sections():
		if basename in folder[section]:
			sections.append(section)
	return sections

def get_category(basename):
	cats = get_machine_folder(basename, 'catlist')
	#It would theoretically be possible for a machine to appear twice, but catlist doesn't do that I think
	if not cats:
		return 'Unknown', 'Unknown', 'Unknown', False
	cat = cats[0]

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_nsfw = False
		if subgenre.endswith('* Mature *'):
			is_nsfw = True
			subgenre = subgenre[:-10]

		return category, genre, subgenre, is_nsfw

	genre, _, subgenre = cat.partition(' / ')
	return None, genre, subgenre, False

def get_languages(basename):
	langs = get_machine_folder(basename, 'languages')
	if not langs:
		return None

	return [get_language_by_english_name(lang) for lang in langs]

#Some games have memory card slots, but they don't actually support saving, it's just t hat the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['diggerma', 'neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']

def add_save_type(machine):
	if machine.metadata.platform == 'Arcade':
		has_memory_card = False
		for media_slot in machine.media_slots:
			if not media_slot.instances: #Does this ever happen?
				continue
			if media_slot.type == 'memcard':
				has_memory_card = True

		has_memory_card = has_memory_card and (machine.family not in not_actually_save_supported)

		machine.metadata.save_type = SaveType.MemoryCard if has_memory_card else SaveType.Nothing
	else:
		has_nvram = machine.uses_device('nvram')
		has_i2cmem = machine.uses_device('i2cmem')

		#Assume that if there's non-volatile memory that it's used for storing some kind of save data, and not like... stuff
		#This may be wrong!!!!!!!!!!! but it seems to hold true for plug & play TV games and electronic handheld games so that'd be the main idea
		machine.metadata.save_type = SaveType.Internal if has_nvram or has_i2cmem else SaveType.Nothing

def add_status(machine):
	driver = machine.driver_element
	#See comments for overall_status property for what that actually means
	machine.metadata.specific_info['MAME-Overall-Emulation-Status'] = machine.overall_status
	machine.metadata.specific_info['MAME-Emulation-Status'] = machine.emulation_status
	machine.metadata.specific_info['Cocktail-Status'] = mame_statuses.get(driver.attrib.get('cocktail'), EmulationStatus.Good)
	machine.metadata.specific_info['Supports-Savestate'] = driver.attrib.get('savestate') == 'supported'

	unemulated_features = []
	for feature_type, feature_status in machine.feature_statuses.items():
		if feature_status == 'unemulated':
			unemulated_features.append(feature_type)
		else:
			#Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
			#Note: MAME 0.208 has added capture, media, tape, punch, drum, rom, comms; although I guess I don't need to write any more code here
			machine.metadata.specific_info['MAME-%s-Status' % feature_type.capitalize()] = mame_statuses.get(feature_status, EmulationStatus.Unknown)

	if unemulated_features:
		machine.metadata.specific_info['MAME-Unemulated-Features'] = unemulated_features

#Stealing this from mame_machines.py while I'm still using it there
#These all indicate something that _is_ a plug & play system if they exist
plug_and_play_software_lists = ('vii', 'jakks_gamekey', 'ekara')
def is_plug_and_play(machine):
	#"Game Console / Home Videogame Console" in catlist.ini doesn't differentiate between plug & play systems that are meant to be used by themselves, and normal consoles which are meant to be used by other software. So, we'll do that ourselves
	if machine.software_lists:
		for software_list in machine.software_lists:
			if software_list.startswith(plug_and_play_software_lists):
				return True
		return False

	#Hmm...
	return True

def add_metadata_from_catlist(machine):
	category, genre, subgenre, nsfw = get_category(machine.basename)
	if category == 'Unknown' and machine.has_parent:
		category, genre, subgenre, nsfw = get_category(machine.parent_basename)
	
	#Fix some errata present in the default catlist.ini, maybe one day I should tell them about it, but I'm shy or maybe they're meant to be like that
	if subgenre == 'Laser Disk Simulator':
		#Both of these spellings appear twice...
		subgenre = 'Laserdisc Simulator'
	if subgenre == 'Punched Car':
		subgenre = 'Punched Card'
	#ddrstraw is Rhythm / Dance but it's more accurately a plug & play game, although that is the genre, so it's not wrong
	#kuzmich is just Platform / Run Jump, it's an arcade machine though (but it kinda doesn't have coins at this point in time, and I dunno if it's supposed to, or it just be like that)
	#evio is Music / Instruments which is the genre, yes, but it is indeed plug & play. Hmm...
	
	machine.metadata.media_type = MediaType.Standalone

	if category == 'Unknown':
		#Not in catlist or user doesn't have catlist
		machine.metadata.genre = 'Unknown'
		machine.metadata.subgenre = 'Unknown'
	elif category:
		#'Arcade: ' or whatever else at the beginning
		machine.metadata.platform = category
		machine.metadata.genre = genre
		machine.metadata.subgenre = subgenre
		machine.metadata.nsfw = nsfw
	else:
		#Non-arcade thing
		machine.metadata.genre = genre
		machine.metadata.subgenre = subgenre

	filename_tags = find_filename_tags.findall(machine.name)
	for tag in filename_tags:
		if 'prototype' in tag.lower() or 'location test' in tag.lower():
			if machine.has_parent:
				if 'Unreleased' in machine.parent.metadata.categories:
					machine.metadata.categories = ['Unreleased']
				else:
					machine.metadata.categories = ['Betas']
			else:
				machine.metadata.categories = ['Unreleased']
			break
		if 'bootleg' in tag.lower():
			if machine.has_parent:
				if 'Unreleased' in machine.parent.metadata.categories:
					machine.metadata.categories = ['Bootleg']
				else:
					machine.metadata.categories = ['Hacks']
			else:
				machine.metadata.categories = ['Bootleg']
			break
		if 'hack' in tag.lower():
			machine.metadata.categories = ['Hacks']
	if machine.is_mechanical:
		machine.metadata.categories = ['Electromechanical']
	if machine.is_hack:
		machine.metadata.categories = ['Hacks']
	if machine.uses_device('coin_hopper'):
		#Redemption games sometimes also have one, but then they will have their category set later by their subgenre being Redemption
		machine.metadata.categories = ['Gambling']

	#Now we separate things into additional platforms where relevant

	#Home systems that have the whole CPU etc inside the cartridge, and hence work as separate systems in MAME instead of being in roms.py
	if machine.source_file == 'cps1' and '(CPS Changer, ' in machine.name:
		machine.name = machine.name.replace('CPS Changer, ', '')
		machine.metadata.platform = 'CPS Changer'
		machine.metadata.media_type = MediaType.Cartridge
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return 
	if machine.name.endswith('(XaviXPORT)'):
		machine.metadata.platform = 'XaviXPORT'
		machine.metadata.media_type = MediaType.Cartridge
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return
	if machine.name.endswith('(Domyos Interactive System)'):
		machine.metadata.platform = 'Domyos Interactive System'
		machine.metadata.media_type = MediaType.Cartridge
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return
	if machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		#Select-a-Game does not work this way since 0.221 but might as well keep that there for older versions
		platform, _, machine.name = machine.name.partition(': ')
		machine.metadata.platform = platform
		machine.metadata.media_type = MediaType.Cartridge if platform in ('Select-A-Game', 'R-Zone') else MediaType.Standalone
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return

	if (genre == 'Computer' and subgenre in ('Business - Terminal', 'Home System', 'Laptop - Notebook - Portable', 'Child Computer', 'Microcomputer')) or (genre == 'Calculator' and subgenre == 'Pocket Computer') or (genre == 'Handheld' and subgenre in ('Pocket Device - Pad - PDA', 'Child Computer')) or (genre == 'Board Game') or (genre == 'Utilities' and subgenre in ('Arcade System', 'Redemption Board')) or (genre == 'Misc.' and subgenre == 'Virtual Environment'):
		#Board Game is more like chess machines than actual board games
		#Hmm, need a better name for this I think
		machine.metadata.platform = 'Standalone System'
	if genre == 'Game Console' and subgenre == 'Home Videogame':
		if is_plug_and_play(machine):
			machine.metadata.platform = 'Plug & Play'
			if not machine.metadata.categories:
				machine.metadata.categories = ['Games']
		else:
			machine.metadata.platform = 'Standalone System'
	if genre == 'Utilities' and subgenre == 'Update':
		machine.metadata.categories = ['Applications']
	if genre == 'Misc.' and subgenre in ('Electronic Game', 'Electronic Board Game'):
		#"Electronic Game" could also be considered Handheld
		machine.metadata.platform = 'Board Game'
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
	if not category and ((genre == 'Handheld' and subgenre.startswith("Plug n' Play TV Game")) or (genre == 'Rhythm' and subgenre == 'Dance') or (genre == 'MultiGame' and subgenre == 'Compilation') or (genre == 'Game Console' and subgenre == 'Fitness Game') or (genre == 'Music' and subgenre == 'Instruments')):
		#MultiGame / Compilation is also used for some handheld systems (and also there is Arcade: MultiGame / Compilation)
		machine.metadata.platform = 'Plug & Play'
		if subgenre.startswith("Plug n' Play TV Game /"):
			#Oh hey we can actually have a genre now
			machine.metadata.genre = subgenre.split(' / ')[-1]
			machine.metadata.subgenre = None

		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
	if genre == 'Electromechanical' and subgenre == 'Pinball':
		#There are a few things under Arcade: Electromechanical / Utilities that are also pinball stuff, although perhaps not all of them. It only becomes apparent due to them using the "genpin" sample set
		machine.metadata.platform = 'Pinball'
	if genre == 'Handheld' and subgenre == 'Electronic Game':
		#Note: "Handheld / Electronic Game" could also be a tabletop system which takes AC input and you would not be able to hold in your hands at all (see also: cpacman), but since catlist.ini doesn't take that into account, I don't really have a way of doing so either
		machine.metadata.platform = 'Handheld'
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
	if genre == 'Handheld' and subgenre == 'Home Videogame Console':
		#Home Videogame Console seems to be used for stuff that would be normally excluded due to having software lists and hence being a platform for other software (e.g. GBA), or stuff that ends up there because it has no software list yet (e.g. Gizmondo, Sony PocketStation), but also some stuff like kcontra (Contra handheld) that should definitely be called a handheld, or various "plug & play" (except without the plug) stuff like BittBoy 300 in 1 or VG Pocket
		#Anyway that's why I put that there
		#Other genres of handheld: Pocket Device - Pad - PDA; Child Computer (e.g. Speak & Spell) but those seem more suited to Standalone System particularly the former
		machine.metadata.platform = 'Handheld' if is_plug_and_play(machine) else 'Standalone System'
	if genre == 'Misc.' and subgenre == 'Unknown':
		machine.metadata.genre = 'Unknown'
	
	if (category == 'Arcade' and (genre == 'Misc.' and subgenre in ('Laserdisc Simulator', 'Print Club', 'Redemption'))) or (genre == 'Music' and subgenre == 'Jukebox'):
		machine.metadata.categories = [subgenre]
	elif genre == 'Utilities' and subgenre in ('Test ROM', 'Test'):
		machine.metadata.categories = ['Test ROMs']
	elif genre == 'Electromechanical' or (category == 'Arcade' and genre in ('Utilties', 'Medal Game')):
		machine.metadata.categories = [genre]
	elif (genre == 'Misc.' and subgenre == 'Coin Pusher') or (genre == 'Coin Pusher' and subgenre == 'Misc.'):
		machine.metadata.categories = ['Coin Pusher']
	elif category == 'Arcade' and ((genre == 'Casino') or (genre == 'Slot Machine') or (genre == 'Electromechanical' and subgenre == 'Reels') or (genre == 'Multiplay' and subgenre == 'Cards')):
		machine.metadata.categories = ['Gambling']

	if not machine.metadata.categories:
		#If it has no coins then it doesn't meet the definition of "coin operated machine" I guess and it seems wrong to put it in the arcade category
		machine.metadata.categories = ['Non-Arcade'] if machine.coin_slots == 0 else ['Arcade']
	if not machine.metadata.platform:
		#Ditto here, although I hesitate to actually name this lack of platform "Non-Arcade" but I don't want to overthink things
		machine.metadata.platform = 'Non-Arcade' if machine.coin_slots == 0 else 'Arcade'
	#Misc has a lot of different things in it and I guess catlist just uses it as a catch-all for random things which don't really fit anywhere else and there's not enough to give them their own category, probably
	#Anyway, the name 'Non-Arcade' sucks because it's just used as a "this isn't anything in particular" thing

def add_languages(machine, name_tags):
	languages = get_languages(machine.basename)
	if languages:
		machine.metadata.languages = languages
	else:
		if machine.has_parent:
			languages = get_languages(machine.parent_basename)
			if languages:
				machine.metadata.languages = languages
				return

		languages = detect_things_from_filename.get_languages_from_tags_directly(name_tags)
		if languages:
			machine.metadata.languages = languages
		elif machine.metadata.regions:
			region_language = get_language_from_regions(machine.metadata.regions)
			if region_language:
				machine.metadata.languages = [region_language]

def add_metadata(machine):
	machine.metadata.cpu_info.set_inited()
	cpus = find_cpus(machine.xml)
	if cpus:
		for cpu_xml in cpus:
			cpu = CPU()
			cpu.load_from_xml(cpu_xml)
			machine.metadata.cpu_info.add_cpu(cpu)

	machine.metadata.screen_info = ScreenInfo()
	displays = machine.xml.findall('display')
	machine.metadata.screen_info.load_from_xml_list(displays)

	add_input_info(machine)
	add_save_type(machine)

	name_tags = find_filename_tags.findall(machine.name)
	machine.metadata.regions = detect_things_from_filename.get_regions_from_filename_tags(name_tags, loose=True)

	add_languages(machine, name_tags)

	revision = detect_things_from_filename.get_revision_from_filename_tags(name_tags)
	if revision:
		machine.metadata.specific_info['Revision'] = revision
	version = detect_things_from_filename.get_version_from_filename_tags(name_tags)
	if version:
		machine.metadata.specific_info['Version'] = version

	#Might not be so hardcoded one day...
	machine.metadata.emulator_name = 'MAME'

	add_status(machine)

def add_input_info(machine):
	machine.metadata.input_info.set_inited()
	if machine.input_element is None:
		#Seems like this doesn't actually happen
		if main_config.debug:
			print('Oi m8', machine.basename, '/', machine.name, 'has no input')
		return

	control_elements = machine.input_element.findall('control')
	if not control_elements:
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in
		if machine.number_of_players > 0:
			machine.metadata.input_info.add_option(input_metadata.Custom('Unknown input device'))
		return

	controller = input_metadata.CombinedController()

	has_normal_input = False
	has_added_vii_motion_controls = False
	normal_input = input_metadata.NormalController()

	for control in control_elements:
		buttons = int(control.attrib.get('buttons', 0))

		if control.attrib.get('player', '1') != '1':
			#I care not for these "other people" and "social interaction" concepts
			#Anyway, this would only matter for stuff where player 2 has a different control scheme like Lucky & Wild, and... not sure what I'm gonna do about that, because we wanna avoid doubling up on input types where number of players > 1, and then that seems to be correct anyway
			continue

		#Still kinda feel like this is messy but ehhh
		#Input metadata will probably never be perfect, MAME -listxml outputs things for a different purpose really, it just be like that sometimes
		#I wonder if I'd be better off making some kind of controls.ini file myself
		input_type = control.attrib['type']
		if input_type == 'only_buttons':
			has_normal_input = True
			normal_input.face_buttons += buttons
		elif input_type == 'joy':
			has_normal_input = True
			normal_input.face_buttons += buttons
			normal_input.dpads += 1
		elif input_type == 'doublejoy':
			has_normal_input = True
			normal_input.face_buttons += buttons
			normal_input.dpads += 2
		elif input_type == 'triplejoy':
			has_normal_input = True
			normal_input.face_buttons += buttons
			normal_input.dpads += 3
		elif input_type == 'paddle':
			if machine.metadata.genre == 'Driving':
				#Yeah this looks weird and hardcody and dodgy but am I wrong
				if buttons > 0:
					has_normal_input = True
					normal_input.face_buttons += buttons
				controller.components.append(input_metadata.SteeringWheel())
			elif machine.basename == 'vii':
				#Uses 3 "paddle" inputs to represent 3-axis motion and I guess I'll have to deal with that
				if not has_added_vii_motion_controls:
					controller.components.append(input_metadata.MotionControls())
					has_added_vii_motion_controls = True
			else:
				paddle = input_metadata.Paddle()
				paddle.buttons = buttons
				controller.components.append(paddle)
		elif input_type == 'stick':
			has_normal_input = True
			normal_input.analog_sticks += 1
			normal_input.face_buttons += buttons
		elif input_type == 'pedal':
			if buttons > 0:
				has_normal_input = True
				normal_input.face_buttons += buttons
			pedal = input_metadata.Pedal()
			controller.components.append(pedal)
		elif input_type == 'lightgun':
			#TODO: See if we can be clever and detect if this is actually a touchscreen, like platform = handheld or something
			light_gun = input_metadata.LightGun()
			light_gun.buttons = buttons
			controller.components.append(light_gun)
		elif input_type == 'positional':
			#What _is_ a positional exactly
			positional = input_metadata.Positional()
			controller.components.append(positional)
		elif input_type == 'dial':
			dial = input_metadata.Dial()
			dial.buttons = buttons
			controller.components.append(dial)
		elif input_type == 'trackball':
			trackball = input_metadata.Trackball()
			trackball.buttons = buttons
			controller.components.append(trackball)
		elif input_type == 'mouse':
			mouse = input_metadata.Mouse()
			mouse.buttons = buttons
			controller.components.append(mouse)
		elif input_type == 'keypad':
			keypad = input_metadata.Keypad()
			keypad.keys = buttons
			controller.components.append(keypad)
		elif input_type == 'keyboard':
			keyboard = input_metadata.Keyboard()
			keyboard.keys = buttons
			controller.components.append(keyboard)
		elif input_type == 'mahjong':
			mahjong = input_metadata.Mahjong()
			mahjong.buttons = buttons
			controller.components.append(mahjong)
		elif input_type == 'hanafuda':
			hanafuda = input_metadata.Hanafuda()
			hanafuda.buttons = buttons
			controller.components.append(hanafuda)
		elif input_type == 'gambling':
			gambling = input_metadata.Gambling()
			gambling.buttons = buttons
			controller.components.append(gambling)
		else:
			if buttons:
				description = 'Custom input device with {0}'.format(pluralize(buttons, 'button'))
			else:
				description = 'Custom input device'
			controller.components.append(input_metadata.Custom(description))

	if has_normal_input:
		controller.components.append(normal_input)

	machine.metadata.input_info.input_options = [controller]
