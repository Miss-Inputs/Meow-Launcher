from datetime import datetime
from enum import Enum

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import cd_read
from metadata import CPUInfo, ScreenInfo, Screen
from common import convert_alphanumeric, NotAlphanumericException
from config import main_config
from data.nintendo_licensee_codes import nintendo_licensee_codes

class NintendoDiscRegion(Enum):
	#Also seems to be used for Wii discs and WiiWare
	NTSC_J = 0
	NTSC_U = 1
	PAL = 2
	RegionFree = 3 #Seemingly Wii only
	NTSC_K = 4 #Seemingly Wii only

def convert3BitColor(c):
	n = c * (256 // 0b111)
	return 255 if n > 255 else n

def convert4BitColor(c):
	n = c * (256 // 0b1111)
	return 255 if n > 255 else n

def convert5BitColor(c):
	n = c * (256 // 0b11111)
	return 255 if n > 255 else n

def convert_rgb5a3(colour):
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

def add_banner_info(game, banner):
	banner_magic = banner[:4]
	if banner_magic in (b'BNR1', b'BNR2'):
		#There are text strings in here if we feel like using them
		#Offsets:
		#	Short title line 1 = 0x1820:0x1840
		#	Short title line 2 = 0x1840:0x1860
		#	Title line 1 = 0x1860:0x18a0
		#	Title line 2 = 0x18a0:0x18e0
		#	Description = 0x18e0:0x1960
		#(BNR2 has 6 instances of these 320 bytes with English, German, French, Spanish, Italian, Dutch in that order)
		#Null padded, Shift-JIS on NTSC-J discs, Latin-1 (seemingly) on NTSC-U and PAL discs
		#Dolphin uses line 2 as Publisher field but that's not always accurate (e.g. Paper Mario: The Thousand Year Door puts subtitle of the game's name on line 2) so it won't be used here
		#print('\n'.join(banner[0x1820:0x1960].decode('ascii', errors='ignore').split('\0')))
		if have_pillow:
			banner_width = 96
			banner_height = 32

			banner_image = Image.new('RGBA', (banner_width, banner_height))

			offset = 32 #Part of the banner where image data starts
			#Divvied into 4x4 tiles (8 tiles high, 24 tiles wide)

			tile_height = banner_height // 4
			tile_width = banner_width // 4
			for y in range(tile_height):
				for x in range(tile_width):

					for tile_y in range(4):
						for tile_x in range(4):
							colour = int.from_bytes(banner[offset: offset + 2], 'big')

							converted_colour = convert_rgb5a3(colour)

							image_x = (x * 4) + tile_x
							image_y = (y * 4) + tile_y
							banner_image.putpixel((image_x, image_y), converted_colour)
							offset += 2

			game.metadata.images['Banner'] = banner_image
	else:
		if main_config.debug:
			print('Invalid banner magic', game.rom.path, banner_magic)


def add_fst_info(game, fst_offset, fst_size, is_gcz):
	if fst_offset and fst_size and fst_size < (128 * 1024 * 1024):
		fst = cd_read.read_gcz(game.rom.path, amount=fst_size, seek_to=fst_offset) if is_gcz else game.rom.read(amount=fst_size, seek_to=fst_offset)
		number_of_fst_entries = int.from_bytes(fst[8:12], 'big')
		if fst_size < (number_of_fst_entries * 12):
			if main_config.debug:
				print('Invalid FST in', game.rom.path, ':', fst_size, '<', number_of_fst_entries * 12)
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
				file_offset = int.from_bytes(entry[4:8], 'big')
				file_length = int.from_bytes(entry[8:12], 'big')
				banner = cd_read.read_gcz(game.rom.path, amount=file_length, seek_to=file_offset) if is_gcz else game.rom.read(amount=file_length, seek_to=file_offset)
				add_banner_info(game, banner)

def add_gamecube_specific_metadata(game, header, is_gcz):
	game.metadata.platform = 'GameCube'
	try:
		apploader_date = header[0x2440:0x2450].decode('ascii').rstrip('\x00')
		try:
			actual_date = datetime.strptime(apploader_date, '%Y/%m/%d')
			game.metadata.year = actual_date.year
			game.metadata.month = actual_date.strftime('%B')
			game.metadata.day = actual_date.day
		except ValueError:
			pass
	except UnicodeDecodeError:
		pass

	region_code = int.from_bytes(header[0x458:0x45c], 'big')
	try:
		game.metadata.specific_info['Region-Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass

	fst_offset = int.from_bytes(header[0x424:0x428], 'big')
	fst_size = int.from_bytes(header[0x428:0x42c], 'big')

	try:
		add_fst_info(game, fst_offset, fst_size, is_gcz)
	except (IndexError, ValueError) as ex:
		if main_config.debug:
			print(game.rom.path, 'encountered error when parsing FST', ex)

def add_wii_specific_metadata(game, header, is_gcz):
	#This should go in wii.py but then that would be a recursive import, so I guess I didn't think this through
	game.metadata.platform = 'Wii'
	wii_header = cd_read.read_gcz(game.rom.path, 0x40_000, 0xf000) if is_gcz else game.rom.read(seek_to=0x40_000, amount=0xf000)
	#There is also partition info in here
	#Unused (presumably would be region-related stuff): 0xe004:0xe010
	#Parental control ratings: 0xe010:0xe020
	region_code = int.from_bytes(wii_header[0xe000:0xe004], 'big')
	try:
		game.metadata.specific_info['Region-Code'] = NintendoDiscRegion(region_code)
	except ValueError:
		pass

def add_gamecube_wii_disc_metadata(game, header, is_gcz):
	internal_title = header[32:64] #Potentially quite a lot bigger but we don't need that much out of it
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
		if licensee_code in nintendo_licensee_codes:
			publisher = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	if not (product_code == 'RELS' and licensee_code == 'AB'):
		#This is found on a few prototype discs, it's not valid
		game.metadata.product_code = product_code
		game.metadata.publisher = publisher

	disc_number = header[6] + 1
	if disc_number:
		game.metadata.specific_info['Disc-Number'] = disc_number

	game.metadata.revision = header[7]
	is_wii = header[0x18:0x1c] == b']\x1c\x9e\xa3'
	is_gamecube = header[0x1c:0x20] == b'\xc23\x9f='
	#Is this ever set to both? In theory no, but... hmm

	if is_gamecube:
		add_gamecube_specific_metadata(game, header, is_gcz)
	elif is_wii:
		add_wii_specific_metadata(game, header, is_gcz)
	else:
		game.metadata.specific_info['No-Disc-Magic'] = True

def add_gamecube_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'IBM PowerPC 603'
	cpu_info.clock_speed = 485 * 1000 * 1000
	game.metadata.cpu_info = cpu_info

	screen = Screen()
	screen.width = 640
	screen.height = 480
	screen.type = 'raster'
	screen.tag = 'screen'
	screen.refresh_rate = 60

	screen_info = ScreenInfo()
	screen_info.screens = [screen]
	game.metadata.screen_info = screen_info

def add_gamecube_metadata(game):
	add_gamecube_system_info(game)

	#TODO: TGC, dol

	if game.rom.extension in ('gcz', 'iso', 'gcm'):
		if game.rom.extension == 'gcz':
			header = cd_read.read_gcz(game.rom.path, amount=0x2450)
			is_gcz = True
		elif game.rom.extension in ('iso', 'gcm'):
			header = game.rom.read(amount=0x2450)
			is_gcz = False
		add_gamecube_wii_disc_metadata(game, header, is_gcz)
