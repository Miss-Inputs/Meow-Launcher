#For mildly uninteresting systems that I still want to add system info for etc
import re
from enum import Enum, auto

import input_metadata
from common_types import MediaType, SaveType
from info.region_info import TVSystem
from mame_helpers import MAMENotInstalledException
from mame_machine import does_machine_match_game, get_machines_from_source_file
from software_list_info import (find_in_software_lists_with_custom_matcher,
                                get_crc32_for_software_list,
                                get_software_list_entry)


def add_entex_adventure_vision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	game.metadata.input_info.add_option(builtin_gamepad)

	#I don't think so mate
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_game_pocket_computer_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	game.metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_gamate_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_casio_pv1000_info(game):
	game.metadata.tv_type = TVSystem.NTSC
	#Japan only. I won't assume the region in case some maniac decides to make homebrew for it or something, but it could only ever be NTSC

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)
	#(Start, select,) A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_mega_duck_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_watara_supervision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_apfm1000_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)
	#There's not really anything in there which tells us if we need the Imagination Machine for a particular cart. There's something about RAM, though.

def add_arcadia_info(game):
	keypad = input_metadata.Keypad() #2 controllers hardwired into the system. If MAME is any indication, the buttons on the side don't do anything or are equivalent to keypad 2?
	keypad.keys = 12 #MAME mentions 16 here... maybe some variant systems have more
	stick = input_metadata.NormalController()
	stick.analog_sticks = 1 #According to MAME it's an analog stick but everywhere else suggests it's just digital?
	#controller.face_buttons = 2 #???? Have also heard that the 2 buttons do the same thing as each other
	controller = input_metadata.CombinedController([keypad, stick])
	game.metadata.input_info.add_option(controller)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)
	#Nothing really here other than alt titles (for other languages). I guess this proves that the Bandai Arcadia really isn't different.

def add_astrocade_info(game):
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

	add_generic_info(game)

def add_casio_pv2000_info(game):
	#Input info is keyboard and joystick I guess? Maybe only one of them sometimes?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_channel_f_info(game):
	#Input info is uhhh that weird twisty thing I guess (I still cannot understand it)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)
	#Usage: Hit CTRL and A to start.

def add_pc88_info(game):
	#Input info: Keyboard or joystick

	game.metadata.tv_type = TVSystem.NTSC
	add_generic_info(game)
	#Needs BASIC V1 or older
	#Mount both disk A and B to start
	#Needs BASIC V1
	#Mount Main disk and Scenario 1 to start
	#Mount Main disk and Scenario 2 to start
	#Needs CD-ROM support
	#Needs N-BASIC

def add_sg1000_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	uses_tablet = False
	software = get_software_list_entry(game)
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

def add_sharp_x1_info(game):
	#Input info: Keyboard and/or joystick

	game.metadata.tv_type = TVSystem.NTSC
	add_generic_info(game)
	#Type FILES then move the cursor to the line of the game and type LOAD (to load) and type RUN when loaded
	#Runs in HuBASIC
	#Load SIRIUS 1 from Extra Hyper
	#Once booted in S-OS, type "L DALK" to load, and "J 9600" to run
	#In BASIC, type FILES to list the disk content

def add_sharp_x68k_info(game):
	#Input info: Keyboard and/or joystick

	game.metadata.tv_type = TVSystem.NTSC
	#Many games are known to have SaveType.Floppy, but can't tell programmatically...
	add_generic_info(game)
	#Requires Disk 1 and Disk 3 mounted to boot
	#Use mouse at select screen
	#Requires "Harukanaru Augusta" to work
	#Requires to be installed
	#Requires SX-Windows
	#Use command.x in Human68k OS
	#Type BPHXTST in Human68k OS
	#Type S_MARIO.X in Human68k OS

def add_tomy_tutor_info(game):
	#Input info: Keyboard (56 keys) and/or joystick (2 buttons + dpad)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_vc4000_info(game):
	normal_controller = input_metadata.NormalController()
	normal_controller.analog_sticks = 1
	normal_controller.face_buttons = 2

	keypad = input_metadata.Keypad()
	keypad.keys = 12

	controller = input_metadata.CombinedController([normal_controller, keypad])
	game.metadata.input_info.add_option(controller)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	add_generic_info(game)

