import subprocess
import hashlib
from enum import Enum, auto

import input_metadata
from common_types import SaveType
from info.region_info import TVSystem
from software_list_info import find_in_software_lists, get_crc32_for_software_list
import platform_metadata.atari_controllers as controllers

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
	Nothing = auto()
	Joystick = auto()
	Paddle = auto() #2 players per port
	Mouse = auto() #2 buttons, Stella lists an AMIGAMOUSE and ATARIMOUSE (ST mouse) and I dunno if those are functionally different
	Trackball = auto() #Functionally 1 button, but has 2 physical buttons to be ambidextrous; see atari_8_bit.py
	KeyboardController = auto() #This is... 2 keypads joined together (12 keys each)
	Compumate = auto() #42-key keyboard (part of a whole entire computer)
	MegadriveGamepad = auto() #See megadrive.py
	Boostergrip = auto() #Effectively a 3-button joystick, passes through to the standard 2600 joystick and adds 2 buttons
	DrivingController = auto() #Has 360 degree movement, so not quite like a paddle. MAME actually calls it a trackball
	Mindlink = auto()
	LightGun = auto() #Presumably this is the XEGS XG-1, which has 1 button (see atari_8_bit.py)
	Other = auto()
	#Light pen would also be possible

	#Not controllers but plug into the controller port:
	AtariVox = auto()
	SaveKey = auto()
	KidVid = auto()

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
		return Atari2600Controller.MegadriveGamepad
	elif controller == 'BOOSTERGRIP':
		return Atari2600Controller.Boostergrip
	elif controller == 'DRIVING':
		return Atari2600Controller.DrivingController
	elif controller == 'MINDLINK':
		return Atari2600Controller.Mindlink
	elif controller == 'ATARIVOX':
		return Atari2600Controller.AtariVox
	elif controller == 'SAVEKEY':
		return Atari2600Controller.SaveKey
	elif controller == 'KIDVID':
		return Atari2600Controller.KidVid
	#Track & Field controller is just a joystick with no up or down, so Stella doesn't count it as separate from joystick
	return Atari2600Controller.Other

def parse_stella_cart_note(game, note):
	#Adventures in the Park
	#Featuring Panama Joe
	#Hack of Adventure
	#Journey to Rivendell (The Lord of the Rings I)
	#O Monstro Marinho
	#Pitfall Harry's Jungle Adventure (Jungle Runner)
	#ROM must be started in bank 0
	#Set right difficulty to 'A' for BoosterGrip in both ports
	#Use Color/BW switch to change between galactic chart and front views
	#Uses Joystick Coupler (Dual Control Module) (not specified by joystick info)

	#Controllers that just act like joysticks I think:
	#Uses the Track & Field Controller
	#Uses Joyboard
	#Uses the Amiga Joyboard
	#Uses the Joyboard controller
	if note.startswith('AKA '):
		pass #Could add an Alternate-Name field but mehhhhhhhhhhh (There is an "AKA Bachelor Party, Uses the paddle controllers" but we will also skip that)
	elif note == 'Uses Joystick (left) and Keypad (right) Controllers':
		#We should already know this from the controller fields but might as well add it while we're here
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Joystick
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.KeyboardController
	elif note == 'Uses Mindlink Controller (left only)':
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Mindlink
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Nothing
	elif note in ('Uses the Keypad Controllers (left only)', 'Uses Keypad Controller'):
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.KeyboardController
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Nothing
	elif note == 'Uses the Paddle Controllers (left only)':
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Paddle
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Nothing
	elif note == 'Uses the Light Gun Controller (left only)':
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.LightGun
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Nothing
	elif note == 'Uses right joystick controller':
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Nothing
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Joystick
	elif note in ('Uses the KidVid Controller', 'Uses the Kid Vid Controller'):
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Joystick
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.KidVid
	elif note == 'Uses the Driving Controllers':
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.DrivingController
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.DrivingController
	elif note in ('Uses the Keypad Controllers', 'Uses Keypad Controllers'):
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.KeyboardController
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.KeyboardController
	elif note in ('Uses the paddle controllers', 'Uses the Paddle Controllers'):
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Paddle
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Paddle
	elif note == 'Uses the Joystick Controllers (swapped)':
		game.metadata.specific_info['Swap-Ports'] = True
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Joystick
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Joystick
	elif note == 'Uses the Paddle Controllers (swapped)':
		game.metadata.specific_info['Swap-Ports'] = True
		game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Paddle
		game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Paddle
	elif note == 'Console ports are swapped':
		game.metadata.specific_info['Swap-Ports'] = True
	else:
		game.metadata.specific_info['Notes'] = note

