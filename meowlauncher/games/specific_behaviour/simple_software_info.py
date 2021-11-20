import re
from typing import TYPE_CHECKING

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.games.common.generic_info import add_generic_software_info #We can then add more metadata on top of this, if we're fine with usage and such being unparsed and just added automatically

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.metadata import Metadata

#Straightforward stuff that doesn't really warrant going into its own source file I think

def add_pc_booter_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'PC Booter':
		usage = software.infos.get('user_notes')
	metadata.specific_info['Hacked By'] = software.infos.get('cracked')
	#Other info strings seen:
	#OEM = Mercer
	#Original Publisher = Nihon Falcom
	metadata.specific_info['Version'] = software.infos.get('version')

def add_super_cassette_vision_software_info(software: 'Software', metadata: 'Metadata'):
	add_generic_software_info(software, metadata)
	metadata.specific_info['Has Extra RAM?'] = software.has_data_area('ram') #Or feature "slot" ends with "_ram"

def add_microtan_65_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'Requires Joystick':
		joystick = input_metadata.NormalController() #1 start button
		joystick.dpads = 1
		joystick.face_buttons = 2
		metadata.input_info.add_option(joystick)
	elif usage == 'Requires Hex Keypad':
		hex_keypad = input_metadata.Keypad()
		hex_keypad.keys = 20
		metadata.input_info.add_option(hex_keypad)
	elif usage in {'Requires ASCII Keyboard', 'Requires ASCII Keyboard: A=Up, Z=Down, <=Left, >=Right'}:
		keyboard = input_metadata.Keyboard()
		keyboard.keys = 62
		metadata.input_info.add_option(keyboard)
	else:
		metadata.add_notes(usage)

def add_pc_engine_cd_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
	usage = software.get_info('usage')
	if usage not in ('Game Express CD Card required', 'CD-Rom System Card required'):
		#This is already specified by "requirement"
		metadata.add_notes(usage)
	
def add_amstrad_pcw_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'Requires CP/M':
		metadata.specific_info['Requires CP/M?'] = True

_requires_ram_regex = re.compile(r'Requires (\d+) MB of RAM')
def add_fm_towns_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage:
		match = _requires_ram_regex.match(usage)
		if match:
			metadata.specific_info['Minimum RAM'] = match[1]
			if match.end() < len(usage):
				metadata.add_notes(usage)

def add_sord_m5_software_info(software: 'Software', metadata: 'Metadata'):
	#Input info if I cared: 55 key keyboard + 0 button joystick
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage == 'Requires 36k RAM':
		metadata.specific_info['Minimum RAM'] = '36K'
	else:
		metadata.add_notes(usage)
	
def add_msx_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	usage = software.get_info('usage')
	if usage in {'Requires a Japanese system', 'Requires a Japanese system for the Japanese text'}:
		metadata.specific_info['Japanese Only?'] = True
	elif usage in {'Requires an Arabic MSX', 'Requires an Arabic MSX2'}:
		metadata.specific_info['Arabic Only?'] = True
	else:
		metadata.add_notes(usage)
	if 'cart' in software.parts:
		cart_part = software.get_part('cart')
		metadata.specific_info['Slot'] = cart_part.get_feature('slot')
		metadata.specific_info['PCB'] = cart_part.get_feature('pcb')
		metadata.specific_info['Mapper'] = cart_part.get_feature('mapper')

def add_sg1000_software_info(software: 'Software', metadata: 'Metadata'):
	metadata.save_type = SaveType.Nothing #Until proven otherwise

	software.add_standard_metadata(metadata)
	uses_tablet = software.get_part_feature('peripheral') == 'tablet'
	#There doesn't seem to be a way to know if software is a SC-3000 cart, unless I just say whichever one has the .sc extension. So I'll do that

	if uses_tablet:
		#A drawing tablet, but that's more or less a touchscreen
		#No buttons here?
		metadata.input_info.add_option(input_metadata.Touchscreen())
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2
		normal_controller.dpads = 1
		metadata.input_info.add_option(normal_controller)
	
def add_virtual_boy_software_info(software: 'Software', metadata: 'Metadata'):
	add_generic_software_info(software, metadata)
	
	#We won't need to get serial here I guess
	has_save_hardware = software.has_data_area('eeprom') or software.has_data_area('sram') or software.get_part_feature('battery')
	#I am making assumptions about how saving works and I could be wrong
	metadata.save_type = SaveType.Cart if has_save_hardware else SaveType.Nothing

def add_atari_5200_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	uses_trackball = software.get_part_feature('peripheral') == 'trackball'

	metadata.save_type = SaveType.Nothing #Probably

	#This doesn't really matter anyway, because MAME doesn't let you select controller type by slot device yet; and none of the other 5200 emulators are cool
	metadata.specific_info['Uses Trackball?'] = uses_trackball

	if uses_trackball:
		metadata.input_info.add_option(input_metadata.Trackball())
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2 #1, 2, (Pause, Reset, Start) I think? I think it works the same way for trackballs
		normal_controller.analog_sticks = 1
		metadata.input_info.add_option(normal_controller)

def add_intellivision_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)

	usage = software.get_info('usage')
	if usage == 'Uses Intellivoice':
		metadata.specific_info['Uses Intellivoice?'] = True
	elif usage in {'Requires ECS and Keyboard', 'Requires ECS and Intellivoice'}:
		#Both of these are functionally the same for our intent and purpose, as MAME's intvecs driver always has a keyboard and Intellivoice module. I dunno if an Intellivision ECS without a keyboard is even a thing.
		metadata.specific_info['Uses ECS?'] = True

	#Other usage notes:
	#Will not run on Intellivision 2
	#This cart has unique Left and Right overlays
	#Requires ECS and Music Synthesizer

	#We don't have any reason to use the intv2 driver so that's not a worry; overlays aren't really a concern either, and I dunno about this music synthesizer thing
