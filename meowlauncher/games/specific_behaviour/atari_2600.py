import hashlib
import subprocess
from collections.abc import Mapping
from typing import TYPE_CHECKING, Optional, cast

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.games.mame_common.software_list_find_utils import (
    find_in_software_lists, matcher_args_for_bytes)
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.platform_types import Atari2600Controller
from meowlauncher.util.region_info import TVSystem

from .common import atari_controllers as controllers

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

_stella_configs = emulator_configs.get('Stella')

#Not gonna use stella -rominfo on individual stuff as it takes too long and just detects TV type with no other useful info that isn't in the -listrominfo db
def get_stella_database() -> Mapping[str, Mapping[str, str]]:
	proc = subprocess.run([_stella_configs.exe_path, '-listrominfo'], stdout=subprocess.PIPE, universal_newlines=True, check=True)

	lines = proc.stdout.splitlines()
	first_line = lines[0]
	lines = lines[1:]

	columns = dict(enumerate(first_line.split('|')))

	games = {}
	for line in lines:
		game_columns = line.split('|')
		game = {}

		md5 = None
		for i, game_column in enumerate(game_columns):
			if i in columns:
				if columns[i] in {'Cartridge_MD5', 'Cart_MD5'}:
					md5 = game_column.lower()
				elif game_column:
					game[columns[i]] = game_column

		if md5:
			games[md5] = game

	return games

def _controller_from_stella_db_name(controller: str) -> Atari2600Controller:
	if controller in {'JOYSTICK', 'AUTO'}:
		return Atari2600Controller.Joystick
	if controller in {'PADDLES', 'PADDLES_IAXIS', 'PADDLES_IAXDR'}:
		#Not sure what the difference in the latter two are
		return Atari2600Controller.Paddle
	if controller in {'AMIGAMOUSE', 'ATARIMOUSE'}:
		return Atari2600Controller.Mouse
	if controller == 'TRAKBALL':
		return Atari2600Controller.Trackball
	if controller == 'KEYBOARD':
		return Atari2600Controller.KeyboardController
	if controller in 'COMPUMATE':
		return Atari2600Controller.Compumate
	if controller == 'GENESIS':
		return Atari2600Controller.MegadriveGamepad
	if controller == 'BOOSTERGRIP':
		return Atari2600Controller.Boostergrip
	if controller == 'DRIVING':
		return Atari2600Controller.DrivingController
	if controller == 'MINDLINK':
		return Atari2600Controller.Mindlink
	if controller == 'ATARIVOX':
		return Atari2600Controller.AtariVox
	if controller == 'SAVEKEY':
		return Atari2600Controller.SaveKey
	if controller == 'KIDVID':
		return Atari2600Controller.KidVid
	#Track & Field controller is just a joystick with no up or down, so Stella doesn't count it as separate from joystick
	return Atari2600Controller.Other

def _parse_stella_cart_note(metadata: 'Metadata', note: str):
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
		#There is an "AKA Bachelor Party, Uses the paddle controllers" but we will ignore that, apparently
		#TODO: Will need to check for ", " anyway as some games have more than one alternate name
		metadata.add_alternate_name(note.removeprefix('AKA '))
	elif note == 'Uses Joystick (left) and Keypad (right) Controllers':
		#We should already know this from the controller fields but might as well add it while we're here
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Joystick
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.KeyboardController
	elif note == 'Uses Mindlink Controller (left only)':
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Mindlink
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Nothing
	elif note in {'Uses the Keypad Controllers (left only)', 'Uses Keypad Controller'}:
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.KeyboardController
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Nothing
	elif note == 'Uses the Paddle Controllers (left only)':
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Paddle
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Nothing
	elif note == 'Uses the Light Gun Controller (left only)':
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.LightGun
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Nothing
	elif note == 'Uses right joystick controller':
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Nothing
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Joystick
	elif note in {'Uses the KidVid Controller', 'Uses the Kid Vid Controller'}:
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Joystick
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.KidVid
	elif note == 'Uses the Driving Controllers':
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.DrivingController
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.DrivingController
	elif note in {'Uses the Keypad Controllers', 'Uses Keypad Controllers'}:
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.KeyboardController
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.KeyboardController
	elif note in {'Uses the paddle controllers', 'Uses the Paddle Controllers'}:
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Paddle
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Paddle
	elif note == 'Uses the Joystick Controllers (swapped)':
		metadata.specific_info['Swap Ports?'] = True
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Joystick
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Joystick
	elif note == 'Uses the Paddle Controllers (swapped)':
		metadata.specific_info['Swap Ports?'] = True
		metadata.specific_info['Left Peripheral'] = Atari2600Controller.Paddle
		metadata.specific_info['Right Peripheral'] = Atari2600Controller.Paddle
	elif note == 'Console ports are swapped':
		metadata.specific_info['Swap Ports?'] = True
	else:
		metadata.add_notes(note)

