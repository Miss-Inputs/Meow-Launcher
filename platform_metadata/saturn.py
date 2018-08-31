import os
import calendar

import cd_read
from .sega_common import licensee_codes

def add_saturn_info(game, header):
	#42:48 Version
	#56:64 Device info (disc number/total discs)
	#64:80 Compatible regions; only 10 characters are used
	#80:96 Peripherals #TODO this, and set up game.metadata.input_info (no other peripherals are related to that)
	#96:208 Internal name

	hardware_id = header[0:16].decode('ascii', errors='ignore')
	if hardware_id != 'SEGA SEGASATURN ':
		#Won't boot on a real Dreamcast. I should check how much emulators care...
		game.metadata.specific_info['Hardware-ID'] = hardware_id
		game.metadata.specific_info['Invalid-Hardware-ID'] = True
		return

	try:
		maker = header[16:32].decode('ascii').rstrip()
		if maker.startswith('SEGA TP '):
			#"Sega Third Party", I guess
			maker_code = maker[len('SEGA TP '):]
			if maker_code in licensee_codes:
				game.metadata.publisher = licensee_codes[maker_code]
		elif maker == 'SEGA ENTERPRISES':
			game.metadata.publisher = 'Sega'
		else:
			game.metadata.publisher = maker
	except UnicodeDecodeError:
		pass

	try:
		game.metadata.product_code = header[32:42].decode('ascii').rstrip()
	except UnicodeDecodeError:
		pass

	release_date = header[48:56].decode('ascii', errors='backslashreplace').rstrip()

	try:
		game.metadata.year = int(release_date[0:4])
		game.metadata.month = calendar.month_name[int(release_date[4:6])]
		game.metadata.day = int(release_date[6:8])
	except ValueError:
		pass


def add_saturn_metadata(game):
	if game.rom.extension == 'cue':
		first_track, sector_size = cd_read.get_first_data_cue_track(game.rom.path)

		if not os.path.isfile(first_track):
			print(game.rom.path, 'has invalid cuesheet')
			return
		try:
			header = cd_read.read_mode_1_cd(first_track, sector_size, seek_to=0, amount=256)
		except NotImplementedError:
			return
	elif game.rom.extension == 'ccd':
		img_file = os.path.splitext(game.rom.path)[0] + '.img'
		#I thiiiiiiiiink .ccd/.img always has 2352-byte sectors?
		try:
			header = cd_read.read_mode_1_cd(img_file, 2352, seek_to=0, amount=256)
		except NotImplementedError:
			return
	elif game.rom.extension == 'iso':
		header = game.rom.read(seek_to=0, amount=256)
	else:
		return

	add_saturn_info(game, header)
