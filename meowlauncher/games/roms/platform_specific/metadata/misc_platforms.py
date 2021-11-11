#Not worth putting these in their own source file I think
from enum import Enum, auto

from meowlauncher import input_metadata
from meowlauncher.common_types import MediaType
from meowlauncher.games.mame_common.machine import (
    Machine, does_machine_match_game, get_machines_from_source_file)
from meowlauncher.games.mame_common.mame_executable import \
    MAMENotInstalledException
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.games.mame_common.software_list_info import \
    get_software_list_entry
from meowlauncher.games.roms.rom_game import ROMGame

from .generic import add_generic_info


def add_vic10_info(game: ROMGame):
	#Input info: Keyboard or joystick

	has_header = game.metadata.media_type == MediaType.Cartridge and (game.rom.get_size() % 256) == 2
	game.metadata.specific_info['Headered'] = has_header
	software = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		software.add_standard_metadata(game.metadata)
		#What the heck is an "assy"?

def add_vic20_info(game: ROMGame):
	#Input info: Keyboard and/or joystick

	has_header = game.metadata.media_type == MediaType.Cartridge and (game.rom.get_size() % 256) == 2
	game.metadata.specific_info['Headered'] = has_header
	software = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		software.add_standard_metadata(game.metadata)
		notes = software.get_info('usage')
		if notes == 'Game Paddles required':
			game.metadata.specific_info['Peripheral'] = 'Paddle'
		else:
			game.metadata.add_notes(notes)
		
		#Enter 'SYS <some number>' to run
		#Needs VICKIT 4 to run
		#SYS 40969 for 40 column mode, SYS 40972 for 80 column mode, SYS 40975 for VIC mode, SYS 40978 to restart 40/80 column mode

class ColecoController(Enum):
	Normal = auto()
	SuperActionController = auto()
	RollerController = auto()
	DrivingController = auto()

def add_colecovision_info(game: ROMGame):
	#Can get year, publisher unreliably from the title screen info in the ROM; please do not do that

	peripheral = ColecoController.Normal
	peripheral_required = False

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)

		usage = software.get_info('usage')
		if usage == 'Supports Super Action Controllers':
			peripheral = ColecoController.SuperActionController
		elif usage == 'Requires Super Action Controllers':
			peripheral = ColecoController.SuperActionController
			peripheral_required = True
		elif usage == 'Supports roller controller':
			peripheral = ColecoController.RollerController
		elif usage == 'Requires roller controller':
			peripheral = ColecoController.RollerController
			peripheral_required = True
		elif usage == 'Supports driving controller':
			peripheral = ColecoController.DrivingController
		elif usage == 'Requires driving controller':
			peripheral = ColecoController.DrivingController
			peripheral_required = True
		else:
			game.metadata.add_notes(usage)

	normal_controller_part = input_metadata.NormalController()
	normal_controller_part.face_buttons = 2
	normal_controller_part.dpads = 1
	normal_controller_keypad = input_metadata.Keypad()
	normal_controller_keypad.keys = 12
	normal_controller = input_metadata.CombinedController([normal_controller_part, normal_controller_keypad])

	super_action_controller_buttons = input_metadata.NormalController()
	super_action_controller_buttons.face_buttons = 4 #Not really on the face, they're on the hand grip part, but still
	super_action_controller_buttons.dpads = 1
	super_action_controller_speed_roller = input_metadata.Dial() #Kind of, it's like a one-dimensional trackball from what I can tell
	super_action_controller_keypad = input_metadata.Keypad()
	super_action_controller_keypad.keys = 12
	super_action_controller = input_metadata.CombinedController([super_action_controller_buttons, super_action_controller_speed_roller, super_action_controller_keypad])

	roller_controller = input_metadata.Trackball()
	#Not sure how many buttons?
	driving_controller = input_metadata.SteeringWheel()
	#Gas pedal is on + off so I guess it counts as one button

	game.metadata.specific_info['Peripheral'] = peripheral
	if peripheral == ColecoController.Normal:
		game.metadata.input_info.add_option(normal_controller)
	else:
		if peripheral == ColecoController.DrivingController:
			game.metadata.input_info.add_option(driving_controller)
		elif peripheral == ColecoController.RollerController:
			game.metadata.input_info.add_option(roller_controller)
		elif peripheral == ColecoController.SuperActionController:
			game.metadata.input_info.add_option(super_action_controller)
		if not peripheral_required:
			game.metadata.input_info.add_option(normal_controller)
	#Doesn't look like you can set controller via command line at the moment, oh well

