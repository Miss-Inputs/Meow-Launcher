try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import os
from enum import Flag

import input_metadata
from common import (NotAlphanumericException, convert_alphanumeric,
                    junk_suffixes)
from common_types import SaveType
from data._3ds_publisher_overrides import consistentified_manufacturers
from data.nintendo_licensee_codes import nintendo_licensee_codes
from info.region_info import TVSystem
from metadata import CPU, Screen, ScreenInfo
from .wii import parse_ratings

class _3DSRegionCode(Flag):
	Japan = 1
	USA = 2
	Europe = 4
	Australia = 8 #Not used, Europe is used in its place
	China = 16
	Korea = 32
	Taiwan = 64
	RegionFree = 0x7fffffff

	def __str__(self):
		return self.name

def add_3ds_system_info(game):
	game.metadata.tv_type = TVSystem.Agnostic

	cpu = CPU()
	cpu.chip_name = 'ARM11'
	cpu.clock_speed = 268 * 1000 * 1000 #New 3DS is 804 MHz
	game.metadata.cpu_info.add_cpu(cpu)

	top_screen = Screen()
	top_screen.width = 400
	top_screen.height = 200
	top_screen.type = 'lcd'
	top_screen.tag = 'top'
	top_screen.refresh_rate = 59.834

	bottom_screen = Screen()
	bottom_screen.width = 320
	bottom_screen.height = 200
	bottom_screen.type = 'lcd'
	bottom_screen.tag = 'bottom'
	bottom_screen.refresh_rate = 59.834

	screen_info = ScreenInfo()
	screen_info.screens = [top_screen, bottom_screen]
	game.metadata.screen_info = screen_info

	#Although we can't know for sure if the game uses the touchscreen, it's safe to assume that it probably does
	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.analog_sticks = 1
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2

	controller = input_metadata.CombinedController([builtin_gamepad, input_metadata.Touchscreen()])
	game.metadata.input_info.add_option(controller)

media_unit = 0x200

def parse_ncch(game, offset):
	#Skip over SHA-256 siggy and magic
	header = game.rom.read(seek_to=offset + 0x104, amount=0x100)
	#Content size: 0-4 (media unit)
	#Partition ID: 4-12
	try:
		maker = convert_alphanumeric(header[12:14])
		if maker in nintendo_licensee_codes:
			game.metadata.publisher = nintendo_licensee_codes[maker]
	except NotAlphanumericException:
		pass
	#NCCH version: 14-16 (always 2?)
	game.metadata.specific_info['NCCH-Version'] = int.from_bytes(header[14:16], 'little')
	#Something about a hash: 16-20
	#Program ID: 20-28
	#Reserved: 28-44
	#Logo region hash: 44-76
	try:
		product_code = header[76:86].decode('ascii')
		game.metadata.product_code = product_code
		#As usual, can get country and type from here, but it has more letters and as such you can also get category as well, or like... type 2 electric boogaloo. This also means we can't use convert_alphanumeric because it contains dashes, so I guess I need to fiddle with that method if I want to use it like that
		#(To be precise: P = retail/cart, N = digital only, M = DLC, T = demos, U = patches)
		#Should ignore everything if it's CTR-P-CTAP
	except UnicodeDecodeError:
		pass
	#Extended header hash: 92-124
	#Extended header size: 124-128
	#Reserved: 128-132
	flags = header[132:140]
	is_data = (flags[5] & 1) > 0
	is_executable = (flags[5] & 2) > 0
	is_not_cxi = is_data and not is_executable
	game.metadata.specific_info['Is-CXI'] = not is_not_cxi
	#Is system update = flags[5] & 4
	#Is electronic manual = flags[5] & 8
	#Is trial = flags[5] & 16
	#Is zero key encrypted = flags[7] & 1
	is_decrypted = (flags[7] & 4) > 0
	game.metadata.specific_info['Decrypted'] = is_decrypted

	plain_region_offset = (int.from_bytes(header[140:144], 'little') * media_unit) + offset
	plain_region_length = (int.from_bytes(header[144:148], 'little') * media_unit)
	#logo_region_offset = (int.from_bytes(header[148:152], 'little') * media_unit) + offset
	#logo_region_length = (int.from_bytes(header[152:156], 'little') * media_unit)
	exefs_offset = (int.from_bytes(header[156:160], 'little') * media_unit) + offset
	exefs_length = (int.from_bytes(header[160:164], 'little') * media_unit)
	#romfs_offset = (int.from_bytes(header[172:176], 'little') * media_unit) + offset
	#romfs_length = (int.from_bytes(header[176:180], 'little') * media_unit)

	if plain_region_length:
		parse_plain_region(game, plain_region_offset, plain_region_length)
	#Logo region: Stuff and things
	if exefs_length:
		parse_exefs(game, exefs_offset)
	#RomFS: Filesystem really

	#Don't really need extended header, it's at offset + 0x200 if CXI and decrypted

