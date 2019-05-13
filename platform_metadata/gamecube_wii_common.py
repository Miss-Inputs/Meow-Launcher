from enum import Enum

import cd_read
from common import NotAlphanumericException, convert_alphanumeric
from config import main_config
from data.nintendo_licensee_codes import nintendo_licensee_codes

class NintendoDiscRegion(Enum):
	# Also seems to be used for Wii discs and WiiWare
	NTSC_J = 0
	NTSC_U = 1
	PAL = 2
	RegionFree = 3  # Seemingly Wii only
	NTSC_K = 4  # Seemingly Wii only

def gamecube_read(game, seek_to, amount):
	if game.rom.extension == 'gcz':
		return cd_read.read_gcz(game.rom.path, amount=amount, seek_to=seek_to)
	# FIXME won't work for wbfs
	return game.rom.read(amount=amount, seek_to=seek_to)

def add_gamecube_wii_disc_metadata(game, header):
	internal_title = header[32:128]
	game.metadata.specific_info['Internal-Title'] = internal_title.decode('ascii', errors='backslashreplace').rstrip('\0 ')
	if internal_title[:28] == b'GAMECUBE HOMEBREW BOOTLOADER':
		return

	product_code = None
	try:
		product_code = convert_alphanumeric(header[:4])
	except NotAlphanumericException:
		pass

	publisher = None
	try:
		licensee_code = convert_alphanumeric(header[4:6])
		publisher = nintendo_licensee_codes.get(licensee_code)
	except NotAlphanumericException:
		pass

	if not (product_code == 'RELS' and licensee_code == 'AB'):
		# This is found on a few prototype discs, it's not valid
		game.metadata.product_code = product_code
		game.metadata.publisher = publisher

	disc_number = header[6] + 1
	if disc_number:
		game.metadata.disc_number = disc_number

	game.metadata.revision = header[7]

	#Audio streaming: header[8] > 1
	#Audio streaming buffer size: header[9]
	#Unused: 10-24

	is_wii = header[0x18:0x1c] == b']\x1c\x9e\xa3'
	is_gamecube = header[0x1c:0x20] == b'\xc23\x9f='
	# Is this ever set to both? In theory no, but... hmm

	if not is_wii and not is_gamecube:
		game.metadata.specific_info['No-Disc-Magic'] = True
	elif main_config.debug:
		if game.metadata.platform == 'Wii' and not is_wii:
			print(game.rom.path, 'lacks Wii disc magic')
		if game.metadata.platform == 'GameCube' and not is_gamecube:
			print(game.rom.path, 'lacks GameCube disc magic')
	