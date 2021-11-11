from typing import Optional, Sequence, cast

from meowlauncher import detect_things_from_filename, input_metadata
from meowlauncher.common_types import EmulationStatus, MediaType, SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.games.mame_common.machine import Machine, mame_statuses
from meowlauncher.games.mame_common.mame_helpers import get_image
from meowlauncher.games.mame_common.mame_support_files import (
    ArcadeCategory, MachineCategory, add_history, get_category, get_languages,
    organize_catlist)
from meowlauncher.games.mame_common.mame_utils import (find_cpus,
                                                       image_config_keys)
from meowlauncher.metadata import CPU, Metadata, ScreenInfo
from meowlauncher.util.region_info import get_language_from_regions
from meowlauncher.util.utils import find_filename_tags_at_end, pluralize

from .mame_game import MAMEGame

#I still want to dismantle this class with the fury of a thousand suns

#Some games have memory card slots, but they don't actually support saving, it's just t hat the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['diggerma', 'neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']

def add_save_type(game: MAMEGame) -> None:
	if game.metadata.platform == 'Arcade':
		has_memory_card = False
		for media_slot in game.machine.media_slots:
			if not media_slot.instances: #Does this ever happen?
				continue
			if media_slot.type == 'memcard':
				has_memory_card = True

		has_memory_card = has_memory_card and (game.machine.family not in not_actually_save_supported)

		game.metadata.save_type = SaveType.MemoryCard if has_memory_card else SaveType.Nothing
	else:
		has_nvram = game.machine.uses_device('nvram')
		has_i2cmem = game.machine.uses_device('i2cmem')

		#Assume that if there's non-volatile memory that it's used for storing some kind of save data, and not like... stuff
		#This may be wrong!!!!!!!!!!! but it seems to hold true for plug & play TV games and electronic handheld games so that'd be the main idea
		game.metadata.save_type = SaveType.Internal if has_nvram or has_i2cmem else SaveType.Nothing

def add_status(machine: Machine, metadata: Metadata) -> None:
	#See comments for overall_status property for what that actually means
	metadata.specific_info['MAME-Overall-Emulation-Status'] = machine.overall_status
	metadata.specific_info['MAME-Emulation-Status'] = machine.emulation_status
	driver = machine.driver_element
	metadata.specific_info['Cocktail-Status'] = mame_statuses.get(driver.attrib.get('cocktail'), EmulationStatus.Good) if driver else EmulationStatus.Unknown
	metadata.specific_info['Supports-Savestate'] = driver.attrib.get('savestate') == 'supported' if driver else EmulationStatus.Unknown

	unemulated_features = []
	for feature_type, feature_status in machine.feature_statuses.items():
		if feature_status == 'unemulated':
			unemulated_features.append(feature_type)
		else:
			#Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
			#Note: MAME 0.208 has added capture, media, tape, punch, drum, rom, comms; although I guess I don't need to write any more code here
			metadata.specific_info['MAME-%s-Status' % feature_type.capitalize()] = mame_statuses.get(feature_status, EmulationStatus.Unknown)

	if unemulated_features:
		metadata.specific_info['MAME-Unemulated-Features'] = unemulated_features

def add_metadata_from_category(game: MAMEGame, category: Optional[MachineCategory]):
	if not category:
		#Not in catlist or user doesn't have catlist
		return
	if isinstance(category, ArcadeCategory):
		game.metadata.specific_info['Has-Adult-Content'] = category.is_mature
	catlist = organize_catlist(category)
	if catlist.platform:
		if catlist.definite_platform or not game.machine.is_system_driver:
			game.metadata.platform = catlist.platform
	if catlist.genre:
		game.metadata.genre = catlist.genre
	if catlist.subgenre:
		game.metadata.subgenre = catlist.subgenre
	if catlist.category and (catlist.definite_category or not game.metadata.categories):
		game.metadata.categories = [catlist.category]

