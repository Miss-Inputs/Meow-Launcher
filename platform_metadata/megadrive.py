import sys
import re

from common import convert_alphanumeric, NotAlphanumericException
from metadata import SaveType, PlayerInput, InputType
from platform_metadata.sega_common import licensee_codes

debug = '--debug' in sys.argv

copyright_regex = re.compile(r'\(C\)(\S{4}.)(\d{4})\.(.{3})')
t_with_zero = re.compile('^T-0')
t_not_followed_by_dash = re.compile('^T(?!-)')
acceptable_peripherals = set('046ABCDFGJKLMPRTV')
def add_megadrive_metadata(game):
	header = game.rom.read(0x100, 0x100)
	try:
		console_name = header[:16].decode('ascii')
	except UnicodeDecodeError:
		return

	if not console_name.startswith('SEGA') and not console_name.startswith(' SEGA'):
		return

	#TODO: Get product code and version from serial too
	try:
		copyright_match = copyright_regex.match(header[16:32].decode('ascii'))
		if copyright_match:
			maker = copyright_match[1].strip().rstrip(',')
			maker = t_with_zero.sub('T-', maker)
			maker = t_not_followed_by_dash.sub('T-', maker)
			if maker in licensee_codes:
				game.metadata.publisher = licensee_codes[maker]
			game.metadata.year = copyright_match[2]
			#Month = group 3
	except UnicodeDecodeError:
		pass
	
	game.metadata.input_info.console_buttons = 1 #Reset button counts as a button because games can use it apparently
	player = PlayerInput()
	player.buttons = 3
	peripherals = [c for c in header[144:160].decode('ascii', errors='ignore') if c != '\x00' and c != ' ']
	num_players = 2 #Assumed, becuase we can't really tell if it's 1 or 2 players
	#TODO: Whoops I can't have a single amount of buttons for all inputs I need to rethink everything including what I'm doing with my life
	if set(peripherals) <= acceptable_peripherals:
		if 'M' in peripherals:
			player.inputs.append(InputType.Mouse)
		elif 'V' in peripherals:
			player.inputs.append(InputType.Paddle)
		elif 'A' in peripherals:
			player.inputs.append(InputType.Analog)
		elif 'G' in peripherals:
			player.inputs.append(InputType.LightGun)
		elif 'K' in peripherals:
			player.inputs.append(InputType.Keyboard)
		elif 'J' in peripherals:
			player.inputs.append(InputType.Digital)
		elif '6' in peripherals:
			player.buttons = 6
			player.inputs.append(InputType.Digital)
			game.metadata.specific_info['Uses-6-Button-Controller'] = True
		elif '0' in peripherals:
			#SMS gamepad
			player.buttons = 2
			player.inputs.append(InputType.Digital)
		elif 'L' in peripherals:
			#Activator
			player.inputs.append(InputType.MotionControls)	
		elif '4' in peripherals or 'O' in peripherals:
			#Team Play and J-Cart respectively
			num_players = 4
		elif 'C' in peripherals:
			game.metadata.specific_info['Uses-CD'] = True
	else:
		if debug:
			print(game.rom.path, 'has weird peripheral chars:', set(peripherals) - acceptable_peripherals)
	if debug:
		#Other peripheral characters of interest that I dunno what to do with
		#A lot of homebrew has D in there. There's some Megadrive documentation that says "Just put JD in here and don't ask questions". It doesn't say what the D is. What does the D do? Why the D?
		if 'B' in peripherals:
			print(game.rom.path, 'has B (control ball)')
		if 'F' in peripherals:
			print(game.rom.path, 'has F (floppy drive)')
		if 'P' in peripherals:
			print(game.rom.path, 'has P (printer)')
		if 'R' in peripherals:
			#Something to do with SegaNet/Meganet perhaps?
			print(game.rom.path, 'has R (serial)')
		if 'T' in peripherals:
			#Doesn't seem to have anything to do with Pico games
			print(game.rom.path, 'has T (tablet)')
		if 'D' in peripherals:
			print(game.rom.path, 'has the D')

	game.metadata.input_info.players += [player] * num_players

	save_id = header[0xb0:0xb4]
	#Apparently... what the heck
	game.metadata.save_type = SaveType.Cart if save_id[:2] == b'RA' else SaveType.Nothing
	

	#Hmm... get regions from [0xfd:0xff] or nah
