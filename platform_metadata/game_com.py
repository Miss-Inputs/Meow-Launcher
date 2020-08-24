import input_metadata
from info.region_info import TVSystem

from .minor_systems import add_generic_info

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

def parse_rom_header(game, header):
	game.metadata.specific_info['Internal-Title'] = header[17:26].decode('ascii', errors='ignore').rstrip()
	#26:28: Game ID, but does that have any relation to product code?

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
