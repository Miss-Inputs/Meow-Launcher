try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import os
import struct
from xml.etree import ElementTree

import input_metadata
from common import NotAlphanumericException, convert_alphanumeric
from config.main_config import main_config
from config.system_config import system_configs
from data.nintendo_licensee_codes import nintendo_licensee_codes
from info.region_info import get_region_by_name

from .gametdb import TDB, add_info_from_tdb
from .wii import parse_ratings

#TODO: Detect PassMe carts, and reject the rest of the header if so (well, product code and publisher)
#For DSiWare, we can get public.sav and private.sav filesize, and that tells us if SaveType = Internal or Nothing. But we won't worry about DSiWare for now due to lack of accessible emulation at the moment.

def load_tdb():
	if 'DS' not in system_configs:
		return None

	tdb_path = system_configs['DS'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError) as blorp:
		if main_config.debug:
			print('Oh no failed to load DS TDB because', blorp)
		return None
tdb = load_tdb()

def add_cover(metadata, product_code):
	#Intended for the covers database from GameTDB
	covers_path = system_configs['DS'].options.get('covers_path')
	if not covers_path:
		return
	cover_path = os.path.join(covers_path, product_code)
	for ext in ('png', 'jpg'):
		if os.path.isfile(cover_path + os.extsep + ext):
			metadata.images['Cover'] = cover_path + os.extsep + ext
			break

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

def add_banner_title_metadata(metadata, banner_title, language=None):
	lines = banner_title.splitlines()
	metadata_name = 'Banner-Title'
	if language:
		metadata_name = '{0}-{1}'.format(language, metadata_name)
	if lines:
		#The lines are generally either 2 lines like this
		#Art Academy
		#Nintendo
		#or 3 lines like this:
		#Cooking Guide
		#Can't decide what to eat?
		#Nintendo
		if len(lines) == 1:
			metadata.specific_info[metadata_name] = lines[0]
		else:
			metadata.specific_info[metadata_name] = ' '.join(lines[:-1])
			#This is usually the publisher… but it has a decent chance of being something else so I'm not gonna set metadata.publisher from it
			metadata.specific_info[metadata_name + '-Final-Line'] = lines[-1]

def parse_ds_header(rom, metadata, header):
	internal_title = header[0:12].decode('ascii', errors='backslashreplace').rstrip('\0')
	if internal_title:
		metadata.specific_info['Internal-Title'] = internal_title

	try:
		product_code = convert_alphanumeric(header[12:16])
		metadata.product_code = product_code
		add_info_from_tdb(tdb, metadata, product_code)
		add_cover(metadata, product_code)
		
	except NotAlphanumericException:
		pass

	try:
		if not metadata.publisher:
			licensee_code = convert_alphanumeric(header[16:18])
			if licensee_code in nintendo_licensee_codes:
				metadata.publisher = nintendo_licensee_codes[licensee_code]
	except NotAlphanumericException:
		pass

	is_dsi = False
	unit_code = header[18]
	if unit_code == 0:
		metadata.specific_info['DSi-Enhanced'] = False
	elif unit_code == 2:
		is_dsi = True
		metadata.specific_info['DSi-Enhanced'] = True
	elif unit_code == 3:
		is_dsi = True
		metadata.platform = "DSi"

	if is_dsi:
		region_flags = int.from_bytes(header[0x1b0:0x1b4], 'little')
		if region_flags < 0xffff0000:
			#If they're set any higher than this, it's region free
			#GBATEK says region free is 0xffffffff specifically but Pokemon gen 5 is 0xffffffef so who knows
			#Although either way, it doesn't imply regions is world, it just means it'll work worldwide, so like... ehh... regions is a weird metadata field tbh
			metadata.regions = parse_dsi_region_flags(region_flags)
		parse_ratings(metadata, header[0x2f0:0x300], True, False)
	else:
		region = header[29]
		if region == 0x40:
			metadata.regions = [get_region_by_name('Korea')]
		elif region == 0x80:
			metadata.regions = [get_region_by_name('China')]
			metadata.specific_info['Is-iQue'] = True
		#If 0, could be anywhere else
	metadata.specific_info['Revision'] = header[30]

	banner_offset = int.from_bytes(header[0x68:0x6C], 'little')
	if banner_offset:
		#The extended part of the banner if is_dsi contains animated icon frames, so we don't really need it
		banner_size = int.from_bytes(header[0x208:0x20c], 'little') if is_dsi else 0xA00
		banner = rom.read(seek_to=banner_offset, amount=banner_size)
		version = int.from_bytes(banner[0:2], 'little')
		metadata.specific_info['Banner-Version'] = version
		#2 = has Chinese, 3 = has Korean, 0x103, has DSi stuff

		if version in (1, 2, 3, 0x103):
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
					banner_title = banner[0x240 + (i * 256): 0x240 + (i * 256) + 256].decode('utf-16le').rstrip('\0 \uffff')
					#if banner_title and not all([c == '\uffff' for c in banner_title]):
					if banner_title:
						banner_titles[banner_languages[i]] = banner_title
				except (UnicodeDecodeError, IndexError):
					continue
			
			for lang, title in banner_titles.items():
				add_banner_title_metadata(metadata, title, lang)

			if banner_titles:
				banner_title = banner_titles.get('English', list(banner_titles.values())[0])
				add_banner_title_metadata(metadata, banner_title)

			if len(banner) >= 0x240:
				if have_pillow:
					icon_bitmap = banner[0x20:0x220]
					icon_palette = struct.unpack('H' * 16, banner[0x220:0x240])
					metadata.images['Icon'] = decode_icon(icon_bitmap, icon_palette)

def add_ds_input_info(metadata):
	builtin_buttons = input_metadata.NormalController()
	builtin_buttons.dpads = 1
	builtin_buttons.face_buttons = 4 #I forgot why we're not counting Start and Select but I guess that's a thing
	builtin_buttons.shoulder_buttons = 2
	builtin_gamepad = input_metadata.CombinedController([builtin_buttons, input_metadata.Touchscreen()])

	bluetooth_keyboard = input_metadata.Keyboard()
	bluetooth_keyboard.keys = 64 #If I counted correctly from the image...

	if metadata.product_code:
		if metadata.product_code.startswith('UZP'):
			#For now, we'll detect stuff by product code... this is Learn with Pokemon Typing Adventure, and it's different because the Bluetooth adapter is in the cartridge itself
			metadata.specific_info['Uses-Keyboard'] = True
			#Keyboard is technically optional, as I understand it, so I guess it's a separate option
			metadata.input_info.add_option(bluetooth_keyboard)

	if metadata.platform == 'DSi':
		#Since the DSi has no GBA slot, there's nothing to put funny expansion devices into.
		#Hmmm... would I be able to make that assumption with DSi-enhanced games?
		metadata.input_info.add_option(builtin_gamepad)
		return

	#Certain games use other input_info that I haven't automagically detected:
	#Slide Adventure MAGKID: Slidey thing (effectively a mouse)
	#Easy Piano: Play & Compose: Piano (dunno much about it)
	#Guitar Hero: On Tour series: Guitar grip (4 buttons)
	#Arkanoid DS: Paddle (also usable by some other Taito games) (might be just optional?)
	#Tony Hawk's Motion: Gyroscope
	#Various homebrew: DS Motion Pack

	#But for now let's just do the standard controls, and hence cause code duplication
	metadata.input_info.add_option(builtin_gamepad)


def add_ds_metadata(game):
	header = game.rom.read(amount=0x300)
	parse_ds_header(game.rom, game.metadata, header)
	add_ds_input_info(game.metadata)
