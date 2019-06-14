import re
from datetime import datetime
import os
from enum import Enum, auto

import cd_read
import input_metadata
from common_types import SaveType
from software_list_info import get_software_list_entry
from data.sega_licensee_codes import licensee_codes

standard_gamepad = input_metadata.NormalController()
standard_gamepad.face_buttons = 3
standard_gamepad.dpads = 1

copyright_regex = re.compile(r'\(C\)(\S{4}.)(\d{4})\.(.{3})')
t_with_zero = re.compile(r'^T-0')
t_not_followed_by_dash = re.compile(r'^T(?!-)')

class MegadriveRegionCodes(Enum):
	Japan = auto() #J
	USA = auto() #U
	Europe = auto() #E

	#These might _not_ actually be valid, but they show up in retail games sometimes:
	World = auto() #F, I have seen some documentation say this is France but that doesn't seem to be how it's used
	Japan1 = auto() #1.. not sure what's different than normal J but I've only seen it in 32X so far
	BrazilUSA = auto() #4
	EuropeA = auto() #A, not sure what makes this different from normal Europe? But it happens
	JapanUSA = auto() #5, sometimes this is used in place of J and U together for some reason
	Europe8 = auto() #8, not sure what's different than normal Europe?
	USAEurope = auto() #C, not sure what's different than World?

def parse_peripherals(game, peripherals):
	game.metadata.input_info.buttons = 3
	for peripheral_char in peripherals:
		if peripheral_char == 'M':
			#3 buttons if I'm not mistaken
			mouse = input_metadata.Mouse()
			mouse.buttons = 3
			game.metadata.input_info.add_option(mouse)
		elif peripheral_char == 'V':
			#Is this just the SMS paddle?
			game.metadata.input_info.add_option(input_metadata.Paddle())
		elif peripheral_char == 'A':
			xe_1_ap = input_metadata.NormalController()
			xe_1_ap.face_buttons = 10
			xe_1_ap.shoulder_buttons = 4
			xe_1_ap.analog_sticks = 2 #The second one only has one axis, though
			game.metadata.input_info.add_option(xe_1_ap)
		elif peripheral_char == 'G':
			menacer = input_metadata.LightGun()
			menacer.buttons = 2 #Also pause button
			game.metadata.input_info.add_option(menacer)
		elif peripheral_char == 'K':
			xband_keyboard = input_metadata.Keyboard()
			xband_keyboard.keys = 68 #I think I counted that right... I was just looking at the picture
			game.metadata.input_info.add_option(xband_keyboard)
		elif peripheral_char == 'J':
			game.metadata.input_info.add_option(standard_gamepad)
		elif peripheral_char == '6':
			six_button_gamepad = input_metadata.NormalController()
			six_button_gamepad.face_buttons = 6
			six_button_gamepad.dpads = 1
			game.metadata.input_info.add_option(six_button_gamepad)
			game.metadata.specific_info['Uses-6-Button-Controller'] = True
		elif peripheral_char == '0':
			sms_gamepad = input_metadata.NormalController()
			sms_gamepad.face_buttons = 2
			sms_gamepad.dpads = 1
			game.metadata.input_info.add_option(sms_gamepad)
		elif peripheral_char == 'L':
			#Activator
			game.metadata.input_info.add_option(input_metadata.MotionControls())
		elif peripheral_char in ('4', 'O'):
			#Team Play and J-Cart respectively
			#num_players = 4
			pass
		elif peripheral_char == 'C':
			game.metadata.specific_info['Uses-CD'] = True
		#Apparently these also exist with dubious/unclear definitions:
		#P: "Printer"
		#B: "Control Ball"
		#F: "Floppy Drive"
		#R: "RS232C Serial"
		#T: "Tablet"

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
	
	domestic_title = header[32:80].decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	overseas_title = header[80:128].decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	if domestic_title:
		game.metadata.specific_info['Internal-Title'] = domestic_title
	if overseas_title:
		#Often the same as domestic title, but for games that get their names changed yet work on multiple regions, domestic is the title in Japan and and overseas is in USA (and maybe Europe). I don't know what happens if a game is originally in USA then gets its name changed when it goes to Japan, but it might just be "Japan is domestic and everwhere else is overseas"
		game.metadata.specific_info['Internal-Overseas-Title'] = overseas_title
	#Product type: 128:130, it's usually GM for game but then some other values appear too (especially in Sega Pico)
	#Space for padding: 130

	try:
		serial = header[131:142].decode('ascii')
		game.metadata.product_code = serial[:8].rstrip('\0 ')
		#- in between
		version = serial[-2]
		if version.isdigit():
			game.metadata.specific_info['Revision'] = int(version)
	except UnicodeDecodeError:
		pass
	#Checksum: header[142:144]

	peripherals = [c for c in header[144:160].decode('ascii', errors='ignore') if c not in ('\x00', ' ')]
	parse_peripherals(game, peripherals)

	save_id = header[0xb0:0xb4]
	#Apparently... what the heck
	#FIXME: This seems to be different on Mega CD. I need to handle it differently anyway, since it should be SaveType.Internal
	game.metadata.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing

	regions = header[0xf0:0xf3]
	region_codes = []
	if b'J' in regions:
		region_codes.append(MegadriveRegionCodes.Japan)
	if b'U' in regions:
		region_codes.append(MegadriveRegionCodes.USA)
	if b'E' in regions:
		region_codes.append(MegadriveRegionCodes.Europe)
	if b'F' in regions:
		region_codes.append(MegadriveRegionCodes.World)
	if b'1' in regions:
		region_codes.append(MegadriveRegionCodes.Japan1)
	if b'4' in regions:
		region_codes.append(MegadriveRegionCodes.BrazilUSA)
	if b'5' in regions:
		region_codes.append(MegadriveRegionCodes.JapanUSA)
	if b'A' in regions:
		region_codes.append(MegadriveRegionCodes.EuropeA)
	if b'8' in regions:
		region_codes.append(MegadriveRegionCodes.Europe8) #Apparently...
	if b'C' in regions:
		region_codes.append(MegadriveRegionCodes.USAEurope) #Apparently...
	#Seen in some betas and might just be invalid:
	#D - Brazil?
	game.metadata.specific_info['Region-Code'] = region_codes

