import input_metadata
from info.region_info import TVSystem

from .minor_systems import add_generic_info

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

# typedef struct
# {
#     uint8_t  size;
#     uint8_t  entryBank;
#     uint16_t entryAddress;
#     uint8_t  unk;
#     char     system[9];
#     uint8_t  iconBank;
#     uint8_t  iconX;
#     uint8_t  iconY;
#     char     title[9];
#     uint8_t  gameId[2];
#     uint8_t  securityCode;
#     uint8_t  pad[3];
# } romHeader;

def parse_icon(game, icon_bank, icon_offset_x, icon_offset_y):
	bank_size = (256 * 256) // 4
	bank_address = bank_size * icon_bank
	if bank_address > game.rom.get_size():
		#ROM is funny in some way, either underdumped or header is being annoying
		#if main_config.debug:
		#	print(game.rom.path, 'Icon address', icon_address, 'goes beyond', game.rom.get_size())
		return
	bank_data = game.rom.read(seek_to=bank_address, amount=bank_size)

	#Hm, these are meant to be 4-color (2bpp) images so maybe I could use P mode, or would that just cause more problems than it would solve
	white = (255, 255, 255)
	light = (192, 192, 192)
	dark = (96, 96, 96)
	black = (0, 0, 0, 0)
	palette = (white, light, dark, black)

	whole_bank = Image.new('RGB', (256, 256))
	for i in range(bank_size):
		four_pixel_group = bank_data[i]
		#Do 4 pixels at a time because it's 2bpp
		colours = (
			palette[(four_pixel_group & 0b11000000) >> 6],
			palette[(four_pixel_group & 0b00110000) >> 4],
			palette[(four_pixel_group & 0b00001100) >> 2],
			palette[four_pixel_group & 0b00000011],
		)
		for j in range(4):
			pixel = (i * 4) + j
			x = pixel // 256
			y = (pixel % 256)
			whole_bank.putpixel((x, y), colours[j])

	icon = whole_bank.crop((icon_offset_x, icon_offset_y, icon_offset_x + 64, icon_offset_y + 64))
	game.metadata.images['Icon'] = icon

def parse_rom_header(game, header):
	#Shoutouts to https://github.com/Tpot-SSL/GameComHDK and https://github.com/simontime/gcfix/blob/master/gcfix.c and https://github.com/GerbilSoft/rom-properties/blob/master/src/libromdata/Handheld/gcom_structs.h because there is no other documentation that I know of
	game.metadata.specific_info['Internal-Title'] = header[17:26].decode('ascii', errors='ignore').rstrip()
	#26:28: Game ID, but does that have any relation to product code?

	if have_pillow:
		icon_bank = header[14]
		icon_offset_x = header[15]
		icon_offset_y = header[16]
		
		parse_icon(game, icon_bank, icon_offset_x, icon_offset_y)

def add_game_com_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #A B C D
	game.metadata.input_info.add_option(builtin_gamepad)

	rom_header = game.rom.read(amount=31)
	if rom_header[5:14] != b'TigerDMGC':
		rom_header = game.rom.read(amount=31, seek_to=0x40000)
	if rom_header[5:14] == b'TigerDMGC':
		#If it still isn't there, never mind
		parse_rom_header(game, rom_header)

	#Might have saving, actually. I'm just not sure about how it works.
	add_generic_info(game)
