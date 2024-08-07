import contextlib
import logging
import os
from enum import IntEnum
from functools import cache
from typing import TYPE_CHECKING
from xml.etree import ElementTree

from meowlauncher.settings.platform_config import platform_configs
from meowlauncher.util.utils import NotAlphanumericError, convert_alphanumeric, load_dict

from .gametdb import TDB, add_info_from_tdb

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')


class NintendoDiscRegion(IntEnum):
	NTSC_J = 0
	NTSC_U = 1
	PAL = 2
	RegionFree = 3  # Seemingly Wii only
	NTSC_K = 4  # Seemingly Wii only


@cache
def _load_tdb() -> TDB | None:
	if 'Wii' not in platform_configs:
		return None

	tdb_path = platform_configs['Wii'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError):
		logger.exception('Oh no failed to load Wii TDB because')
		return None


def add_cover(game_info: 'GameInfo', product_code: str, licensee_code: str) -> None:
	"""Intended for the covers database from GameTDB"""
	if 'Wii' not in platform_configs:
		return

	covers_path = platform_configs['Wii'].options.get('covers_path')
	if not covers_path:
		return
	cover_path = covers_path.joinpath(product_code + licensee_code)
	for ext in ('png', 'jpg'):
		potential_cover_path = cover_path.with_suffix(os.extsep + ext)
		if potential_cover_path.is_file():
			game_info.images['Cover'] = potential_cover_path
			return


def add_gamecube_wii_disc_metadata(rom: 'FileROM', game_info: 'GameInfo', header: bytes) -> None:
	internal_title = header[32:128]
	game_info.specific_info['Internal Title'] = internal_title.rstrip(b'\0 ').decode(
		'ascii', errors='backslashreplace'
	)
	if internal_title[:28] == b'GAMECUBE HOMEBREW BOOTLOADER':
		return

	product_code = None
	with contextlib.suppress(NotAlphanumericError):
		product_code = convert_alphanumeric(header[:4])

	publisher = None
	licensee_code = None
	try:
		licensee_code = convert_alphanumeric(header[4:6])
		publisher = nintendo_licensee_codes.get(licensee_code)
	except NotAlphanumericError:
		pass

	if not (product_code == 'RELS' and licensee_code == 'AB'):
		# This is found on a few prototype discs, it's not valid
		game_info.product_code = product_code
		game_info.publisher = publisher
		if product_code and licensee_code:
			add_info_from_tdb(_load_tdb(), game_info, product_code + licensee_code)
			add_cover(game_info, product_code, licensee_code)

	disc_number = header[6] + 1
	if disc_number:
		game_info.disc_number = disc_number

	game_info.specific_info['Revision'] = header[7]

	# Audio streaming: header[8] > 1
	# Audio streaming buffer size: header[9]
	# Unused: 10-24

	is_wii = header[0x18:0x1C] == b']\x1c\x9e\xa3'
	is_gamecube = header[0x1C:0x20] == b'\xc23\x9f='
	# Is this ever set to both? In theory no, but... hmm

	if not is_wii and not is_gamecube:
		game_info.specific_info['No Disc Magic?'] = True
	elif game_info.platform == 'Wii' and not is_wii:
		logger.info('%s lacks Wii disc magic', rom)
	elif game_info.platform == 'GameCube' and not is_gamecube:
		logger.info('%s lacks GameCube disc magic', rom)


def just_read_the_wia_rvz_header_for_now(rom: 'FileROM', game_info: 'GameInfo') -> None:
	"""I'll get around to it I swear
	TODO: Around to it"""
	wia_header = rom.read(amount=0x48)
	wia_disc_struct_size = int.from_bytes(wia_header[12:16], 'big')
	wia_disc_struct = rom.read(seek_to=0x48, amount=wia_disc_struct_size)
	disc_header = wia_disc_struct[16:128]
	add_gamecube_wii_disc_metadata(rom, game_info, disc_header)
