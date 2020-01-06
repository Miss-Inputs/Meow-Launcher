from info.region_info import TVSystem
import input_metadata
from software_list_info import get_software_list_entry
from common_types import MediaType
import platform_metadata.atari_controllers as controllers

def add_info_from_software_list(game, software):
	software.add_standard_metadata(game.metadata)
	compatibility = software.compatibility
	if 'XL' in compatibility or 'XL/XE' in compatibility:
		game.metadata.specific_info['Machine'] = 'XL'
		game.metadata.mame_driver = 'a800xl'
	#TODO: Should XE (but not XL) ever appear as compatibility?
	if 'OSb' in compatibility:
		game.metadata.specific_info['Requires-OS-B'] = True

	peripheral = software.get_part_feature('peripheral')

	joystick = input_metadata.NormalController()
	joystick.dpads = 1
	joystick.face_buttons = 2
	keyboard = input_metadata.Keyboard()
	keyboard.keys = 57 #From looking at photos so I may have lost count; XL/XE might have more keys

	if peripheral == 'cx77_touch':
		#Tablet
		game.metadata.input_info.add_option(input_metadata.Touchscreen())
	elif peripheral == 'cx75_pen':
		#Light pen
		game.metadata.input_info.add_option(input_metadata.LightGun())
	elif peripheral == 'koala_pad,koala_pen':
		#Combination tablet/light pen
		game.metadata.input_info.add_option([input_metadata.LightGun(), input_metadata.Touchscreen])
	elif peripheral == 'trackball':
		game.metadata.input_info.add_option(controllers.cx22_trackball)
	elif peripheral == 'lightgun':
		#XEGS only
		game.metadata.input_info.add_option(controllers.xegs_gun)
	else:
		#trackfld = Track & Field controller but is that just a spicy joystick?
		game.metadata.input_info.add_option([joystick, keyboard])

	game.metadata.specific_info['Peripheral'] = peripheral

	requirement = software.get_shared_feature('requirement')
	if requirement == 'a800:basicb':
		game.metadata.specific_info['Requires-BASIC'] = True
		#Also: a800:msbasic2, a800:basxe41, a800:writerd, a800:spectra2 (none of those are games, the first two are just language extensions, the latter is noted as not being supported anyway, therefore meh)

	usage = software.get_info('usage')
	if usage == 'Plays music only in PAL':
		game.metadata.tv_type = TVSystem.PAL
	elif usage == 'BASIC must be enabled.':
		game.metadata.specific_info['Requires-BASIC'] = True
	else:
		game.metadata.notes = usage
	#To be used with Atari 1400 onboard modem.
	#3 or 4 player gameplay available only on 400/800 systems
	#Chalkboard Inc.'s Powerpad Tablet required
	#Requires Lower-Silesian Turbo 2000 hardware modification installed in a tape recorder.
	#Requires a special boot disk, currently unavailable.
	#Expando-Vision hardware device required
	#Kantronics interface II required
	#Needs an Bit-3 80 Column Board or Austin-Franklin 80-Column Board to run.
	#Pocket Modem required
	#Requires Atari 850 interface and 1200 baud modem to run.
	#2 joysticks required to play.
	#Requires the Atari Super Turbo hardware modification (or compatible ATT, UM) installed in a tape recorder.
	#Personal Peripherals Inc. Super Sketch device required
	#Modem required (and a working Chemical Bank service, obviously inactive for decades)
	#You must type 'X=USR(32768)' from the BASIC prompt to initialize it.

	#Meaningless for our purposes:
	#Keyboard overlay was supplied with cartridge

def add_atari_8bit_metadata(game):
	headered = False

	if game.metadata.media_type == MediaType.Cartridge:
		header = game.rom.read(amount=16)
		magic = header[:4]
		if magic == b'CART':
			headered = True
			cart_type = int.from_bytes(header[4:8], 'big')
			#TODO: Have nice table of cart types like with Game Boy mappers
			game.metadata.specific_info['Cart-Type'] = cart_type
			game.metadata.specific_info['Slot'] = 'Right' if cart_type in [21, 59] else 'Left'

	game.metadata.specific_info['Headered'] = headered

	software = get_software_list_entry(game, skip_header=16 if headered else 0)
	if software:
		add_info_from_software_list(game, software)

	if 'Machine' not in game.metadata.specific_info:
		for tag in game.filename_tags:
			#Use filename tags for now since there's not a great reliable method of detecting XL/XE requirement for floppies I have at the moment
			if tag in ('(XL)', '[XL]', '(XL-XE)', '[XL-XE]'):
				game.metadata.specific_info['Machine'] = 'XL'
				game.metadata.mame_driver = 'a800xl'
				break
			if tag in ('(XE)', '[XE]'):
				game.metadata.specific_info['Machine'] = 'XE'
				game.metadata.mame_driver = 'a800xe'
				break
	if '[BASIC]' in game.filename_tags:
		game.metadata.specific_info['Requires-BASIC'] = True
		