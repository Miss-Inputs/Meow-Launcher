"""I still want to dismantle this class with the fury of a thousand suns, some of it belongs in machine, some belongs in mame_support_files"""
import contextlib
import logging
from collections import Counter
from collections.abc import Iterable, Sequence
from fractions import Fraction
from typing import TYPE_CHECKING, Any, cast
from xml.etree import ElementTree

from meowlauncher import input_info
from meowlauncher.common_types import MediaType, SaveType
from meowlauncher.games.mame_common.machine import Machine
from meowlauncher.games.mame_common.mame_helpers import get_image
from meowlauncher.games.mame_common.mame_support_files import (
	ArcadeCategory,
	MachineCategory,
	add_history,
	get_category,
	get_languages,
	organize_catlist,
)
from meowlauncher.games.mame_common.mame_utils import image_config_keys, iter_cpus
from meowlauncher.util.detect_things_from_filename import (
	get_languages_from_tags_directly,
	get_regions_from_filename_tags,
	get_revision_from_filename_tags,
	get_version_from_filename_tags,
)
from meowlauncher.util.region_info import get_common_language_from_regions
from meowlauncher.util.utils import find_filename_tags_at_end, format_unit, pluralize

if TYPE_CHECKING:
	from meowlauncher.info import GameInfo

	from .mame_game import ArcadeGame

logger = logging.getLogger(__name__)

_not_actually_save_supported = {
	'diggerma',
	'neobombe',
	'pbobbl2n',
	'popbounc',
	'shocktro',
	'shocktr2',
	'irrmaze',
}
"""Some games have memory card slots, but they don't actually support saving, it's just t hat the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story."""


def _format_count(list_of_something: Iterable[Any]) -> str | None:
	counter = Counter(list_of_something)
	if len(counter) == 1 and next(iter(counter.keys()), None) is None:
		return None
	return ' + '.join(
		str(value) if count == 1 else f'{value} * {count}'
		for value, count in counter.items()
		if value
	)


class CPU:
	def __init__(self, xml: ElementTree.Element):
		self.chip_name = xml.attrib.get('name')
		self.tag = xml.attrib.get('tag')
		self.clock_speed = None
		if xml.attrib['name'] != 'Netlist CPU Device' and 'clock' in xml.attrib:
			with contextlib.suppress(ValueError):
				self.clock_speed = int(xml.attrib['clock'])


class CPUInfo:
	def __init__(self, cpus: Iterable[CPU]) -> None:
		self.cpus = set(cpus)

	@property
	def number_of_cpus(self) -> int:
		return len(self.cpus)

	@property
	def chip_names(self) -> str | None:
		return _format_count(cpu.chip_name for cpu in self.cpus)

	@property
	def clock_speeds(self) -> str | None:
		return _format_count(
			format_unit(cpu.clock_speed, 'Hz') for cpu in self.cpus if cpu.clock_speed
		)

	@property
	def tags(self) -> str | None:
		return _format_count(cpu.tag for cpu in self.cpus)


class Display:
	def __init__(self, xml: ElementTree.Element):
		self.type = xml.attrib['type']
		self.tag = xml.attrib['tag']
		try:
			self.width: int | None = int(xml.attrib['width'])
			self.height: int | None = int(xml.attrib['height'])
		except KeyError:
			self.width = None
			self.height = None

		self.refresh_rate = None
		if 'refresh' in xml.attrib:
			with contextlib.suppress(ValueError):
				self.refresh_rate = float(xml.attrib['refresh'])

	@property
	def resolution(self) -> str:
		if self.width and self.height:
			return f'{self.width:.0f}x{self.height:.0f}'
		# Other types are vector (Asteroids, etc) or svg (Game & Watch games, etc)
		# They might actually have a height/width
		return self.type.capitalize()

	@property
	def aspect_ratio(self) -> Fraction | None:
		if self.width and self.height:
			return Fraction(self.width, self.height)
		return None


class DisplayCollection:
	def __init__(self, display_xmls: Iterable[ElementTree.Element]):
		self.displays = {Display(display_xml) for display_xml in display_xmls}

	def __len__(self) -> int:
		return len(self.displays)

	@property
	def resolutions(self) -> str | None:
		return _format_count(display.resolution for display in self.displays if display.resolution)

	@property
	def refresh_rates(self) -> str | None:
		return _format_count(
			format_unit(display.refresh_rate, 'Hz')
			for display in self.displays
			if display.refresh_rate
		)

	@property
	def aspect_ratios(self) -> str | None:
		return _format_count(
			':'.join(str(i) for i in display.aspect_ratio.as_integer_ratio())
			for display in self.displays
			if display.aspect_ratio
		)

	@property
	def display_types(self) -> str | None:
		return _format_count(display.type for display in self.displays if display.type)

	@property
	def display_tags(self) -> str | None:
		return _format_count(display.tag for display in self.displays if display.tag)


