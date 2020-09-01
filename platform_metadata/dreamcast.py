import calendar
import os
import re

import cd_read
from common_types import SaveType
from data.sega_licensee_codes import licensee_codes

from .minor_systems import add_generic_info
from .saturn import SaturnRegionCodes

#I'm just assuming Saturn and Dreamcast have the same way of doing region codes... well, it's just mostly JUE that need worrying about at this point anyway

gdi_regex = re.compile(r'^(?:\s+)?(?P<trackNumber>\d+)\s+(?P<unknown1>\S+)\s+(?P<type>\d)\s+(?P<sectorSize>\d+)\s+(?:"(?P<name>.+)"|(?P<name_unquoted>\S+))\s+(?P<unknown2>.+)$')

def add_peripherals_info(metadata, peripherals):
	metadata.specific_info['Uses-Windows-CE'] = (peripherals & 1) > 0
	metadata.specific_info['Supports-VGA'] = (peripherals & (1 << 4)) > 0
	metadata.specific_info['Force-Feedback'] = (peripherals & (1 << 9)) > 0
	metadata.specific_info['Supports-Microphone'] = (peripherals & (1 << 10)) > 0
	metadata.save_type = SaveType.MemoryCard if peripherals & (1 << 11) else SaveType.Nothing
	#TODO: Set up metadata.input_info
	metadata.specific_info['Uses-Start-A-B-Dpad'] = (peripherals & (1 << 12)) > 0
	metadata.specific_info['Uses-C-Button'] = (peripherals & (1 << 13)) > 0 #Is this for Naomi, or something? That shouldn't exist
	metadata.specific_info['Uses-D-Button'] = (peripherals & (1 << 14)) > 0
	metadata.specific_info['Uses-X-Button'] = (peripherals & (1 << 15)) > 0
	metadata.specific_info['Uses-Y-Button'] = (peripherals & (1 << 16)) > 0
	metadata.specific_info['Uses-Z-Button'] = (peripherals & (1 << 17)) > 0
	metadata.specific_info['Uses-Expanded-Dpad'] = (peripherals & (1 << 18)) > 0 #Second dpad?
	metadata.specific_info['Uses-Analog-R'] = (peripherals & (1 << 19)) > 0
	metadata.specific_info['Uses-Analog-L'] = (peripherals & (1 << 20)) > 0
	metadata.specific_info['Uses-Analog-Horizontal'] = (peripherals & (1 << 21)) > 0
	metadata.specific_info['Uses-Analog-Vertical'] = (peripherals & (1 << 22)) > 0
	metadata.specific_info['Uses-Expanded-Analog-Horizontal'] = (peripherals & (1 << 23)) > 0
	metadata.specific_info['Uses-Expanded-Analog-Vertical'] = (peripherals & (1 << 24)) > 0
	metadata.specific_info['Uses-Keyboard'] = (peripherals & (1 << 25)) > 0

device_info_regex = re.compile(r'^(?P<checksum>[\dA-Fa-f]{4}) GD-ROM(?P<discNum>\d+)/(?P<totalDiscs>\d+) *$')
#Might not be " GD-ROM" on some Naomi stuff or maybe some homebrews or protos, but anyway, whatevs
def add_info_from_main_track(metadata, track_path, sector_size):
	try:
		header = cd_read.read_mode_1_cd(track_path, sector_size, amount=256)
	except NotImplementedError:
		return

	#96-112 Boot filename

	hardware_id = header[0:16].decode('ascii', errors='ignore')
	if hardware_id != 'SEGA SEGAKATANA ':
		#Won't boot on a real Dreamcast. I should check how much emulators care...
		metadata.specific_info['Hardware-ID'] = hardware_id
		metadata.specific_info['Invalid-Hardware-ID'] = True
		return

	copyright_info = header[16:32].decode('ascii', errors='ignore')
	#Seems to be always "SEGA ENTERPRISES"?
	metadata.specific_info['Copyright'] = copyright_info

	device_info = header[32:48].decode('ascii', errors='ignore').rstrip()
	device_info_match = device_info_regex.match(device_info)
	if device_info_match:
		try:
			metadata.disc_number = int(device_info_match['discNum'])
			metadata.disc_total = int(device_info_match['totalDiscs'])
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
	metadata.specific_info['Region-Code'] = region_codes

	try:
		peripherals = int(header[56:64], 16)
		add_peripherals_info(metadata, peripherals)
	except ValueError:
		pass

	metadata.product_code = header[64:74].decode('ascii', errors='backslashreplace').rstrip()
	try:
		version = header[74:80].decode('ascii').rstrip()
		if version[0] == 'V' and version[2] == '.':
			metadata.specific_info['Version'] = 'v' + version[1:]
	except UnicodeDecodeError:
		pass	

	release_date = header[80:96].decode('ascii', errors='backslashreplace').rstrip()

	try:
		metadata.year = int(release_date[0:4])
		metadata.month = calendar.month_name[int(release_date[4:6])]
		metadata.day = int(release_date[6:8])
	except ValueError:
		pass

	try:
		maker = header[112:128].decode('ascii').rstrip()
		if maker == 'SEGA ENTERPRISES':
			metadata.publisher = 'Sega'
		elif maker.startswith(('SEGA LC-', 'SEGA-LC-')):
			maker_code = maker[len('SEGA LC-'):]
			if maker_code in licensee_codes:
				metadata.publisher = licensee_codes[maker_code]
		elif maker:
			metadata.publisher = maker
	except UnicodeDecodeError:
		pass
		
	metadata.specific_info['Internal-Title'] = header[128:256].decode('ascii', errors='backslashreplace').rstrip('\0 ')


def add_info_from_gdi(rom, metadata):
	data = rom.read().decode('utf8', errors='backslashreplace')
	for line in data.splitlines():
		match = gdi_regex.match(line)
		if match:
			track_number = int(match['trackNumber'])
			#is_data = match['type'] == '4'
			sector_size = int(match['sectorSize'])
			filename = match['name_unquoted'] if match['name_unquoted'] else match['name']
			#print(game.rom.path, track_number, is_data, sector_size, filename)
			if track_number == 3:
				full_name = filename if filename.startswith('/') else os.path.join(os.path.dirname(rom.path), filename)
				add_info_from_main_track(metadata, full_name, sector_size)


def add_dreamcast_metadata(game):
	if game.rom.extension == 'gdi':
		add_info_from_gdi(game.rom, game.metadata)

	add_generic_info(game)
