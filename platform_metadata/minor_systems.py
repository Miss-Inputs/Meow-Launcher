#For mildly uninteresting systems that I still want to add system info for etc
from enum import Enum, auto

import input_metadata
from common_types import SaveType, MediaType
from info.region_info import TVSystem
from software_list_info import get_software_list_entry, get_crc32_for_software_list, find_in_software_lists

def add_entex_adventure_vision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	game.metadata.input_info.add_option([builtin_gamepad])

	#I don't think so mate
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_game_pocket_computer_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	game.metadata.input_info.add_option([builtin_gamepad])

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_gamate_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_casio_pv1000_info(game):
	game.metadata.tv_type = TVSystem.NTSC
	#Japan only. I won't assume the region in case some maniac decides to make homebrew for it or something, but it could only ever be NTSC

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])
	#(Start, select,) A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_mega_duck_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_watara_supervision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_apfm1000_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#There's not really anything in there which tells us if we need the Imagination Machine for a particular cart. There's something about RAM, though.

def add_arcadia_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#Nothing really here other than alt titles (for other languages). I guess this proves that the Bandai Arcadia really isn't different.

def add_astrocade_info(game):
	joystick = input_metadata.NormalController()
	joystick.dpads = 1
	joystick.face_buttons = 1 #Sort of a trigger button, as it's a gun-shaped grip
	#Controller also integrates a paddle

	keypad = input_metadata.Keypad() #Mounted onto the system
	keypad.keys = 24
	game.metadata.input_info.add_option([normal_controller, keypad, input_metadata.Paddle()])

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

def add_casio_pv2000_info(game):
	#Input info is keyboard and joystick I guess? Maybe only one of them sometimes?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_channel_f_info(game):
	#Input info is uhhh that weird twisty thing I guess (I still cannot understand it)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

def add_pc88_info(game):
	#Input info: Keyboard or joystick

	game.metadata.tv_type = TVSystem.NTSC
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#TODO: Tell us if this is part of a multi-floppy thing

def add_sg1000_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	uses_tablet = False
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		uses_tablet = software.get_part_feature('peripheral') == 'tablet'
		#There doesn't seem to be a way to know if software is a SC-3000 cart, unless I just say whichever one has the .sc extension. So I'll do that

	if uses_tablet:
		#A drawing tablet, but that's more or less a touchscreen
		#No buttons here?
		game.metadata.input_info.add_option([input_metadata.Touchscreen()])
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2
		normal_controller.dpads = 1
		game.metadata.input_info.add_option([normal_controller])

def add_sharp_x1_info(game):
	#Input info: Keyboard and/or joystick

	game.metadata.tv_type = TVSystem.NTSC
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#TODO: Tell us if this is part of a multi-floppy thing

def add_sharp_x68k_info(game):
	#Input info: Keyboard and/or joystick

	game.metadata.tv_type = TVSystem.NTSC
	#Many games are known to have SaveType.Floppy, but can't tell programmatically...
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#TODO: Tell us if this is part of a multi-floppy thing

def add_tomy_tutor_info(game):
	#Input info: Keyboard and/or joystick

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_vc4000_info(game):
	normal_controller = input_metadata.NormalController()
	normal_controller.analog_sticks = 1
	normal_controller.face_buttons = 2

	keypad = input_metadata.Keypad()
	keypad.keys = 12
	game.metadata.input_info.add_option([normal_controller, keypad])

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_vic10_info(game):
	#Input info: Keyboard or joystick

	has_header = game.metadata.media_type == MediaType.Cartridge and (game.rom.get_size() % 256) == 2
	game.metadata.specific_info['Headered'] = has_header
	software = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#What the heck is an "assy"?

