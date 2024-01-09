import logging
import os
import struct
from collections.abc import Collection, Sequence
from typing import TYPE_CHECKING, cast
from xml.etree import ElementTree

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher import input_info
from meowlauncher.settings.platform_config import platform_configs
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.util.region_info import Region, regions_by_name
from meowlauncher.util.utils import (NotAlphanumericException,
                                     convert_alphanumeric, load_dict)

from .common.gametdb import TDB, add_info_from_tdb
from .common.nintendo_common import DSi3DSAgeRatings, add_ratings_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

_nintendo_licensee_codes = load_dict(None, 'nintendo_licensee_codes')

#For DSiWare, we can get public.sav and private.sav filesize, and that tells us if SaveType = Internal or Nothing. But we won't worry about DSiWare for now

def _load_tdb() -> TDB | None:
	if 'DS' not in platform_configs:
		return None

	tdb_path = platform_configs['DS'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError):
		logger.exception('Oh no failed to load DS TDB')
		return None
_tdb = _load_tdb()

def _add_cover(metadata: 'GameInfo', product_code: str) -> None:
	#Intended for the covers database from GameTDB
	covers_path = platform_configs['DS'].options.get('covers_path')
	if not covers_path:
		return
	cover_path = covers_path.joinpath(product_code)
	for ext in ('png', 'jpg'):
		potential_cover_path = cover_path.with_suffix(os.extsep + ext)
		if potential_cover_path.is_file():
			metadata.images['Cover'] = potential_cover_path
			break

def _convert_ds_colour_to_rgba(colour: int, is_transparent: bool) -> tuple[int, int, int, int]:
	red = (colour & 0b_00000_00000_11111) << 3
	green = (colour & 0b_00000_11111_00000) >> 2
	blue = (colour & 0b_11111_00000_00000) >> 7

	return (red, green, blue, 0 if is_transparent else 0xff)

def _decode_icon(bitmap: bytes, palette: Sequence[int]) -> 'Image.Image':
	icon = Image.new('RGBA', (32, 32))

	rgb_palette = [(0, 0, 0, 0)] * 16
	for i, colour in enumerate(palette):
		rgb_palette[i] = _convert_ds_colour_to_rgba(colour, i == 0)

	pos = 0
	data = [(0, 0, 0, 0)] * 32 * 32
	for tile_y in range(0, 4):
		for tile_x in range(0, 4):
			for y in range(0, 8):
				for x in range(0, 4):
					pixel_x = (x * 2) + (8 * tile_x)
					pixel_y = y + (8 * tile_y)
					data[pixel_y * 32 + pixel_x] = rgb_palette[bitmap[pos] & 0x0f]
					data[pixel_y * 32 + pixel_x + 1] = rgb_palette[(bitmap[pos] & 0xf0) >> 4]
					pos += 1
	icon.putdata(data)
	return icon

def _parse_dsi_region_flags(region_flags: int) -> Collection[Region]:
	regions = set()
	if region_flags & 1:
		regions.add(regions_by_name['Japan'])
	if region_flags & 2:
		regions.add(regions_by_name['USA'])
	if region_flags & 4:
		regions.add(regions_by_name['Europe'])
	if region_flags & 8:
		regions.add(regions_by_name['Australia'])
	if region_flags & 16:
		regions.add(regions_by_name['China'])
	if region_flags & 32:
		regions.add(regions_by_name['Korea'])
	return regions

def _add_banner_title_metadata(metadata: 'GameInfo', banner_title: str, language: str | None=None) -> None:
	lines = banner_title.splitlines()
	metadata_name = 'Banner Title'
	if language:
		metadata_name = f'{language} {metadata_name}'
	if lines:
		#The lines are generally either 2 lines like this
		#Art Academy
		#Nintendo
		#or 3 lines like this:
		#Cooking Guide
		#Can't decide what to eat?
		#Nintendo
		if len(lines) == 1:
			metadata.add_alternate_name(lines[0], metadata_name)
		else:
			metadata.add_alternate_name(' '.join(lines[:-1]), metadata_name)
			#This is usually the publisher… but it has a decent chance of being something else so I'm not gonna set metadata.publisher from it
			metadata.specific_info[metadata_name + ' Final Line'] = lines[-1]

def _parse_banner(rom: FileROM, metadata: 'GameInfo', header: bytes, is_dsi: bool, banner_offset: int) -> None:
	#The extended part of the banner if is_dsi contains animated icon frames, so we don't really need it
	banner_size = int.from_bytes(header[0x208:0x20c], 'little') if is_dsi else 0xA00
	banner = rom.read(seek_to=banner_offset, amount=banner_size)
	version = int.from_bytes(banner[0:2], 'little')
	metadata.specific_info['Banner Version'] = version
	#2 = has Chinese, 3 = has Korean, 0x103, has DSi stuff

	if version in {1, 2, 3, 0x103}:
		banner_titles = {}
		banner_languages = {
			0: 'Japanese',
			1: 'English',
			2: 'French',
			3: 'German',
			4: 'Italian',
			5: 'Spanish',
			6: 'Chinese', #Version >= 2
			7: 'Korean' #Version >= 3
		}

		for i in range(7):
			try:
				banner_title = banner[0x240 + (i * 256): 0x240 + (i * 256) + 256].rstrip(b'\0 \xff') .decode('utf-16le')
				#if banner_title and not all([c == '\uffff' for c in banner_title]):
				if banner_title:
					banner_titles[banner_languages[i]] = banner_title
			except (UnicodeDecodeError, IndexError):
				continue
		
		for lang, title in banner_titles.items():
			_add_banner_title_metadata(metadata, title, lang)

		if banner_titles:
			banner_title = banner_titles.get('English', next(iter(banner_titles.values())))
			_add_banner_title_metadata(metadata, banner_title)

		if len(banner) >= 0x240:
			if have_pillow:
				icon_bitmap = banner[0x20:0x220]
				icon_palette = struct.unpack('H' * 16, banner[0x220:0x240])
				metadata.images['Icon'] = _decode_icon(icon_bitmap, icon_palette)