def add_vic10_info(game):
	#Input info: Keyboard or joystick

	has_header = game.metadata.media_type == MediaType.Cartridge and (game.rom.get_size() % 256) == 2
	game.metadata.specific_info['Headered'] = has_header
	software = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		software.add_standard_metadata(game.metadata)
		#What the heck is an "assy"?

def add_vic20_info(game):
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
			game.metadata.notes = notes
		
		#Enter 'SYS <some number>' to run
		#Needs VICKIT 4 to run
		#SYS 40969 for 40 column mode, SYS 40972 for 80 column mode, SYS 40975 for VIC mode, SYS 40978 to restart 40/80 column mode

class ColecoController(Enum):
	Normal = auto()
	SuperActionController = auto()
	RollerController = auto()
	DrivingController = auto()

def add_colecovision_info(game):
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
			game.metadata.notes = usage

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

def add_hartung_game_master_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

	add_generic_info(game)

def add_bandai_sv8000_info(game):
	game.metadata.tv_type = TVSystem.NTSC #Japan only

	keypad = input_metadata.Keypad() #2 of these
	keypad.keys = 12 #Digits + # *
	joystick = input_metadata.NormalController()
	joystick.dpads = 1 #Keypad with a disc thing on it

	game.metadata.save_type = SaveType.Nothing #I think not

	controller = input_metadata.CombinedController([keypad, joystick])
	game.metadata.input_info.add_option(controller)

	add_generic_info(game)

def add_nichibutsu_my_vision_info(game):
	game.metadata.tv_type = TVSystem.NTSC #Japan only

	buttons = input_metadata.NormalController() #Not normal, but closest there is
	#It's like a keyboard except not; MAME defines it as 14-button "mahjong" + 8-way joystick with 1 button and hmm
	buttons.face_buttons = 19 #Numbered 1 to 14 in a row, then A B C D arranged in directions above that, and an E button next to that
	game.metadata.input_info.add_option(buttons)

	add_generic_info(game)

def add_bbc_bridge_companion_info(game):
	game.metadata.tv_type = TVSystem.PAL #UK only

	buttons = input_metadata.NormalController()
	buttons.face_buttons = 10 #According to the MAME driver, I'm too lazy to look at pictures of the thing
	game.metadata.input_info.add_option(buttons)

	game.metadata.save_type = SaveType.Nothing #Yeah nah

	add_generic_info(game)

def add_cd32_info(game):
	add_generic_info(game)
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2
	game.metadata.input_info.add_option(builtin_gamepad)

def add_neogeo_cd_info(game):
	#Apparently there is a mahjong controller too, but... meh
	add_generic_info(game)
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	game.metadata.input_info.add_option(builtin_gamepad)

def add_ibm_pcjr_info(game):
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
		#Probably get the MAME command line to get a PC DOS 2.1 floppy path from system_config provided by the user, or else they don't get to use ColorPaint
		#Lotus 123jr has a similar predicament, but it also needs .m3u I guess

		#Usages:
		#Mount both carts and a DOS floppy and type 'TUTOR'
		#Boot from a DOS floppy and type 'G'

def _does_intellivision_part_match(part, data):
	total_size = 0
	number_of_roms = 0

	offset = 0
	for data_area in part.data_areas.values():
		#'name' attribute here is actually where in the Intellivision memory map it gets loaded to, not the offset in the file like I keep thinking

		size = data_area.size

		if not data_area.roms:
			continue

		rom = data_area.roms[0]
		number_of_roms += 1
		total_size += size

		crc32 = rom.crc32
		segment = data[offset: offset + size]
		segment_crc32 = get_crc32_for_software_list(segment)
		if segment_crc32 != crc32:
			return False

		offset += size

	if number_of_roms == 0:
		return False

	if total_size != len(data):
		return False

	return True

