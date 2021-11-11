import os
from enum import Enum
from typing import Optional
from xml.etree import ElementTree

from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.metadata import Metadata
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

from .gametdb import TDB, add_info_from_tdb

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')
class NintendoDiscRegion(Enum):
	NTSC_J = 0
	NTSC_U = 1
	PAL = 2
	RegionFree = 3  # Seemingly Wii only
	NTSC_K = 4  # Seemingly Wii only

def load_tdb() -> Optional[TDB]:
	if 'Wii' not in platform_configs:
		return None

	tdb_path = platform_configs['Wii'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError) as blorp:
		if main_config.debug:
			print('Oh no failed to load Wii TDB because', blorp)
		return None
tdb = load_tdb()

def add_cover(metadata: Metadata, product_code: str, licensee_code: str):
	#Intended for the covers database from GameTDB
	if 'Wii' not in platform_configs:
		return

	covers_path = platform_configs['Wii'].options.get('covers_path')
	if not covers_path:
		return
	cover_path = os.path.join(covers_path, product_code + licensee_code)
	for ext in ('png', 'jpg'):
		if os.path.isfile(cover_path + os.extsep + ext):
			metadata.images['Cover'] = cover_path + os.extsep + ext
			return

def add_gamecube_wii_disc_metadata(rom, metadata: Metadata, header: bytes):
	internal_title = header[32:128]
	metadata.specific_info['Internal-Title'] = internal_title.decode('ascii', errors='backslashreplace').rstrip('\0 ')
	if internal_title[:28] == b'GAMECUBE HOMEBREW BOOTLOADER':
		return

	product_code = None
	try:
		product_code = convert_alphanumeric(header[:4])
	except NotAlphanumericException:
		pass

	publisher = None
	licensee_code = None
	try:
		licensee_code = convert_alphanumeric(header[4:6])
		publisher = nintendo_licensee_codes.get(licensee_code)
	except NotAlphanumericException:
		pass

	if not (product_code == 'RELS' and licensee_code == 'AB'):
		# This is found on a few prototype discs, it's not valid
		metadata.product_code = product_code
		metadata.publisher = publisher
		if product_code and licensee_code:
			add_info_from_tdb(tdb, metadata, product_code + licensee_code)
			add_cover(metadata, product_code, licensee_code)

	disc_number = header[6] + 1
	if disc_number:
		metadata.disc_number = disc_number

	metadata.specific_info['Revision'] = header[7]

	#Audio streaming: header[8] > 1
	#Audio streaming buffer size: header[9]
	#Unused: 10-24

	is_wii = header[0x18:0x1c] == b']\x1c\x9e\xa3'
	is_gamecube = header[0x1c:0x20] == b'\xc23\x9f='
	# Is this ever set to both? In theory no, but... hmm

	if not is_wii and not is_gamecube:
		metadata.specific_info['No-Disc-Magic'] = True
	elif main_config.debug:
		if metadata.platform == 'Wii' and not is_wii:
			print(rom.path, 'lacks Wii disc magic')
		if metadata.platform == 'GameCube' and not is_gamecube:
			print(rom.path, 'lacks GameCube disc magic')
	
def just_read_the_wia_rvz_header_for_now(rom, metadata: Metadata):
	#I'll get around to it I swear
	wia_header = rom.read(amount=0x48)
	wia_disc_struct_size = int.from_bytes(wia_header[12:16], 'big')
	wia_disc_struct = rom.read(seek_to=0x48, amount=wia_disc_struct_size)
	disc_header = wia_disc_struct[16:128]
	add_gamecube_wii_disc_metadata(rom, metadata, disc_header)
