import re
import os
import calendar

import cd_read
from common_types import SaveType
from data.sega_licensee_codes import licensee_codes
from .saturn import SaturnRegionCodes
#I'm just assuming Saturn and Dreamcast have the same way of doing region codes... well, it's just mostly JUE that need worrying about at this point anyway

gdi_regex = re.compile(r'^(?:\s+)?(?P<trackNumber>\d+)\s+(?P<unknown1>\S+)\s+(?P<type>\d)\s+(?P<sectorSize>\d+)\s+(?:"(?P<name>.+)"|(?P<name_unquoted>\S+))\s+(?P<unknown2>.+)$')

def add_peripherals_info(game, peripherals):
	game.metadata.specific_info['Uses-Windows-CE'] = (peripherals & 1) > 0
	game.metadata.specific_info['Supports-VGA'] = (peripherals & (1 << 4)) > 0
	game.metadata.specific_info['Force-Feedback'] = (peripherals & (1 << 9)) > 0
	game.metadata.specific_info['Supports-Microphone'] = (peripherals & (1 << 10)) > 0
	game.metadata.save_type = SaveType.MemoryCard if peripherals & (1 << 11) else SaveType.Nothing
	# Bit 1 << 12: Requires Start + A + B + dpad, but if you don't have those, what are you doing?
	#TODO: Set up game.metadata.input_info
	game.metadata.specific_info['Uses-C-Button'] = (peripherals & (1 << 13)) > 0
	game.metadata.specific_info['Uses-D-Button'] = (peripherals & (1 << 14)) > 0
	game.metadata.specific_info['Uses-X-Button'] = (peripherals & (1 << 15)) > 0
	game.metadata.specific_info['Uses-Y-Button'] = (peripherals & (1 << 16)) > 0
	game.metadata.specific_info['Uses-Z-Button'] = (peripherals & (1 << 17)) > 0
	game.metadata.specific_info['Uses-Expanded-Dpad'] = (peripherals & (1 << 18)) > 0 #Second dpad?
	game.metadata.specific_info['Uses-Analog-R'] = (peripherals & (1 << 19)) > 0
	game.metadata.specific_info['Uses-Analog-L'] = (peripherals & (1 << 20)) > 0
	game.metadata.specific_info['Uses-Analog-Horizontal'] = (peripherals & (1 << 21)) > 0
	game.metadata.specific_info['Uses-Analog-Vertical'] = (peripherals & (1 << 22)) > 0
	game.metadata.specific_info['Uses-Expanded-Analog-Horizontal'] = (peripherals & (1 << 23)) > 0
	game.metadata.specific_info['Uses-Expanded-Analog-Vertical'] = (peripherals & (1 << 24)) > 0
	game.metadata.specific_info['Supports-Keyboard'] = (peripherals & (1 << 25)) > 0

def _match_part_by_serial(software_part, serial):
	#TODO: Handle multiple discs properly
	#This isn't perfect whatsoever, but the hash itself is for the .chd file which doesn't always match up even if you convert stuff to .chd, so this is probably the best that can be done
	part_serial = software_part.software.get_info('serial')
	if not part_serial:
		return False
	part_serial_without_dashes = part_serial.replace('-', '')
	return part_serial == serial or part_serial_without_dashes == serial

device_info_regex = re.compile(r'^(?P<checksum>[\dA-Fa-f]{4}) GD-ROM(?P<discNum>\d+)/(?P<totalDiscs>\d+) *$')
#Might not be " GD-ROM" on some Naomi stuff or maybe some homebrews or protos, but anyway, whatevs
def add_info_from_main_track(game, track_path, sector_size):
	try:
		header = cd_read.read_mode_1_cd(track_path, sector_size, amount=128)
	except NotImplementedError:
		return

	#16-32 Copyright: Seems to always be "SEGA ENTERPRISES" but may or may not be mandatory?
	#74-80 Version
	#96-112 Boot filename
	#128-256 Internal name

	hardware_id = header[0:16].decode('ascii', errors='ignore')
	if hardware_id != 'SEGA SEGAKATANA ':
		#Won't boot on a real Dreamcast. I should check how much emulators care...
		game.metadata.specific_info['Hardware-ID'] = hardware_id
		game.metadata.specific_info['Invalid-Hardware-ID'] = True
		return

	device_info = header[32:48].decode('ascii', errors='ignore').rstrip()
	device_info_match = device_info_regex.match(device_info)
	if device_info_match:
		try:
			game.metadata.specific_info['Disc-Number'] = int(device_info_match['discNum'])
			game.metadata.specific_info['Disc-Total'] = int(device_info_match['totalDiscs'])
		except ValueError:
			pass

	region_info = header[48:56].rstrip()
	region_codes = []
	if b'J' in region_info:
		region_codes.append(SaturnRegionCodes.Japan)
	if b'U' in region_info:
		region_codes.append(SaturnRegionCodes.USA)
	if b'E' in region_info:
		region_codes.append(SaturnRegionCodes.Europe)
	#Some other region codes appear sometimes but they might not be entirely valid
	game.metadata.specific_info['Region-Code'] = region_codes

	try:
		peripherals = int(header[56:64], 16)
		add_peripherals_info(game, peripherals)
	except ValueError:
		pass

	game.metadata.product_code = header[64:74].decode('ascii', errors='backslashreplace').rstrip()

	for software_list in game.software_lists:
		software = software_list.find_software(part_matcher=_match_part_by_serial, part_matcher_args=[game.metadata.product_code])
		if software:
			software.add_generic_info(game)
			break

	release_date = header[80:96].decode('ascii', errors='backslashreplace').rstrip()

	try:
		game.metadata.year = int(release_date[0:4])
		game.metadata.month = calendar.month_name[int(release_date[4:6])]
		game.metadata.day = int(release_date[6:8])
	except ValueError:
		pass

	try:
		maker = header[112:128].decode('ascii').rstrip()
		if maker == 'SEGA ENTERPRISES':
			game.metadata.publisher = 'Sega'
		elif maker.startswith(('SEGA LC-', 'SEGA-LC-')):
			maker_code = maker[len('SEGA LC-'):]
			if maker_code in licensee_codes:
				game.metadata.publisher = licensee_codes[maker_code]
		else:
			game.metadata.publisher = maker
	except UnicodeDecodeError:
		pass

def add_info_from_gdi(game):
	data = game.rom.read().decode('utf8', errors='backslashreplace')
	for line in data.splitlines():
		match = gdi_regex.match(line)
		if match:
			track_number = int(match['trackNumber'])
			#is_data = match['type'] == '4'
			sector_size = int(match['sectorSize'])
			filename = match['name_unquoted'] if match['name_unquoted'] else match['name']
			#print(game.rom.path, track_number, is_data, sector_size, filename)
			if track_number == 3:
				full_name = filename if filename.startswith('/') else os.path.join(game.folder, filename)
				add_info_from_main_track(game, full_name, sector_size)


def add_dreamcast_metadata(game):
	if game.rom.extension == 'gdi':
		add_info_from_gdi(game)
