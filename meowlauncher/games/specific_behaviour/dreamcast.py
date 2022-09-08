import re
from pathlib import Path
from typing import TYPE_CHECKING

from meowlauncher.common_types import SaveType
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.metadata import Date, Metadata
from meowlauncher.platform_types import SaturnRegionCodes
from meowlauncher.util import cd_read
from meowlauncher.util.utils import load_dict

from meowlauncher.games.common.generic_info import add_generic_software_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame

_licensee_codes = load_dict(None, 'sega_licensee_codes')

#I'm just assuming Saturn and Dreamcast have the same way of doing region codes... well, it's just mostly JUE that need worrying about at this point anyway

_gdi_regex = re.compile(r'^(?:\s+)?(?P<trackNumber>\d+)\s+(?P<unknown1>\S+)\s+(?P<type>\d)\s+(?P<sectorSize>\d+)\s+(?:"(?P<name>.+)"|(?P<name_unquoted>\S+))\s+(?P<unknown2>.+)$')

def _add_peripherals_info(metadata: Metadata, peripherals: int) -> None:
	metadata.specific_info['Uses Windows CE?'] = (peripherals & 1) > 0
	metadata.specific_info['Supports VGA?'] = (peripherals & (1 << 4)) > 0
	metadata.specific_info['Uses Other Expansions?'] = (peripherals & (1 << 8)) > 0 #How very vague and mysterious…
	metadata.specific_info['Force Feedback?'] = (peripherals & (1 << 9)) > 0
	metadata.specific_info['Supports Microphone?'] = (peripherals & (1 << 10)) > 0
	metadata.save_type = SaveType.MemoryCard if peripherals & (1 << 11) else SaveType.Nothing
	#TODO: Set up metadata.input_info

	button_bits = {
		'Start, A, B, D-pad': 12,
		'C': 13, #Naomi?
		'D': 14, #Naomi?
		'X': 15,
		'Y': 16,
		'Z': 17,
		'Exanded D-pad': 18, #Some kind of second dpad? 8-way? What does this mean
		'Analog R': 19,
		'Analog L': 20,
		'Analog Horizontal': 21,
		'Analog Vertical': 22,
		'Expanded Analog Horizontal': 23, #What does this mean
		'Expanded Analog Vertical': 24,
	}
	buttons = {k for k, v in button_bits.items() if peripherals & (1 << v)}
	metadata.specific_info['Controls Used'] = buttons
	
	metadata.specific_info['Uses Gun?'] = (peripherals & (1 << 25)) > 0
	metadata.specific_info['Uses Keyboard?'] = (peripherals & (1 << 26)) > 0
	metadata.specific_info['Uses Mouse?'] = (peripherals & (1 << 27)) > 0

_device_info_regex = re.compile(r'^(?P<checksum>[\dA-Fa-f]{4}) GD-ROM(?P<discNum>\d+)/(?P<totalDiscs>\d+) *$')
#Might not be " GD-ROM" on some Naomi stuff or maybe some homebrews or protos, but anyway, whatevs

def _add_info_from_main_track(metadata: Metadata, track_path: Path, sector_size: int) -> None:
	try:
		header = cd_read.read_mode_1_cd(track_path, sector_size, amount=256)
	except NotImplementedError:
		return

	hardware_id = header[0:16]
	if hardware_id != b'SEGA SEGAKATANA ':
		#Won't boot on a real Dreamcast. I should check how much emulators care...
		#Well it does mean the rest of this header is bogus
		metadata.specific_info['Hardware ID'] = hardware_id.decode('ascii', errors='backslashreplace')
		metadata.specific_info['Invalid Hardware ID?'] = True
		return

	copyright_info = header[16:32].decode('ascii', errors='backslashreplace')
	#Seems to be always "SEGA ENTERPRISES"?
	metadata.specific_info['Copyright'] = copyright_info

	device_info = header[32:48].strip(b' ').decode('ascii', errors='backslashreplace')
	device_info_match = _device_info_regex.match(device_info)
	if device_info_match:
		try:
			metadata.disc_number = int(device_info_match['discNum'])
			metadata.disc_total = int(device_info_match['totalDiscs'])
		except ValueError:
			pass

	region_info = header[48:56]
	region_codes = set()
	if b'J' in region_info:
		region_codes.add(SaturnRegionCodes.Japan)
	if b'U' in region_info:
		region_codes.add(SaturnRegionCodes.USA)
	if b'E' in region_info:
		region_codes.add(SaturnRegionCodes.Europe)
	#Some other region codes appear sometimes but they might not be entirely valid
	metadata.specific_info['Region Code'] = region_codes

	try:
		peripherals = int(header[56:64], 16)
		_add_peripherals_info(metadata, peripherals)
	except ValueError:
		pass

	metadata.product_code = header[64:74].rstrip(b' ').decode('ascii', errors='backslashreplace')
	try:
		version = header[74:80].rstrip(b' ').decode('ascii')
		if version[0] == 'V' and version[2] == '.':
			metadata.specific_info['Version'] = 'v' + version[1:]
	except UnicodeDecodeError:
		pass	

	release_date = header[80:96].rstrip(b' ').decode('ascii', errors='backslashreplace')

	try:
		year = release_date[0:4]
		month = release_date[4:6]
		day = release_date[6:8]
		metadata.specific_info['Header Date'] = Date(year, month, day)
		guessed = Date(year, month, day, True)
		if guessed.is_better_than(metadata.release_date):
			metadata.release_date = guessed
	except ValueError:
		pass
	
	try:
		metadata.specific_info['Executable Name'] = header[96:112].rstrip(b' ').decode('ascii')
	except UnicodeDecodeError:
		pass

	try:
		maker = header[112:128].rstrip(b' ').decode('ascii')
		if maker == 'SEGA ENTERPRISES':
			metadata.publisher = 'Sega'
		elif maker.startswith(('SEGA LC-', 'SEGA-LC-')):
			maker_code = maker[len('SEGA LC-'):]
			if maker_code in _licensee_codes:
				metadata.publisher = _licensee_codes[maker_code]
		elif maker:
			metadata.publisher = maker
	except UnicodeDecodeError:
		pass
		
	metadata.specific_info['Internal Title'] = header[128:256].rstrip(b'\0 ').decode('ascii', errors='backslashreplace')

def add_dreamcast_rom_info(rom: FileROM, metadata: Metadata) -> None:
	if rom.extension == 'gdi':
		data = rom.read().decode('utf8', errors='backslashreplace')
		for line in data.splitlines():
			match = _gdi_regex.match(line)
			if match:
				track_number = int(match['trackNumber'])
				#is_data = match['type'] == '4'
				sector_size = int(match['sectorSize'])
				filename = match['name_unquoted'] if match['name_unquoted'] else match['name']
				if track_number == 3:
					full_name = Path(filename) if filename.startswith('/') else rom.path.parent.joinpath(filename)
					_add_info_from_main_track(metadata, full_name, sector_size)

def add_dreamcast_custom_info(game: 'ROMGame') -> None:
	if game.rom.extension == 'gdi' and isinstance(game.rom, FileROM):
		add_dreamcast_rom_info(game.rom, game.metadata)

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass
