import os
import calendar
from enum import Enum, auto

import cd_read
import input_metadata
from config import main_config
from data.sega_licensee_codes import licensee_codes
from software_list_info import get_software_list_entry

class SaturnPeripheral(Enum):
	StandardController = auto()
	AnalogController = auto() #Or "3D Control Pad" if you prefer
	LightGun = auto()
	Keyboard = auto()
	Mouse = auto()
	Wheel = auto()

class SaturnRegionCodes(Enum):
	Japan = auto() #J
	USA = auto() #U
	Europe = auto() #E
	#Some retail discs also have T (Taiwan?) but that doesn't seem to be a unique system for region locking purposes and also nobody can tell me for sure what it is, so I'll just stick with those three for now
	#Some protos and devkits have JTUBKAEL which is... well, it's those four and BKAL which could be like Brazil Korea Australia (or Asia) and Latin America, possibly

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
		analog_controller = input_metadata.NormalController()
		analog_controller.face_buttons = 6 # A B C X Y Z
		analog_controller.analog_triggers = 2
		analog_controller.analog_sticks = 1
		analog_controller.dpads = 1
		game.metadata.input_info.add_option(analog_controller)
	elif uses_standard_controller:
		standard_controller = input_metadata.NormalController()
		standard_controller.face_buttons = 6 # A B C X Y Z
		standard_controller.shoulder_buttons = 2 #L R
		standard_controller.dpads = 1
		game.metadata.input_info.add_option(standard_controller)

	if uses_gun:
		virtua_gun = input_metadata.LightGun()
		virtua_gun.buttons = 1 #Also start and I dunno if offscreen shot would count as a button
		game.metadata.input_info.add_option(virtua_gun)
	if uses_keyboard:
		keyboard = input_metadata.Keyboard()
		keyboard.keys = 101
		#Japan keyboard has 89 keys... bleh, it doesn't seem to say which keyboard it refers to
		game.metadata.input_info.add_option(keyboard)
	if uses_mouse:
		mouse = input_metadata.Mouse()
		mouse.buttons = 3
		game.metadata.input_info.add_option(mouse)
	if uses_wheel:
		game.metadata.input_info.add_option(input_metadata.SteeringWheel())

def add_saturn_info(game, header):
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

	try:
		version = header[42:48].decode('ascii').rstrip()
		if version[0] == 'V' and version[2] == '.':
			game.metadata.specific_info['Version'] = 'v' + version[1:]
	except UnicodeDecodeError:
		pass

	release_date = header[48:56].decode('ascii', errors='backslashreplace').rstrip()

	if not release_date.startswith('0'):
		#If it starts with 0 the date format is WRONG stop it because I know the Saturn wasn't invented yet before 1000 AD
		try:
			game.metadata.year = int(release_date[0:4])
			game.metadata.month = calendar.month_name[int(release_date[4:6])]
			game.metadata.day = int(release_date[6:8])
		except IndexError:
			if main_config.debug:
				print(game.rom.path, 'has invalid date in header:', release_date)
		except ValueError:
			pass

	device_info = header[56:64].decode('ascii', errors='ignore').rstrip()
	if device_info.startswith('CD-'):
		#CART16M is seen here instead of "CD-1/1" on some protos?
		disc_number, _, disc_total = device_info[3:].partition('/')
		try:
			game.metadata.disc_number = int(disc_number)
			game.metadata.disc_total = int(disc_total)
		except ValueError:
			pass

	region_info = header[64:80].rstrip()
	#Only 10 characters are used
	region_codes = []
	if b'J' in region_info:
		region_codes.append(SaturnRegionCodes.Japan)
	if b'U' in region_info:
		region_codes.append(SaturnRegionCodes.USA)
	if b'E' in region_info:
		region_codes.append(SaturnRegionCodes.Europe)
	#Some other region codes appear sometimes but they might not be entirely valid
	game.metadata.specific_info['Region-Code'] = region_codes

	peripherals = header[80:96].decode('ascii', errors='backslashreplace').rstrip()
	parse_peripherals(game, peripherals)

	internal_name = header[96:208].decode('ascii', errors='backslashreplace').rstrip()
	#Sometimes / : - are used as delimiters, and there can also be J:JapaneseNameU:USAName
	if internal_name:
		game.metadata.specific_info['Internal-Title'] = internal_name


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

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game.metadata)
		game.metadata.notes = software.get_info('usage')
