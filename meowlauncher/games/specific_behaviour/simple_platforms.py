import re
from typing import TYPE_CHECKING

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.metadata import Metadata

#Straightforward stuff that doesn't require a FileROM and has nothing to look into

def add_entex_adventure_vision_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	metadata.input_info.add_option(builtin_gamepad)

	#I don't think so mate
	metadata.save_type = SaveType.Nothing

def add_game_pocket_computer_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_gamate_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_casio_pv1000_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)
	#(Start, select,) A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_mega_duck_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)
	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_watara_supervision_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_arcadia_info(metadata: 'Metadata'):
	keypad = input_metadata.Keypad() #2 controllers hardwired into the system. If MAME is any indication, the buttons on the side don't do anything or are equivalent to keypad 2?
	keypad.keys = 12 #MAME mentions 16 here... maybe some variant systems have more
	stick = input_metadata.NormalController()
	stick.analog_sticks = 1 #According to MAME it's an analog stick but everywhere else suggests it's just digital?
	#controller.face_buttons = 2 #???? Have also heard that the 2 buttons do the same thing as each other
	controller = input_metadata.CombinedController([keypad, stick])
	metadata.input_info.add_option(controller)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_astrocade_info(metadata: 'Metadata'):
	joystick = input_metadata.NormalController()
	joystick.dpads = 1
	joystick.face_buttons = 1 #Sort of a trigger button, as it's a gun-shaped grip
	#Controller also integrates a paddle

	keypad = input_metadata.Keypad() #Mounted onto the system
	keypad.keys = 24

	controller = input_metadata.CombinedController([joystick, keypad, input_metadata.Paddle()])
	metadata.input_info.add_option(controller)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_vc4000_info(metadata: 'Metadata'):
	normal_controller = input_metadata.NormalController()
	normal_controller.analog_sticks = 1
	normal_controller.face_buttons = 2

	keypad = input_metadata.Keypad()
	keypad.keys = 12

	controller = input_metadata.CombinedController([normal_controller, keypad])
	metadata.input_info.add_option(controller)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_hartung_game_master_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

def add_vz200_info(metadata: 'Metadata'):
	keyboard = input_metadata.Keyboard()
	keyboard.keys = 45
	#There are in theory joysticks, but they don't seem to ever be a thing
	metadata.input_info.add_option(keyboard)

def add_bandai_sv8000_info(metadata: 'Metadata'):
	keypad = input_metadata.Keypad() #2 of these
	keypad.keys = 12 #Digits + # *
	joystick = input_metadata.NormalController()
	joystick.dpads = 1 #Keypad with a disc thing on it

	metadata.save_type = SaveType.Nothing #I think not

	controller = input_metadata.CombinedController([keypad, joystick])
	metadata.input_info.add_option(controller)

def add_nichibutsu_my_vision_info(metadata: 'Metadata'):
	buttons = input_metadata.NormalController() #Not normal, but closest there is
	#It's like a keyboard except not; MAME defines it as 14-button "mahjong" + 8-way joystick with 1 button and hmm
	buttons.face_buttons = 19 #Numbered 1 to 14 in a row, then A B C D arranged in directions above that, and an E button next to that
	metadata.input_info.add_option(buttons)

def add_bbc_bridge_companion_info(metadata: 'Metadata'):
	buttons = input_metadata.NormalController()
	buttons.face_buttons = 10 #According to the MAME driver, I'm too lazy to look at pictures of the thing
	metadata.input_info.add_option(buttons)

	metadata.save_type = SaveType.Nothing #Yeah nah

