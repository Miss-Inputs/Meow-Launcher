import re
import subprocess

from metadata import SaveType, PlayerInput, InputType
from info.region_info import TVSystem


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

stella_display_format_line_regex = re.compile(r'^\s*Display Format:\s*(PAL|NTSC)\*')
stella_cart_md5_line_regex = re.compile(r'^\s*Cart MD5:\s*([a-z0-9]{32})')
def autodetect_from_stella(game):
	proc = subprocess.run(['stella', '-rominfo', game.rom.path], stdout=subprocess.PIPE, universal_newlines=True)
	if proc.returncode != 0:
		return None

	md5 = None
	lines = proc.stdout.splitlines()
	for line in lines:
		cart_md5_match = stella_cart_md5_line_regex.match(line)
		if cart_md5_match:
			md5 = cart_md5_match[1]
			break

		display_format_match = stella_display_format_line_regex.match(line)
		if display_format_match:
			game.tv_type = TVSystem[display_format_match.group(1)]
		#Can also get bankswitch type from here if needed. Controller 0 and Controller 1 too, but then it's probably better to just get that from the database
	return md5

def add_controller_info(game, controller):
	#TODO: Take note of Controller_SwapPaddles
	#TODO: Use some attribute to note if PADDLES_IAXIS or PADDLES_IAXDR, whatever those do exactly that's different from just PADDLES
	#Track & Field controller is just a joystick with no up or down, so Stella doesn't count it as separate from joystick

	#TODO: Hella refactor this too I guess

	if not controller:
		return

	player = PlayerInput()
	player.buttons = 1
	if controller in ('PADDLES', 'PADDLES_IAXIS', 'PADDLES_IAXDR'):
		player.inputs = [InputType.Paddle]
		#Paddles come in pairs and hence have 2 players per port
		game.metadata.input_info.players += [player] * 2
		return
	elif controller == 'JOYSTICK':
		player.inputs = [InputType.Digital]
	elif controller in ('AMIGAMOUSE', 'ATARIMOUSE'):
		#ATARIMOUSE is an ST mouse, to be precise
		#TODO: Should differentiate between AMIGAMOUSE and ATARIMOUSE? Maybe that's needed for something
		player.buttons = 2
		player.inputs = [InputType.Mouse]
	elif controller == 'TRAKBALL':
		#Reminder to not do player.buttons = 2, while it does have 2 physical buttons, they're just to make it ambidextrous; they function as the same single button
		player.inputs = [InputType.Trackball]
	elif controller == 'KEYBOARD':
		#The Keyboard Controller is actually a keypad, go figure. Actually, it's 2 keypads, go figure twice. BASIC Programming uses both at once and Codebreakers uses them separately for each player, so there's not really anything else we can say here.
		player.buttons = 12
		player.inputs = [InputType.Keypad]
	elif controller in 'COMPUMATE':
		#The CompuMate is a whole dang computer, not just a keyboard. But I guess it's the same sorta thing
		player.buttons = 42
		player.inputs = [InputType.Keyboard]
	elif controller == 'GENESIS':
		player.buttons = 3
		#TODO: Do I really need that specific info or do I wanna just do buttons = 3 to detect that?
		game.metadata.specific_info['Uses-Genesis-Controller'] = True
		player.inputs = [InputType.Digital]
	elif controller == 'BOOSTERGRIP':
		player.buttons = 3 #There are two on the boostergrip, but it passes through to the 2600 controller
		game.metadata.specific_info['Uses-Boostergrip'] = True
		player.inputs = [InputType.Digital]	
	elif controller == 'DRIVING':
		#Has 360 degree movement, so not quite like a paddle. MAME actually calls it a trackball
		player.inputs = [InputType.SteeringWheel]
	elif controller == 'MINDLINK':
		player.inputs = [InputType.Biological]
	else:
		player.inputs = [InputType.Custom]

	game.metadata.input_info.players.append(player)

def parse_stella_db(game, game_info):
	#TODO: Get year out of name	
	if 'Cartridge_Manufacturer' in game_info:
		manufacturer = game_info['Cartridge_Manufacturer']
		if ', ' in manufacturer:
			game.metadata.publisher, _, game.metadata.developer = manufacturer.partition(', ')
		else:
			game.metadata.publisher = manufacturer
	if 'Cartridge_ModelNo' in game_info:
		game.metadata.product_code = game_info['Cartridge_ModelNo']
	if 'Cartridge_Note' in game_info:
		#TODO: Ignore things like "Uses the Paddle Controllers" and "Console ports are swapped" that are already specified by other fields
		#TODO: Do something with "AKA blah blah blah" (X-Alternate-Name?) or ignore that
		game.metadata.specific_info['Notes'] = game_info['Cartridge_Note']		
	if 'Display_Format' in game_info:
		display_format = game_info['Display_Format']
		if display_format == 'NTSC':
			game.metadata.tv_type = TVSystem.NTSC
		elif display_format == 'PAL':
			game.metadata_tv_type = TVSystem.PAL
		#TODO: Can also be SECAM, NTSC50, PAL60, or SECAM60

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
		if game_info['Controller_SwapPorts'] == 'YES':
			swap_ports = True

	if swap_ports:
		add_controller_info(game, right_controller)
		add_controller_info(game, left_controller)
	else:
		add_controller_info(game, left_controller)
		add_controller_info(game, right_controller)

_stella_db = None
def add_atari_2600_metadata(game):
	game.metadata.input_info.console_buttons = 2 #Select and Reset

	global _stella_db 
	#Python, you're officially a fucking dumbarse. Of course that's a fucking global variable. It is right there. Two lines above here. In the global fucking scope.
	if _stella_db is None:
		try:
			_stella_db = get_stella_database()
		except subprocess.CalledProcessError:
			pass
	
	md5 = autodetect_from_stella(game)
	if md5 in _stella_db:
		game_info = _stella_db[md5]
		parse_stella_db(game, game_info)	
