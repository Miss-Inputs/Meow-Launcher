from info.region_info import TVSystem
from software_list_info import get_software_list_entry
import input_metadata

def add_lynx_metadata(game):
	game.metadata.tv_type = TVSystem.Agnostic

	builtin_gamepad = input_metadata.NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.add_option(builtin_gamepad)

	magic = game.rom.read(amount=4)
	is_headered = magic == b'LYNX'
	game.metadata.specific_info['Headered'] = is_headered
	if is_headered:
		header = game.rom.read(amount=64)
		#UBYTE   magic[4];
		#UWORD   page_size_bank0;
		#UWORD   page_size_bank1;
		#UWORD   version; #That'd be the header version by the looks of it, not the revision of the cart
		#UBYTE   cartname[32];
		#UBYTE   manufname[16];
		#UBYTE   rotation;
		#UBYTE   spare[5];
		game.metadata.publisher = header[0x2a:0x3a].decode('ascii').strip('\0')
		rotation = header[0x3b]
		if rotation == 0:
			game.metadata.specific_info['Screen-Rotation'] = 'None'
		elif rotation == 1:
			game.metadata.specific_info['Screen-Rotation'] = 'Left'
		elif rotation == 2:
			game.metadata.specific_info['Screen-Rotation'] = 'Right'

	software = get_software_list_entry(game, skip_header=64 if is_headered else 0)
	if software:
		software.add_generic_info(game)
