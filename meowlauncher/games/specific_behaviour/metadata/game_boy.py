import re
from typing import TYPE_CHECKING, cast
from zlib import crc32

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.mame_common.software_list_info import (
    find_in_software_lists, matcher_args_for_bytes)
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.platform_types import GameBoyColourFlag
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

game_boy_config = platform_configs.get('Game Boy')
nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

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

gbx_mappers = {
	#Official
	b'ROM\0': 'ROM only',
	b'MBC1': 'MBC1',
	b'MBC2': 'MBC2',
	b'MBC3': 'MBC3',
	b'MBC5': 'MBC5',
	b'MBC7': 'MBC7',
	b'MB1M': 'MBC1 Multicart',
	b'MMM1': 'MMM01',
	b'CAMR': 'Pocket Camera',
	#Licensed 3rd-party
	b'HUC1': 'HuC1',
	b'HUC3': 'HuC3',
	b'TAM5': 'Bandai TAMA5',
	#Unlicensed
	b'BBD\0': 'BBD',
	b'HITK': 'Hitek',
	b'SNTX': 'Sintax',
	b'NTO1': 'NT older type 1',
	b'NTO2': 'NT older type 2',
	b'NTN\0': 'NT newer',
	b'LICH': 'Li Cheng',
	b'LBMC': 'Last Bible Multicart',
	b'LIBA': 'Liebao Technology',
	b'PKJD': 'Pokemon Jade/Diamond bootleg'
}

def parse_slot(metadata: 'Metadata', slot: str):
	if slot in mame_rom_slots:
		original_mapper = metadata.specific_info.get('Mapper', 'None')

		metadata.specific_info['Stated Mapper'] = original_mapper

		new_mapper = mame_rom_slots[slot]

		if new_mapper != original_mapper:
			metadata.specific_info['Override Mapper?'] = True
			metadata.specific_info['Mapper'] = new_mapper

nintendo_logo_crc32 = 0x46195417
def parse_gameboy_header(metadata: 'Metadata', header: bytes):
	nintendo_logo = header[4:0x34]
	nintendo_logo_valid = crc32(nintendo_logo) == nintendo_logo_crc32
	metadata.specific_info['Nintendo Logo Valid'] = nintendo_logo_valid
	
	title = header[0x34:0x44]
	cgb_flag = title[15]
	title_length = 16
	try:
		metadata.specific_info['Is Colour?'] = GameBoyColourFlag(cgb_flag)
		title_length = 15
	except ValueError:
		#On older carts, this would just be the last character of the title, so it would be some random value
		#Anyway, that would logically mean it is not in colour
		metadata.specific_info['Is Colour?'] = GameBoyColourFlag.No
	#On newer games, product code is at title[11:15], the tricky part is what exactly is a newer game and what isn't, because if the product code isn't there then those characters are just the last 4 characters of the title. It seems that it's always there on GBC exclusives, and _maybe_ there on GBC-enhanced games. And that's only for officially licensed stuff of course.
	#Well, might as well try that. If it's junk, we're looking up the software list later for the proper serial anyway.
	if cgb_flag == 0xc0:
		try:
			metadata.product_code = title[11:15].decode('ascii').rstrip('\0')
			title_length = 11
		except UnicodeDecodeError:
			pass
	else:
		#Things end in null chars, so if there's null chars in the middle, that indicates if nothing else that the title ends there. If there is then 4 chars left over, that would probably be the product code
		maybe_title_and_serial = re.split(b'\0+', title[:title_length].rstrip(b'\0'))
		if len(maybe_title_and_serial) == 2:
			title_length = len(maybe_title_and_serial[0])
			if len(maybe_title_and_serial[1]) == 4:
				metadata.product_code = maybe_title_and_serial[1].decode('ascii').rstrip('\0')

	#Might as well add that to the info. I thiiink it's just ASCII and not Shift-JIS
	metadata.specific_info['Internal Title'] = title[:title_length].decode('ascii', errors='backslashreplace').rstrip('\0')
	
	metadata.specific_info['SGB Enhanced?'] = header[0x46] == 3
	if header[0x47] in game_boy_mappers:
		mapper = game_boy_mappers[header[0x47]]
		metadata.specific_info['Mapper'] = mapper.name
		metadata.save_type = SaveType.Cart if mapper.has_battery else SaveType.Nothing
		metadata.specific_info['Force Feedback?'] = mapper.has_rumble
		metadata.specific_info['Has RTC?'] = mapper.has_rtc
		if mapper.has_accelerometer:
			metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls())

	metadata.specific_info['Destination Code'] = header[0x4a]
	#0 means Japan and 1 means not Japan. Not sure how reliable that is.
	licensee_code_int = header[0x4b]
	if licensee_code_int == 0x33:
		try:
			licensee_code = convert_alphanumeric(header[0x44:0x46])
			if licensee_code in nintendo_licensee_codes:
				metadata.publisher = nintendo_licensee_codes[licensee_code]
		except NotAlphanumericException:
			pass
	else:
		licensee_code = '{:02X}'.format(licensee_code_int)
		if licensee_code in nintendo_licensee_codes:
			metadata.publisher = nintendo_licensee_codes[licensee_code]
	metadata.specific_info['Revision'] = header[0x4c]

