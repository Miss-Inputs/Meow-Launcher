try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import struct

import input_metadata
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

	game.metadata.tv_type = TVSystem.Agnostic

def convert_ds_colour_to_rgba(colour, is_transparent):
	red = (colour & 0b_00000_00000_11111) << 3
	green = (colour & 0b_00000_11111_00000) >> 2
	blue = (colour & 0b_11111_00000_00000) >> 7

	return (red, green, blue, 0 if is_transparent else 0xff)

def decode_icon(bitmap, palette):
	icon = Image.new('RGBA', (32, 32))

	rgb_palette = [None] * 16
	for i, colour in enumerate(palette):
		rgb_palette[i] = convert_ds_colour_to_rgba(colour, i == 0)

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

def parse_dsi_region_flags(region_flags):
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
	return regions

def parse_ds_header(game, header):
	try:
		product_code = convert_alphanumeric(header[12:16])
		game.metadata.product_code = product_code
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
			#Although either way, it doesn't imply regions is world, it just means it'll work worldwide, so like... ehh... regions is a weird metadata field tbh
			game.metadata.regions = parse_dsi_region_flags(region_flags)
	else:
		region = header[29]
		if region == 0x40:
			game.metadata.regions = [get_region_by_name('Korea')]
		elif region == 0x80:
			game.metadata.regions = [get_region_by_name('China')]
			game.metadata.specific_info['Is-iQue'] = True
		#If 0, could be anywhere else
	game.metadata.revision = header[30]

	banner_offset = int.from_bytes(header[0x68:0x6C], 'little')
	if banner_offset:
		#The extended part of the banner if is_dsi contains animated icon frames, so we don't really need it
		banner = game.rom.read(seek_to=banner_offset, amount=header[0x208] if is_dsi else 0xA00)
		version = int.from_bytes(banner[0:2], 'little')
		game.metadata.specific_info['Banner-Version'] = version
		if version in (1, 2, 3, 0x103) and len(banner) >= 0x240:
			#game.metadata.specific_info['Banner-Text-English'] = banner[0x340:0x440].decode('utf-16-le', errors='backslashreplace').rstrip('\0')
			if have_pillow:
				icon_bitmap = banner[0x20:0x220]
				icon_palette = struct.unpack('H' * 16, banner[0x220:0x240])
				game.icon = decode_icon(icon_bitmap, icon_palette)

def add_ds_input_info(game):
	builtin_buttons = input_metadata.NormalController()
	builtin_buttons.dpads = 1
	builtin_buttons.face_buttons = 4 #I forgot why we're not counting Start and Select but I guess that's a thing
	builtin_buttons.shoulder_buttons = 2
	builtin_gamepad = input_metadata.CombinedController([builtin_buttons, input_metadata.Touchscreen()])

	bluetooth_keyboard = input_metadata.Keyboard()
	bluetooth_keyboard.keys = 64 #If I counted correctly from the image...

	if game.metadata.product_code:
		if game.metadata.product_code.startswith('UZP'):
			#For now, we'll detect stuff by product code... this is Learn with Pokemon Typing Adventure, and it's different because the Bluetooth adapter is in the cartridge itself
			game.metadata.specific_info['Uses-Keyboard'] = True
			#Keyboard is technically optional, as I understand it, so I guess it's a separate option
			game.metadata.input_info.add_option(bluetooth_keyboard)

	if game.metadata.platform == 'DSi':
		#Since the DSi has no GBA slot, there's nothing to put funny expansion devices into.
		#Hmmm... would I be able to make that assumption with DSi-enhanced games?
		game.metadata.input_info.add_option(builtin_gamepad)
		return

	#Certain games use other input_info that I haven't automagically detected:
	#Slide Adventure MAGKID: Slidey thing (effectively a mouse)
	#Easy Piano: Play & Compose: Piano (dunno much about it)
	#Guitar Hero: On Tour series: Guitar grip (4 buttons)
	#Arkanoid DS: Paddle (also usable by some other Taito games) (might be just optional?)
	#Tony Hawk's Motion: Gyroscope
	#Various homebrew: DS Motion Pack

	#But for now let's just do the standard controls, and hence cause code duplication
	game.metadata.input_info.add_option(builtin_gamepad)


def add_ds_metadata(game):
	add_ds_system_info(game)

	header = game.rom.read(amount=0x209)
	parse_ds_header(game, header)
	add_ds_input_info(game)
