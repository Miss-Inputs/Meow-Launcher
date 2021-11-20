import re
from typing import TYPE_CHECKING

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType

from .generic import add_generic_software_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame


#Straightforward stuff that doesn't require a FileROM and has nothing to look into

def add_entex_adventure_vision_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	game.metadata.input_info.add_option(builtin_gamepad)

	#I don't think so mate
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_game_pocket_computer_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	game.metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_gamate_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_casio_pv1000_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)
	#(Start, select,) A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_mega_duck_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_watara_supervision_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_arcadia_info(game: 'ROMGame'):
	keypad = input_metadata.Keypad() #2 controllers hardwired into the system. If MAME is any indication, the buttons on the side don't do anything or are equivalent to keypad 2?
	keypad.keys = 12 #MAME mentions 16 here... maybe some variant systems have more
	stick = input_metadata.NormalController()
	stick.analog_sticks = 1 #According to MAME it's an analog stick but everywhere else suggests it's just digital?
	#controller.face_buttons = 2 #???? Have also heard that the 2 buttons do the same thing as each other
	controller = input_metadata.CombinedController([keypad, stick])
	game.metadata.input_info.add_option(controller)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass
	#Nothing really here other than alt titles (for other languages). I guess this proves that the Bandai Arcadia really isn't different.

def add_astrocade_info(game: 'ROMGame'):
	joystick = input_metadata.NormalController()
	joystick.dpads = 1
	joystick.face_buttons = 1 #Sort of a trigger button, as it's a gun-shaped grip
	#Controller also integrates a paddle

	keypad = input_metadata.Keypad() #Mounted onto the system
	keypad.keys = 24

	controller = input_metadata.CombinedController([joystick, keypad, input_metadata.Paddle()])
	game.metadata.input_info.add_option(controller)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_pc88_info(game: 'ROMGame'):
	#Input info: Keyboard or joystick
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass
	#Needs BASIC V1 or older
	#Mount both disk A and B to start
	#Needs BASIC V1
	#Mount Main disk and Scenario 1 to start
	#Mount Main disk and Scenario 2 to start
	#Needs CD-ROM support
	#Needs N-BASIC

def add_sg1000_info(game: 'ROMGame'):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	uses_tablet = False
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		uses_tablet = software.get_part_feature('peripheral') == 'tablet'
		#There doesn't seem to be a way to know if software is a SC-3000 cart, unless I just say whichever one has the .sc extension. So I'll do that

	if uses_tablet:
		#A drawing tablet, but that's more or less a touchscreen
		#No buttons here?
		game.metadata.input_info.add_option(input_metadata.Touchscreen())
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2
		normal_controller.dpads = 1
		game.metadata.input_info.add_option(normal_controller)

def add_sharp_x1_info(game: 'ROMGame'):
	#Input info: Keyboard and/or joystick

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	#Type FILES then move the cursor to the line of the game and type LOAD (to load) and type RUN when loaded
	#Runs in HuBASIC
	#Load SIRIUS 1 from Extra Hyper
	#Once booted in S-OS, type "L DALK" to load, and "J 9600" to run
	#In BASIC, type FILES to list the disk content

def add_sharp_x68k_info(game: 'ROMGame'):
	#Input info: Keyboard and/or joystick

	#Many games are known to have SaveType.Floppy, but can't tell programmatically...
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass
	#Requires Disk 1 and Disk 3 mounted to boot
	#Use mouse at select screen
	#Requires "Harukanaru Augusta" to work
	#Requires to be installed
	#Requires SX-Windows
	#Use command.x in Human68k OS
	#Type BPHXTST in Human68k OS
	#Type S_MARIO.X in Human68k OS