def add_save_type(game: 'ArcadeGame') -> None:
	if game.info.platform == 'Arcade':
		has_memory_card = False
		for media_slot in game.machine.media_slots:
			if not media_slot.instances:  # Does this ever happen?
				continue
			if media_slot.type == 'memcard':
				has_memory_card = True

		has_memory_card = has_memory_card and (
			game.machine.family_basename not in _not_actually_save_supported
		)

		game.info.save_type = SaveType.MemoryCard if has_memory_card else SaveType.Nothing
	else:
		has_nvram = game.machine.uses_device('nvram')
		has_i2cmem = game.machine.uses_device('i2cmem')

		# Assume that if there's non-volatile memory that it's used for storing some kind of save data, and not like... stuff
		# This may be wrong!!!!!!!!!!! but it seems to hold true for plug & play TV games and electronic handheld games so that'd be the main idea
		game.info.save_type = SaveType.Internal if has_nvram or has_i2cmem else SaveType.Nothing


def add_status(machine: Machine, game_info: 'GameInfo') -> None:
	# See comments for overall_status property for what that actually means
	game_info.specific_info['MAME Overall Emulation Status'] = machine.overall_status
	game_info.specific_info['MAME Emulation Status'] = machine.emulation_status
	game_info.specific_info['Cocktail Status'] = machine.cocktail_status
	driver = machine.driver_element
	savestate_status = None
	if driver:
		savestate_attrib = driver.attrib.get('savestate')
		if (
			savestate_attrib == 'supported'
		):  # TODO: Why did the code have this, did something change in a new version and I forgot? I guess I'll need to find out, otherwise this could just check for 'unsupported'
			savestate_status = True
		elif savestate_attrib == 'unsupported':
			savestate_status = False
		# Else I don't know

	if savestate_status is not None:
		game_info.specific_info['Supports Savestate?'] = savestate_status

	unemulated_features = set()
	imperfect_features = set()
	for feature_type, feature_status in machine.feature_statuses.items():
		# Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
		# Note: MAME 0.208 has added capture, media, tape, punch, drum, rom, comms; although I guess I don't need to write any more code here
		if feature_status == 'unemulated':
			unemulated_features.add(feature_type)
		else:
			imperfect_features.add(feature_type)
	if unemulated_features:
		game_info.specific_info['MAME Unemulated Features'] = unemulated_features
	if imperfect_features:
		game_info.specific_info['MAME Imperfect Features'] = unemulated_features


def add_metadata_from_category(game: 'ArcadeGame', category: MachineCategory | None) -> None:
	if not category:
		# Not in catlist or user doesn't have catlist
		return
	if isinstance(category, ArcadeCategory):
		game.info.specific_info['Has Adult Content?'] = category.is_mature
	catlist = organize_catlist(category)
	if catlist.platform and (catlist.definite_platform or not game.machine.is_system_driver):
		game.info.platform = catlist.platform
	if catlist.genre:
		game.info.genre = catlist.genre
	if catlist.subgenre:
		game.info.subgenre = catlist.subgenre
	if catlist.category and (catlist.definite_category or not game.info.categories):
		game.info.categories = [catlist.category]


