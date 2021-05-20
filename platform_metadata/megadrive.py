import os
import re
from datetime import datetime

import cd_read
import input_metadata
from common import load_dict
from common_types import SaveType
from mame_helpers import MAMENotInstalledException
from mame_machine import does_machine_match_game, get_machines_from_source_file
from metadata import Date
from platform_types import MegadriveRegionCodes
from software_list_info import get_software_list_entry

from .atari_controllers import megadrive_pad as standard_gamepad

licensee_codes = load_dict(None, 'sega_licensee_codes')

copyright_regex = re.compile(r'\(C\)(\S{4}.)(\d{4})\.(.{3})')
t_with_zero = re.compile(r'^T-0')
t_not_followed_by_dash = re.compile(r'^T(?!-)')

def parse_peripherals(metadata, peripherals):
	metadata.input_info.buttons = 3
	for peripheral_char in peripherals:
		if peripheral_char == 'M':
			#3 buttons if I'm not mistaken
			mouse = input_metadata.Mouse()
			mouse.buttons = 3
			metadata.input_info.add_option(mouse)
		elif peripheral_char == 'V':
			#Is this just the SMS paddle?
			metadata.input_info.add_option(input_metadata.Paddle())
		elif peripheral_char == 'A':
			xe_1_ap = input_metadata.NormalController()
			xe_1_ap.face_buttons = 10
			xe_1_ap.shoulder_buttons = 4
			xe_1_ap.analog_sticks = 2 #The second one only has one axis, though
			metadata.input_info.add_option(xe_1_ap)
		elif peripheral_char == 'G':
			menacer = input_metadata.LightGun()
			menacer.buttons = 2 #Also pause button
			metadata.input_info.add_option(menacer)
		elif peripheral_char == 'K':
			xband_keyboard = input_metadata.Keyboard()
			xband_keyboard.keys = 68 #I think I counted that right... I was just looking at the picture
			metadata.input_info.add_option(xband_keyboard)
		elif peripheral_char == 'J':
			metadata.input_info.add_option(standard_gamepad)
		elif peripheral_char == '6':
			six_button_gamepad = input_metadata.NormalController()
			six_button_gamepad.face_buttons = 6
			six_button_gamepad.dpads = 1
			metadata.input_info.add_option(six_button_gamepad)
			metadata.specific_info['Uses-6-Button-Controller'] = True
		elif peripheral_char == '0':
			sms_gamepad = input_metadata.NormalController()
			sms_gamepad.face_buttons = 2
			sms_gamepad.dpads = 1
			metadata.input_info.add_option(sms_gamepad)
		elif peripheral_char == 'L':
			#Activator
			metadata.input_info.add_option(input_metadata.MotionControls())
		elif peripheral_char in ('4', 'O'):
			#Team Play and J-Cart respectively
			#num_players = 4
			pass
		elif peripheral_char == 'C':
			metadata.specific_info['Uses-CD'] = True
		#Apparently these also exist with dubious/unclear definitions:
		#P: "Printer"
		#B: "Control Ball"
		#F: "Floppy Drive"
		#R: "RS232C Serial"
		#T: "Tablet"

