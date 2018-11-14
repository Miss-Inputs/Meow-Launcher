import os
import calendar
from enum import Enum, auto

import cd_read
import input_metadata
from config import command_line_flags
from .sega_common import licensee_codes

class SaturnPeripheral(Enum):
	StandardController = auto()
	AnalogController = auto() #Or "3D Control Pad" if you prefer
	LightGun = auto()
	Keyboard = auto()
	Mouse = auto()
	Wheel = auto()

def parse_peripherals(game, peripherals):
	uses_standard_controller = False
	uses_analog_controller = False
	uses_gun = False
	uses_keyboard = False
	uses_mouse = False
	uses_wheel = False

	for peripheral in peripherals:
		if peripheral == 'J':
			uses_standard_controller = True
		elif peripheral == 'A':
			uses_analog_controller = True
			game.metadata.specific_info['Uses-3D-Control-Pad'] = True
		elif peripheral == 'G':
			uses_gun = True
			game.metadata.specific_info['Uses-Gun'] = True
		elif peripheral == 'K':
			uses_keyboard = True
			game.metadata.specific_info['Uses-Keyboard'] = True
		elif peripheral == 'M':
			uses_mouse = True
			game.metadata.specific_info['Uses-Mouse'] = True
		elif peripheral == 'S':
			#Steering wheel
			uses_wheel = True
			game.metadata.specific_info['Uses-Steering-Wheel'] = True
		#T = multitap, dunno what to do about that

	#Hmmm... tricky to figure out how to best represent this, as it's possible to use different controllers
	#I guess these two are the standard controllers, and everything else is optional
	if uses_analog_controller:
		analog_controller = input_metadata.NormalInput()
		analog_controller.face_buttons = 6 # A B C X Y Z
		analog_controller.analog_triggers = 2
		analog_controller.analog_sticks = 1
		analog_controller.dpads = 1
		game.metadata.input_info.add_option([analog_controller])
	elif uses_standard_controller:
		standard_controller = input_metadata.NormalInput()
		standard_controller.face_buttons = 6 # A B C X Y Z
		standard_controller.shoulder_buttons = 2 #L R
		standard_controller.dpads = 1
		game.metadata.input_info.add_option([standard_controller])

	if uses_gun:
		game.metadata.input_info.add_option([input_metadata.LightGun()])
	if uses_keyboard:
		game.metadata.input_info.add_option([input_metadata.Keyboard()])
	if uses_mouse:
		game.metadata.input_info.add_option([input_metadata.Mouse()])
	if uses_wheel:
		game.metadata.input_info.add_option([input_metadata.SteeringWheel()])

def add_saturn_info(game, header):
	#42:48 Version
	#56:64 Device info (disc number/total discs)
	#64:80 Compatible regions; only 10 characters are used
	#96:208 Internal name

	hardware_id = header[0:16].decode('ascii', errors='ignore')
	if hardware_id != 'SEGA SEGASATURN ':
		#Won't boot on a real Saturn. I should check how much emulators care...
		game.metadata.specific_info['Hardware-ID'] = hardware_id
		game.metadata.specific_info['Invalid-Hardware-ID'] = True
		return

	try:
		maker = header[16:32].decode('ascii').rstrip()
		if maker.startswith('SEGA TP '):
			#"Sega Third Party", I guess
			maker_code = maker[len('SEGA TP '):]
			if maker_code in licensee_codes:
				game.metadata.publisher = licensee_codes[maker_code]
		elif maker == 'SEGA ENTERPRISES':
			game.metadata.publisher = 'Sega'
		else:
			game.metadata.publisher = maker
	except UnicodeDecodeError:
		pass

	try:
		game.metadata.product_code = header[32:42].decode('ascii').rstrip()
	except UnicodeDecodeError:
		pass

	release_date = header[48:56].decode('ascii', errors='backslashreplace').rstrip()

	try:
		game.metadata.year = int(release_date[0:4])
		game.metadata.month = calendar.month_name[int(release_date[4:6])]
		game.metadata.day = int(release_date[6:8])
	except IndexError:
		if command_line_flags['debug']:
			print(game.rom.path, 'has invalid date in header:', release_date)
		pass
	except ValueError:
		pass

	peripherals = header[80:96].decode('ascii', errors='backslashreplace').rstrip()
	parse_peripherals(game, peripherals)

def add_saturn_metadata(game):
	if game.rom.extension == 'cue':
		first_track, sector_size = cd_read.get_first_data_cue_track(game.rom.path)

		if not os.path.isfile(first_track):
			print(game.rom.path, 'has invalid cuesheet')
			return
		try:
			header = cd_read.read_mode_1_cd(first_track, sector_size, seek_to=0, amount=256)
		except NotImplementedError:
			return
	elif game.rom.extension == 'ccd':
		img_file = os.path.splitext(game.rom.path)[0] + '.img'
		#I thiiiiiiiiink .ccd/.img always has 2352-byte sectors?
		try:
			header = cd_read.read_mode_1_cd(img_file, 2352, seek_to=0, amount=256)
		except NotImplementedError:
			return
	elif game.rom.extension == 'iso':
		header = game.rom.read(seek_to=0, amount=256)
	else:
		return

	add_saturn_info(game, header)