def add_vic20_info(game):
	#Input info: Keyboard and/or joystick

	has_header = game.metadata.media_type == MediaType.Cartridge and (game.rom.get_size() % 256) == 2
	game.metadata.specific_info['Headered'] = has_header
	software = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

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
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

		usage = game.metadata.specific_info['Notes']
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

	normal_controller = input_metadata.NormalController()
	normal_controller.face_buttons = 2
	normal_controller.dpads = 1
	normal_controller_keypad = input_metadata.Keypad()
	normal_controller_keypad.keys = 12
	#TODO: This doesn't look right, maybe make some kind of CombinedController thing

	super_action_controller = input_metadata.NormalController()
	super_action_controller.face_buttons = 4
	#Something called a "speed roller" ???
	super_action_controller_keypad = input_metadata.Keypad()
	super_action_controller_keypad.keys = 12

	roller_controller = input_metadata.Trackball()
	#Not sure how many buttons?
	driving_controller = input_metadata.SteeringWheel()
	#Gas pedal is on + off so I guess it counts as one button

	game.metadata.specific_info['Peripheral'] = peripheral
	if peripheral == ColecoController.Normal:
		game.metadata.input_info.add_option([normal_controller, normal_controller_keypad])
	else:
		if peripheral == ColecoController.DrivingController:
			game.metadata.input_info.add_option([driving_controller])
		elif peripheral == ColecoController.RollerController:
			game.metadata.input_info.add_option([roller_controller])
		elif peripheral == ColecoController.SuperActionController:
			game.metadata.input_info.add_option([super_action_controller, super_action_controller_keypad])
		if not peripheral_required:
			game.metadata.input_info.add_option([normal_controller, normal_controller_keypad])
	#Doesn't look like you can set controller via command line at the moment, oh well

def add_hartung_game_master_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

def add_bandai_sv8000_info(game):
	game.metadata.tv_type = TVSystem.NTSC #Japan only
	#TODO Input info: Some wanky pair of keypads, thanks I hate it

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

def add_nichibutsu_my_vision_info(game):
	game.metadata.tv_type = TVSystem.NTSC #Japan only
	#TODO Input info: Some kinda weird partial-keyboard thingy

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

def add_bbc_bridge_companion_info(game):
	game.metadata.tv_type = TVSystem.PAL #UK only

	buttons = input_metadata.NormalController()
	buttons.face_buttons = 10 #According to the MAME driver, I'm too lazy to look at pictures of the thing
	game.metadata.input_info.add_option([buttons])

	game.metadata.save_type = SaveType.Nothing #Yeah nah

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

#-- Beyond this point, there may be unexplored things which may result in these systems being spun off into their own module. Maybe. It just seems likely. Or maybe I do know full well they have a header, and either I haven't explored it yet, or I'm just a lazy bugger

def add_amiga_info(game):
	software = get_software_list_entry(game)
	chipset = None
	if software:
		software.add_generic_info(game)
		chipset = 'OCS'
		if software.get_info('usage') == 'Requires ECS':
			chipset = 'ECS'
		elif software.get_info('usage') == 'Requires AGA':
			chipset = 'AGA'

	if not chipset:
		for tag in game.filename_tags:
			if tag in ('(AGA)', '(OCS-AGA)'):
				chipset = 'AGA'
				break
	game.metadata.specific_info['Chipset'] = chipset

def add_cd32_info(game):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])

def add_neogeo_cd_info(game):
	#Apparently there is a mahjong controller too, but... meh
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	game.metadata.input_info.add_option([builtin_gamepad])

def add_ibm_pcjr_info(game):
	#TODO .jrc files should have a header with something in them, so eventually, IBM PCjr will get its own module here
	#Input info: Keyboard or joystick

	magic = game.rom.read(amount=25)
	is_headered = magic == b'PCjr Cartridge image file'
	game.metadata.specific_info['Headered'] = is_headered

	software = get_software_list_entry(game, skip_header=512 if is_headered else 0)
	if software:
		software.add_generic_info(game)
		#TODO: If sharedfeat requirement = ibmpcjr_flop:pcdos21, do something about that
		#Probably get the MAME command line to get a PC DOS 2.1 floppy path from specific_config provided by the user, or else they don't get to use ColorPaint
		#Lotus 123jr has a similar predicament, but it also needs .m3u I guess