def add_megadrive_info(metadata, header):
	try:
		console_name = header[:16].decode('ascii')
	except UnicodeDecodeError:
		metadata.specific_info['Bad-TMSS'] = True
		return

	if not console_name.startswith('SEGA') and not console_name.startswith(' SEGA') and console_name not in ('IMA IKUNOUJYUKU ', 'IMA IKUNOJYUKU  ', 'SAMSUNG PICO    '):
		metadata.specific_info['Console-Name'] = console_name
		metadata.specific_info['Bad-TMSS'] = True
		return

	if metadata.platform == 'Mega CD' and console_name.startswith('SEGA 32X'):
		#Could also set platform to something like "Mega CD 32X" I guess
		metadata.specific_info['32X-Only'] = True

	try:
		copyright_string = header[16:32].decode('ascii')
		metadata.specific_info['Copyright'] = copyright_string
		copyright_match = copyright_regex.match(copyright_string)
		if copyright_match:
			maker = copyright_match[1].strip().rstrip(',')
			maker = t_with_zero.sub('T-', maker)
			maker = t_not_followed_by_dash.sub('T-', maker)
			if maker in licensee_codes:
				metadata.publisher = licensee_codes[maker]
			year = copyright_match[2]
			try:
				month = datetime.strptime(copyright_match[3], '%b').month
			except ValueError:
				#There are other spellings such as JUR, JLY out there, but oh well
				month = '??'
			metadata.specific_info['Copyright-Date'] = Date(year, month)
			if not metadata.release_date:
				metadata.release_date = Date(year, month, is_guessed=True)
	except UnicodeDecodeError:
		pass
	
	domestic_title = header[32:80].decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	overseas_title = header[80:128].decode('shift_jis', errors='backslashreplace').rstrip('\0 ')
	if domestic_title:
		metadata.specific_info['Internal-Title'] = domestic_title
	if overseas_title:
		#Often the same as domestic title, but for games that get their names changed yet work on multiple regions, domestic is the title in Japan and and overseas is in USA (and maybe Europe). I don't know what happens if a game is originally in USA then gets its name changed when it goes to Japan, but it might just be "Japan is domestic and everwhere else is overseas"
		metadata.specific_info['Internal-Overseas-Title'] = overseas_title
	#Product type: 128:130, it's usually GM for game but then some other values appear too (especially in Sega Pico)
	#Space for padding: 130

	try:
		serial = header[131:142].decode('ascii')
		metadata.product_code = serial[:8].rstrip('\0 ')
		#- in between
		version = serial[-2]
		if version.isdigit():
			metadata.specific_info['Revision'] = int(version)
	except UnicodeDecodeError:
		pass
	#Checksum: header[142:144]

	peripherals = [c for c in header[144:160].decode('ascii', errors='ignore') if c not in ('\x00', ' ')]
	parse_peripherals(metadata, peripherals)

	if metadata.platform == 'Mega Drive':
		save_id = header[0xb0:0xb4]
		#Apparently... what the heck
		#This seems to be different on Mega CD, and also 32X
		metadata.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing

	modem_info = header[0xbc:0xc8]
	memo_bytes = header[0xc8:0xf0]
	modem_string = None
	if modem_info[:2] == b'MO':
		metadata.specific_info['Supports-Modem'] = True
	elif modem_info[:11] == b'No modem...':
		metadata.specific_info['Supports-Modem'] = False
	else:
		modem_string = modem_info.decode('ascii', errors='ignore').strip('\0 ')
		
	try:
		memo = memo_bytes.decode('ascii').strip('\0 ')
		if modem_string:
			#Not really correct, but a few homebrews use the modem part to put in a longer message (and sometimes, varying amounts of it - the first 2 or 4 bytes might be filled with garbage data…)
			memo = modem_string + memo
		
		if memo:
			if memo == 'SV':
				metadata.specific_info['Uses-SVP'] = True
			else:
				#This only seems to really be used for homebrews bootlegs etc
				metadata.descriptions['Memo'] = memo
	except UnicodeDecodeError:
		pass

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
	metadata.specific_info['Region-Code'] = region_codes
	if console_name[:12] == 'SEGA GENESIS' and not region_codes:
		#Make a cheeky guess
		metadata.specific_info['Region-Code'] = [MegadriveRegionCodes.USA]

def get_smd_header(rom):
	#Just get the first block which is all that's needed for the header, otherwise this would be a lot more complicated (just something to keep in mind if you ever need to convert a whole-ass .smd ROM)
	block = rom.read(seek_to=512, amount=16384)

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

def _get_megaplay_games():
	try:
		return _get_megaplay_games.result
	except AttributeError:
		_get_megaplay_games.result = list(get_machines_from_source_file('megaplay'))
		return _get_megaplay_games.result