def parse_plain_region(game, offset, length):
	#Plain region stores the libraries used, at least for official games
	#See also: https://github.com/Zowayix/ROMniscience/wiki/3DS-libraries-used for research
	plain_region = game.rom.read(seek_to=offset, amount=length)
	libraries = [lib.decode('ascii', errors='backslashreplace') for lib in plain_region.split(b'\x00') if lib]

	#TODO: If a game has an update which adds functionality identified by one of these library names, then that'll be a separate file, so it's like... how do we know that Super Smash Bros the .3ds file has amiibo support when Super Smash Bros 1.1.7 update data the .cxi is where it says that, because with and only with the update data it would support amiibos, etc; if that all makes sense
	#Unless like... I search ~/.local/share/citra-emu/sdmc/Nintendo 3DS for what update CIAs are installed and... aaaaaaaaaaaaaaaa
	for library in libraries:
		if library.startswith('[SDK+ISP:QRDec'):
			game.metadata.specific_info['Reads-QR-Codes'] = True
		elif library.startswith('[SDK+ISP:QREnc'):
			game.metadata.specific_info['Makes-QR-Codes'] = True
		elif library == '[SDK+NINTENDO:ExtraPad]':
			game.metadata.specific_info['Uses-Circle-Pad-Pro'] = True
			#ZL + ZR + right analog stick; New 3DS has these too but the extra controls there are internally represented as a Circle Pad Pro for compatibility so this all works out I think
			game.metadata.input_info.input_options[0].inputs[0].components[0].analog_sticks += 1
			game.metadata.input_info.input_options[0].inputs[0].components[0].shoulder_buttons += 2
		elif library.startswith == '[SDK+NINTENDO:Gyroscope]':
			game.metadata.specific_info['Uses-Gyroscope'] = True
			game.metadata.input_info.input_options[0].inputs.append(input_metadata.MotionControls)
		elif library == '[SDK+NINTENDO:IsRunOnSnake]':
			#There's also an IsRunOnSnakeForApplet found in some not-completely-sure-what-they-are builtin apps and amiibo Settings. Not sure if it does what I think it does
			game.metadata.specific_info['New-3DS-Enhanced'] = True
		elif library == '[SDK+NINTENDO:NFP]':
			game.metadata.specific_info['Uses-Amiibo'] = True
		elif library.startswith('[SDK+NINTENDO:CTRFaceLibrary-'):
			game.metadata.specific_info['Uses-Miis'] = True

def parse_exefs(game, offset):
	header = game.rom.read(seek_to=offset, amount=0x200)
	for i in range(0, 10):
		try:
			filename = header[(i * 16): (i * 16) + 8].decode('ascii').rstrip('\x00')
		except UnicodeDecodeError:
			continue
		file_offset = int.from_bytes(header[(i * 16) + 8: (i * 16) + 8 + 4], 'little') + 0x200 + offset
		file_length = int.from_bytes(header[(i * 16) + 12: (i * 16) + 12 + 4], 'little')
		if filename == 'icon':
			parse_smdh(game, file_offset, file_length)
		#Logo contains some stuff, banner contains 3D graphics and sounds for the home menu, .code contains actual executable