def _does_intellivision_part_match(part, data, _):
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
	#Input info: Crappy keypad, but also a keyboard component and computer module exists, also a piano keyboard
	software = find_in_software_lists(game.software_lists, crc=game.rom.read(), part_matcher=_does_intellivision_part_match)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

		usage = game.metadata.specific_info.get('Notes')
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
	game.metadata.input_info.add_option([builtin_gamepad])

	game.metadata.save_type = SaveType.Nothing #Nope!

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_atari_5200_info(game):
	#Can get the title screen information from inside the ROM to get the year (and also title). But that's hella unreliable, won't work properly for homebrews released after 2000, and requires implementing the 5200 title screen's custom character set (which I do know, it's just a pain in the arse)

	uses_trackball = False
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		uses_trackball = software.get_part_feature('peripheral') == 'trackball'

	game.metadata.save_type = SaveType.Nothing #Probably

	#This doesn't really matter anyway, because MAME doesn't let you select controller type by slot device yet; and none of the other 5200 emulators are cool
	game.metadata.specific_info['Uses-Trackball'] = uses_trackball

	if uses_trackball:
		game.metadata.input_info.add_option([input_metadata.Trackball()])
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2 #1, 2, (Pause, Reset, Start) I think? I think it works the same way for trackballs
		normal_controller.analog_sticks = 1
		game.metadata.input_info.add_option([normal_controller])

def add_game_com_info(game):
	#Could have its own header. I think it does, but like.. who's gonna document such a thing? The wide community of Game.com enthusiasts?
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #A B C D
	game.metadata.input_info.add_option([builtin_gamepad])

	#Might have saving, actually. I'm just not sure about how it works.

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_lynx_info(game):
	#TODO .lnx files should have a header with something in them, so eventually, Lynx will get its own module here
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.add_option([builtin_gamepad])

	magic = game.rom.read(amount=4)
	is_headered = magic == b'LYNX'
	game.metadata.specific_info['Headered'] = is_headered

	software = get_software_list_entry(game, skip_header=64 if is_headered else 0)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_apple_ii_info(game):
	#Possible input info: Keyboard and joystick by default, mouse if mouse card exists

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		if software.get_info('usage') == 'Works with Apple II Mouse Card in slot 4: -sl4 mouse':
			#Not setting up input_info just yet because I don't know if it uses joystick/keyboard as well. I guess I probably never will, but like... well.... dang
			game.metadata.specific_info['Uses-Mouse'] = True
		game.metadata.product_code = software.get_info('serial')

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

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_super_cassette_vision_info(game):
	#TODO Input iunfo: Joystick + keypad thingo
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.specific_info['Has-Extra-RAM'] = software.has_data_area('ram') #Or feature "slot" ends with "_ram"

def add_stub_info(game):
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

	#TODO PET: Add keyboard as input info, there are theoretically userport joysticks but nah
	#Apple III: Possible input info: Keyboard and joystick by default, mouse if mouse card exists
	#PC Engine: Input could be 2 buttons or 6 buttons, usually the former. Might be other types too? Some games should have saving via TurboBooster-Plus (Wii U VC seems to let me save in Neutopia anyway without passwords or savestates), which I guess would be SaveType.Internal
	#Coleco Adam: Input info: Keyboard / Coleco numpad?
	#MSX1/2: Input info: Keyboard or joystick; Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper
	#GX4000: Input info: 2-button gamepad, analog stick, or light gun (Skeet Shoot, The Enforcer); gx4000.xml software list decides to put that inside a comment above the <software> element rather than anything parseable
	#Sord M5: Input info: Keyboard, maybe joystick? Take note of info > usage = requiring 36K RAM, though we just set our M5 to have max RAM anyway, seems to be harmless
