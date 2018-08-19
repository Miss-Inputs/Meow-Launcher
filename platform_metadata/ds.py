try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import struct

from info.region_info import TVSystem
from region_detect import get_region_by_name
from metadata import CPUInfo, ScreenInfo, Screen
from common import convert_alphanumeric, NotAlphanumericException
from .nintendo_common import nintendo_licensee_codes

#TODO: Detect PassMe carts, and reject the rest of the header if so (well, product code and publisher)
#For DSiWare, we can get public.sav and private.sav filesize, and that tells us if SaveType = Internal or Nothing. But we won't worry about DSiWare for now due to lack of accessible emulation at the moment.

def add_ds_system_info(game):
	cpu_info = CPUInfo()
	cpu_info.main_cpu = 'ARM946ES'
	cpu_info.clock_speed = 67 * 1000 * 1000
	game.metadata.cpu_info = cpu_info

	top_screen = Screen()
	top_screen.width = 256
	top_screen.height = 192
	top_screen.type = 'lcd'
	top_screen.tag = 'top'
	top_screen.refresh_rate = 59.8261
	
	bottom_screen = Screen()
	bottom_screen.width = 256
	bottom_screen.height = 192
	bottom_screen.type = 'lcd'
	bottom_screen.tag = 'bottom'
	bottom_screen.refresh_rate = 59.8261
	
	screen_info = ScreenInfo()
	screen_info.screens = [top_screen, bottom_screen]
	game.metadata.screen_info = screen_info

def decode_icon(bitmap, palette):
	icon = Image.new('RGBA', (32, 32))
	
	rgb_palette = [None] * 16
	for i, colour in enumerate(palette):
		#Convert from DS colour format to normal RGB
		red = (colour & 0b_00000_00000_11111) << 3
		green = (colour & 0b_00000_11111_00000) >> 2
		blue = (colour & 0b_11111_00000_00000) >> 7

		alpha = 0xff
		if i == 0:
			alpha = 0
		rgb_palette[i] = (red, green, blue, alpha)

	pos = 0
	for tile_y in range(0, 4):
		for tile_x in range(0, 4):
			for y in range(0, 8):
				for x in range(0, 4):
					pixel_x = (x * 2) + (8 * tile_x)
					pixel_y = y + (8 * tile_y)
					icon.putpixel((pixel_x, pixel_y), rgb_palette[bitmap[pos] & 0x0f])
					icon.putpixel((pixel_x + 1, pixel_y), rgb_palette[(bitmap[pos] & 0xf0) >> 4])
					pos += 1
	return icon

def add_ds_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic
	add_ds_system_info(game)

	header = game.rom.read(amount=0x200)
	
	try:
		product_code = convert_alphanumeric(header[12:16])
		game.metadata.specific_info['Product-Code'] = product_code
	except NotAlphanumericException:
		pass

	try:
		licensee_code = convert_alphanumeric(header[16:18])
		if licensee_code in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	is_dsi = False
	unit_code = header[18]
	if unit_code == 0:
		game.metadata.specific_info['DSi-Enhanced'] = False
	elif unit_code == 2:
		is_dsi = True
		game.metadata.specific_info['DSi-Enhanced'] = True
	elif unit_code == 3:
		is_dsi = True
		game.metadata.platform = "DSi"
		#We won't set this upgraded clock speed for DSi-enhanced DS games for now, since nothing emulates them in that mode
		game.metadata.cpu_info.clock_speed = '133 MHz'

	if is_dsi:
		region_flags = int.from_bytes(header[0x1b0:0x1b4], 'little')
		if region_flags < 0xffff0000:
			#If they're set any higher than this, it's region free
			#GBATEK says region free is 0xffffffff specifically but Pokemon gen 5 is 0xffffffef so who knows
			regions = []
			if region_flags & 1:
				regions.append(get_region_by_name('Japan'))
			if region_flags & 2:
				regions.append(get_region_by_name('USA'))
			if region_flags & 4:
				regions.append(get_region_by_name('Europe'))
			if region_flags & 8:
				regions.append(get_region_by_name('Australia'))
			if region_flags & 16:
				regions.append(get_region_by_name('China'))
			if region_flags & 32:
				regions.append(get_region_by_name('Korea'))
			game.metadata.regions = regions
	else:
		region = header[29]
		if region == 0x40:
			game.metadata.regions = [get_region_by_name('Korea')]
		elif region == 0x80:
			game.metadata.regions = [get_region_by_name('China')]
		#If 0, could be anywhere else
	game.metadata.revision = header[30]

	banner_offset = int.from_bytes(header[0x68:0x6C], 'little')
	if banner_offset:
		#TODO: amount = header[0x208] if is_dsi, though the extended part of the banner contains animated icon frames, so we don't really need it
		banner = game.rom.read(seek_to=banner_offset, amount=0xA00)
		version = int.from_bytes(banner[0:2], 'little')
		game.metadata.specific_info['Banner-Version'] = version
		if version in (1, 2, 3, 0x103):
			#game.metadata.specific_info['Banner-Text-English'] = banner[0x340:0x440].decode('utf-16-le', errors='backslashreplace').rstrip('\0')
			if have_pillow:
				icon_bitmap = banner[0x20:0x220]
				icon_palette = struct.unpack('H' * 16, banner[0x220:0x240])
				game.icon = decode_icon(icon_bitmap, icon_palette)