def add_ibm_pcjr_info(game: ROMGame):
	#Input info: Keyboard or joystick

	magic = game.rom.read(amount=32)

	header_length = 0

	if magic[:25] == b'PCjr Cartridge image file':
		game.metadata.specific_info['Headered'] = True
		#.jrc files just have a comment from 49:549 (null terminated ASCII I guess) for the most part so that might not be interesting to poke into
		game.metadata.specific_info['Header-Format'] = 'JRipCart'
		header_length = 512
	elif magic[:10] == b'Filename: ' and magic[0x14:0x1d] == b'Created: ':
		#Fields here are more plain texty, but otherwise there's just like... a filename and creation date, which is meaningless, and a generic description field, and also a start address
		game.metadata.specific_info['Headered'] = True
		game.metadata.specific_info['Header-Format'] = 'PCJrCart'
		header_length = 128

	software = get_software_list_entry(game, header_length)
	if software:
		software.add_standard_metadata(game.metadata)
		#TODO: If sharedfeat requirement = ibmpcjr_flop:pcdos21, do something about that
		#Probably get the MAME command line to get a PC DOS 2.1 floppy path from platform_config provided by the user, or else they don't get to use ColorPaint
		#Lotus 123jr has a similar predicament, but it also needs .m3u I guess

		#Usages:
		#Mount both carts and a DOS floppy and type 'TUTOR'
		#Boot from a DOS floppy and type 'G'

def add_pet_info(game: ROMGame):
	add_generic_info(game)
	#Usage strings in pet_rom:
	#Requires BASIC 2 (works on pet2001n).  Enter 'SYS 37000' to run
	#SYS38000

	keyboard = input_metadata.Keyboard()
	keyboard.keys = 74
	game.metadata.input_info.add_option(keyboard)
	#Don't know about joysticks and I know of no software that uses them
	for tag in game.filename_tags:
		#(2001, 3008, 3016, 3032, 3032B, 4016, 4032, 4032B, 8032, 8096, 8296, SuperPET)
		if (tag[0] == '(' and tag[-1] == ')') or (tag[0] == '[' and tag[-1] == ']'):
			tag = tag[1:-1]

		for model in ('3008', '3016', '3032', '3032B', '4016', '4032', '4032B', '8032', '8096', '8296', 'SuperPET'):
			if tag in (model, 'CBM %s' % model, 'CBM%s' % model, 'PET %s' % model, 'PET%s' % model):
				game.metadata.specific_info['Machine'] = model
				continue
		if tag in ('PET 2001', 'PET2001', 'CBM 2001', 'CBM2001'):
			#We don't search for just "(2001)" in case that's used to denote the year
			game.metadata.specific_info['Machine'] = '2001'
			continue
		for ram in (8, 16, 32, 96, 128):
			if tag.lower() in ('%dk ram' % ram, '%dkb ram' % ram):
				game.metadata.specific_info['Minimum-RAM'] = ram
				continue

def _get_uapce_games() -> list[Machine]:
	try:
		return _get_uapce_games.result #type: ignore[attr-defined]
	except AttributeError:
		try:
			if not default_mame_executable:
				#CBF tbhkthbai
				return []	
			_get_uapce_games.result = list(get_machines_from_source_file('uapce', default_mame_executable)) #type: ignore[attr-defined]
		except MAMENotInstalledException:
			return []
		return _get_uapce_games.result #type: ignore[attr-defined]

def add_pc_engine_info(game: ROMGame):
	#Not sure how to detect 2/6 buttons, or usage of TurboBooster-Plus, but I want to
	equivalent_arcade = None
	for uapce_machine in _get_uapce_games():
		if does_machine_match_game(game.rom.name, game.metadata.names.values(), uapce_machine):
			equivalent_arcade = uapce_machine
			break
	if equivalent_arcade:
		game.metadata.specific_info['Equivalent-Arcade'] = equivalent_arcade

	add_generic_info(game)

	#Apple III: Possible input info: Keyboard and joystick by default, mouse if mouse card exists
	#Coleco Adam: Input info: Keyboard / Coleco numpad?
	#MSX1/2: Input info: Keyboard or joystick; Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper
	#Jaguar input info: There's the default ugly gamepad and also another ugly gamepad with more buttons which I dunno what's compatible with
	#CD-i: That one controller but could also be the light gun thingo
	#Memorex VIS: 4-button wireless not-quite-gamepad-but-effectively-one-thing (A, B, 1, 2), can have 2-button mouse? There are also 3 and 4 buttons and 2-1-Solo switch that aren't emulated yet
	#The rest are weird computers where we can't tell if they use any kind of optional joystick or not so it's like hhhh whaddya do
