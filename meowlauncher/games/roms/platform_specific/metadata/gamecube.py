from datetime import datetime
from typing import Optional, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.games.roms.rom import ROM, FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Date, Metadata

from .common.gamecube_wii_common import (NintendoDiscRegion,
                                         add_gamecube_wii_disc_metadata,
                                         just_read_the_wia_rvz_header_for_now)

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

def convert3BitColor(c: int) -> int:
	n = c * (256 // 0b111)
	return 255 if n > 255 else n

def convert4BitColor(c: int) -> int:
	n = c * (256 // 0b1111)
	return 255 if n > 255 else n

def convert5BitColor(c: int) -> int:
	n = c * (256 // 0b11111)
	return 255 if n > 255 else n

def convert_rgb5a3(colour: int) -> tuple[int, int, int, int]:
	if (colour & 32768) == 0:
		alpha = convert3BitColor((colour & 0b0111_0000_0000_0000) >> 12)
		red = convert4BitColor((colour & 0b0000_1111_0000_0000) >> 8)
		green = convert4BitColor((colour & 0b0000_0000_1111_0000) >> 4)
		blue = convert4BitColor(colour & 0b0000_0000_0000_1111)
	else:
		alpha = 255
		red = convert5BitColor((colour & 0b0_11111_00000_00000) >> 10)
		green = convert5BitColor((colour & 0b0_00000_11111_00000) >> 5)
		blue = convert5BitColor(colour & 0b0_00000_00000_11111)
	return (red, green, blue, alpha)

def parse_gamecube_banner_text(metadata: Metadata, banner_bytes: bytes, encoding: str, lang: Optional[str]=None):
	short_title_line_1 = banner_bytes[0:0x20].decode(encoding, errors='backslashreplace').rstrip('\0 ')
	short_title_line_2 = banner_bytes[0x20:0x40].decode(encoding, errors='backslashreplace').rstrip('\0 ')
	title_line_1 = banner_bytes[0x40:0x80].decode(encoding, errors='backslashreplace').rstrip('\0 ')
	title_line_2 = banner_bytes[0x80:0xc0].decode(encoding, errors='backslashreplace').rstrip('\0 ')
	description = banner_bytes[0xc0:0x140].decode(encoding, errors='backslashreplace').rstrip('\0 ').replace('\n', ' ')

	prefix = 'Banner'
	if lang:
		prefix = '{0}-{1}'.format(lang, prefix)
	metadata.add_alternate_name(short_title_line_1, '{0}-Short-Title'.format(prefix))
	metadata.specific_info['{0}-Short-Title-Line-2'.format(prefix)] = short_title_line_2
	metadata.add_alternate_name(title_line_1, '{0}-Title'.format(prefix))
	metadata.specific_info['{0}-Title-Line-2'.format(prefix)] = title_line_2
	metadata.descriptions['{0}-Description'.format(prefix)] = description

def decode_icon(banner: bytes) -> 'Image':
	width = 96
	height = 32

	image = Image.new('RGBA', (width, height))
	data = [(0, 0, 0, 0)] * width * height

	offset = 32 #Part of the banner where image data starts
	#Divvied into 4x4 tiles (8 tiles high, 24 tiles wide)

	tile_height = height // 4
	tile_width = width // 4
	for y in range(tile_height):
		for x in range(tile_width):

			for tile_y in range(4):
				for tile_x in range(4):
					colour = int.from_bytes(banner[offset: offset + 2], 'big')

					converted_colour = convert_rgb5a3(colour)

					image_x = (x * 4) + tile_x
					image_y = (y * 4) + tile_y
					data[image_y * width + image_x] = converted_colour
					offset += 2
	image.putdata(data)
	return image

def add_banner_info(rom: ROM, metadata: Metadata, banner: bytes):
	banner_magic = banner[:4]
	if banner_magic in {b'BNR1', b'BNR2'}:
		#(BNR2 has 6 instances of all of these with English, German, French, Spanish, Italian, Dutch in that order)
		#Dolphin uses line 2 as Publisher field but that's not always accurate (e.g. Paper Mario: The Thousand Year Door puts subtitle of the game's name on line 2) so it won't be used here
		#Very often, short title and not-short title are exactly the same, but not always. I guess it just be like that
		encoding = 'shift_jis' if metadata.specific_info['Region-Code'] == NintendoDiscRegion.NTSC_J else 'latin-1'
		parse_gamecube_banner_text(metadata, banner[0x1820:0x1960], encoding)

		if banner_magic == b'BNR2':
			languages = {
				#0: English, but we have already done that
				1: 'German',
				2: 'French',
				3: 'Spanish',
				4: 'Italian',
				5: 'Dutch',
			}
			for i, lang_name in languages.items():
				offset = 0x1820 + (i * 0x140)
				parse_gamecube_banner_text(metadata, banner[offset: offset + 0x140], encoding, lang_name)

		if have_pillow:
			metadata.images['Banner'] = decode_icon(banner)
	else:
		if main_config.debug:
			print('Invalid banner magic', rom.path, banner_magic)

def add_fst_info(rom: FileROM, metadata: Metadata, fst_offset: int, fst_size: int, offset: int=0):
	if fst_offset and fst_size and fst_size < (128 * 1024 * 1024):
		fst = rom.read(fst_offset, fst_size)
		number_of_fst_entries = int.from_bytes(fst[8:12], 'big')
		if fst_size < (number_of_fst_entries * 12):
			if main_config.debug:
				print('Invalid FST in', rom.path, ':', fst_size, '<', number_of_fst_entries * 12)
			return
		string_table = fst[number_of_fst_entries * 12:]
		for i in range(1, number_of_fst_entries):
			entry = fst[i * 12: (i * 12) + 12]
			if entry[0] != 0:
				continue
			offset_into_string_table = int.from_bytes(entry[1:4], 'big')
			#Actually it's a null terminated string but we only care about the one file, so cbf finding a null, I'll just check for the expected length
			banner_name = string_table[offset_into_string_table:offset_into_string_table+len('opening.bnr')]
			if banner_name == b'opening.bnr':
				file_offset = int.from_bytes(entry[4:8], 'big') + offset
				file_length = int.from_bytes(entry[8:12], 'big')
				banner = rom.read(file_offset, file_length)
				add_banner_info(rom, metadata, banner)

def add_gamecube_disc_metadata(rom: FileROM, metadata: Metadata, header: bytes, tgc_data: Optional[dict[str, int]]=None):
	metadata.platform = 'GameCube'

	if rom.extension != 'tgc':
		#Not gonna bother working out what's going on with apploader offsets in tgc
		try:
			apploader_date = header[0x2440:0x2450].decode('ascii').rstrip('\0')
			try:
				actual_date = datetime.strptime(apploader_date, '%Y/%m/%d')
				year = actual_date.year
				month = actual_date.month
				day = actual_date.day
				metadata.specific_info['Build-Date'] = Date(year, month, day)
				if not metadata.release_date or metadata.release_date.is_guessed:
					metadata.release_date = Date(year, month, day, True)
			except ValueError:
				pass
		except UnicodeDecodeError:
			pass

	region_code = int.from_bytes(header[0x458:0x45c], 'big')
	try:
		metadata.specific_info['Region-Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass

	if tgc_data:
		fst_offset = tgc_data['fst offset']
		fst_size = tgc_data['fst size']
	else:
		fst_offset = int.from_bytes(header[0x424:0x428], 'big')
		fst_size = int.from_bytes(header[0x428:0x42c], 'big')

	try:
		if tgc_data:
			add_fst_info(rom, metadata, fst_offset, fst_size, tgc_data['file offset'])
		else:
			add_fst_info(rom, metadata, fst_offset, fst_size)
	except (IndexError, ValueError) as ex:
		if main_config.debug:
			print(rom.path, 'encountered error when parsing FST', ex)

def add_tgc_metadata(rom: FileROM, metadata: Metadata):
	tgc_header = rom.read(0, 60) #Actually it is bigger than that
	magic = tgc_header[0:4]
	if magic != b'\xae\x0f8\xa2':
		if main_config.debug:
			print('Hmm', rom.path, 'is .tgc but TGC magic is invalid', magic)
		return
	tgc_header_size = int.from_bytes(tgc_header[8:12], 'big')
	fst_real_offset = int.from_bytes(tgc_header[16:20], 'big')
	fst_real_size = int.from_bytes(tgc_header[20:24], 'big')
	#apploader_real_offset = int.from_bytes(tgc_header[28:32], 'big')
	#apploader_real_size = int.from_bytes(tgc_header[32:36], 'big')
	#These fields are "?" in YAGD, but Dolphin uses them, so they probably know what they're doing and this is probably the right way
	real_offset = int.from_bytes(tgc_header[36:40], 'big')
	virtual_offset = int.from_bytes(tgc_header[52:56], 'big')
	file_offset = real_offset - virtual_offset

	header = rom.read(tgc_header_size, 0x460)

	add_gamecube_disc_metadata(rom, metadata, header, {
		#'apploader offset': apploader_real_offset,
		#'apploader size': apploader_real_size,
		'fst offset': fst_real_offset,
		'fst size': fst_real_size,
		'file offset': file_offset,
	})

def add_gamecube_metadata(game: ROMGame):
	if game.rom.extension in {'gcz', 'iso', 'gcm'}:
		rom = cast(FileROM, game.rom)
		header = rom.read(0, 0x2450)
		add_gamecube_wii_disc_metadata(rom, game.metadata, header)
		add_gamecube_disc_metadata(rom, game.metadata, header)
	elif game.rom.extension == 'tgc':
		add_tgc_metadata(cast(FileROM, game.rom), game.metadata)
	elif game.rom.extension in {'wia', 'rvz'}:
		just_read_the_wia_rvz_header_for_now(cast(FileROM, game.rom), game.metadata)