def get_smd_header(game):
	#Just get the first block which is all that's needed for the header, otherwise this would be a lot more complicated (just something to keep in mind if you ever need to convert a whole-ass .smd ROM)
	block = game.rom.read(seek_to=512, amount=16384)

	buf = bytearray(16386)
	midpoint = 8192
	even = 1 #Hmm, maybe I have these the wrong way around
	odd = 2

	for i, b in enumerate(block):
		if i <= midpoint:
			buf[even] = b
			even += 2
		else:
			buf[odd] = b
			odd += 2

	return bytes(buf[0x100:0x200])

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
	elif game.rom.extension == 'smd':
		header = get_smd_header(game)
	else:
		header = game.rom.read(0x100, 0x100)

	add_megadrive_info(game, header)

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game.metadata)
		game.metadata.specific_info['Uses-SVP'] = software.get_shared_feature('addon') == 'SVP'
		if software.get_shared_feature('incompatibility') == 'TMSS':
			game.metadata.specific_info['Bad-TMSS'] = True

		slot = software.get_part_feature('slot')
		if slot == 'rom_eeprom' or software.has_data_area('sram'):
			game.metadata.save_type = SaveType.Cart
		else:
			game.metadata.save_type = SaveType.Nothing

		if software.name == 'aqlian':
			#This is naughty, but this bootleg game doesn't run on some stuff so I want to be able to detect it
			game.metadata.specific_info['Mapper'] = 'aqlian'
		else:
			if slot not in (None, 'rom_sram'):
				game.metadata.specific_info['Mapper'] = slot
			if software.name == 'pokemon':
				#This is also a bit naughty, but Pocket Monsters has different compatibility compared to other games with rom_kof99
				game.metadata.specific_info['Mapper'] = slot + '_pokemon'
