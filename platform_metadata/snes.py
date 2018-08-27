from enum import Enum, auto
import calendar

from metadata import SaveType
from region_detect import get_region_by_name
from common import convert_alphanumeric, NotAlphanumericException
from software_list_info import get_software_list_entry
from .nintendo_common import nintendo_licensee_codes

def parse_sufami_turbo_header(game):
	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		game.metadata.product_code = software.get_info('serial')

	game.metadata.platform = 'Sufami Turbo'

	header = game.rom.read(amount=56)
	#Magic: 0:14 Should be "BANDAI SFC-ADX"
	#Name: 16:30
	#Game ID: 48:51 Could this be considered product code?
	#Series index: 51
	#ROM speed: 52
	#Features: 53 Not sure what this does, though = 1 may indicate SRAM or linkable
	#ROM size: 54 In 128KB units
	save_size = header[55]
	#In 2KB units, if you wanted to actually know the size
	#The SRAM is in the mini-cartridge, not the Sufami Turbo BIOS cart itself
	game.metadata.save_type = SaveType.Cart if save_size > 0 else SaveType.Nothing

class BadSNESHeaderException(Exception):
	pass

def make_ram_rom_sizes():
	sizes = {}
	for i in range(0, 256):
		sizes[i] = (1 << i) * 1024
	return sizes
ram_rom_sizes = make_ram_rom_sizes()

rom_layouts = {
	0x20: "LoROM",
	0x21: "HiROM",
	0x22: "LoROM + S-DD1",
	0x23: "LoROM + SA-1",
	0x30: "LoROM + FastROM",
	0x31: "HiROM + FastROM",
	0x32: "ExLoROM",
	0x35: "ExHiROM",
	0x3a: 'ExHiROM + FastROM + SPC7110',
}

class ExpansionChip(Enum):
	DSP_1 = auto()
	SuperFX = auto()
	SuperFX2 = auto()
	OBC_1 = auto()
	SA_1 = auto()
	S_DD1 = auto()
	SuperGB = auto() #For Super GB BIOS carts
	BSX = auto() #For Satellaview BIOS carts
	CX4 = auto()
	ST018 = auto()
	ST01x = auto() #ST010/ST011
	SPC7110 = auto()


class ROMType():
	def __init__(self, expansion_chip=None, has_ram=False, has_battery=False, has_rtc=False):
		self.expansion_chip = expansion_chip
		self.has_ram = has_ram
		self.has_battery = has_battery
		self.has_rtc = has_rtc

rom_types = {
	0: ROMType(),
	1: ROMType(has_ram=True),
	2: ROMType(has_ram=True, has_battery=True),
	3: ROMType(ExpansionChip.DSP_1),
	4: ROMType(ExpansionChip.DSP_1, has_ram=True),
	5: ROMType(ExpansionChip.DSP_1, has_ram=True, has_battery=True),
	18: ROMType(has_battery=True), #Might not be used...
	19: ROMType(ExpansionChip.SuperFX),
	20: ROMType(ExpansionChip.SuperFX2), #Well, it's a different value from 19. 19 is seen in Star Fox, this is seen in Doom... could be GSU-1 and GSU-2, I dunno
	21: ROMType(ExpansionChip.SuperFX, has_battery=True),
	26: ROMType(ExpansionChip.SuperFX2, has_battery=True),
	37: ROMType(ExpansionChip.OBC_1),
	50: ROMType(ExpansionChip.SA_1, has_battery=True), #Different from 53... somehow... probably?
	52: ROMType(ExpansionChip.SA_1),
	53: ROMType(ExpansionChip.SA_1, has_battery=True),
	67: ROMType(ExpansionChip.S_DD1),
	69: ROMType(ExpansionChip.S_DD1, has_ram=True, has_battery=True),
	85: ROMType(has_ram=True, has_battery=True, has_rtc=True),
	227: ROMType(ExpansionChip.SuperGB, has_ram=True),
	229: ROMType(ExpansionChip.BSX),
	243: ROMType(ExpansionChip.CX4),
	245: ROMType(ExpansionChip.ST018),
	246: ROMType(ExpansionChip.ST01x),
	249: ROMType(ExpansionChip.SPC7110),
}

