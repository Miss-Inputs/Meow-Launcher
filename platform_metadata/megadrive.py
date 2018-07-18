from common import convert_alphanumeric, NotAlphanumericException
from metadata import SaveType
from info.region_info import TVSystem

def add_megadrive_metadata(game):
	header = game.rom.read(0x100, 0x100)
	#TODO: Parse copyright at header[16:32] to get author (from giant lookup table) and year if possible
	peripherals = [c for c in header[144:160].decode('ascii', errors='ignore') if c != '\x00' and c != ' ']
	#TODO Definitely needs a hecking rewrite to have multiple input methods
	if 'M' in peripherals:
		game.metadata.input_method = 'Mouse'
	elif 'V' in peripherals:
		game.metadata.input_method = 'Paddle'
	elif 'A' in peripherals:
		game.metadata.input_method = 'Stick'
	elif 'G' in peripherals:
		game.metadata.input_method = 'Light Gun'
	elif 'K' in peripherals:
		game.metadata.input_method = 'Keyboard'
	else:
		if 'J' in peripherals:
			game.metadata.input_method = 'Normal'
		elif '6' in peripherals:
			game.metadata_input_method = 'Normal'
			game.metadata.specific_info['Uses-6-Button-Controller'] = True
	#Other peripheral characters of interest:
	#0 = SMS gamepad
	#4 = Team Play
	#B = "Control Ball" (trackball?)
	#C = CD-ROM
	#F = Floppy drive
	#L = Activator
	#O = J-Cart
	#P = Printer
	#R = Serial
	#T = Tablet

	save_id = header[0xb0:0xb4]
	#Apparently... what the heck
	game.metadata.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing
	

	#Hmm... get regions from [0xfd:0xff] or nah