def _add_info_from_catlist(game: 'ArcadeGame') -> None:
	category = get_category(game.machine.basename)
	if not category and game.machine.has_parent:
		category = get_category(cast(str, game.machine.parent_basename))

	add_metadata_from_category(game, category)

	# TODO: This function sucks, needs refactoring to make it easier to read
	# I guess you have results here from catlist -
	# Arcade: Has a genre and subgenre, takes coins, can be mature
	# Plug & play with genre
	# Plug & play without genre
	# Handheld: LCD handhelds, etc
	# Game consoles with the chip inside the cart: XavixPORT, CPS Changer, Domyos Interactive System, Select-a-Game (pre-0.221), R-Zone
	# Game & Watch: Handheld but we call it a different platform because it's what most people would expect
	# Board games
	# Pinball: Arcade but we call it a different platform I guess
	# Other non-game systems that are just like computers or whatever that aren't in emulated_platforms
	game.info.media_type = MediaType.Standalone

	filename_tags = find_filename_tags_at_end(game.machine.name)
	for tag in filename_tags:
		if 'prototype' in tag.lower() or 'location test' in tag.lower():
			if game.machine.has_parent:
				if cast(Machine, game.machine.parent).is_proto:
					game.info.categories = ('Unreleased',)
				else:
					game.info.categories = ('Betas',)
			else:
				game.info.categories = ('Unreleased',)
			break
		if 'bootleg' in tag.lower():
			if game.machine.has_parent:
				if cast(Machine, game.machine.parent).is_proto:  # Ehh? I guess?
					game.info.categories = ('Bootleg',)
				else:
					game.info.categories = ('Hacks',)
			else:
				game.info.categories = ('Bootleg',)
			break
		if 'hack' in tag.lower():
			game.info.categories = ('Hacks',)
	if game.machine.is_mechanical:
		game.info.categories = ('Electromechanical',)
	if game.machine.is_hack:
		game.info.categories = ('Hacks',)
	if game.machine.uses_device('coin_hopper'):
		# Redemption games sometimes also have one, but then they will have their category set later by their subgenre being Redemption
		game.info.categories = ('Gambling',)

	# Now we separate things into additional platforms where relevant

	# Home systems that have the whole CPU etc inside the cartridge, and hence work as separate systems in MAME instead of being in roms.py
	if game.machine.source_file == 'cps1' and '(CPS Changer, ' in game.machine.name:
		game.machine.name = game.machine.name.replace('CPS Changer, ', '')
		game.info.platform = 'CPS Changer'
		game.info.media_type = MediaType.Cartridge
		if not game.info.categories:
			game.info.categories = ('Games',)
		return
	if game.machine.name.endswith('(XaviXPORT)'):
		game.info.platform = 'XaviXPORT'
		game.info.media_type = MediaType.Cartridge
		if not game.info.categories:
			game.info.categories = ('Games',)
		return
	if game.machine.name.endswith('(Domyos Interactive System)'):
		game.info.platform = 'Domyos Interactive System'
		game.info.media_type = MediaType.Cartridge
		if not game.info.categories:
			game.info.categories = ('Games',)
		return
	if game.machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		# Select-a-Game does not work this way since 0.221 but might as well keep that there for older versions
		platform, _, game.machine.name = game.machine.name.partition(': ')
		game.info.platform = platform
		game.info.media_type = (
			MediaType.Cartridge if platform in {'Select-A-Game', 'R-Zone'} else MediaType.Standalone
		)
		if not game.info.categories:
			game.info.categories = ('Games',)
		return

	if not game.info.categories:
		# If it has no coins then it doesn't meet the definition of "coin operated machine" I guess and it seems wrong to put it in the arcade category
		game.info.categories = ('Non-Arcade',) if game.machine.coin_slots == 0 else ('Arcade',)
	if not game.info.platform:
		# Ditto here, although I hesitate to actually name this lack of platform "Non-Arcade" but I don't want to overthink things
		game.info.platform = 'Non-Arcade' if game.machine.coin_slots == 0 else 'Arcade'
	# Misc has a lot of different things in it and I guess catlist just uses it as a catch-all for random things which don't really fit anywhere else and there's not enough to give them their own category, probably
	# Anyway, the name 'Non-Arcade' sucks because it's just used as a "this isn't anything in particular" thing


def add_languages(game: 'ArcadeGame', name_tags: Sequence[str]) -> None:
	languages = get_languages(game.machine.basename)
	if languages:
		game.info.languages = languages
	else:
		if game.machine.has_parent:
			languages = get_languages(cast(str, game.machine.parent_basename))
			if languages:
				game.info.languages = languages
				return

		languages = get_languages_from_tags_directly(name_tags)
		if languages:
			game.info.languages = languages
		elif game.info.regions:
			region_language = get_common_language_from_regions(game.info.regions)
			if region_language:
				game.info.languages = {region_language}


def add_images(game: 'ArcadeGame') -> None:
	for image_name, config_key in image_config_keys.items():
		image = get_image(config_key, game.machine.basename)
		if image:
			game.info.images[image_name] = image
			continue
		if game.machine.has_parent:
			image = get_image(config_key, game.machine.parent_basename)
			if image:
				game.info.images[image_name] = image
				continue
		if image_name == 'Icon' and game.machine.bios_basename:
			image = get_image(config_key, game.machine.bios_basename)
			if image:
				game.info.images[image_name] = image


