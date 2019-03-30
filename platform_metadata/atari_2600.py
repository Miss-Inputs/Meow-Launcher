import subprocess
import hashlib
from enum import Enum, auto

import input_metadata
from common_types import SaveType
from info.region_info import TVSystem
from software_list_info import find_in_software_lists, get_crc32_for_software_list

#Not gonna use stella -rominfo on individual stuff as it takes too long and just detects TV type with no other useful info that isn't in the -listrominfo db
def get_stella_database():
	proc = subprocess.run(['stella', '-listrominfo'], stdout=subprocess.PIPE, universal_newlines=True)
	proc.check_returncode()

	lines = proc.stdout.splitlines()
	first_line = lines[0]
	lines = lines[1:]

	columns = {}
	column_names = first_line.split('|')
	for i, column_name in enumerate(column_names):
		columns[i] = column_name

	games = {}
	for line in lines:
		game_columns = line.split('|')
		game = {}

		md5 = None
		for i, game_column in enumerate(game_columns):
			if i in columns:
				if columns[i] == 'Cartridge_MD5':
					md5 = game_column.lower()
				elif game_column:
					game[columns[i]] = game_column

		if md5:
			games[md5] = game

	return games

class Atari2600Controller(Enum):
	Joystick = auto()
	Paddle = auto() #2 players per port
	Mouse = auto() #2 buttons, Stella lists an AMIGAMOUSE and ATARIMOUSE (ST mouse) and I dunno if those are functionally different
	Trackball = auto() #Functionally 1 button, but has 2 physical buttons to be ambidextrous
	KeyboardController = auto() #This is... 2 keypads joined together (12 keys each)
	Compumate = auto() #42-key keyboard (part of a whole entire computer)
	MegadriveGamepad = auto() #See megadrive.py
	Boostergrip = auto() #Effectively a 3-button joystick, passes through to the standard 2600 joystick and adds 2 buttons
	DrivingController = auto() #Has 360 degree movement, so not quite like a paddle. MAME actually calls it a trackball
	Mindlink = auto()
	Other = auto()


def _controller_from_stella_db_name(controller):
	if not controller:
		return None

	if controller in ('JOYSTICK', 'AUTO'):
		return Atari2600Controller.Joystick
	elif controller in ('PADDLES', 'PADDLES_IAXIS', 'PADDLES_IAXDR'):
		#Not sure what the difference in the latter two are
		return Atari2600Controller.Paddle
	elif controller in ('AMIGAMOUSE', 'ATARIMOUSE'):
		return Atari2600Controller.Mouse
	elif controller == 'TRAKBALL':
		return Atari2600Controller.Trackball
	elif controller == 'KEYBOARD':
		return Atari2600Controller.KeyboardController
	elif controller in 'COMPUMATE':
		return Atari2600Controller.Compumate
	elif controller == 'GENESIS':
		#game.metadata.specific_info['Uses-Genesis-Controller'] = True
		return Atari2600Controller.MegadriveGamepad
	elif controller == 'BOOSTERGRIP':
		return Atari2600Controller.Boostergrip
		#game.metadata.specific_info['Uses-Boostergrip'] = True
	elif controller == 'DRIVING':
		return Atari2600Controller.DrivingController
	elif controller == 'MINDLINK':
		return Atari2600Controller.Mindlink
	#Track & Field controller is just a joystick with no up or down, so Stella doesn't count it as separate from joystick
	return Atari2600Controller.Other