def _get_megatech_games():
	try:
		return _get_megatech_games.result
	except AttributeError:
		_get_megatech_games.result = list(get_machines_from_source_file('megatech'))
		return _get_megatech_games.result

def try_find_equivalent_arcade(rom, metadata):
	if not hasattr(try_find_equivalent_arcade, 'arcade_bootlegs'):
		try:
			try_find_equivalent_arcade.arcade_bootlegs = list(get_machines_from_source_file('megadriv_acbl'))
		except MAMENotInstalledException:
			try_find_equivalent_arcade.arcade_bootlegs = []
	if not hasattr(try_find_equivalent_arcade, 'megaplay_games'):
		try:
			try_find_equivalent_arcade.megaplay_games = list(get_machines_from_source_file('megaplay'))
		except MAMENotInstalledException:
			try_find_equivalent_arcade.megaplay_games = []
	if not hasattr(try_find_equivalent_arcade, 'megatech_games'):
		try:
			try_find_equivalent_arcade.megatech_games = list(get_machines_from_source_file('megatech'))
		except MAMENotInstalledException:
			try_find_equivalent_arcade.megatech_games = []

	for bootleg_machine in try_find_equivalent_arcade.arcade_bootlegs:
		if does_machine_match_game(rom.name, metadata, bootleg_machine):
			return bootleg_machine
	for megaplay_machine in try_find_equivalent_arcade.megaplay_games:
		if does_machine_match_game(rom.name, metadata, megaplay_machine):
			return megaplay_machine
	for megatech_machine in try_find_equivalent_arcade.megatech_games:
		if does_machine_match_game(rom.name, metadata, megatech_machine):
			return megatech_machine	
	return None

def add_megadrive_software_list_metadata(software, metadata):
	software.add_standard_metadata(metadata)
	if software.get_shared_feature('addon') == 'SVP':
		metadata.specific_info['Uses-SVP'] = True
	if software.get_shared_feature('incompatibility') == 'TMSS':
		metadata.specific_info['Bad-TMSS'] = True

	slot = software.get_part_feature('slot')
	if slot == 'rom_eeprom' or software.has_data_area('sram'):
		metadata.save_type = SaveType.Cart
	elif metadata.platform == 'Mega Drive':
		metadata.save_type = SaveType.Nothing

	if software.name == 'aqlian':
		#This is naughty, but this bootleg game doesn't run on some stuff so I want to be able to detect it
		metadata.specific_info['Mapper'] = 'aqlian'
	else:
		if slot not in (None, 'rom_sram', 'rom_fram'):
			mapper = slot[4:] if slot.startswith('rom_') else slot
			if mapper in ('eeprom', 'nbajam_alt', 'nbajamte', 'nflqb96', 'cslam', 'nhlpa', 'blara', 'eeprom_mode1'):
				metadata.specific_info['Mapper'] = 'EEPROM'
			elif mapper == 'jcart':
				metadata.specific_info['Mapper'] = 'J-Cart'
			elif mapper in ('codemast', 'mm96'):
				metadata.specific_info['Mapper'] = 'J-Cart + EEPROM'
			else:
				#https://github.com/mamedev/mame/blob/master/src/devices/bus/megadrive/md_carts.cpp
				metadata.specific_info['Mapper'] = mapper
		if software.name == 'pokemon' and software.software_list_name == 'megadriv':
			#This is also a bit naughty, but Pocket Monsters has different compatibility compared to other games with rom_kof99
			metadata.specific_info['Mapper'] = slot + '_pokemon'


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
		header = get_smd_header(game.rom)
	else:
		header = game.rom.read(0x100, 0x100)

	add_megadrive_info(game.metadata, header)
	if game.metadata.platform == 'Mega Drive':
		equivalent_arcade = try_find_equivalent_arcade(game.rom, game.metadata)
		if equivalent_arcade:
			game.metadata.specific_info['Equivalent-Arcade'] = equivalent_arcade

	software = get_software_list_entry(game)
	if software:
		add_megadrive_software_list_metadata(software, game.metadata)
