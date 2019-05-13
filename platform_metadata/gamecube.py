from datetime import datetime

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from config import main_config
from metadata import CPU, Screen, ScreenInfo

from .gamecube_wii_common import NintendoDiscRegion, gamecube_read, add_gamecube_wii_disc_metadata

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
		#(BNR2 has 6 instances of all of these with English, German, French, Spanish, Italian, Dutch in that order)
		#Dolphin uses line 2 as Publisher field but that's not always accurate (e.g. Paper Mario: The Thousand Year Door puts subtitle of the game's name on line 2) so it won't be used here
		#Very often, short title and not-short title are exactly the same, but not always. I guess it just be like that
		encoding = 'shift_jis' if game.metadata.specific_info['Region-Code'] == NintendoDiscRegion.NTSC_J else 'latin-1'
		short_title_line_1 = banner[0x1820:0x1840].decode(encoding, errors='backslashreplace').rstrip('\0')
		short_title_line_2 = banner[0x1840:0x1860].decode(encoding, errors='backslashreplace').rstrip('\0')
		title_line_1 = banner[0x1860:0x18a0].decode(encoding, errors='backslashreplace').rstrip('\0')
		title_line_2 = banner[0x18a0:0x18e0].decode(encoding, errors='backslashreplace').rstrip('\0')
		description = banner[0x18e0:0x1960].decode(encoding, errors='backslashreplace').rstrip('\0').replace('\n', ' ')
		
		game.metadata.specific_info['Banner-Short-Title'] = short_title_line_1
		game.metadata.specific_info['Banner-Short-Title-Line-2'] = short_title_line_2
		game.metadata.specific_info['Banner-Title'] = title_line_1
		game.metadata.specific_info['Banner-Title-Line-2'] = title_line_2
		game.metadata.specific_info['Banner-Description'] = description

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


def add_fst_info(game, fst_offset, fst_size):
	if fst_offset and fst_size and fst_size < (128 * 1024 * 1024):
		fst = gamecube_read(game, fst_offset, fst_size)
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
				banner = gamecube_read(game, file_offset, file_length)
				add_banner_info(game, banner)

def add_gamecube_disc_metadata(game, header):
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
		add_fst_info(game, fst_offset, fst_size)
	except (IndexError, ValueError) as ex:
		if main_config.debug:
			print(game.rom.path, 'encountered error when parsing FST', ex)

def add_gamecube_system_info(game):
	cpu = CPU()
	cpu.chip_name = 'IBM PowerPC 603'
	cpu.clock_speed = 485 * 1000 * 1000
	game.metadata.cpu_info.add_cpu(cpu)

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
		header = gamecube_read(game, 0, 0x2450)
		add_gamecube_wii_disc_metadata(game, header)
		add_gamecube_disc_metadata(game, header)