def parse_stella_db(game, game_info):
	if 'Cartridge_Manufacturer' in game_info:
		manufacturer = game_info['Cartridge_Manufacturer']
		if ', ' in manufacturer:
			game.metadata.publisher, _, game.metadata.developer = manufacturer.partition(', ')
		else:
			game.metadata.publisher = manufacturer
			#TODO: Clean up manufacturer names (UA Limited > UA)
	if 'Cartridge_ModelNo' in game_info:
		game.metadata.product_code = game_info['Cartridge_ModelNo']
	if 'Cartridge_Note' in game_info:
		note = game_info['Cartridge_Note']
		#Adventures in the Park
		#Featuring Panama Joe
		#Hack of Adventure
		#Journey to Rivendell (The Lord of the Rings I)
		#O Monstro Marinho
		#Pitfall Harry's Jungle Adventure (Jungle Runner)
		#ROM must be started in bank 0
		#Set right difficulty to 'A' for BoosterGrip in both ports
		#Use Color/BW switch to change between galactic chart and front views
		#Uses Joyboard (this isn't specified in the joystick port info, for some reason)
		#Uses Joystick Coupler (Dual Control Module) (not specified by joystick info)
		#Uses the Amiga Joyboard (also need to parse this)
		#Uses the Joyboard controller
		if note.startswith('AKA '):
			pass #Could add an Alternate-Name field but mehhhhhhhhhhh (There is an "AKA Bachelor Party, Uses the paddle controllers" but we will also skip that)
		elif note == 'Console ports are swapped':
			pass #We already know this from Controller_SwapPorts field
		elif note in ('Uses Joystick (left) and Keypad (right) Controllers', 'Uses Keypad Controller', 'Uses Keypad Controllers', 'Uses Mindlink Controller (left only)', 'Uses the MindLink controller', 'Uses right joystick controller', 'Uses the paddle controllers', 'Uses the Paddle Controllers', 'Uses the Paddle Controllers (left only)', 'Uses the Paddle Controllers (swapped)', 'Uses the Driving Controllers', 'Uses the Joystick Controllers (swapped)', 'Uses the Keypad Controllers', 'Uses the Keypad Controllres (left only)', 'Uses the Kid Vid Controller', 'Uses the KidVid Controller', 'Uses the Light Gun Controller (left only)', 'Uses the Track & Field Controller'):
			pass #We already know this as well from the controller fields
			#Although it wouldn't hurt to add that to the cartridge port, once I refactor this mess
		else:
			game.metadata.specific_info['Notes'] = note
	if 'Display_Format' in game_info:
		display_format = game_info['Display_Format']
		if display_format in ('NTSC', 'PAL60', 'SECAM60'):
			#Treat PAL60 etc as NTSC because meh
			game.metadata.tv_type = TVSystem.NTSC
		elif display_format in ('PAL', 'SECAM', 'NTSC50'):
			game.metadata_tv_type = TVSystem.PAL

	left_controller = None
	if 'Controller_Left' in game_info:
		left_controller = game_info['Controller_Left']

	right_controller = None
	no_save = True
	if 'Controller_Right' in game_info:
		right_controller = game_info['Controller_Right']
		if right_controller in ('ATARIVOX', 'SAVEKEY'):
			game.metadata.save_type = SaveType.MemoryCard
			#If these devices are plugged in, they aren't controllers
			right_controller = None
			no_save = False

		if right_controller == 'KIDVID':
			game.metadata.specific_info['Uses-Kid-Vid'] = True
			right_controller = None

	if no_save:
		game.metadata.save_type = SaveType.Nothing

	swap_ports = False
	if 'Controller_SwapPorts' in game_info:
		if game_info.get('Controller_SwapPorts', 'NO') == 'YES' or game_info.get('Controller_SwapPaddles', 'NO') == 'YES':
			#Not exactly sure how this works
			swap_ports = True

	if swap_ports:
		game.metadata.specific_info['Left-Peripheral'] = _controller_from_stella_db_name(right_controller)
		game.metadata.specific_info['Right-Peripheral'] = _controller_from_stella_db_name(left_controller)
	else:
		game.metadata.specific_info['Left-Peripheral'] = _controller_from_stella_db_name(left_controller)
		game.metadata.specific_info['Right-Peripheral'] = _controller_from_stella_db_name(right_controller)

_stella_db = None

def add_atari_2600_metadata(game):
	global _stella_db
	#Python, you're officially a fucking dumbarse. Of course that's a fucking global variable. It is right there. Two lines above here. In the global fucking scope.
	if _stella_db is None:
		try:
			_stella_db = get_stella_database()
		except subprocess.CalledProcessError:
			pass

	whole_cart = game.rom.read()
	crc32 = get_crc32_for_software_list(whole_cart)
	md5 = hashlib.md5(whole_cart).hexdigest().lower()
	if md5 in _stella_db:
		game_info = _stella_db[md5]
		parse_stella_db(game, game_info)

	software = find_in_software_lists(game.software_lists, crc=crc32)
	if software:
		existing_notes = game.metadata.specific_info.get('Notes')
		software.add_generic_info(game)
		usage = software.get_info('usage')
		if existing_notes and usage:
			game.metadata.specific_info['Notes'] = usage + ';' + existing_notes

		if game.metadata.publisher == 'Homebrew':
			#For consistency. There's no company literally called "Homebrew"
			game.metadata.publisher = game.metadata.developer

		game.metadata.specific_info['Uses-Supercharger'] = software.get_shared_feature('requirement') == 'scharger'
		#TODO: Add 'peripheral' feature:
		#"Kid's Controller", "kidscontroller" (both are used)
		#"paddles"
		#"keypad"
