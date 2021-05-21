from enum import Enum, auto

import input_metadata
from common import load_dict
from common_types import SaveType
from info.region_info import TVSystem
from metadata import Date
from platform_types import SMSPeripheral
from software_list_info import get_software_list_entry

licensee_codes = load_dict(None, 'sega_licensee_codes')

def decode_bcd(i):
	if not isinstance(i, int):
		return (decode_bcd(i[1]) * 100) + decode_bcd(i[0])

	hi = (i & 0xf0) >> 4
	lo = i & 0x0f
	return (hi * 10) + lo

def parse_sdsc_header(rom, metadata, header):
	major_version = decode_bcd(header[0])
	minor_version = decode_bcd(header[1])
	metadata.specific_info['Version'] = 'v{0}.{1}'.format(major_version, minor_version)

	day = decode_bcd(header[2])
	month = decode_bcd(header[3])
	year = decode_bcd(header[4:6])
	metadata.release_date = Date(year, month, day)

	author_offset = int.from_bytes(header[6:8], 'little')
	name_offset = int.from_bytes(header[8:10], 'little')
	description_offset = int.from_bytes(header[10:12], 'little')
	if 0 < author_offset < 0xffff:
		#Assume sane maximum of 255 chars
		try:
			metadata.developer = metadata.publisher = rom.read(seek_to=author_offset, amount=255).partition(b'\x00')[0].decode('ascii')
		except UnicodeDecodeError:
			pass
	if 0 < name_offset < 0xffff:
		try:
			metadata.add_alternate_name(rom.read(seek_to=name_offset, amount=255).partition(b'\x00')[0].decode('ascii'), 'Header-Title')
		except UnicodeDecodeError:
			pass
	if 0 < description_offset < 0xffff:
		try:
			metadata.descriptions['Description'] = rom.read(seek_to=description_offset, amount=255).partition(b'\x00')[0].decode('ascii')
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

def parse_standard_header(rom, base_offset):
	header_data = {}
	header = rom.read(seek_to=base_offset, amount=16)

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

def try_parse_standard_header(rom, metadata):
	rom_size = rom.get_size()
	possible_offsets = [0x1ff0, 0x3ff0, 0x7ff0]

	header_data = None
	for possible_offset in possible_offsets:
		if possible_offset >= rom_size:
			continue

		try:
			header_data = parse_standard_header(rom, possible_offset)
			break
		except BadSMSHeaderException:
			continue

	if header_data:
		metadata.specific_info['Revision'] = header_data['Revision']
		metadata.product_code = header_data['Product code']
		metadata.specific_info['Region-Code'] = header_data['Region'] #Too lazy to make an enum for both SMS and GG regions

		if header_data['Is Game Gear']:
			metadata.platform = 'Game Gear'
		else:
			metadata.platform = 'Master System'

		if 'Publisher' in header_data:
			metadata.publisher = header_data['Publisher']
	else:
		#All non-Japanese/Korean systems have a BIOS which checks the checksum, so if there's no header at all, they just won't boot it
		metadata.specific_info['Japanese-Only'] = True

def add_info_from_software_list(metadata, software):
	software.add_standard_metadata(metadata)

	usage = software.infos.get('usage')
	if usage == 'Only runs with PAL/50Hz drivers, e.g. smspal':
		metadata.specific_info['TV-Type'] = TVSystem.PAL
	elif usage in ('Input works only with drivers of Japanese region, e.g. sms1kr,smsj', 'Only runs with certain drivers, e.g. smsj - others show SOFTWARE ERROR'):
		metadata.specific_info['Japanese-Only'] = True
	elif usage == 'Video mode is correct only on SMS 2 drivers, e.g. smspal':
		metadata.specific_info['SMS2-Only'] = True
	elif usage == 'Video only works correctly on drivers with SMS1 VDP, e.g. smsj':
		metadata.specific_info['SMS1-Only'] = True
	else:
		metadata.add_notes(usage)
	#Other usage strings:
	#To play in 3-D on SMS1, hold buttons 1 and 2 while powering up the system.

	slot = software.get_part_feature('slot')
	if slot == 'codemasters':
		metadata.specific_info['Mapper'] = 'Codemasters'
	elif slot == 'eeprom':
		metadata.specific_info['Mapper'] = 'EEPROM' #Is this really describable as a "mapper"?
		metadata.save_type = SaveType.Cart
	elif slot == '4pak':
		metadata.specific_info['Mapper'] = '4 Pak'
	elif slot == 'hicom':
		metadata.specific_info['Mapper'] = 'Hi-Com'
	elif slot == 'korean':
		metadata.specific_info['Mapper'] = 'Korean'
	elif slot == 'korean_nb':
		metadata.specific_info['Mapper'] = 'Korean Unbanked'
	elif slot == 'zemina':
		metadata.specific_info['Mapper'] = 'Zemina'
	elif slot == 'janggun':
		metadata.specific_info['Mapper'] = 'Janggun'
	elif slot == 'nemesis':
		metadata.specific_info['Mapper'] = 'Nemesis'
	elif slot == 'seojin':
		metadata.specific_info['Mapper'] = 'Seo Jin'

	if software.get_part_feature('battery') == 'yes':
		metadata.save_type = SaveType.Cart
	else:
		metadata.save_type = SaveType.Nothing

	if metadata.platform == 'Master System':
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
			metadata.input_info.add_option(input_metadata.Touchscreen())
		elif controller_1 == 'lphaser':
			peripheral = SMSPeripheral.Lightgun
			light_phaser = input_metadata.LightGun()
			light_phaser.buttons = 1
			metadata.input_info.add_option(light_phaser)
		elif controller_1 == 'paddle':
			peripheral = SMSPeripheral.Paddle
			paddle = input_metadata.Paddle()
			paddle.buttons = 2
			metadata.input_info.add_option(paddle)
		elif controller_1 == 'sportspad':
			peripheral = SMSPeripheral.SportsPad
			sports_pad = input_metadata.Trackball()
			sports_pad.buttons = 2
			metadata.input_info.add_option(sports_pad)
		else:
			#Not sure if this is an option for games that use lightgun/paddle/etc? I'll assume it's not
			metadata.input_info.add_option(builtin_gamepad)

		metadata.specific_info['Peripheral'] = peripheral

def get_sms_metadata(game):
	sdsc_header = game.rom.read(seek_to=0x7fe0, amount=16)
	if sdsc_header[:4] == b'SDSC':
		parse_sdsc_header(game.rom, game.metadata, sdsc_header[4:])

	try_parse_standard_header(game.rom, game.metadata)

	if game.metadata.platform == 'Game Gear':
		#Because there's no accessories to make things confusing, we can assume the Game Gear's input info, but not the Master System's
		builtin_gamepad = input_metadata.NormalController()
		builtin_gamepad.dpads = 1
		builtin_gamepad.face_buttons = 2 #'1' on left, '2' on right
		game.metadata.input_info.add_option(builtin_gamepad)

	software = get_software_list_entry(game)
	if software:
		add_info_from_software_list(game.metadata, software)