countries = {
	0: get_region_by_name('Japan'),
	1: get_region_by_name('USA'),
	2: get_region_by_name('Europe'), #Includes Oceania and Asia too... I guess I have some refactoring to do. Like maybe PAL should be a region
	3: get_region_by_name('Sweden'), #Includes Scandanavia
	4: get_region_by_name('Finland'),
	5: get_region_by_name('Denmark'),
	6: get_region_by_name('France'),
	7: get_region_by_name('Netherlands'),
	8: get_region_by_name('Spain'),
	9: get_region_by_name('Germany'), #Also includes Austria and Switzerland, apparently
	10: get_region_by_name('Italy'),
	11: get_region_by_name('Hong Kong'), #Also includes China... apparently? Were SNES games officially sold there?
	12: get_region_by_name('Indonesia'),
	13: get_region_by_name('Korea'),
	15: get_region_by_name('Canada'),
	16: get_region_by_name('Brazil'),
	17: get_region_by_name('Australia'), #Is this actually used? Australian-specific releases (e.g. TMNT) use Europe still
}

def parse_snes_header(game, base_offset):
	#In order to make things simpler, we'll just ignore any carts that are out of line. You wouldn't be able to get interesting results from homebrew or bootleg games anyway
	#Hence why we won't add metadata to the game object straight away, we'll store it in a dict first and add it all later, so we add nothing at all from invalid headers

	#Note that amount goes up to 256 if you include exception vectors, but... nah
	header = game.rom.read(seek_to=base_offset, amount=0xe0)
	try:
		header[0xc0:0xd5].decode('shift_jis')
	except UnicodeDecodeError:
		raise BadSNESHeaderException('Title not ASCII or Shift-JIS: %s' % header[0xc0:0xd5].decode('shift_jis', errors='backslashreplace'))

	metadata = {}

	rom_layout = header[0xd5]
	if rom_layout in rom_layouts:
		metadata['ROM layout'] = rom_layouts[rom_layout]
		#FIXME: HAL's Hole in Golf has 70 here, because that's the letter F, and the title immediately preceding this is "HAL HOLE IN ONE GOL". Looks like they overwrote this part of the header with the letter F. Whoops.
	else:
		raise BadSNESHeaderException('ROM layout is weird: %d' % rom_layout)

	rom_type = header[0xd6]
	if rom_type in rom_types:
		metadata['ROM type'] = rom_types[rom_type]
	else:
		raise BadSNESHeaderException('ROM type is weird: %d' % rom_type)

	rom_size = header[0xd7]
	if rom_size not in ram_rom_sizes:
		raise BadSNESHeaderException('ROM size is weird: %d' % rom_size)
	ram_size = header[0xd8]
	#We'll just use ROM type to detect presence of save data rather than this
	if ram_size not in ram_rom_sizes:
		raise BadSNESHeaderException('RAM size is weird: %d' % ram_size)
	country = header[0xd9]
	#Dunno if I want to validate against countries, honestly. Might go wrong
	if country in countries:
		metadata['Country'] = countries[country]
	
	licensee = header[0xda]
	#Hmm.. not sure if I should validate that, but... it shouldn't be 0x00 or 0xff, maybe?
	
	metadata['Revision'] = header[0xdb]
	
	inverse_checksum = int.from_bytes(header[0xdc:0xde], 'little')
	checksum = int.from_bytes(header[0xde:0xe0], 'little')
	#Can't be arsed calculating the checksum because it's complicated (especially with some weird ROM sizes), but we know they have to add up to 0xffff
	if (checksum | inverse_checksum) != 0xffff:
		raise BadSNESHeaderException("Checksum and inverse checksum don't add up: %d %d" % (checksum, inverse_checksum))

	if licensee == 0x33:
		#TODO: If title[-1] == 00, this is an early version that only indicates the chipset subtype. It's only used for ST010/11 games anyway though... apparently
		try:
			maker_code = convert_alphanumeric(header[0xb0:0xb2])
			metadata['Licensee'] = maker_code
		except NotAlphanumericException:
			raise BadSNESHeaderException('Licensee code in extended header not alphanumeric: %s' % header[0xb0:0xb2].decode('ascii', errors='backslashreplace'))

		try:
			product_code = convert_alphanumeric(header[0xb2:0xb6])
			metadata['Product code'] = product_code
		except NotAlphanumericException:
			if header[0xb4:0xb6] == b'  ':
				try:
					product_code = convert_alphanumeric(header[0xb2:0xb4])
					metadata['Product code'] = product_code
				except NotAlphanumericException:
					raise BadSNESHeaderException('2 char product code not alphanumeric: %s' % header[0xb2:0xb4].decode('ascii', errors='backslashreplace'))
			else:
				raise BadSNESHeaderException('4 char product code not alphanumeric: %s' % header[0xb2:0xb6].decode('ascii', errors='backslashreplace'))
	else:
		metadata['Licensee'] = '{:02X}'.format(licensee)

	return metadata