def add_cd32_info(metadata: 'Metadata'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

def add_neogeo_cd_info(metadata: 'Metadata'):
	#Apparently there is a mahjong controller too, but... meh
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	metadata.input_info.add_option(builtin_gamepad)

def add_juicebox_info(metadata: 'Metadata'):
	#Hmm... apparently there's 0x220 bytes at the beginning which need to be copied from retail carts to get homebrew test ROMs to boot
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.face_buttons = 5 #Rewind/forward/stop/play/function
	metadata.input_info.add_option(builtin_gamepad)

	metadata.save_type = SaveType.Nothing #Nope!

def add_super_cassette_vision_info(metadata: 'Metadata'):
	keypad = input_metadata.Keypad() #Part of main body of console
	keypad.keys = 12 #Digits + CL EN

	joystick = input_metadata.NormalController() #2 of them hardwired in
	joystick.face_buttons = 2

	metadata.input_info.add_option([keypad, joystick])

def add_super_acan_info(metadata: 'Metadata'):
	controller = input_metadata.NormalController()
	controller.shoulder_buttons = 2
	controller.dpads = 1
	controller.face_buttons = 4 #Also Select + Start
	metadata.input_info.add_option(controller)

def add_vsmile_info(metadata: 'Metadata'):
	controller = input_metadata.NormalController()
	controller.analog_sticks = 1 #Hmm MAME has it as a digital joystick with 8 buttons but Wikipedia says analog, whomst is correct? I dunno
	controller.face_buttons = 4 #Also enter + Learning Zone + exit + help

	metadata.input_info.add_option(controller)

def add_vsmile_babby_info(metadata: 'Metadata'):
	controller = input_metadata.NormalController()
	controller.face_buttons = 6 #5 shapes + "fun button" (aka cloud) + apparently the ball is actually just a button; also exit

	metadata.input_info.add_option(controller)

def add_pc_booter_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'PC Booter':
		usage = software.infos.get('user_notes')
	metadata.specific_info['Hacked By'] = software.infos.get('cracked')
	#Other info strings seen:
	#OEM = Mercer
	#Original Publisher = Nihon Falcom
	metadata.specific_info['Version'] = software.infos.get('version')

def add_super_cassette_vision_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	metadata.specific_info['Has Extra RAM?'] = software.has_data_area('ram') #Or feature "slot" ends with "_ram"

def add_microtan_65_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'Requires Joystick':
		joystick = input_metadata.NormalController() #1 start button
		joystick.dpads = 1
		joystick.face_buttons = 2
		metadata.input_info.add_option(joystick)
	elif usage == 'Requires Hex Keypad':
		hex_keypad = input_metadata.Keypad()
		hex_keypad.keys = 20
		metadata.input_info.add_option(hex_keypad)
	elif usage in {'Requires ASCII Keyboard', 'Requires ASCII Keyboard: A=Up, Z=Down, <=Left, >=Right'}:
		keyboard = input_metadata.Keyboard()
		keyboard.keys = 62
		metadata.input_info.add_option(keyboard)
	else:
		metadata.add_notes(usage)

def add_pc_engine_cd_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
	usage = software.get_info('usage')
	if usage not in ('Game Express CD Card required', 'CD-Rom System Card required'):
		#This is already specified by "requirement"
		metadata.add_notes(usage)
	
def add_amstrad_pcw_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'Requires CP/M':
		metadata.specific_info['Requires CP/M?'] = True

_requires_ram_regex = re.compile(r'Requires (\d+) MB of RAM')
def add_fm_towns_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage:
		match = _requires_ram_regex.match(usage)
		if match:
			metadata.specific_info['Minimum RAM'] = match[1]
			if match.end() < len(usage):
				metadata.add_notes(usage)

def add_sord_m5_software_info(software: 'Software', metadata: 'Metadata'):
	#Input info if I cared: 55 key keyboard + 0 button joystick
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'Requires 36k RAM':
		metadata.specific_info['Minimum RAM'] = '36K'
	else:
		metadata.add_notes(usage)
	
def add_msx_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage in {'Requires a Japanese system', 'Requires a Japanese system for the Japanese text'}:
		metadata.specific_info['Japanese Only?'] = True
	elif usage in {'Requires an Arabic MSX', 'Requires an Arabic MSX2'}:
		metadata.specific_info['Arabic Only?'] = True
	else:
		metadata.add_notes(usage)
	if 'cart' in software.parts:
		cart_part = software.get_part('cart')
		metadata.specific_info['Slot'] = cart_part.get_feature('slot')
		metadata.specific_info['PCB'] = cart_part.get_feature('pcb')
		metadata.specific_info['Mapper'] = cart_part.get_feature('mapper')

def add_sg1000_software_info(software: 'Software', metadata: 'Metadata'):
	metadata.save_type = SaveType.Nothing #Until proven otherwise

	software.add_standard_metadata(metadata)
	uses_tablet = software.get_part_feature('peripheral') == 'tablet'
	#There doesn't seem to be a way to know if software is a SC-3000 cart, unless I just say whichever one has the .sc extension. So I'll do that

	if uses_tablet:
		#A drawing tablet, but that's more or less a touchscreen
		#No buttons here?
		metadata.input_info.add_option(input_metadata.Touchscreen())
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2
		normal_controller.dpads = 1
		metadata.input_info.add_option(normal_controller)
	