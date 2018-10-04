import sys
import re
from datetime import datetime
import os

import cd_read
import input_metadata
from metadata import SaveType
from software_list_info import get_software_list_entry
from .sega_common import licensee_codes

debug = '--debug' in sys.argv

copyright_regex = re.compile(r'\(C\)(\S{4}.)(\d{4})\.(.{3})')
t_with_zero = re.compile('^T-0')
t_not_followed_by_dash = re.compile('^T(?!-)')
acceptable_peripherals = set('046ABCDFGJKLMPRTV')

def parse_peripherals(game, peripherals):
	standard_gamepad = input_metadata.NormalInput()
	standard_gamepad.face_buttons = 3
	standard_gamepad.dpads = 1

	game.metadata.input_info.buttons = 3
	if set(peripherals) <= acceptable_peripherals:
		#TODO: I could just do the "whoops this is a weird peripheral_char" as a final else inside the for loop... eh
		for peripheral_char in peripherals:
			if peripheral_char == 'M':
				#3 buttons if I'm not mistaken
				game.metadata.input_info.add_option([input_metadata.Mouse()])
			elif peripheral_char == 'V':
				game.metadata.input_info.add_option([input_metadata.Paddle()])
			elif peripheral_char == 'A':
				xe_1_ap = input_metadata.NormalInput()
				xe_1_ap.face_buttons = 10
				xe_1_ap.shoulder_buttons = 4
				xe_1_ap.analog_sticks = 2 #The second one only has one axis, though
				game.metadata.input_info.add_option([xe_1_ap])
			elif peripheral_char == 'G':
				game.metadata.input_info.add_option([input_metadata.LightGun()])
			elif peripheral_char == 'K':
				game.metadata.input_info.add_option([input_metadata.Keyboard()])
			elif peripheral_char == 'J':
				game.metadata.input_info.add_option([standard_gamepad])
			elif peripheral_char == '6':
				six_button_gamepad = input_metadata.NormalInput()
				six_button_gamepad.face_buttons = 6
				six_button_gamepad.dpads = 1
				game.metadata.input_info.add_option([six_button_gamepad])
				game.metadata.specific_info['Uses-6-Button-Controller'] = True
			elif peripheral_char == '0':
				sms_gamepad = input_metadata.NormalInput()
				sms_gamepad.face_buttons = 2
				sms_gamepad.dpads = 1
				game.metadata.input_info.add_option([sms_gamepad])
			elif peripheral_char == 'L':
				#Activator
				game.metadata.input_info.add_option([input_metadata.MotionControls()])
			elif peripheral_char == '4' or peripheral_char == 'O':
				#Team Play and J-Cart respectively
				#num_players = 4
				pass
			elif peripheral_char == 'C':
				game.metadata.specific_info['Uses-CD'] = True
	else:
		if debug:
			print(game.rom.path, 'has weird peripheral chars:', set(peripherals) - acceptable_peripherals)
	if debug:
		#Other peripheral characters of interest that I dunno what to do with
		#A lot of homebrew has D in there. There's some Megadrive documentation that says "Just put JD in here and don't ask questions". It doesn't say what the D is. What does the D do? Why the D?
		if 'B' in peripherals:
			print(game.rom.path, 'has B (control ball)')
		if 'F' in peripherals:
			print(game.rom.path, 'has F (floppy drive)')
		if 'P' in peripherals:
			print(game.rom.path, 'has P (printer)')
		if 'R' in peripherals:
			#Something to do with SegaNet/Meganet perhaps?
			print(game.rom.path, 'has R (serial)')
		if 'T' in peripherals:
			#Doesn't seem to have anything to do with Pico games
			print(game.rom.path, 'has T (tablet)')
		if 'D' in peripherals:
			print(game.rom.path, 'has the D')

def add_megadrive_info(game, header):
	try:
		console_name = header[:16].decode('ascii')
	except UnicodeDecodeError:
		game.metadata.specific_info['Bad-TMSS'] = True
		return

	if not console_name.startswith('SEGA') and not console_name.startswith(' SEGA'):
		game.metadata.specific_info['Bad-TMSS'] = True
		return

	try:
		copyright_match = copyright_regex.match(header[16:32].decode('ascii'))
		if copyright_match:
			maker = copyright_match[1].strip().rstrip(',')
			maker = t_with_zero.sub('T-', maker)
			maker = t_not_followed_by_dash.sub('T-', maker)
			if maker in licensee_codes:
				game.metadata.publisher = licensee_codes[maker]
			game.metadata.year = copyright_match[2]
			try:
				game.metadata.month = datetime.strptime(copyright_match[3], '%b').strftime('%B')
			except ValueError:
				#There are other spellings such as JUR, JLY out there, but oh well
				pass
	except UnicodeDecodeError:
		pass

	try:
		#There's a space at header[130] apparently, so I guess that might be part of the thing, but eh
		serial = header[131:142].decode('ascii')
		game.metadata.product_code = serial[:8]
		#- in between
		version = serial[-2]
		if version.isdigit():
			game.metadata.revision = int(version)
	except UnicodeDecodeError:
		pass
	#Checksum: header[142:144]

	peripherals = [c for c in header[144:160].decode('ascii', errors='ignore') if c != '\x00' and c != ' ']
	parse_peripherals(game, peripherals)

	save_id = header[0xb0:0xb4]
	#Apparently... what the heck
	#FIXME: This seems to be different on Mega CD. I need to handle it differently anyway, since it should be SaveType.Internal
	game.metadata.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing

	#Hmm... get regions from [0xfd:0xff] or nah

def add_megadrive_metadata(game):
	if game.rom.extension == 'cue':
		first_track, sector_size = cd_read.get_first_data_cue_track(game.rom.path)
		if not os.path.isfile(first_track):
			print(game.rom.path, 'has invalid cuesheet')
			return
		try:
			header = cd_read.read_mode_1_cd(first_track, sector_size, 0x100, 0x100)
		except NotImplementedError:
			return
	else:
		header = game.rom.read(0x100, 0x100)

	add_megadrive_info(game, header)

	if game.metadata.platform != 'Mega CD':
		#Mega CD software lists have CHDs and whatnot and they're weird to deal with so I won't right now
		software = get_software_list_entry(game)
		if software:
			software.add_generic_info(game)
			game.metadata.product_code = software.get_info('serial')
			game.metadata.specific_info['Uses-SVP'] = software.get_shared_feature('addon') == 'SVP'
			if software.get_shared_feature('incompatibility') == 'TMSS':
				game.metadata.specific_info['Bad-TMSS'] = True
