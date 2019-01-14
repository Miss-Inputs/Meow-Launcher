import calendar
from enum import Enum, auto

import input_metadata
from common_types import SaveType
from region_detect import get_region_by_name
from info.region_info import TVSystem
from software_list_info import get_software_list_entry
from .sega_common import licensee_codes

class SMSPeripheral(Enum):
	StandardController = auto()
	Lightgun = auto()
	Paddle = auto()
	Tablet = auto()
	SportsPad = auto()

def decode_bcd(i):
	if not isinstance(i, int):
		return (decode_bcd(i[1]) * 100) + decode_bcd(i[0])

	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def parse_sdsc_header(game, header):
	#Minor version: header[0]
	#Major version: header[1]

	day = decode_bcd(header[2])
	month = decode_bcd(header[3])
	year = decode_bcd(header[4:6])
	if day >= 1 and day <= 31:
		game.metadata.day = day
	if month >= 1 and month <= 12:
		game.metadata.month = calendar.month_name[month]
	if year:
		game.metadata.year = year

	author_offset = int.from_bytes(header[6:8], 'little')
	#Name offset: header[8:10]
	#Description offset: header[10:12]
	if author_offset > 0 and author_offset < 0xffff:
		#Assume sane maximum of 255 chars
		try:
			game.metadata.developer = game.rom.read(seek_to=author_offset, amount=255).partition(b'\x00')[0].decode('ascii')
		except UnicodeDecodeError:
			pass

class BadSMSHeaderException(Exception):
	pass

regions = {
	#Second tuple thing: True if Game Gear, False if SMS
	#Not sure of the difference between export GG and international GG
	3: ('Japanese', False),
	4: ('Export', False),
	5: ('Japanese', True),
	6: ('Export', True),
	7: ('International', True),
}

def parse_standard_header(game, base_offset):
	header_data = {}
	header = game.rom.read(seek_to=base_offset, amount=16)

	if header[:8] != b'TMR SEGA':
		raise BadSMSHeaderException('TMR missing')

	#Reserved: 8:10
	#Checksum: 10:12
	product_code_hi = header[12:14]
	product_code_lo = (header[14] & 0xf0) >> 4
	header_data['Revision'] = header[14] & 0x0f

	product_code = '{0}{1:04}'.format('' if product_code_lo == 0 else product_code_lo, decode_bcd(product_code_hi))
	header_data['Product code'] = product_code

	region_code = (header[15] & 0xf0) >> 4
	#ROM size = header[15] & 0x0f, uses lookup table; used for calculating checksum

	if region_code in regions:
		header_data['Region'], header_data['Is Game Gear'] = regions[region_code]
		if header_data['Is Game Gear']:
			if len(product_code) >= 5:
				#:-3
				maker_code = 'T-' + product_code[:-3]
				if maker_code in licensee_codes:
					header_data['Publisher'] = licensee_codes[maker_code]
			else:
				header_data['Publisher'] = 'Sega'
	else:
		raise BadSMSHeaderException('Weird region: ' + str(region_code))

	return header_data

def try_parse_standard_header(game):
	rom_size = game.rom.get_size()
	possible_offsets = [0x1ff0, 0x3ff0, 0x7ff0]

	header_data = None
	for possible_offset in possible_offsets:
		if possible_offset >= rom_size:
			continue

		try:
			header_data = parse_standard_header(game, possible_offset)
			break
		except BadSMSHeaderException:
			continue

	if header_data:
		game.metadata.revision = header_data['Revision']
		game.metadata.product_code = header_data['Product code']
		game.metadata.specific_info['Region-Code'] = header_data['Region'] #Too lazy to make an enum for both SMS and GG regions

		if header_data['Is Game Gear']:
			game.metadata.platform = 'Game Gear'
		else:
			game.metadata.platform = 'Master System'

		if 'Publisher' in header_data:
			game.metadata.publisher = header_data['Publisher']

def add_info_from_software_list(game, software):
	software.add_generic_info(game)
	game.metadata.product_code = software.get_info('serial')

	usage = software.get_info('usage')
	if usage == 'Only runs with PAL/50Hz drivers, e.g. smspal':
		game.metadata.tv_type = TVSystem.PAL
	elif usage in ('Input works only with drivers of Japanese region, e.g. sms1kr,smsj', 'Only runs with certain drivers, e.g. smsj - others show SOFTWARE ERROR'):
		game.metadata.specific_info['Japanese-Only'] = True
	elif usage == 'Video mode is correct only on SMS 2 drivers, e.g. smspal':
		game.metadata.specific_info['SMS2-Only'] = True
	elif usage == 'Video only works correctly on drivers with SMS1 VDP, e.g. smsj':
		game.metadata.specific_info['SMS1-Only'] = True
	#Other usage strings:
	#To play in 3-D on SMS1, hold buttons 1 and 2 while powering up the system.

	slot = software.get_part_feature('slot')
	if slot == 'codemasters':
		game.metadata.specific_info['Mapper'] = 'Codemasters'

	if slot == 'eeprom' or software.get_part_feature('battery') == 'yes':
		game.metadata.save_type == SaveType.Cart
	else:
		game.metadata.save_type == SaveType.Nothing

	if game.metadata.platform == 'Master System':
		builtin_gamepad = input_metadata.NormalController()
		builtin_gamepad.dpads = 1
		builtin_gamepad.face_buttons = 2

		controller_1 = software.get_shared_feature('ctrl1_default')
		#ctrl2_default is only ever equal to ctrl1_default when it is present, so ignore it for our purposes
		#Note that this doesn't actually tell us about games that _support_ given peripherals, just what games need them
		peripheral = SMSPeripheral.StandardController
		#All of these peripherals have 2 buttons as well?
		if controller_1 == 'graphic':
			peripheral = SMSPeripheral.Tablet
			game.metadata.input_info.add_option(input_metadata.Touchscreen())
		elif controller_1 == 'lphaser':
			peripheral = SMSPeripheral.Lightgun
			#game.metadata.input_info.inputs = [InputType.LightGun]
			game.metadata.input_info.add_option(input_metadata.LightGun())
		elif controller_1 == 'paddle':
			peripheral = SMSPeripheral.Paddle
			game.metadata.input_info.add_option(input_metadata.Paddle())
		elif controller_1 == 'sportspad':
			peripheral = SMSPeripheral.SportsPad
			game.metadata.input_info.add_option(input_metadata.Trackball())
		else:
			#Not sure if this is an option for games that use lightgun/paddle/etc? I'll assume it's not
			game.metadata.input_info.add_option(builtin_gamepad)

		game.metadata.specific_info['Peripheral'] = peripheral

def get_sms_metadata(game):
	sdsc_header = game.rom.read(seek_to=0x7fe0, amount=12)
	if sdsc_header[:4] == b'SDSC':
		parse_sdsc_header(game, sdsc_header[4:])

	try_parse_standard_header(game)

	if game.metadata.platform == 'Game Gear':
		game.metadata.tv_type = TVSystem.Agnostic
		#Because there's no accessories to make things confusing, we can assume the Game Gear's input info, but not the Master System's
		builtin_gamepad = input_metadata.NormalController()
		builtin_gamepad.dpads = 1
		builtin_gamepad.face_buttons = 2 #'1' on left, '2' on right
		game.metadata.input_info.add_option(builtin_gamepad)

	software = get_software_list_entry(game)
	if software:
		add_info_from_software_list(game, software)