def add_intellivision_info(game):
	#There's probably some way to get info from title screen in ROM, but I haven't explored that in ROMniscience yet
	#Input info: Keyboard Module, ECS (49 keys), or 12-key keypad + 3 buttons + dpad (I don't think it's actually a paddle unless I'm proven otherwise), or Music Synthesizer (49 keys) (TODO add this I'm tired right now)
	software = find_in_software_lists_with_custom_matcher(game.software_lists, _does_intellivision_part_match, [game.rom.read()])
	if software:
		software.add_standard_metadata(game.metadata)

		usage = software.get_info('usage')
		if usage == 'Uses Intellivoice':
			game.metadata.specific_info['Uses-Intellivoice'] = True
		elif usage in ('Requires ECS and Keyboard', 'Requires ECS and Intellivoice'):
			#Both of these are functionally the same for our intent and purpose, as MAME's intvecs driver always has a keyboard and Intellivoice module. I dunno if an Intellivision ECS without a keyboard is even a thing.
			game.metadata.specific_info['Uses-ECS'] = True

		#Other usage notes:
		#Will not run on Intellivision 2
		#This cart has unique Left and Right overlays
		#Requires ECS and Music Synthesizer

		#We don't have any reason to use the intv2 driver so that's not a worry; overlays aren't really a concern either, and I dunno about this music synthesizer thing

def add_juicebox_info(game):
	#Hmm... apparently there's 0x220 bytes at the beginning which need to be copied from retail carts to get homebrew test ROMs to boot
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.face_buttons = 5 #Rewind/forward/stop/play/function
	game.metadata.input_info.add_option(builtin_gamepad)

	game.metadata.save_type = SaveType.Nothing #Nope!

	add_generic_info(game)

def add_atari_5200_info(game):
	#Can get the title screen information from inside the ROM to get the year (and also title). But that's hella unreliable, won't work properly for homebrews released after 2000, and requires implementing the 5200 title screen's custom character set (which I do know, it's just a pain in the arse)

	uses_trackball = False
	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		uses_trackball = software.get_part_feature('peripheral') == 'trackball'

	game.metadata.save_type = SaveType.Nothing #Probably

	#This doesn't really matter anyway, because MAME doesn't let you select controller type by slot device yet; and none of the other 5200 emulators are cool
	game.metadata.specific_info['Uses-Trackball'] = uses_trackball

	if uses_trackball:
		game.metadata.input_info.add_option(input_metadata.Trackball())
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2 #1, 2, (Pause, Reset, Start) I think? I think it works the same way for trackballs
		normal_controller.analog_sticks = 1
		game.metadata.input_info.add_option(normal_controller)

def add_fm7_info(game):
	#Possible input info: Keyboard and joystick but barely anything uses said joystick
	game.metadata.tv_type = TVSystem.NTSC #Japan only

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
	add_generic_info(game)

def add_super_cassette_vision_info(game):
	keypad = input_metadata.Keypad() #Part of main body of console
	keypad.keys = 12 #Digits + CL EN

	joystick = input_metadata.NormalController() #2 of them hardwired in
	joystick.face_buttons = 2

	game.metadata.input_info.add_option([keypad, joystick])

	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.specific_info['Has-Extra-RAM'] = software.has_data_area('ram') #Or feature "slot" ends with "_ram"

def add_super_acan_info(game):
	add_generic_info(game)
	controller = input_metadata.NormalController()
	controller.shoulder_buttons = 2
	controller.dpads = 1
	controller.face_buttons = 4 #Also Select + Start
	game.metadata.input_info.add_option(controller)

def add_pc_booter_info(game):
	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'PC Booter':
			usage = software.infos.get('user_notes')
		game.metadata.specific_info['Hacked-By'] = software.infos.get('cracked')
		#Other info strings seen:
		#OEM = Mercer
		#Original Publisher = Nihon Falcom
		game.metadata.specific_info['Version'] = software.infos.get('version')