def parse_stella_db(game, game_info):
	game.metadata.specific_info['Stella-Name'] = game_info.get('Cartridge_Name')
	note = game_info.get('Cartridge_Note')
	if 'Cartridge_Manufacturer' in game_info:
		manufacturer = game_info['Cartridge_Manufacturer']
		if ', ' in manufacturer:
			game.metadata.publisher, _, game.metadata.developer = manufacturer.partition(', ')
		else:
			game.metadata.publisher = manufacturer
			#TODO: Clean up manufacturer names (UA Limited > UA)
	if 'Cartridge_ModelNo' in game_info:
		game.metadata.product_code = game_info['Cartridge_ModelNo']
	if 'Display_Format' in game_info:
		display_format = game_info['Display_Format']
		if display_format in ('NTSC', 'PAL60', 'SECAM60'):
			#Treat PAL60 etc as NTSC because meh
			game.metadata.tv_type = TVSystem.NTSC
		elif display_format in ('PAL', 'SECAM', 'NTSC50'):
			game.metadata_tv_type = TVSystem.PAL

	left_controller = game_info.get('Controller_Left')
	right_controller = game_info.get('Controller_Right')
	game.metadata.specific_info['Left-Peripheral'] = _controller_from_stella_db_name(left_controller)
	game.metadata.specific_info['Right-Peripheral'] = _controller_from_stella_db_name(right_controller)

	if game_info.get('Controller_SwapPorts', 'NO') == 'YES' or game_info.get('Controller_SwapPaddles', 'NO') == 'YES':
		#Not exactly sure how this works
		game.metadata.specific_info['Swap-Ports'] = True
	if note:
		parse_stella_cart_note(game, note)

def add_input_info_from_peripheral(game, peripheral):
	if peripheral == Atari2600Controller.Nothing:
		return
	elif peripheral == Atari2600Controller.Joystick:
		game.metadata.input_info.add_option(controllers.joystick)
	elif peripheral == Atari2600Controller.Boostergrip:
		game.metadata.input_info.add_option(controllers.boostergrip)
	elif peripheral == Atari2600Controller.Compumate:
		game.metadata.input_info.add_option(controllers.compumate)
	elif peripheral == Atari2600Controller.DrivingController:
		game.metadata.input_info.add_option(controllers.driving_controller)
	elif peripheral == Atari2600Controller.KeyboardController:
		game.metadata.input_info.add_option(controllers.keypad)
	elif peripheral == Atari2600Controller.LightGun:
		game.metadata.input_info.add_option(controllers.xegs_gun)
	elif peripheral == Atari2600Controller.MegadriveGamepad:
		from .megadrive import standard_gamepad as megadrive_pad
		game.metadata.input_info.add_option(megadrive_pad)
	elif peripheral == Atari2600Controller.Mindlink:
		game.metadata.input_info.add_option(controllers.mindlink)
	elif peripheral == Atari2600Controller.Mouse:
		game.metadata.input_info.add_option(controllers.atari_st_mouse)
	elif peripheral == Atari2600Controller.Paddle:
		game.metadata.input_info.add_option(controllers.paddle)
	elif peripheral == Atari2600Controller.Trackball:
		game.metadata.input_info.add_option(controllers.cx22_trackball)
	elif peripheral == Atari2600Controller.Other:
		game.metadata.input_info.add_option(input_metadata.Custom())

def parse_peripherals(game):
	left = game.metadata.specific_info.get('Left-Peripheral')
	right = game.metadata.specific_info.get('Right-Peripheral')

	game.metadata.save_type = SaveType.MemoryCard if right in (Atari2600Controller.AtariVox, Atari2600Controller.SaveKey) else SaveType.Nothing
	if right == Atari2600Controller.KidVid:
		game.metadata.specific_info['Uses-Kid-Vid'] = True

	if left:
		add_input_info_from_peripheral(game, left)
	if right is not None and right != left:
		add_input_info_from_peripheral(game, right)

class StellaDB():
	class __StellaDB():
		def __init__(self):
			try:
				self.db = get_stella_database()
			except subprocess.CalledProcessError:
				self.db = None

	__instance = None
	@staticmethod
	def get_stella_db():
		if StellaDB.__instance is None:
			StellaDB.__instance = StellaDB.__StellaDB()
		return StellaDB.__instance.db

def add_atari_2600_metadata(game):
	stella_db = StellaDB.get_stella_db()

	whole_cart = game.rom.read()
	crc32 = get_crc32_for_software_list(whole_cart)
	if stella_db:
		md5 = hashlib.md5(whole_cart).hexdigest().lower()
		if md5 in stella_db:
			game_info = stella_db[md5]
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
		if 'cart' in software.parts:
			#"cass" and "cass1" "cass2" "cass3" etc are also possible but a2600_cass doesn't have peripheral in it so it'll be fine
			cart_part = software.get_part('cart')
			peripheral = cart_part.get_feature('peripheral')
			if peripheral in ("Kid's Controller", 'kidscontroller'):
				#The Kids Controller is functionally identical to the Keyboard Controller, but there is only one of them and it goes in the left
				game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.KeyboardController
				game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.Nothing
			elif peripheral == 'paddles':
				game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.Paddle
				#Does the right one go in there too? Maybe
			elif peripheral == 'keypad':
				game.metadata.specific_info['Left-Peripheral'] = Atari2600Controller.KeyboardController
				game.metadata.specific_info['Right-Peripheral'] = Atari2600Controller.KeyboardController

	parse_peripherals(game)
