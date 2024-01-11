"""Not worth putting these in their own source file I think
#TODO: Yeah sure but they still belong somewhere else??"""
from enum import Enum, auto
from functools import lru_cache
from typing import TYPE_CHECKING, cast

from meowlauncher import input_info
from meowlauncher.common_types import ByteAmount, MediaType
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.mame_common.machine import (
	Machine,
	does_machine_match_name,
	iter_machines_from_source_file,
)
from meowlauncher.games.mame_common.mame_executable import MAMENotInstalledError
from meowlauncher.games.mame_common.mame_helpers import default_mame_executable
from meowlauncher.games.roms.rom import FileROM

if TYPE_CHECKING:
	from collections.abc import Collection, Sequence

	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo


def add_vic10_custom_info(game: 'ROMGame') -> None:
	#Input info: Keyboard or joystick

	rom = cast(FileROM, game.rom)
	has_header = False
	if game.info.media_type == MediaType.Cartridge and (rom.size % 256) == 2:
		has_header = True
		rom.header_length_for_crc_calculation = 2
	game.info.specific_info['Headered?'] = has_header
	software = game.get_software_list_entry()
	if software:
		add_generic_software_info(software, game.info)
		#What the heck is an "assy"?

def add_vic20_custom_info(game: 'ROMGame') -> None:
	#Input info: Keyboard and/or joystick

	rom = cast(FileROM, game.rom)
	has_header = False
	if game.info.media_type == MediaType.Cartridge and (rom.size % 256) == 2:
		has_header = True
		rom.header_length_for_crc_calculation = 2
	game.info.specific_info['Headered?'] = has_header
	software = game.get_software_list_entry()
	if software:
		software.add_standard_info(game.info)
		notes = software.get_info('usage')
		if notes == 'Game Paddles required':
			game.info.specific_info['Peripheral'] = 'Paddle'
		else:
			game.info.add_notes(notes)
		
		#Enter 'SYS <some number>' to run
		#Needs VICKIT 4 to run
		#SYS 40969 for 40 column mode, SYS 40972 for 80 column mode, SYS 40975 for VIC mode, SYS 40978 to restart 40/80 column mode

class ColecoController(Enum):
	Normal = auto()
	SuperActionController = auto()
	RollerController = auto()
	DrivingController = auto()

def add_colecovision_software_info(software: 'Software', game_info: 'GameInfo') -> None:
	"""Can get year, publisher unreliably from the title screen info in the ROM, or you could also not do that"""

	peripheral: ColecoController = ColecoController.Normal
	peripheral_required = False

	software.add_standard_info(game_info)

	usage = software.get_info('usage')
	if usage == 'Supports Super Action Controllers':
		peripheral = ColecoController.SuperActionController
	elif usage == 'Requires Super Action Controllers':
		peripheral = ColecoController.SuperActionController
		peripheral_required = True
	elif usage == 'Supports roller controller':
		peripheral = ColecoController.RollerController
	elif usage == 'Requires roller controller':
		peripheral = ColecoController.RollerController
		peripheral_required = True
	elif usage == 'Supports driving controller':
		peripheral = ColecoController.DrivingController
	elif usage == 'Requires driving controller':
		peripheral = ColecoController.DrivingController
		peripheral_required = True
	else:
		game_info.add_notes(usage)

	normal_controller_part = input_info.NormalController()
	normal_controller_part.face_buttons = 2
	normal_controller_part.dpads = 1
	normal_controller_keypad = input_info.Keypad()
	normal_controller_keypad.keys = 12
	normal_controller = input_info.CombinedController([normal_controller_part, normal_controller_keypad])

	super_action_controller_buttons = input_info.NormalController()
	super_action_controller_buttons.face_buttons = 4 #Not really on the face, they're on the hand grip part, but still
	super_action_controller_buttons.dpads = 1
	super_action_controller_speed_roller = input_info.Dial() #Kind of, it's like a one-dimensional trackball from what I can tell
	super_action_controller_keypad = input_info.Keypad()
	super_action_controller_keypad.keys = 12
	super_action_controller = input_info.CombinedController([super_action_controller_buttons, super_action_controller_speed_roller, super_action_controller_keypad])

	roller_controller = input_info.Trackball()
	#Not sure how many buttons?
	driving_controller = input_info.SteeringWheel()
	#Gas pedal is on + off so I guess it counts as one button

	game_info.specific_info['Peripheral'] = peripheral
	if peripheral == ColecoController.Normal:
		game_info.input_info.add_option(normal_controller)
	else:
		if peripheral == ColecoController.DrivingController:
			game_info.input_info.add_option(driving_controller)
		elif peripheral == ColecoController.RollerController:
			game_info.input_info.add_option(roller_controller)
		elif peripheral == ColecoController.SuperActionController:
			game_info.input_info.add_option(super_action_controller)
		if not peripheral_required:
			game_info.input_info.add_option(normal_controller)
	#Doesn't look like you can set controller via command line at the moment, oh well