def add_vsmile_info(game):
	add_generic_info(game)
	controller = input_metadata.NormalController()
	controller.analog_sticks = 1 #Hmm MAME has it as a digital joystick with 8 buttons but Wikipedia says analog, whomst is correct? I dunno
	controller.face_buttons = 4 #Also enter + Learning Zone + exit + help

	game.metadata.input_info.add_option(controller)

def add_vsmile_babby_info(game):
	add_generic_info(game)
	controller = input_metadata.NormalController()
	controller.face_buttons = 6 #5 shapes + "fun button" (aka cloud) + apparently the ball is actually just a button; also exit

	game.metadata.input_info.add_option(controller)

def add_vz200_info(game):
	add_generic_info(game)
	keyboard = input_metadata.Keyboard()
	keyboard.keys = 45
	#There are in theory joysticks, but they don't seem to ever be a thing
	game.metadata.input_info.add_option(keyboard)

def add_pet_info(game):
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

def add_microtan_65_info(game):
	software = get_software_list_entry(game)
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
		elif usage in ('Requires ASCII Keyboard', 'Requires ASCII Keyboard: A=Up, Z=Down, <=Left, >=Right'):
			keyboard = input_metadata.Keyboard()
			keyboard.keys = 62
			game.metadata.input_info.add_option(keyboard)
		else:
			game.metadata.notes = usage

def _get_uapce_games():
	try:
		return _get_uapce_games.result
	except AttributeError:
		try:
			_get_uapce_games.result = list(get_machines_from_source_file('uapce'))
		except MAMENotInstalledException:
			return []
		return _get_uapce_games.result

def add_pc_engine_info(game):
	#Not sure how to detect 2/6 buttons, or usage of TurboBooster-Plus, but I want to
	equivalent_arcade = None
	for uapce_machine in _get_uapce_games():
		if does_machine_match_game(game.rom.name, game.metadata, uapce_machine):
			equivalent_arcade = uapce_machine
			break
	if equivalent_arcade:
		game.metadata.specific_info['Equivalent-Arcade'] = equivalent_arcade

	add_generic_info(game)
	
def add_amstrad_pcw_info(game):
	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'Requires CP/M':
			game.metadata.specific_info['Requires-CPM'] = True

requires_ram_regex = re.compile(r'Requires (\d+) MB of RAM')
def add_fm_towns_info(game):
	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		match = requires_ram_regex.match(usage)
		if match:
			game.metadata.specific_info['Minimum-RAM'] = match[1]
			if match.end() < len(usage):
				game.metadata.notes = usage

def add_generic_info(game):
	#For any system not otherwise specified
	software = get_software_list_entry(game)

	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.notes = software.get_info('usage')
		game.metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
		for info_name, info_value in software.infos.items():
			if info_name in ('usage', 'release', 'serial', 'developer', 'alt_title', 'alt_name', 'alt_disk', 'barcode', 'ring_code', 'version'):
				#We have already added this
				continue
			game.metadata.specific_info[info_name.replace('_', '-').replace(' ', '-').title()] = info_value

	#TODO:
	#Apple III: Possible input info: Keyboard and joystick by default, mouse if mouse card exists
	#Coleco Adam: Input info: Keyboard / Coleco numpad?
	#MSX1/2: Input info: Keyboard or joystick; Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper
	#GX4000: Input info: 2-button gamepad, analog stick, or light gun (Skeet Shoot, The Enforcer); gx4000.xml software list decides to put that inside a comment above the <software> element rather than anything parseable
	#Sord M5: Input info: Keyboard (55 keys), maybe joystick (0 buttons??)? Take note of info > usage = requiring 36K RAM, though we just set our M5 to have max RAM anyway, seems to be harmless
	#Jaguar input info: There's the default ugly gamepad and also another ugly gamepad with more buttons which I dunno what's compatible with
	#CD-i: That one controller but could also be the light gun thingo
	#Memorex VIS: 4-button wireless not-quite-gamepad-but-effectively-one-thing (A, B, 1, 2), can have 2-button mouse? There are also 3 and 4 buttons and 2-1-Solo switch that aren't emulated yet
	#The rest are weird computers where we can't tell if they use any kind of optional joystick or not so it's like hhhh whaddya do