def _parse_stella_db(metadata: 'Metadata', game_db_entry: Mapping[str, Optional[str]]):
	stella_name = game_db_entry.get('Cartridge_Name', game_db_entry.get('Cart_Name'))
	if stella_name:
		metadata.add_alternate_name(stella_name, 'Stella Name')
	note = game_db_entry.get('Cartridge_Note', game_db_entry.get('Cart_Note'))
	
	manufacturer = game_db_entry.get('Cartridge_Manufacturer', game_db_entry.get('Cart_Manufacturer'))
	if manufacturer:
		if ', ' in manufacturer:
			metadata.publisher, _, metadata.developer = manufacturer.partition(', ')
		else:
			metadata.publisher = manufacturer
			#TODO: Clean up manufacturer names (UA Limited > UA)
	
	metadata.product_code = game_db_entry.get('Cartridge_ModelNo', game_db_entry.get('Cart_ModelNo'))
	metadata.specific_info['Rarity'] = game_db_entry.get('Cartridge_Rarity', game_db_entry.get('Cart_Rarity'))
	if 'Display_Format' in game_db_entry:
		display_format = game_db_entry['Display_Format']
		if display_format in {'NTSC', 'PAL60', 'SECAM60'}:
			#Treat PAL60 etc as NTSC because meh
			metadata.specific_info['TV Type'] = TVSystem.NTSC
		elif display_format in {'PAL', 'SECAM', 'NTSC50'}:
			metadata.specific_info['TV Type'] = TVSystem.PAL

	left_controller = game_db_entry.get('Controller_Left')
	right_controller = game_db_entry.get('Controller_Right')
	if left_controller:
		metadata.specific_info['Left Peripheral'] = _controller_from_stella_db_name(left_controller)
	if right_controller:
		metadata.specific_info['Right Peripheral'] = _controller_from_stella_db_name(right_controller)

	if game_db_entry.get('Controller_SwapPorts', 'NO') == 'YES' or game_db_entry.get('Controller_SwapPaddles', 'NO') == 'YES':
		#Not exactly sure how this works
		metadata.specific_info['Swap Ports?'] = True
	if note:
		_parse_stella_cart_note(metadata, note)

def _add_input_info_from_peripheral(metadata: 'Metadata', peripheral: Atari2600Controller):
	if peripheral == Atari2600Controller.Nothing:
		return
		
	if peripheral == Atari2600Controller.Joystick:
		metadata.input_info.add_option(controllers.joystick)
	elif peripheral == Atari2600Controller.Boostergrip:
		metadata.input_info.add_option(controllers.boostergrip)
	elif peripheral == Atari2600Controller.Compumate:
		metadata.input_info.add_option(controllers.compumate)
	elif peripheral == Atari2600Controller.DrivingController:
		metadata.input_info.add_option(controllers.driving_controller)
	elif peripheral == Atari2600Controller.KeyboardController:
		metadata.input_info.add_option(controllers.keypad)
	elif peripheral == Atari2600Controller.LightGun:
		metadata.input_info.add_option(controllers.xegs_gun)
	elif peripheral == Atari2600Controller.MegadriveGamepad:
		metadata.input_info.add_option(controllers.megadrive_pad)
	elif peripheral == Atari2600Controller.Mindlink:
		metadata.input_info.add_option(controllers.mindlink)
	elif peripheral == Atari2600Controller.Mouse:
		metadata.input_info.add_option(controllers.atari_st_mouse)
	elif peripheral == Atari2600Controller.Paddle:
		metadata.input_info.add_option(controllers.paddle)
	elif peripheral == Atari2600Controller.Trackball:
		metadata.input_info.add_option(controllers.cx22_trackball)
	elif peripheral == Atari2600Controller.Other:
		metadata.input_info.add_option(input_metadata.Custom())

def _parse_peripherals(metadata: 'Metadata'):
	left = metadata.specific_info.get('Left Peripheral')
	right = metadata.specific_info.get('Right Peripheral')

	metadata.save_type = SaveType.MemoryCard if right in (Atari2600Controller.AtariVox, Atari2600Controller.SaveKey) else SaveType.Nothing
	if right == Atari2600Controller.KidVid:
		metadata.specific_info['Uses Kid Vid?'] = True

	if left:
		_add_input_info_from_peripheral(metadata, left)
	if right is not None and right != left:
		_add_input_info_from_peripheral(metadata, right)

class StellaDB():
	class __StellaDB():
		def __init__(self):
			self.db = None
			try:
				self.db = get_stella_database()
			except (subprocess.CalledProcessError, FileNotFoundError):
				pass

	__instance = None
	@staticmethod
	def get_stella_db():
		if StellaDB.__instance is None:
			StellaDB.__instance = StellaDB.__StellaDB()
		return StellaDB.__instance.db

def add_atari_2600_custom_info(game: 'ROMGame'):
	stella_db = StellaDB.get_stella_db()

	whole_cart = cast(FileROM, game.rom).read()
	if stella_db:
		md5 = hashlib.md5(whole_cart).hexdigest().lower()
		if md5 in stella_db:
			game_info = stella_db[md5]
			_parse_stella_db(game.metadata, game_info)

	software = find_in_software_lists(game.related_software_lists, matcher_args_for_bytes(whole_cart))
	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.add_notes(software.get_info('usage'))
		
		if game.metadata.publisher == 'Homebrew':
			#For consistency. There's no company literally called "Homebrew"
			game.metadata.publisher = game.metadata.developer

		if software.get_shared_feature('requirement') == 'scharger':
			game.metadata.specific_info['Uses Supercharger?'] = True
		if 'cart' in software.parts:
			#"cass" and "cass1" "cass2" "cass3" etc are also possible but a2600_cass doesn't have peripheral in it so it'll be fine
			cart_part = software.get_part('cart')
			peripheral = cart_part.get_feature('peripheral')
			if peripheral in {"Kid's Controller", 'kidscontroller'}:
				#The Kids Controller is functionally identical to the Keyboard Controller, but there is only one of them and it goes in the left
				game.metadata.specific_info['Left Peripheral'] = Atari2600Controller.KeyboardController
				game.metadata.specific_info['Right Peripheral'] = Atari2600Controller.Nothing
			elif peripheral == 'paddles':
				game.metadata.specific_info['Left Peripheral'] = Atari2600Controller.Paddle
				#Does the right one go in there too? Maybe
			elif peripheral == 'keypad':
				game.metadata.specific_info['Left Peripheral'] = Atari2600Controller.KeyboardController
				game.metadata.specific_info['Right Peripheral'] = Atari2600Controller.KeyboardController

	_parse_peripherals(game.metadata)