def add_vc4000_info(game: 'ROMGame'):
	normal_controller = input_metadata.NormalController()
	normal_controller.analog_sticks = 1
	normal_controller.face_buttons = 2

	keypad = input_metadata.Keypad()
	keypad.keys = 12

	controller = input_metadata.CombinedController([normal_controller, keypad])
	game.metadata.input_info.add_option(controller)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_hartung_game_master_info(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_bandai_sv8000_info(game: 'ROMGame'):
	keypad = input_metadata.Keypad() #2 of these
	keypad.keys = 12 #Digits + # *
	joystick = input_metadata.NormalController()
	joystick.dpads = 1 #Keypad with a disc thing on it

	game.metadata.save_type = SaveType.Nothing #I think not

	controller = input_metadata.CombinedController([keypad, joystick])
	game.metadata.input_info.add_option(controller)

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_nichibutsu_my_vision_info(game: 'ROMGame'):
	buttons = input_metadata.NormalController() #Not normal, but closest there is
	#It's like a keyboard except not; MAME defines it as 14-button "mahjong" + 8-way joystick with 1 button and hmm
	buttons.face_buttons = 19 #Numbered 1 to 14 in a row, then A B C D arranged in directions above that, and an E button next to that
	game.metadata.input_info.add_option(buttons)

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_bbc_bridge_companion_info(game: 'ROMGame'):
	buttons = input_metadata.NormalController()
	buttons.face_buttons = 10 #According to the MAME driver, I'm too lazy to look at pictures of the thing
	game.metadata.input_info.add_option(buttons)

	game.metadata.save_type = SaveType.Nothing #Yeah nah

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_cd32_info(game: 'ROMGame'):
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

def add_neogeo_cd_info(game: 'ROMGame'):
	#Apparently there is a mahjong controller too, but... meh
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	game.metadata.input_info.add_option(builtin_gamepad)

def add_juicebox_info(game: 'ROMGame'):
	#Hmm... apparently there's 0x220 bytes at the beginning which need to be copied from retail carts to get homebrew test ROMs to boot
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.face_buttons = 5 #Rewind/forward/stop/play/function
	game.metadata.input_info.add_option(builtin_gamepad)

	game.metadata.save_type = SaveType.Nothing #Nope!

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_fm7_info(game: 'ROMGame'):
	#Possible input info: Keyboard and joystick but barely anything uses said joystick

	#info usage strings to make use of:
	#"Requires FM77AV40" (unsupported system)
	#"Requires FM-77AV40SX" (unsupported system)
	#"Load F-BASIC first, then LOADM &quot;CALLEB&quot; and RUN &quot;MAIN&quot;"
	#"Type RUN&quot;SD1&quot; or RUN&quot;SD2&quot; in F-BASIC"
	#"Run from F-BASIC"
	#"In F-BASIC, set 1 drive and 0 files, then type LOAD&quot;START&quot;,R"
	#"Type RUN&quot;XXX&quot; with XXX=MAGUS, LIZARD, BLUE.FOX or ナイザー in F-BASIC"
	#Sounds like there's a few disks which don't autoboot...
	#"Type LOADM&quot;&quot;,R to load" is on a few tapes
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

def add_super_cassette_vision_info(game: 'ROMGame'):
	keypad = input_metadata.Keypad() #Part of main body of console
	keypad.keys = 12 #Digits + CL EN

	joystick = input_metadata.NormalController() #2 of them hardwired in
	joystick.face_buttons = 2

	game.metadata.input_info.add_option([keypad, joystick])

	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.specific_info['Has Extra RAM?'] = software.has_data_area('ram') #Or feature "slot" ends with "_ram"

def add_super_acan_info(game: 'ROMGame'):
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	controller = input_metadata.NormalController()
	controller.shoulder_buttons = 2
	controller.dpads = 1
	controller.face_buttons = 4 #Also Select + Start
	game.metadata.input_info.add_option(controller)

def add_pc_booter_info(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'PC Booter':
			usage = software.infos.get('user_notes')
		game.metadata.specific_info['Hacked By'] = software.infos.get('cracked')
		#Other info strings seen:
		#OEM = Mercer
		#Original Publisher = Nihon Falcom
		game.metadata.specific_info['Version'] = software.infos.get('version')

def add_vsmile_info(game: 'ROMGame'):
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	controller = input_metadata.NormalController()
	controller.analog_sticks = 1 #Hmm MAME has it as a digital joystick with 8 buttons but Wikipedia says analog, whomst is correct? I dunno
	controller.face_buttons = 4 #Also enter + Learning Zone + exit + help

	game.metadata.input_info.add_option(controller)

def add_vsmile_babby_info(game: 'ROMGame'):
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	controller = input_metadata.NormalController()
	controller.face_buttons = 6 #5 shapes + "fun button" (aka cloud) + apparently the ball is actually just a button; also exit

	game.metadata.input_info.add_option(controller)

def add_vz200_info(game: 'ROMGame'):
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	keyboard = input_metadata.Keyboard()
	keyboard.keys = 45
	#There are in theory joysticks, but they don't seem to ever be a thing
	game.metadata.input_info.add_option(keyboard)

def add_microtan_65_info(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'Requires Joystick':
			joystick = input_metadata.NormalController() #1 start button
			joystick.dpads = 1
			joystick.face_buttons = 2
			game.metadata.input_info.add_option(joystick)
		elif usage == 'Requires Hex Keypad':
			hex_keypad = input_metadata.Keypad()
			hex_keypad.keys = 20
			game.metadata.input_info.add_option(hex_keypad)
		elif usage in {'Requires ASCII Keyboard', 'Requires ASCII Keyboard: A=Up, Z=Down, <=Left, >=Right'}:
			keyboard = input_metadata.Keyboard()
			keyboard.keys = 62
			game.metadata.input_info.add_option(keyboard)
		else:
			game.metadata.add_notes(usage)

def add_pc_engine_cd_info(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
		usage = software.get_info('usage')
		if usage not in ('Game Express CD Card required', 'CD-Rom System Card required'):
			#This is already specified by "requirement"
			game.metadata.add_notes(usage)
	
def add_amstrad_pcw_info(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'Requires CP/M':
			game.metadata.specific_info['Requires CP/M?'] = True

requires_ram_regex = re.compile(r'Requires (\d+) MB of RAM')
def add_fm_towns_info(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage:
			match = requires_ram_regex.match(usage)
			if match:
				game.metadata.specific_info['Minimum RAM'] = match[1]
				if match.end() < len(usage):
					game.metadata.add_notes(usage)

def add_sord_m5_info(game: 'ROMGame'):
	#Input info if I cared: 55 key keyboard + 0 button joystick
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'Requires 36k RAM':
			game.metadata.specific_info['Minimum RAM'] = '36K'
		else:
			game.metadata.add_notes(usage)
	
def add_msx_info(game: 'ROMGame'):
	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage in {'Requires a Japanese system', 'Requires a Japanese system for the Japanese text'}:
			game.metadata.specific_info['Japanese Only?'] = True
		elif usage in {'Requires an Arabic MSX', 'Requires an Arabic MSX2'}:
			game.metadata.specific_info['Arabic Only?'] = True
		else:
			game.metadata.add_notes(usage)
		if 'cart' in software.parts:
			cart_part = software.get_part('cart')
			game.metadata.specific_info['Slot'] = cart_part.get_feature('slot')
			game.metadata.specific_info['PCB'] = cart_part.get_feature('pcb')
			game.metadata.specific_info['Mapper'] = cart_part.get_feature('mapper')