def add_metadata_from_catlist(game: MAMEGame) -> None:
	category = get_category(game.machine.basename)
	if not category and game.machine.has_parent:
		category = get_category(cast(str, game.machine.parent_basename))
	
	add_metadata_from_category(game, category)
	
	#TODO: This function sucks, needs refactoring to make it easier to read
	#I guess you have results here from catlist -
	#Arcade: Has a genre and subgenre, takes coins, can be mature
	#Plug & play with genre
	#Plug & play without genre
	#Handheld: LCD handhelds, etc
	#Game consoles with the chip inside the cart: XavixPORT, CPS Changer, Domyos Interactive System, Select-a-Game (pre-0.221), R-Zone
	#Game & Watch: Handheld but we call it a different platform because it's what most people would expect
	#Board games
	#Pinball: Arcade but we call it a different platform I guess
	#Other non-game systems that are just like computers or whatever that aren't in emulated_platforms
	game.metadata.media_type = MediaType.Standalone

	filename_tags = find_filename_tags_at_end(game.machine.name)
	for tag in filename_tags:
		if 'prototype' in tag.lower() or 'location test' in tag.lower():
			if game.machine.has_parent:
				if cast(Machine, game.machine.parent).is_proto:
					game.metadata.categories = ['Unreleased']
				else:
					game.metadata.categories = ['Betas']
			else:
				game.metadata.categories = ['Unreleased']
			break
		if 'bootleg' in tag.lower():
			if game.machine.has_parent:
				if cast(Machine, game.machine.parent).is_proto: #Ehh? I guess?
					game.metadata.categories = ['Bootleg']
				else:
					game.metadata.categories = ['Hacks']
			else:
				game.metadata.categories = ['Bootleg']
			break
		if 'hack' in tag.lower():
			game.metadata.categories = ['Hacks']
	if game.machine.is_mechanical:
		game.metadata.categories = ['Electromechanical']
	if game.machine.is_hack:
		game.metadata.categories = ['Hacks']
	if game.machine.uses_device('coin_hopper'):
		#Redemption games sometimes also have one, but then they will have their category set later by their subgenre being Redemption
		game.metadata.categories = ['Gambling']

	#Now we separate things into additional platforms where relevant

	#Home systems that have the whole CPU etc inside the cartridge, and hence work as separate systems in MAME instead of being in roms.py
	if game.machine.source_file == 'cps1' and '(CPS Changer, ' in game.machine.name:
		game.machine.name = game.machine.name.replace('CPS Changer, ', '')
		game.metadata.platform = 'CPS Changer'
		game.metadata.media_type = MediaType.Cartridge
		if not game.metadata.categories:
			game.metadata.categories = ['Games']
		return 
	if game.machine.name.endswith('(XaviXPORT)'):
		game.metadata.platform = 'XaviXPORT'
		game.metadata.media_type = MediaType.Cartridge
		if not game.metadata.categories:
			game.metadata.categories = ['Games']
		return
	if game.machine.name.endswith('(Domyos Interactive System)'):
		game.metadata.platform = 'Domyos Interactive System'
		game.metadata.media_type = MediaType.Cartridge
		if not game.metadata.categories:
			game.metadata.categories = ['Games']
		return
	if game.machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		#Select-a-Game does not work this way since 0.221 but might as well keep that there for older versions
		platform, _, game.machine.name = game.machine.name.partition(': ')
		game.metadata.platform = platform
		game.metadata.media_type = MediaType.Cartridge if platform in ('Select-A-Game', 'R-Zone') else MediaType.Standalone
		if not game.metadata.categories:
			game.metadata.categories = ['Games']
		return

	if not game.metadata.categories:
		#If it has no coins then it doesn't meet the definition of "coin operated machine" I guess and it seems wrong to put it in the arcade category
		game.metadata.categories = ['Non-Arcade'] if game.machine.coin_slots == 0 else ['Arcade']
	if not game.metadata.platform:
		#Ditto here, although I hesitate to actually name this lack of platform "Non-Arcade" but I don't want to overthink things
		game.metadata.platform = 'Non-Arcade' if game.machine.coin_slots == 0 else 'Arcade'
	#Misc has a lot of different things in it and I guess catlist just uses it as a catch-all for random things which don't really fit anywhere else and there's not enough to give them their own category, probably
	#Anyway, the name 'Non-Arcade' sucks because it's just used as a "this isn't anything in particular" thing

