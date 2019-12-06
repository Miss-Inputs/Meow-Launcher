import re
from enum import IntEnum
from zlib import crc32

import input_metadata
from common import NotAlphanumericException, convert_alphanumeric
from common_types import SaveType
from data.nintendo_licensee_codes import nintendo_licensee_codes
from info.region_info import TVSystem
from software_list_info import get_software_list_entry


class GameBoyMapper():
	def __init__(self, name, has_ram=False, has_battery=False, has_rtc=False, has_rumble=False, has_accelerometer=False):
		self.name = name
		self.has_ram = has_ram
		self.has_battery = has_battery
		self.has_rtc = has_rtc
		self.has_rumble = has_rumble
		self.has_accelerometer = has_accelerometer

	def __str__(self):
		return self.name

game_boy_mappers = {
	0: GameBoyMapper("ROM only"),
	8: GameBoyMapper("ROM only", has_ram=True),
	9: GameBoyMapper("ROM only", has_ram=True, has_battery=True),

	1: GameBoyMapper('MBC1'),
	2: GameBoyMapper('MBC1', has_ram=True),
	3: GameBoyMapper('MBC1', has_ram=True, has_battery=True),

	5: GameBoyMapper('MBC2'),
	6: GameBoyMapper('MBC2', has_ram=True, has_battery=True),

	11: GameBoyMapper('MMM01'),
	12: GameBoyMapper('MMM01', has_ram=True),
	13: GameBoyMapper('MMM01', has_ram=True, has_battery=True),

	15: GameBoyMapper('MBC3', has_battery=True, has_rtc=True),
	16: GameBoyMapper('MBC3', has_ram=True, has_battery=True, has_rtc=True),
	17: GameBoyMapper('MBC3'),
	18: GameBoyMapper('MBC3', has_ram=True),
	19: GameBoyMapper('MBC3', has_battery=True),

	#MBC4 might not exist. Hmm...

	25: GameBoyMapper('MBC5'),
	26: GameBoyMapper('MBC5', has_ram=True),
	27: GameBoyMapper('MBC5', has_ram=True, has_battery=True),
	28: GameBoyMapper('MBC5', has_rumble=True),
	29: GameBoyMapper('MBC5', has_rumble=True, has_ram=True),
	30: GameBoyMapper('MBC5', has_rumble=True, has_ram=True, has_battery=True),

	32: GameBoyMapper('MBC6', has_ram=True, has_battery=True),
	34: GameBoyMapper('MBC7', has_ram=True, has_battery=True, has_accelerometer=True), #Might have rumble? Don't think it does
	252: GameBoyMapper('Pocket Camera', has_ram=True, has_battery=True),
	253: GameBoyMapper('Bandai TAMA5'),
	254: GameBoyMapper('HuC3'),
	255: GameBoyMapper('HuC1', has_ram=True, has_battery=True),
}

mame_rom_slots = {
	'rom_188in1': '188 in 1',
	'rom_atvrac': 'ATV Racing',
	'rom_camera': 'Pocket Camera',
	'rom_chong': 'Chong Wu Xiao Jing Ling',
	'rom_digimon': 'Digimon 2',
	'rom_huc1': 'HuC1',
	'rom_huc3': 'HuC3',
	'rom_lasama': 'Story of Lasama',
	'rom_licheng': 'Li Cheng',
	'rom_m161': 'Mani 4 in 1 DMG-601',
	'rom_mbc1': 'MBC1',
	'rom_mbc1col': 'MBC1 Multicart',
	'rom_mbc2': 'MBC2',
	'rom_mbc3': 'MBC3',
	'rom_mbc5': 'MBC5',
	'rom_mbc6': 'MBC6',
	'rom_mbc7': 'MBC7',
	'rom_mmm01': 'MMM01',
	'rom_rock8': 'Rockman 8',
	'rom_sachen1': 'Sachen',
	'rom_sachen2': 'Sachen GBC',
	'rom_sintax': 'Sintax',
	'rom_sm3sp': 'Super Mario Special 3',
	'rom_tama5': 'Bandai TAMA5',
	'rom_wisdom': 'Wisdom Tree',
	#Sonic 3D Blast 5
	'rom_yong': 'Yong Yong',
}

class GameBoyColourFlag(IntEnum):
	No = 0
	Yes = 0x80
	Required = 0xc0
	#Ah yes, the three boolean values