def add_ibm_pcjr_custom_info(game: 'ROMGame') -> None:
	#Input info: Keyboard or joystick

	rom = cast(FileROM, game.rom)
	magic = rom.read(amount=32)

	if magic[:25] == b'PCjr Cartridge image file':
		game.info.specific_info['Headered?'] = True
		# +  0  signature DB "PCjr Cartridge image file",0Dh,0Ah ;file signature
		# + 27  creator   DB 30 DUP (20h) ;creator signature
		# 							;(for example: "ApH's JRIPCART version 1.0    ")
		# + 57  CR        DB 0Dh,0Ah
		# + 59  comment   DB 400 DUP (1Ah) ;comment (contained program)
		# +459  EOF       DB 1Ah ;End Of File (for DOS "type" command)
		# +460  version   DB 1,0 ;Image version number
		# +462  address   DW ? ;segment address (little endian) at which the beginning
		# 					;of the cartridge appears in the PCjr's memory map.
		# +464  adrmask   DW ? ;a "1" at a given position means a "don't care" at the
		# 					;same position in the address field (this address bit is
		# 					;not decoded by the cartridge logic).
		# +466  reserved  DB 46 DUP (0) ;reserved for future use
		game.info.specific_info['Header Format'] = 'JRipCart'
		rom.header_length_for_crc_calculation = 512
	elif magic[:10] == b'Filename: ' and magic[0x14:0x1d] == b'Created: ':
		#Fields here are more plain texty, but otherwise there's just like... a filename and creation date, which is meaningless, and a generic description field, and also a start address
		game.info.specific_info['Headered?'] = True
		game.info.specific_info['Header Format'] = 'PCJrCart'
		rom.header_length_for_crc_calculation = 128

	software = game.get_software_list_entry()
	if software:
		add_generic_software_info(software, game.info)
		#TODO: If sharedfeat requirement = ibmpcjr_flop:pcdos21, do something about that
		#Probably get the MAME command line to get a PC DOS 2.1 floppy path from platform_config provided by the user, or else they don't get to use ColorPaint
		#Lotus 123jr has a similar predicament, but it also needs .m3u I guess

		#Usages:
		#Mount both carts and a DOS floppy and type 'TUTOR'
		#Boot from a DOS floppy and type 'G'

def add_pet_info_from_filename_tags(tags: 'Sequence[str]', game_info: 'GameInfo') -> None:
	#Usage strings in pet_rom:
	#Requires BASIC 2 (works on pet2001n).  Enter 'SYS 37000' to run
	#SYS38000

	for tag in tags:
		#(2001, 3008, 3016, 3032, 3032B, 4016, 4032, 4032B, 8032, 8096, 8296, SuperPET)
		if (tag[0] == '(' and tag[-1] == ')') or (tag[0] == '[' and tag[-1] == ']'):
			tag = tag[1:-1]

		for model in ('3008', '3016', '3032', '3032B', '4016', '4032', '4032B', '8032', '8096', '8296', 'SuperPET'):
			if tag in {model, f'CBM {model}', f'CBM{model}', f'PET {model}', f'PET{model}'}:
				game_info.specific_info['Machine'] = model
				continue
		if tag in {'PET 2001', 'PET2001', 'CBM 2001', 'CBM2001'}:
			#We don't search for just "(2001)" in case that's used to denote the year
			game_info.specific_info['Machine'] = '2001'
			continue
		for ram in (8, 16, 32, 96, 128):
			if tag.lower() in {f'{ram}k ram', f'{ram}kb ram'}:
				game_info.specific_info['Minimum RAM'] = ByteAmount(ram * 1024)
				continue
	
@lru_cache(maxsize=1)
def _get_uapce_games() -> 'Collection[Machine]':
	try:
		if not default_mame_executable:
			return []
		return set(iter_machines_from_source_file('uapce', default_mame_executable))
	except MAMENotInstalledError:
		return []

def find_equivalent_pc_engine_arcade(game_name: str) -> Machine | None:
	for uapce_machine in _get_uapce_games():
		if does_machine_match_name(game_name, uapce_machine):
			return uapce_machine
	return None