def add_languages(game: MAMEGame, name_tags: Sequence[str]) -> None:
	languages = get_languages(game.machine.basename)
	if languages:
		game.metadata.languages = languages
	else:
		if game.machine.has_parent:
			languages = get_languages(cast(str, game.machine.parent_basename))
			if languages:
				game.metadata.languages = languages
				return

		languages = detect_things_from_filename.get_languages_from_tags_directly(name_tags)
		if languages:
			game.metadata.languages = languages
		elif game.metadata.regions:
			region_language = get_language_from_regions(game.metadata.regions)
			if region_language:
				game.metadata.languages = [region_language]

def add_images(game: MAMEGame) -> None:
	for image_name, config_key in image_config_keys.items():
		image = get_image(config_key, game.machine.basename)
		if image:
			game.metadata.images[image_name] = image
			continue
		if game.machine.has_parent:
			image = get_image(config_key, game.machine.parent_basename)
			if image:
				game.metadata.images[image_name] = image
				continue
		if image_name == 'Icon' and game.machine.bios_basename:
			image = get_image(config_key, game.machine.bios_basename)
			if image:
				game.metadata.images[image_name] = image
		
def add_metadata(game: MAMEGame) -> None:
	add_images(game)
	add_metadata_from_catlist(game)

	game.metadata.cpu_info.set_inited()
	cpus = find_cpus(game.machine.xml)
	if cpus:
		for cpu_xml in cpus:
			cpu = CPU()
			cpu.load_from_xml(cpu_xml)
			game.metadata.cpu_info.add_cpu(cpu)

	game.metadata.screen_info = ScreenInfo()
	displays = game.machine.xml.findall('display')
	game.metadata.screen_info.load_from_xml_list(displays)

	add_input_info(game)
	add_save_type(game)

	name_tags = find_filename_tags_at_end(game.machine.name)
	regions = detect_things_from_filename.get_regions_from_filename_tags(name_tags, loose=True)
	if regions:
		game.metadata.regions = regions

	add_languages(game, name_tags)

	revision = detect_things_from_filename.get_revision_from_filename_tags(name_tags)
	if revision:
		game.metadata.specific_info['Revision'] = revision
	version = detect_things_from_filename.get_version_from_filename_tags(name_tags)
	if version:
		game.metadata.specific_info['Version'] = version

	#Might not be so hardcoded one day...
	game.metadata.emulator_name = 'MAME'

	add_status(game.machine, game.metadata)
	add_history(game.metadata, game.machine.basename)

def add_input_info(game: MAMEGame) -> None:
	game.metadata.input_info.set_inited()
	if game.machine.input_element is None:
		#Seems like this doesn't actually happen
		if main_config.debug:
			print('Oi m8', game.machine.basename, '/', game.machine.name, 'has no input')
		return

	control_elements = game.machine.input_element.findall('control')
	if not control_elements:
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in
		if game.machine.number_of_players > 0:
			game.metadata.input_info.add_option(input_metadata.Custom('Unknown input device'))
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
			if game.metadata.genre == 'Driving':
				#Yeah this looks weird and hardcody and dodgy but am I wrong
				if buttons > 0:
					has_normal_input = True
					normal_input.face_buttons += buttons
				controller.components.append(input_metadata.SteeringWheel())
			elif game.machine.basename == 'vii':
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

	game.metadata.input_info.input_options = [controller]