def parse_slot(game, slot):
	if slot in mame_rom_slots:
		original_mapper = game.metadata.specific_info.get('Mapper', 'None')

		game.metadata.specific_info['Stated-Mapper'] = original_mapper

		new_mapper = mame_rom_slots[slot]

		if new_mapper != original_mapper:
			game.metadata.specific_info['Override-Mapper'] = True
			game.metadata.specific_info['Mapper'] = new_mapper

nintendo_logo_crc32 = 0x46195417
def parse_gameboy_header(game, header):
	nintendo_logo = header[4:0x34]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_logo_crc32
	game.metadata.specific_info['Nintendo-Logo-Valid'] = nintendo_logo_valid
	
	#Title: 0x34:0x44
	title = header[0x34:0x44]
	cgb_flag = title[15]
	title_length = 16
	try:
		game.metadata.specific_info['Is-Colour'] = GameBoyColourFlag(cgb_flag)
		title_length = 15
	except ValueError:
		#On older carts, this would just be the last character of the title, so it would be some random value
		#Anyway, that would logically mean it is not in colour
		game.metadata.specific_info['Is-Colour'] = GameBoyColourFlag.No
	#On newer games, product code is at title[11:15], the tricky part is what exactly is a newer game and what isn't, because if the product code isn't there then those characters are just the last 4 characters of the title. It seems that it's always there on GBC exclusives, and _maybe_ there on GBC-enhanced games. And that's only for officially licensed stuff of course.
	#Well, might as well try that. If it's junk, we're looking up the software list later for the proper serial anyway.
	if cgb_flag == 0xc0:
		try:
			game.metadata.product_code = title[11:15].decode('ascii').rstrip('\0')
			title_length = 11
		except UnicodeDecodeError:
			pass
	else:
		#Things end in null chars, so if there's null chars in the middle, that indicates if nothing else that the title ends there. If there is then 4 chars left over, that would probably be the product code
		maybe_title_and_serial = re.split(b'\0+', title[:title_length].rstrip(b'\0'))
		if len(maybe_title_and_serial) == 2:
			title_length = len(maybe_title_and_serial[0])
			if len(maybe_title_and_serial[1]) == 4:
				game.metadata.product_code = maybe_title_and_serial[1].decode('ascii').rstrip('\0')

	#Might as well add that to the info. I thiiink it's just ASCII and not Shift-JIS
	game.metadata.specific_info['Internal-Title'] = title[:title_length].decode('ascii', errors='backslashreplace').rstrip('\0')
	
	game.metadata.specific_info['SGB-Enhanced'] = header[0x46] == 3
	if header[0x47] in game_boy_mappers:
		mapper = game_boy_mappers[header[0x47]]
		game.metadata.specific_info['Mapper'] = mapper.name
		game.metadata.save_type = SaveType.Cart if mapper.has_battery else SaveType.Nothing
		game.metadata.specific_info['Force-Feedback'] = mapper.has_rumble
		game.metadata.specific_info['Has-RTC'] = mapper.has_rtc
		if mapper.has_accelerometer:
			game.metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls())

	game.metadata.specific_info['Destination-Code'] = header[0x4a]
	#0 means Japan and 1 means not Japan. Not sure how reliable that is.
	licensee_code = header[0x4b]
	if licensee_code == 0x33:
		try:
			licensee_code = convert_alphanumeric(header[0x44:0x46])
			if licensee_code in nintendo_licensee_codes:
				game.metadata.publisher = nintendo_licensee_codes[licensee_code]
		except NotAlphanumericException:
			pass
	else:
		licensee_code = '{:02X}'.format(licensee_code)
		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
	game.metadata.specific_info['Revision'] = header[0x4c]

def add_gameboy_metadata(game):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	game.metadata.input_info.add_option(builtin_gamepad)

	game.metadata.tv_type = TVSystem.Agnostic

	header = game.rom.read(seek_to=0x100, amount=0x50)
	parse_gameboy_header(game, header)

	if game.rom.extension == 'gbc':
		game.metadata.platform = 'Game Boy Color'

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game.metadata)
		game.metadata.specific_info['Has-RTC'] = software.get_part_feature('rtc') == 'yes'
		game.metadata.save_type = SaveType.Cart if software.has_data_area('nvram') else SaveType.Nothing

		slot = software.get_part_feature('slot')
		parse_slot(game, slot)
