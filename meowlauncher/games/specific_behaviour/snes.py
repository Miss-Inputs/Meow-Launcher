import calendar
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any

from meowlauncher.common_types import SaveType
from meowlauncher.games.mame_common.machine import (
    Machine, does_machine_match_name, iter_machines_from_source_file)
from meowlauncher.games.mame_common.mame_executable import \
    MAMENotInstalledException
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.platform_types import SNESExpansionChip
from meowlauncher.util.region_info import regions_by_name
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

from .common import snes_controllers as controllers

if TYPE_CHECKING:
	from collections.abc import Mapping
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.metadata import Metadata

_nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

class BadSNESHeaderException(Exception):
	pass

_ram_rom_sizes = {i: (1 << i) * 1024 for i in range(0, 256)}

_rom_layouts = {
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

@dataclass(frozen=True)
class ROMType():
	expansion_chip: SNESExpansionChip | None = None
	has_ram: bool = False
	has_battery: bool = False
	has_rtc: bool = False		

_rom_types = {
	0: ROMType(),
	1: ROMType(has_ram=True),
	2: ROMType(has_ram=True, has_battery=True),
	3: ROMType(SNESExpansionChip.DSP_1),
	4: ROMType(SNESExpansionChip.DSP_1, has_ram=True),
	5: ROMType(SNESExpansionChip.DSP_1, has_ram=True, has_battery=True),
	18: ROMType(has_battery=True), #Might not be used...
	19: ROMType(SNESExpansionChip.SuperFX),
	20: ROMType(SNESExpansionChip.SuperFX2),
	21: ROMType(SNESExpansionChip.SuperFX, has_battery=True),
	26: ROMType(SNESExpansionChip.SuperFX2, has_battery=True),
	37: ROMType(SNESExpansionChip.OBC_1),
	50: ROMType(SNESExpansionChip.SA_1, has_battery=True), #Different from 53... somehow... probably?
	52: ROMType(SNESExpansionChip.SA_1),
	53: ROMType(SNESExpansionChip.SA_1, has_battery=True),
	67: ROMType(SNESExpansionChip.S_DD1),
	69: ROMType(SNESExpansionChip.S_DD1, has_ram=True, has_battery=True),
	85: ROMType(has_ram=True, has_battery=True, has_rtc=True),
	227: ROMType(SNESExpansionChip.SuperGB, has_ram=True),
	229: ROMType(SNESExpansionChip.BSX),
	243: ROMType(SNESExpansionChip.CX4),
	245: ROMType(SNESExpansionChip.ST018),
	246: ROMType(SNESExpansionChip.ST010), #or ST011, but it doesn't distinguish there
	249: ROMType(SNESExpansionChip.SPC7110),
}

_countries = {
	0: regions_by_name['Japan'],
	1: regions_by_name['USA'],
	2: regions_by_name['Europe'], #Includes Oceania and Asia too... I guess I have some refactoring to do. Like maybe PAL should be a region
	3: regions_by_name['Sweden'], #Includes Scandanavia
	4: regions_by_name['Finland'],
	5: regions_by_name['Denmark'],
	6: regions_by_name['France'],
	7: regions_by_name['Netherlands'],
	8: regions_by_name['Spain'],
	9: regions_by_name['Germany'], #Also includes Austria and Switzerland, apparently
	10: regions_by_name['Italy'],
	11: regions_by_name['Hong Kong'], #Also includes China... apparently? Were SNES games officially sold there?
	12: regions_by_name['Indonesia'],
	13: regions_by_name['Korea'],
	15: regions_by_name['Canada'],
	16: regions_by_name['Brazil'],
	17: regions_by_name['Australia'], #Is this actually used? Australian-specific releases (e.g. TMNT) use Europe still
}

def _parse_sufami_turbo_header(rom: 'FileROM', metadata: 'Metadata') -> None:
	metadata.platform = 'Sufami Turbo'

	#Safe bet that every single ST game just uses a normal controller
	#…Is it?
	metadata.input_info.add_option(controllers.controller)

	header = rom.read(amount=56)
	#Magic: 0:14 Should be "BANDAI SFC-ADX"
	metadata.specific_info['Internal Title'] = header[16:30].decode('shift-jis', 'backslashreplace')
	#Game ID: 48:51 Could this be considered product code?
	metadata.series_index = header[51]
	#ROM speed: 52
	#Features: 53 Not sure what this does, though = 1 may indicate SRAM or linkable
	#ROM size: 54 In 128KB units
	save_size = header[55]
	#In 2KB units, if you wanted to actually know the size
	#The SRAM is in the mini-cartridge, not the Sufami Turbo BIOS cart itself
	metadata.save_type = SaveType.Cart if save_size > 0 else SaveType.Nothing

def _parse_snes_header(rom: 'FileROM', base_offset: int) -> 'Mapping[str, Any]':
	#TODO: Use namedtuple/dataclass
	#In order to make things simpler, we'll just ignore any carts that are out of line. You wouldn't be able to get interesting results from homebrew or bootleg games anyway
	#Hence why we won't add metadata to the game object straight away, we'll store it in a dict first and add it all later, so we add nothing at all from invalid headers
	metadata: dict[str, Any] = {}

	#Note that amount goes up to 256 if you include exception vectors, but... nah
	header = rom.read(seek_to=base_offset, amount=0xe0)
	title = None
	try:
		title = header[0xc0:0xd5].decode('shift_jis')
		metadata['Title'] = title
	except UnicodeDecodeError as ude:
		raise BadSNESHeaderException(f'Title not ASCII or Shift-JIS: {header[0xc0:0xd5].decode("shift_jis", errors="backslashreplace")}') from ude

	
	rom_layout = header[0xd5]
	if rom_layout in _rom_layouts:
		metadata['ROM layout'] = _rom_layouts[rom_layout]
	elif title == "HAL'S HOLE IN ONE GOL":
		#HAL's Hole in Golf has 70 here, because that's the letter F, and the title immediately preceding this is "HAL HOLE IN ONE GOL". Looks like they overwrote this part of the header with the letter F. Whoops.
		#Anyway the internet says it's LoROM + SlowROM
		metadata['ROM layout'] = _rom_layouts[0x20]
	else:
		raise BadSNESHeaderException(f'ROM layout is weird: {hex(rom_layout)}')

	rom_type = header[0xd6]
	if rom_type in _rom_types:
		metadata['ROM type'] = _rom_types[rom_type]
	else:
		raise BadSNESHeaderException(f'ROM type is weird: {rom_type}')

	rom_size = header[0xd7]
	if rom_size not in _ram_rom_sizes:
		raise BadSNESHeaderException(f'ROM size is weird: {rom_size}')
	ram_size = header[0xd8]
	#We'll just use ROM type to detect presence of save data rather than this
	if ram_size not in _ram_rom_sizes:
		raise BadSNESHeaderException(f'RAM size is weird: {ram_size}')
	country = header[0xd9]
	#Dunno if I want to validate against countries, honestly. Might go wrong
	if country in _countries:
		metadata['Country'] = _countries[country]

	licensee = header[0xda]
	#Hmm.. not sure if I should validate that, but... it shouldn't be 0x00 or 0xff, maybe?

	metadata['Revision'] = header[0xdb]

	inverse_checksum = int.from_bytes(header[0xdc:0xde], 'little')
	checksum = int.from_bytes(header[0xde:0xe0], 'little')
	#Can't be arsed calculating the checksum because it's complicated (especially with some weird ROM sizes), but we know they have to add up to 0xffff
	if (checksum | inverse_checksum) != 0xffff:
		raise BadSNESHeaderException(f"Checksum and inverse checksum don't add up: {checksum:02X} {inverse_checksum:02X}")

	if licensee == 0x33:
		try:
			maker_code = convert_alphanumeric(header[0xb0:0xb2])
			metadata['Licensee'] = maker_code
		except NotAlphanumericException as nae:
			raise BadSNESHeaderException(f'Licensee code in extended header not alphanumeric: {header[0xb0:0xb2].decode("ascii", errors="backslashreplace")}') from nae

		try:
			product_code = convert_alphanumeric(header[0xb2:0xb6])
			metadata['Product code'] = product_code
		except NotAlphanumericException as nae:
			if header[0xb4:0xb6] == b'  ':
				try:
					product_code = convert_alphanumeric(header[0xb2:0xb4])
					metadata['Product code'] = product_code
				except NotAlphanumericException as naenae: #get naenaed
					raise BadSNESHeaderException(f'2 char product code not alphanumeric: {header[0xb2:0xb4].decode("ascii", errors="backslashreplace")}') from naenae
			else:
				raise BadSNESHeaderException(f'4 char product code not alphanumeric: {header[0xb2:0xb6].decode("ascii", errors="backslashreplace")}') from nae
	else:
		metadata['Licensee'] = f'{licensee:02X}'

	return metadata

def _add_normal_snes_header(rom: 'FileROM', metadata: 'Metadata') -> None:
	#Note that while we're seeking to xx00 here, the header actually starts at xxc0 (or xxb0 in case of extended header), it's just easier this way
	possible_offsets = {0x7f00, 0xff00, 0x40ff00}
	rom_size = rom.size
	if rom_size % 1024 == 512:
		#512-byte copier header at beginning
		rom.header_length_for_crc_calculation = 512
		metadata.specific_info['Has Copier Header?'] = True
		possible_offsets = {offset + 512 for offset in possible_offsets}
		#While the copier header specifies LoROM/HiROM/etc, they are sometimes wrong, so I will ignore them

	header_data = None
	#ex = None
	for possible_offset in possible_offsets:
		if possible_offset >= rom_size:
			continue

		try:
			header_data = _parse_snes_header(rom, possible_offset)
			break
		except BadSNESHeaderException:
			#ex = bad_snes_ex
			continue

	if header_data:
		metadata.specific_info['Internal Title'] = header_data['Title']
		metadata.specific_info['Mapper'] = header_data.get('ROM layout')
		rom_type = header_data.get('ROM type')
		if rom_type:
			metadata.specific_info['Expansion Chip'] = rom_type.expansion_chip
			metadata.save_type = SaveType.Cart if rom_type.has_battery else SaveType.Nothing
			metadata.specific_info['Has RTC?'] = rom_type.has_rtc
		licensee = header_data.get('Licensee')
		if licensee is not None:
			if licensee in _nintendo_licensee_codes:
				metadata.publisher = _nintendo_licensee_codes[licensee]
		metadata.specific_info['Revision'] = header_data.get('Revision')
		product_code = header_data.get('Product code')
		if product_code:
			metadata.product_code = product_code
	#else:
	#	print(rom.path, 'could not detect header because', ex)

def _parse_satellaview_header(rom: 'FileROM', base_offset: int) -> 'Mapping[str, Any]':
	#TODO Use namedtuple/dataclass
	header = rom.read(seek_to=base_offset, amount=0xe0)
	metadata: dict[str, Any] = {}

	try:
		publisher = convert_alphanumeric(header[0xb0:0xb2])
		metadata['Publisher'] = publisher
	except NotAlphanumericException as nae:
		raise BadSNESHeaderException("Publisher not alphanumeric") from nae

	try:
		title = header[0xc0:0xd0].decode('shift_jis')
		metadata['Title'] = title
	except UnicodeDecodeError as ude:
		raise BadSNESHeaderException(f'Title not ASCII or Shift-JIS: {header[0xc0:0xd0].decode("shift_jis", errors="backslashreplace")}') from ude

	month = (header[0xd6] & 0b_1111_0000) >> 4
	day = (header[0xd7] & 0b_1111_1000) >> 3
	if not month or month > 12:
		raise BadSNESHeaderException(f'Month not valid: {month}')
	if day > 31:
		raise BadSNESHeaderException(f'Day not valid: {day}')
	metadata['Month'] = calendar.month_name[month]
	metadata['Day'] = day

	rom_layout = header[0xd8]
	if rom_layout not in _rom_layouts:
		raise BadSNESHeaderException(f'ROM layout is weird: {rom_layout}')
	metadata['ROM layout'] = _rom_layouts[rom_layout]

	return metadata
	#0xd0-0xd4: Block allocation flags
	#0xd4-0xd6: Boots left (boots_left & 0x8000 = unlimited)
	#0xd9-0xda: Flags (SoundLink enabled, execution area, skip intro)
	#0xda-0xdb: Always 0x33
	#0xdb-0xdc: Version but in some weird format
	#0xdc-0xde: Checksum
	#0xde-0xe0: Inverse checksum

def _add_satellaview_metadata(rom: 'FileROM', metadata: 'Metadata') -> None:
	metadata.platform = 'Satellaview'
	#Safe bet that every single Satellaview game just uses a normal controller
	metadata.input_info.add_option(controllers.controller)
	possible_offsets = [0x7f00, 0xff00, 0x40ff00]
	rom_size = rom.size

	if rom_size % 1024 == 512:
		possible_offsets = [0x8100, 0x10100, 0x410100]
		#Not sure what kind of bonehead puts copier headers on a Satellaview game, but I can easily handle that edge case, so I will

	header_data = None
	for possible_offset in possible_offsets:
		if possible_offset >= rom_size:
			continue

		try:
			header_data = _parse_satellaview_header(rom, possible_offset)
			break
		except BadSNESHeaderException:
			continue

	if header_data:
		metadata.specific_info['Internal Title'] = header_data['Title']
		metadata.specific_info['Mapper'] = header_data.get('ROM layout')
		publisher = header_data.get('Publisher')
		if publisher is not None:
			if publisher in _nintendo_licensee_codes:
				metadata.publisher = _nintendo_licensee_codes[publisher]
		metadata.specific_info['Day'] = header_data.get('Day') #hmm… unfortunately it doesn't have a nice year for us to use
		metadata.specific_info['Month'] = header_data.get('Month')

def find_equivalent_snes_arcade(name: str) -> Machine | None:
	if not default_mame_executable:
		#CBF tbhkthbai
		return None
	if not hasattr(find_equivalent_snes_arcade, 'nss_games'):
		try:
			find_equivalent_snes_arcade.nss_games = set(iter_machines_from_source_file('nss', default_mame_executable)) #type: ignore[attr-defined]
		except MAMENotInstalledException:
			find_equivalent_snes_arcade.nss_games = set() #type: ignore[attr-defined]
	if not hasattr(find_equivalent_snes_arcade, 'arcade_bootlegs'):
		try:
			find_equivalent_snes_arcade.arcade_bootlegs = set(chain(iter_machines_from_source_file('snesb', default_mame_executable), iter_machines_from_source_file('snesb51', default_mame_executable))) #type: ignore[attr-defined]
		except MAMENotInstalledException:
			find_equivalent_snes_arcade.arcade_bootlegs = set() #type: ignore[attr-defined]

	for machine in chain(find_equivalent_snes_arcade.nss_games, find_equivalent_snes_arcade.arcade_bootlegs): #type: ignore[attr-defined]
		if does_machine_match_name(name, machine):
			return machine

	return None

def add_snes_rom_header_info(rom: 'FileROM', metadata: 'Metadata') -> None:
	if rom.extension in {'sfc', 'smc', 'swc'}:
		_add_normal_snes_header(rom, metadata)
	elif rom.extension == 'bs':
		_add_satellaview_metadata(rom, metadata)
	elif rom.extension == 'st':
		_parse_sufami_turbo_header(rom, metadata)

def add_snes_software_list_metadata(software: 'Software', metadata: 'Metadata') -> None:
	software.add_standard_metadata(metadata)
	if metadata.save_type == SaveType.Unknown and metadata.platform != 'Satellaview':
		metadata.save_type = SaveType.Cart if software.has_data_area('nvram') else SaveType.Nothing
	#We can actually get lorom/hirom from feature = slot. Hmm...
	metadata.specific_info['Slot'] = software.get_part_feature('slot')
	expansion_chip = software.get_part_feature('enhancement')
	#This stuff is detected as DSP_1 from the ROM header, so let's do that properly
	if expansion_chip == 'DSP2':
		metadata.specific_info['Expansion Chip'] = SNESExpansionChip.DSP_2
	elif expansion_chip == 'DSP3':
		metadata.specific_info['Expansion Chip'] = SNESExpansionChip.DSP_3
	elif expansion_chip == 'DSP4':
		metadata.specific_info['Expansion Chip'] = SNESExpansionChip.DSP_4
	#Distinguish between subtypes properly
	elif expansion_chip == 'ST010':
		metadata.specific_info['Expansion Chip'] = SNESExpansionChip.ST010
	elif expansion_chip == 'ST011':
		metadata.specific_info['Expansion Chip'] = SNESExpansionChip.ST011

	#Meh...
	if software.name in {'ffant2', 'ffant2a'}:
		metadata.series = 'Final Fantasy'
		metadata.series_index = '4'
	elif software.name in {'ffant3', 'ffant3a', 'ffant3p'}:
		metadata.series = 'Final Fantasy'
		metadata.series_index = '6'
