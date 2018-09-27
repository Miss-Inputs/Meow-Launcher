#For mildly uninteresting systems that I still want to add system info for etc

import input_metadata
from metadata import SaveType
from info.region_info import TVSystem
from software_list_info import get_software_list_entry, _does_split_rom_match, find_in_software_lists

def add_entex_adventure_vision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalInput()
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

	builtin_gamepad = input_metadata.NormalInput()
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

	builtin_gamepad = input_metadata.NormalInput()
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

	builtin_gamepad = input_metadata.NormalInput()
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

	builtin_gamepad = input_metadata.NormalInput()
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

	builtin_gamepad = input_metadata.NormalInput()
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
	#TODO: Input info should always be keypad... I think?

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

def add_msx_info(game):
	#I'll use this for MSX2 as well for now
	#Input info: Keyboard or joystick

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper

def add_pc88_info(game):
	#Input info: Keyboard or joystick

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
		normal_controller = input_metadata.NormalInput()
		normal_controller.face_buttons = 2
		normal_controller.dpads = 1
		game.metadata.input_info.add_option([normal_controller])

def add_sharp_x1_info(game):
	#Input info: Keyboard and/or joystick

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#TODO: Tell us if this is part of a multi-floppy thing

def add_sharp_x68k_info(game):
	#Input info: Keyboard and/or joystick

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
	normal_controller = input_metadata.NormalInput()
	normal_controller.analog_sticks = 1
	normal_controller.face_buttons = 2
	#Keypad is 12 buttons
	game.metadata.input_info.add_option([normal_controller, input_metadata.Keypad()])

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_vic10_info(game):
	#Input info: Keyboard or joystick

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#What the heck is an "assy"?

def add_vic20_info(game):
	#Input info: Keyboard and/or joystick

	#TODO: Is it possible that .a0 etc might have the header too? It shouldn't, but files get misnamed sometimes
	#This won't work with >8KB carts at the moment, because MAME stores those in the software list as two separate ROMs. But then they won't have launchers anyway because our only emulator for VIC-20 is MAME itself, and it doesn't let us just put the two ROMs together ourselves, those games are basically software list only at the moment (because it won't let us have one single file above 8KB).
	has_header = game.rom.extension in ('prg', 'crt') and (game.rom.get_size() % 256) == 2
	software = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_sord_m5_info(game):
	#Input info: Keyboard, maybe joystick?

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')
		#Take note of info > usage = requiring 36K RAM, though we just set our M5 to have max RAM anyway, seems to be harmless

def add_gx4000_info(game):
	#Input info: 2-button gamepad, analog stick, or light gun (Skeet Shoot, The Enforcer); gx4000.xml software list decides to put that inside a comment above the <software> element rather than anything parseable

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

def add_colecovision_info(game):
	#Can get year, publisher unreliably from the title screen info in the ROM; please do not do that
	#Input info: controller, but also steering wheel (Expansion Module 2), roller controller, or Super Action Controller
	#TODO: Parse these usage strings:
	#Supports Super Action Controllers
	#Requires Super Action Controllers
	#Supports roller controller
	#Requires roller controller
	#Supports driving controller
	#Requires driving controller

	software = find_in_software_lists(game.software_lists, game.rom, part_matcher=_does_split_rom_match)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_coleco_adam_info(game):
	#Input info: Keyboard / Coleco numpad?

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

def add_hartung_game_master_info(game):
	builtin_gamepad = input_metadata.NormalInput()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)

#-- Beyond this point, there may be unexplored things which may result in these systems being spun off into their own module. Maybe. It just seems likely. Or maybe I do know full well they have a header, and either I haven't explored it yet, or I'm just a lazy bugger

def add_amiga_info(game):
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		chipset = 'OCS'
		if software.get_info('usage') == 'Requires ECS':
			chipset = 'ECS'
		elif software.get_info('usage') == 'Requires AGA':
			chipset = 'AGA'
		game.metadata.specific_info['Chipset'] = chipset

def add_cd32_info(game):
	builtin_gamepad = input_metadata.NormalInput()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2
	game.metadata.input_info.add_option([builtin_gamepad])

def add_neogeo_cd_info(game):
	#Apparently there is a mahjong controller too, but... meh
	builtin_gamepad = input_metadata.NormalInput()
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
		#Probably get the MAME command liner to get a PC DOS 2.1 floppy path from other_config provided by the user, or else they don't get to use ColorPaint
		#Lotus 123jr has a similar predicament, but it also needs .m3u I guess

def add_intellivision_info(game):
	#There's probably some way to get info from title screen in ROM, but I haven't explored that in ROMniscience yet
	#I think .int is supposed to be headered, but the ROMs I have (from Game Room, I think) seem to be just fine?
	#Input info: Crappy keypad, but also a keyboard component and computer module exists, also a piano keyboard

	#TODO: Some of these have two <dataarea> tags: name="5000" and name="9000". For example, Commando, which is a 32KB ROM in No-Intro, here the two data areas are 16KB each. Is this consistent for all 32KB games, perhaps?
	#24KB games (e.g. B-17 Bomber) are sometimes split up into "5000" (16KB) and "D000" (8KB) data areas, but then some (e.g. Defender) are just one big ROM in the software list
	#Hover Force (48KB) is "5000" (16KB), "9000" (24KB) and "D000" (8KB)
	#Tower of Doom (also 48KB) is "5000" (16KB), "9000" (16KB), "D000" (8KB) and "F000" (8KB)
	#Why this? Why me?
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

		if game.metadata.specific_info.get('Notes') == 'Uses Intellivoice':
			game.metadata.specific_info['Uses-Intellivoice'] = True
			game.metadata.specific_info.pop('Notes')

def add_juicebox_info(game):
	#Hmm... apparently there's 0x220 bytes at the beginning which need to be copied from retail carts to get homebrew test ROMs to boot
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalInput()
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
		normal_controller = input_metadata.NormalInput()
		normal_controller.face_buttons = 2 #1, 2, (Pause, Reset, Start) I think? I think it works the same way for trackballs
		normal_controller.analog_sticks = 1
		game.metadata.input_info.add_option([normal_controller])

def add_uzebox_info(game):
	#TODO: .uze files have 512-byte header, just not much info that we can't already get from software lists
	#But there is an icon at 0x4e:0x14d, just apparently never used; and SNES mouse usage at 0x152
	#Input info: SNES controllers, but that could be any SNES peripheral (mouse, etc)

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		if game.metadata.publisher == 'Belogic':
			game.metadata.publisher = game.metadata.developer
		game.metadata.product_code = software.get_info('serial')

def add_pce_info(game):
	#Input could be 2 buttons or 6 buttons, usually the former. Might be other types too?
	#Some games should have saving via TurboBooster-Plus (Wii U VC seems to let me save in Neutopia anyway without passwords or savestates), which I guess would be SaveType.Internal
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#Other info: alt_title
		game.metadata.product_code = software.get_info('serial')

def add_game_com_info(game):
	#Could have its own header. I think it does, but like.. who's gonna document such a thing? The wide community of Game.com enthusiasts?
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalInput()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #A B C D
	game.metadata.input_info.add_option([builtin_gamepad])

	#Might have saving, actually. I'm just not sure about how it works.

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		#This will tell you that nothing is supported. I think that sometimes the MAME devs are too hard on themselves. Someone needs to cheer them up a bit.
		game.metadata.product_code = software.get_info('serial')

def add_lynx_info(game):
	#TODO .lnx files should have a header with something in them, so eventually, Lynx will get its own module here
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalInput()
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
