import hashlib
import re
import subprocess

from metadata import SaveType
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

stella_input_methods = {
	'JOYSTICK': 'Normal',
	'PADDLES': 'Paddle',
	'PADDLES_IAXIS': 'Paddle',
	'PADDLES_IAXDR': 'Paddle',	
	'BOOSTERGRIP': 'Normal',
	'DRIVING': 'Steering Wheel',
	'KEYBOARD': 'Keyboard',
	'AMIGAMOUSE': 'Mouse',
	'ATARIMOUSE': 'Mouse',
	'TRAKBALL': 'Trackball',
	'GENESIS': 'Normal',
	'COMPUMATE': 'Keyboard', #Kinda, it's an entire goddamn computer
}	

stella_display_format_line_regex = re.compile(r'^\s*Display Format:\s*(PAL|NTSC)\*')
def autodetect_from_stella(game):
	proc = subprocess.run(['stella', '-rominfo', game.rom.path], stdout=subprocess.PIPE, universal_newlines=True)
	if proc.returncode != 0:
		return

	lines = proc.stdout.splitlines()
	for line in lines:
		display_format_match = stella_display_format_line_regex.match(line)
		if display_format_match:
			game.tv_type = TVSystem[display_format_match.group(1)]
		#Can also get bankswitch type from here if needed. Controller 0 and Controller 1 too, but then it's probably better to just get that from the database

_stella_db = None
def add_atari_2600_metadata(game):
	global _stella_db 
	#Python, you're officially a fucking dumbarse. Of course that's a fucking global variable. It is right there. Two lines above here. In the global fucking scope.
	if _stella_db is None:
		try:
			_stella_db = get_stella_database()
		except subprocess.CalledProcessError:
			pass
	
	entire_rom = game.rom.read()
	md5 = hashlib.md5(entire_rom).hexdigest().lower()
	if md5 in _stella_db:
		game_info = _stella_db[md5]
	
		#TODO: Get year out of name	
		if 'Cartridge_Manufacturer' in game_info:
			#TODO: Includes the programmer as well, which is nice, but inconsistent with how X-Author is used elsewhere, maybe split by ', '?
			game.metadata.author = game_info['Cartridge_Manufacturer']
		if 'Cartridge_ModelNo' in game_info:
			game.metadata.specific_info['Product-Code'] = game_info['Cartridge_ModelNo']
		if 'Cartridge_Note' in game_info:
			#TODO: Ignore things like "Uses the Paddle Controllers" and "Console ports are swapped" that are already specified by other fields
			#TODO: Do something with "AKA blah blah blah" (X-Alternate-Name?) or ignore that
			game.metadata.specific_info['Notes'] = game_info['Cartridge_Note']
		if 'Controller_Left' in game_info:
			#TODO: Take note of Controller_SwapPorts or Controller_SwapPaddles and also the right controller
			#TODO: Use some attribute to note if PADDLES_IAXIS or PADDLES_IAXDR, whatever those do exactly that's different from just PADDLES
			#There's also things like the Track & Field controller that Stella just calls JOYSTICK so meh
			left_controller = game_info['Controller_Left']
			if left_controller in stella_input_methods:
				game.metadata.input_method = stella_input_methods[left_controller]
			else:
				#Includes MindLink because I dunno what to call that
				game.metadata.input_method = 'Custom'

			if left_controller == 'GENESIS':
				game.metadata.specific_info['Uses-Genesis-Controller'] = True
			elif left_controller == 'BOOSTERGRIP':
				game.metadata.specific_info['Uses-Boostergrip'] = True
			#TODO: Should differentiate between AMIGAMOUSE and ATARIMOUSE? Maybe that's needed for something	
	
		if 'Controller_Right' in game_info:
			right_controller = game_info['Controller_Right']
			#Really should be detecting this the same way as the left controller, but for now that's confusing and I'll figure it out later, so this just detects the presence of various peripherals.
			if right_controller in ('ATARIVOX', 'SAVEKEY'):
				game.metadata.save_type = SaveType.MemoryCard
			else:
				game.metadata.save_type = SaveType.Nothing

			if right_controller == 'KIDVID':
				game.metadata.specific_info['Uses-Kid-Vid'] = True
		
		if 'Display_Format' in game_info:
			display_format = game_info['Display_Format']
			if display_format == 'NTSC':
				game.metadata.tv_type = TVSystem.NTSC
			elif display_format == 'PAL':
				game.metadata_tv_type = TVSystem.PAL
			elif display_format == 'AUTO':
				#Yeah, I guess we're just reading the whole ROM again after already reading it once to get the MD5. Oh well. They aren't too big.
				#TODO: Actually... what if we run -rominfo first, get MD5 from there, and then if it's in stella_db add more values?
				autodetect_from_stella(game)
			#TODO: Can also be SECAM, NTSC50, PAL60, or SECAM60
	else:
		autodetect_from_stella(game)
	