def add_info(game: 'ArcadeGame') -> None:
	add_images(game)
	_add_info_from_catlist(game)

	add_input_info(game)
	add_save_type(game)

	name_tags = find_filename_tags_at_end(game.machine.name)
	regions = get_regions_from_filename_tags(name_tags, loose=True)
	if regions:
		game.info.regions = regions

	add_languages(game, name_tags)

	revision = get_revision_from_filename_tags(name_tags)
	if revision:
		game.info.specific_info['Revision'] = revision
	version = get_version_from_filename_tags(name_tags)
	if version:
		game.info.specific_info['Version'] = version

	add_status(game.machine, game.info)
	with contextlib.suppress(FileNotFoundError):
		add_history(game.info, game.machine.basename)

	cpu_info = CPUInfo(CPU(cpu_xml) for cpu_xml in iter_cpus(game.machine.xml))
	displays = DisplayCollection(game.machine.xml.iter('display'))

	game.info.specific_info['Number of CPUs'] = cpu_info.number_of_cpus
	if cpu_info.number_of_cpus:
		game.info.specific_info['Main CPU'] = cpu_info.chip_names
		game.info.specific_info['Clock Speed'] = cpu_info.clock_speeds
		game.info.specific_info['CPU Tags'] = cpu_info.tags

	num_displays = len(displays)
	game.info.specific_info['Number of Displays'] = num_displays

	if num_displays:
		game.info.specific_info['Display Resolution'] = displays.resolutions
		game.info.specific_info['Refresh Rate'] = displays.refresh_rates
		game.info.specific_info['Aspect Ratio'] = displays.aspect_ratios

		game.info.specific_info['Display Type'] = displays.display_types
		game.info.specific_info['Display Tag'] = displays.display_tags


def add_input_info(game: 'ArcadeGame') -> None:
	game.info.input_info.set_inited()
	if game.machine.input_element is None:
		# Seems like this doesn't actually happen
		logger.info('Oi m8 %s has no input', game.machine)
		return

	controller = input_info.CombinedController()

	has_normal_input = False
	has_added_vii_motion_controls = False
	normal_input = input_info.NormalController()

	has_control_elements = False

	for control in game.machine.input_element.iter('control'):
		has_control_elements = True
		buttons = int(control.attrib.get('buttons', 0))

		if control.attrib.get('player', '1') != '1':
			# I care not for these "other people" and "social interaction" concepts
			# Anyway, this would only matter for stuff where player 2 has a different control scheme like Lucky & Wild, and... not sure what I'm gonna do about that, because we wanna avoid doubling up on input types where number of players > 1, and then that seems to be correct anyway
			continue

		# Still kinda feel like this is messy but ehhh
		# Input metadata will probably never be perfect, MAME -listxml outputs things for a different purpose really, it just be like that sometimes
		# I wonder if I'd be better off making some kind of controls.ini file myself
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
			if game.info.genre == 'Driving':
				# Yeah this looks weird and hardcody and dodgy but am I wrong
				if buttons > 0:
					has_normal_input = True
					normal_input.face_buttons += buttons
				controller.components.append(input_info.SteeringWheel())
			elif game.machine.basename == 'vii':
				# Uses 3 "paddle" inputs to represent 3-axis motion and I guess I'll have to deal with that
				if not has_added_vii_motion_controls:
					controller.components.append(input_info.MotionControls())
					has_added_vii_motion_controls = True
			else:
				paddle = input_info.Paddle()
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
			pedal = input_info.Pedal()
			controller.components.append(pedal)
		elif input_type == 'lightgun':
			# TODO: See if we can be clever and detect if this is actually a touchscreen, like platform = handheld or something
			light_gun = input_info.LightGun()
			light_gun.buttons = buttons
			controller.components.append(light_gun)
		elif input_type == 'positional':
			# What _is_ a positional exactly
			positional = input_info.Positional()
			controller.components.append(positional)
		elif input_type == 'dial':
			dial = input_info.Dial()
			dial.buttons = buttons
			controller.components.append(dial)
		elif input_type == 'trackball':
			trackball = input_info.Trackball()
			trackball.buttons = buttons
			controller.components.append(trackball)
		elif input_type == 'mouse':
			mouse = input_info.Mouse()
			mouse.buttons = buttons
			controller.components.append(mouse)
		elif input_type == 'keypad':
			keypad = input_info.Keypad()
			keypad.keys = buttons
			controller.components.append(keypad)
		elif input_type == 'keyboard':
			keyboard = input_info.Keyboard()
			keyboard.keys = buttons
			controller.components.append(keyboard)
		elif input_type == 'mahjong':
			mahjong = input_info.Mahjong()
			mahjong.buttons = buttons
			controller.components.append(mahjong)
		elif input_type == 'hanafuda':
			hanafuda = input_info.Hanafuda()
			hanafuda.buttons = buttons
			controller.components.append(hanafuda)
		elif input_type == 'gambling':
			gambling = input_info.Gambling()
			gambling.buttons = buttons
			controller.components.append(gambling)
		else:
			if buttons:
				description = f'Custom input device with {pluralize(buttons, "button")}'
			else:
				description = 'Custom input device'
			controller.components.append(input_info.Custom(description))

	if has_normal_input:
		controller.components.append(normal_input)

	if not has_control_elements:
		# Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		# pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		# playable just fine, so we'll leave them in
		if game.machine.number_of_players > 0:
			game.info.input_info.add_option(input_info.Custom('Unknown input device'))
		return

	game.info.input_info.add_option(controller)
