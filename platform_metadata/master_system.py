import calendar

from region_detect import get_region_by_name
from info.region_info import TVSystem
from .sega_common import licensee_codes
from .software_list_info import add_generic_software_list_info, get_software_info, get_software_list_entry

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
		game.metadata.specific_info['Product-Code'] = header_data['Product code']
		if header_data['Region'] == 'Japanese':
			game.metadata.regions = [get_region_by_name('Japan')]
		
		if header_data['Is Game Gear']:
			game.metadata.platform = 'Game Gear'
		else:
			game.metadata.platform = 'Master System'

		if 'Publisher' in header_data:
			game.metadata.publisher = header_data['Publisher']

def get_sms_metadata(game):
	sdsc_header = game.rom.read(seek_to=0x7fe0, amount=12)
	if sdsc_header[:4] == b'SDSC':
		parse_sdsc_header(game, sdsc_header[4:])

	try_parse_standard_header(game)

	if game.metadata.platform == 'Game Gear':
		game.metadata.tv_type = TVSystem.Agnostic

	software, part = get_software_list_entry(game)
	if software:
		#This will overwrite all that hard work we did to get year and publisher, oh well
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#Input info will be tricky, as nothing tells me if things need light guns, or there are even games like Action Fighter which support the SK-1100 keyboard optionally