def parse_smdh(game, offset=0, length=-1):
	game.metadata.specific_info['Has-SMDH'] = True
	#At this point it's fine to just read in the whole thing
	smdh = game.rom.read(seek_to=offset, amount=length)
	parse_smdh_data(game, smdh)

def parse_smdh_data(game, smdh):
	magic = smdh[:4]
	if magic != b'SMDH':
		return
	#Version = 4-6
	#Reserved = 6-8
	#Titles = 8-0x2008 (512 bytes each (128 short title + 256 long title + 128 publisher ) * 16 languages)
	english_publisher_offset = 8 + (128 + 256 + 128) + 128 + 256 #After Japanese title data, English short title, English long title
	try:
		publisher = smdh[english_publisher_offset: english_publisher_offset + 0x80].decode('utf16').rstrip('\0')
		publisher = junk_suffixes.sub('', publisher)
		if publisher:
			game.metadata.publisher = consistentified_manufacturers.get(publisher, publisher)
	except UnicodeDecodeError:
		pass

	parse_ratings(game, smdh[0x2008:0x2018], True, False)

	region_code_flag = int.from_bytes(smdh[0x2018:0x201c], 'little')
	if region_code_flag in (_3DSRegionCode.RegionFree, 0xffffffff):
		region_codes = [_3DSRegionCode.RegionFree]
	else:
		region_codes = []
		for region in _3DSRegionCode:
			if region == _3DSRegionCode.RegionFree:
				continue
			#I want a list here so this looks weird
			if region.value & region_code_flag:
				region_codes.append(region)
	if region_codes:
		game.metadata.specific_info['Region-Code'] = region_codes
	#Match maker IDs for online play = 0x201c-0x2028
	flags = int.from_bytes(smdh[0x2028:0x202c], 'little')
	#Visible on home menu: flags & 1
	#Autoboot: flags & 2
	#Uses 3D: flags & 4 (but apparently it's more complicated than that and has more to do with parental controls)
	#Requires EULA: flags & 8
	#Autosave on exit: flags & 16
	#Uses extended banner: flags & 32
	#Region rating required: flags & 64
	#Record application usage: flags & 256 (unset on developer/customer service tools to stop them showing up in the activity log)
	#Disable SD card save backup: flags & 1024
	has_save = (flags & 128) > 0
	#Actually just means that a warning is shown when closing, but still
	if game.metadata.save_type == SaveType.Unknown:
		#I guess this'd be SaveType.MemoryCard in some cases, but... meh
		game.metadata.save_type = SaveType.Internal if has_save else SaveType.Nothing
	if flags & 4096:
		game.metadata.platform = 'New 3DS'

	#EULA version: 0x202c-0x202e
	#Reserved 2 = 0x202e-0x2030
	#Optimal animation default frame = 0x2030-0x2034
	cec_id = smdh[0x2034:0x2038]
	game.metadata.specific_info['Uses-StreetPass'] = cec_id != b'\x00\x00\x00\x00'
	#Reserved: 0x2038-0x2040
	#Smol icon (24x24): 0x2040-0x24c0

	#Go with the 48x48 icon
	if have_pillow:
		large_icon = smdh[0x24c0:0x36c0]
		game.icon = decode_icon(large_icon, 48)