def add_normal_snes_header(game):
	#Note that while we're seeking to xx00 here, the header actually starts at xxc0 (or xxb0 in case of extended header), it's just easier this way
	possible_offsets = [0x7f00, 0xff00, 0x40ff00]
	rom_size = game.rom.get_size()
	if rom_size % 1024 == 512:
		possible_offsets = [0x8100, 0x10100, 0x410100]
		#We'll ignore any values in this copier header, I've seen them be wrong about a ROM being LoROM/HiROM before
	
	header_data = None
	for possible_offset in possible_offsets:
		if possible_offset >= rom_size:
			continue

		try:
			header_data = parse_snes_header(game, possible_offset)
			break
		except BadSNESHeaderException:
			continue

	if header_data:
		game.metadata.specific_info['Mapper'] = header_data.get('ROM layout')
		rom_type = header_data.get('ROM type')
		if rom_type:
			game.metadata.specific_info['Expansion-Chip'] = rom_type.expansion_chip
			game.metadata.save_type = SaveType.Cart if rom_type.has_battery else SaveType.Nothing
			game.metadata.specific_info['Has-RTC'] = rom_type.has_rtc
		licensee = header_data.get('Licensee')
		if licensee is not None:
			if licensee in nintendo_licensee_codes:
				game.metadata.publisher = nintendo_licensee_codes[licensee]
			elif licensee != '00':
				game.metadata.publisher = '<unknown Nintendo licensee {0}>'.format(licensee)
		country = header_data.get('Country')
		if country:
			game.metadata.regions = [country]
		game.metadata.revision = header_data.get('Revision')
		product_code = header_data.get('Product code')
		if product_code:
			game.metadata.product_code = product_code

def parse_satellaview_header(game, base_offset):
	header = game.rom.read(seek_to=base_offset, amount=0xe0)
	metadata = {}

	try:
		publisher = convert_alphanumeric(header[0xb0:0xb2])
		metadata['Publisher'] = publisher
	except NotAlphanumericException:
		raise BadSNESHeaderException("Publisher not alphanumeric")
	
	try:
		header[0xc0:0xd0].decode('shift_jis')
	except UnicodeDecodeError:
		raise BadSNESHeaderException('Title not ASCII or Shift-JIS: %s' % header[0xc0:0xd0].decode('shift_jis', errors='backslashreplace'))

	month = (header[0xd6] & 0b_1111_0000) >> 4
	day = (header[0xd7] & 0b_1111_1000) >> 3
	if month == 0 or month > 12:
		raise BadSNESHeaderException('Month not valid: %d' % month)
	if day > 31:
		raise BadSNESHeaderException('Day not valid: %d' % day)
	metadata['Month'] = calendar.month_name[month]
	metadata['Day'] = day

	rom_layout = header[0xd8]
	if rom_layout not in rom_layouts:
		raise BadSNESHeaderException('ROM layout is weird: %d' % rom_layout)
	metadata['ROM layout'] = rom_layouts[rom_layout]

	return metadata
	#0xd0-0xd4: Block allocation flags
	#0xd4-0xd6: Boots left (boots_left & 0x8000 = unlimited)
	#0xd9-0xda: Flags (SoundLink enabled, execution area, skip intro)
	#0xda-0xdb: Always 0x33
	#0xdb-0xdc: Version but in some weird format
	#0xdc-0xde: Checksum
	#0xde-0xe0: Inverse checksum
	

def add_satellaview_metadata(game):
	game.metadata.platform = 'Satellaview'
	possible_offsets = [0x7f00, 0xff00, 0x40ff00]
	rom_size = game.rom.get_size()

	if rom_size % 1024 == 512:
		possible_offsets = [0x8100, 0x10100, 0x410100]
		#Not sure what kind of bonehead puts copier headers on a Satellaview game, but I can easily handle that edge case, so I will
	
	header_data = None
	for possible_offset in possible_offsets:
		if possible_offset >= rom_size:
			continue

		try:
			header_data = parse_satellaview_header(game, possible_offset)
			break
		except BadSNESHeaderException:
			continue
	
	if header_data:
		game.metadata.specific_info['Mapper'] = header_data.get('ROM layout')
		publisher = header_data.get('Publisher')
		if publisher is not None:
			if publisher in nintendo_licensee_codes:
				game.metadata.publisher = nintendo_licensee_codes[publisher]
			elif publisher != '00':
				game.metadata.publisher = '<unknown Nintendo licensee {0}>'.format(publisher)
		game.metadata.day = header_data.get('Day')
		game.metadata.month = header_data.get('Month')

def add_snes_metadata(game):
	if game.rom.extension in ['sfc', 'smc', 'swc']:
		add_normal_snes_header(game)
	elif game.rom.extension == 'bs':
		add_satellaview_metadata(game)
	elif game.rom.extension == 'st':
		parse_sufami_turbo_header(game)