def _add_info_from_ds_header(rom: FileROM, metadata: 'GameInfo', header: bytes) -> None:
	if header[0:4] == b'.\0\0\xea':
		metadata.specific_info['PassMe?'] = True
	else:
		internal_title = header[0:12].rstrip(b'\0').decode('ascii', errors='backslashreplace')
		if internal_title:
			metadata.specific_info['Internal Title'] = internal_title

		try:
			product_code = convert_alphanumeric(header[12:16])
			metadata.product_code = product_code
			add_info_from_tdb(_tdb, metadata, product_code)
			_add_cover(metadata, product_code)
			
		except NotAlphanumericException:
			pass

		try:
			if not metadata.publisher:
				licensee_code = convert_alphanumeric(header[16:18])
				if licensee_code in _nintendo_licensee_codes:
					metadata.publisher = _nintendo_licensee_codes[licensee_code]
		except NotAlphanumericException:
			pass

	is_dsi = False
	unit_code = header[18]
	if unit_code == 0:
		metadata.specific_info['DSi Enhanced?'] = False
	elif unit_code == 2:
		is_dsi = True
		metadata.specific_info['DSi Enhanced?'] = True
	elif unit_code == 3:
		is_dsi = True
		metadata.platform = "DSi"

	if is_dsi:
		region_flags = int.from_bytes(header[0x1b0:0x1b4], 'little')
		if region_flags < 0xffff0000:
			#If they're set any higher than this, it's region free
			#GBATEK says region free is 0xffffffff specifically but Pokemon gen 5 is 0xffffffef so who knows
			#Although either way, it doesn't imply regions is world, it just means it'll work worldwide, so like... ehh... regions is a weird metadata field tbh
			metadata.regions = _parse_dsi_region_flags(region_flags)
		add_ratings_info(metadata, DSi3DSAgeRatings(header[0x2f0:0x300]))
	else:
		region = header[29]
		if region == 0x40:
			metadata.regions = {regions_by_name['Korea']}
		elif region == 0x80:
			metadata.regions = {regions_by_name['China']}
			metadata.specific_info['Is iQue?'] = True
		#If 0, could be anywhere else
	metadata.specific_info['Revision'] = header[30]

	banner_offset = int.from_bytes(header[0x68:0x6C], 'little')
	if banner_offset:
		_parse_banner(rom, metadata, header, is_dsi, banner_offset)

def _add_ds_input_info(metadata: 'GameInfo') -> None:
	builtin_buttons = input_info.NormalController()
	builtin_buttons.dpads = 1
	builtin_buttons.face_buttons = 4 #I forgot why we're not counting Start and Select but I guess that's a thing
	builtin_buttons.shoulder_buttons = 2
	builtin_gamepad = input_info.CombinedController([builtin_buttons, input_info.Touchscreen()])

	bluetooth_keyboard = input_info.Keyboard()
	bluetooth_keyboard.keys = 64 #If I counted correctly from the image...

	if metadata.product_code:
		if metadata.product_code.startswith('UZP'):
			#For now, we'll detect stuff by product code... this is Learn with Pokemon Typing Adventure, and it's different because the Bluetooth adapter is in the cartridge itself
			metadata.specific_info['Uses Keyboard?'] = True
			#Keyboard is technically optional, as I understand it, so I guess it's a separate option
			metadata.input_info.add_option(bluetooth_keyboard)

	if metadata.platform == 'DSi':
		#Since the DSi has no GBA slot, there's nothing to put funny expansion devices into.
		#Hmmm... would I be able to make that assumption with DSi-enhanced games?
		metadata.input_info.add_option(builtin_gamepad)
		return

	#Rumble is detected from GameTDB

	#Certain games use other input_info that I haven't automagically detected:
	#Slide Adventure MAGKID: Slidey thing (effectively a mouse)
	#Easy Piano: Play & Compose: Piano (dunno much about it)
	#Guitar Hero: On Tour series: Guitar grip (4 buttons)
	#Arkanoid DS: Paddle (also usable by some other Taito games) (might be just optional?)
	#Tony Hawk's Motion: Gyroscope
	#Various homebrew: DS Motion Pack

	#But for now let's just do the standard controls, and hence cause code duplication
	metadata.input_info.add_option(builtin_gamepad)

def add_ds_custom_info(game: 'ROMGame') -> None:
	rom = cast(FileROM, game.rom)
	header = rom.read(amount=0x300)
	_add_info_from_ds_header(rom, game.info, header)
	_add_ds_input_info(game.info)