def parse_gbx_footer(rom: FileROM, metadata: 'Metadata'):
	footer = rom.read(seek_to=rom.get_size() - 64, amount=64)
	if footer[60:64] != b'GBX!':
		if main_config.debug:
			print(rom.path, 'GBX footer is invalid, siggy is', footer[60:64])
		return
	if int.from_bytes(footer[48:52], 'big') != 64 or int.from_bytes(footer[52:56], 'big') != 1:
		if main_config.debug:
			print(rom.path, 'GBX has unsupported major version:', int.from_bytes(footer[52:56], 'big'), 'or size:', int.from_bytes(footer[48:52], 'big'))
		return
	#56:60 is minor version, which we expect to be 0, but it'd be okay if not

	original_mapper = metadata.specific_info.get('Mapper', 'None')
	metadata.specific_info['Stated Mapper'] = original_mapper
	new_mapper = gbx_mappers.get(footer[0:4])
	if not new_mapper:
		if main_config.debug:
			print(rom.path, 'GBX has unknown spooky mapper:', footer[0:4])
		new_mapper = footer[0:4].decode()

	if new_mapper != original_mapper:
		#For now we're going to assume other emus don't actually do .gbx properly
		metadata.specific_info['Override Mapper?'] = True
		metadata.specific_info['Mapper'] = new_mapper

	#4 = has battery, #5 = has rumble, #6 = has RTC
	#RAM size: 12:16

def add_gameboy_metadata(game: 'ROMGame'):
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	game.metadata.input_info.add_option(builtin_gamepad)

	rom = cast(FileROM, game.rom)
	header = rom.read(seek_to=0x100, amount=0x50)
	parse_gameboy_header(game.metadata, header)

	if game_boy_config and game_boy_config.options.get('set_gbc_as_different_platform'):
		if game.rom.extension == 'gbc' or game.metadata.specific_info.get('Is Colour?') == GameBoyColourFlag.Required:
			game.metadata.platform = 'Game Boy Color'

	if game.rom.extension == 'gbx':
		software = find_in_software_lists(game.software_lists, matcher_args_for_bytes(rom.read(amount=rom.get_size() - 64)))
	else:
		software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.specific_info['Has RTC?'] = software.get_part_feature('rtc') == 'yes'
		game.metadata.save_type = SaveType.Cart if software.has_data_area('nvram') else SaveType.Nothing

		slot = software.get_part_feature('slot')
		if slot:
			parse_slot(game.metadata, slot)

	if game.rom.extension == 'gbx':
		parse_gbx_footer(rom, game.metadata)
