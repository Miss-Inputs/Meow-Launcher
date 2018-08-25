#For mildly uninteresting systems that I still want to add system info for etc
import zlib

from metadata import PlayerInput, InputType, EmulationStatus, SaveType
from info.region_info import TVSystem
from info.system_info import get_mame_software_list_names_by_system_name
from mame_helpers import get_software_lists_by_names, find_in_software_lists

def get_software_list_entry(game):
	software_list_names = get_mame_software_list_names_by_system_name(game.metadata.platform)
	software_lists = get_software_lists_by_names(software_list_names)
	
	crc32 = '{:08x}'.format(zlib.crc32(game.rom.read()))
	return find_in_software_lists(software_lists, crc=crc32)

def get_software_info(software, name):
	for info in software.findall('info'):
		if info.attrib.get('name') == name:
			return info.text

	return None

def add_generic_software_list_info(game, software):
	game.metadata.specific_info['MAME-Software-Name'] = software.attrib.get('name')
	game.metadata.publisher = software.findtext('publisher')
	game.metadata.year = software.findtext('year')
	emulation_status = EmulationStatus.Good
	if 'supported' in software.attrib:
		supported = software.attrib['supported']
		if supported == 'partial':
			emulation_status = EmulationStatus.Imperfect
		elif supported == 'no':
			emulation_status = EmulationStatus.Broken
	game.metadata.specific_info['MAME-Emulation-Status'] = emulation_status
	game.metadata.specific_info['Notes'] = get_software_info(software, 'usage')

def add_entex_adventure_vision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	game.metadata.input_info.players.append(player)

	#I don't think so mate
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_game_pocket_computer_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4
	game.metadata.input_info.players.append(player)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_gamate_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_casio_pv1000_info(game):
	game.metadata.tv_type = TVSystem.NTSC #Japan only. I won't assume the region in case some maniac decides to make homebrew for it or something, but it could only ever be NTSC
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Start, select, A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.players.append(player)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_mega_duck_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
	
def add_watara_supervision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_apfm1000_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#There's not really anything in there which tells us if we need the Imagination Machine for a particular cart. There's something about RAM, though.

def add_arcadia_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#Nothing really here other than alt titles (for other languages). I guess this proves that the Bandai Arcadia really isn't different.

def add_astrocade_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)

def add_casio_pv2000_info(game):
	#Input info is keyboard and joystick I guess? Maybe only one of them sometimes?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_channel_f_info(game):
	#Input info is uhhh that weird twisty thing I guess

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)


def add_lynx_info(game):
	#TODO .lnx files should have a header with something in them, so eventually, Lynx will get its own module here
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 1 #Pause