tile_order = [
	#What the actual balls?
	0, 1, 8, 9, 2, 3, 10, 11,
	16, 17, 24, 25, 18, 19, 26, 27,
	4, 5, 12, 13, 6, 7, 14, 15,
	20, 21, 28, 29, 22, 23, 30, 31,
	32, 33, 40, 41, 34, 35, 42, 43,
	48, 49, 56, 57, 50, 51, 58, 59,
	36, 37, 44, 45, 38, 39, 46, 47,
	52, 53, 60, 61, 54, 55, 62, 63
]
def decode_icon(icon_data, size):
	#Assumes RGB565, which everything so far uses. Supposedly there can be other encodings, but I'll believe that when I see it
	icon = Image.new('RGB', (size, size))

	i = 0
	for tile_y in range(0, size, 8):
		for tile_x in range(0, size, 8):
			for tile in range(0, 8 * 8):
				x = tile_x + (tile_order[tile] & 0b0000_0111)
				y = tile_y + ((tile_order[tile] & 0b1111_1000) >> 3)

				pixel = icon_data[i] | (icon_data[i + 1] << 8)

				blue = ((pixel >> 0) & 0b0001_1111) << 3
				green = ((pixel >> 5) & 0b0011_1111) << 2
				red = ((pixel >> 11) & 0b0001_1111) << 3

				icon.putpixel((x, y), (red, green, blue))
				i += 2
	return icon

def parse_ncsd(game):
	#Assuming CCI (.3ds) here
	#Skip over SHA-256 signature and magic
	header = game.rom.read(seek_to=0x104, amount=0x100)
	#ROM size: 0-4
	#Media ID: 4-12
	#Partition types: 12-20
	#Partition crypt types: 20-28
	partition_offsets = []
	partition_lengths = []

	for i in range(0, 8):
		partition_offset = int.from_bytes(header[28 + (i * 4):28 + (i * 4) + 4], 'little') * media_unit
		partition_length = int.from_bytes(header[32 + (i * 4):32 + (i * 4) + 4], 'little') * media_unit
		partition_offsets.append(partition_offset)
		partition_lengths.append(partition_length)
	if partition_lengths[0]:
		#Ignore lengths, we're not just gonna read the whole NCCH in one block because that would use a heckton of memory and whatnot
		parse_ncch(game, partition_offsets[0])
	#Partition 1: Electronic manual
	#Partition 2: Download Play child
	#Partition 6: New 3DS update data
	#Partition 7: Update data
	card_info_header = game.rom.read(seek_to=0x200, amount=0x314)
	card2_writeable_address = int.from_bytes(card_info_header[:4], 'little')
	if card2_writeable_address != 0xffffffff:
		game.metadata.save_type = SaveType.Cart
	game.metadata.specific_info['Title-Version'] = int.from_bytes(card_info_header[0x210:0x212], 'little')
	game.metadata.specific_info['Card-Version'] = int.from_bytes(card_info_header[0x212:0x214], 'little')

def parse_3dsx(game):
	header = game.rom.read(amount=0x20)
	header_size = int.from_bytes(header[4:6], 'little')
	has_extended_header = header_size > 32

	look_for_smdh_file = True
	if has_extended_header:
		extended_header = game.rom.read(seek_to=0x20, amount=12)
		smdh_offset = int.from_bytes(extended_header[0:4], 'little')
		smdh_size = int.from_bytes(extended_header[4:8], 'little')

		if smdh_size:
			look_for_smdh_file = False
			parse_smdh(game, smdh_offset, smdh_size)

	if look_for_smdh_file:
		smdh_name = os.path.splitext(game.rom.path)[0] + '.smdh'
		if os.path.isfile(smdh_name):
			with open(smdh_name, 'rb') as smdh_file:
				parse_smdh_data(game, smdh_file.read())

def add_3ds_metadata(game):
	add_3ds_system_info(game)
	magic = game.rom.read(seek_to=0x100, amount=4)
	#Hmm... do we really need this or should we just look at extension?
	if magic == b'NCSD':
		parse_ncsd(game)
	elif magic == b'NCCH':
		parse_ncch(game, 0)
	elif game.rom.extension == '3dsx':
		parse_3dsx(game)
