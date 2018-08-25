#For mildly uninteresting systems that I still want to add system info for etc
import zlib

from metadata import PlayerInput, InputType, EmulationStatus, SaveType
from info.region_info import TVSystem
from info.system_info import get_mame_software_list_names_by_system_name
from mame_helpers import get_software_lists_by_names, find_in_software_lists, consistentify_manufacturer

#Not in here for various reasons:
#Atari 5200, Colecovision: Try parsing title screen from ROM first
#Intellivison: .int is actually a custom headered file format I think, so that might be tricky to deal with
#Neo Geo CD, CD-i, PC Engine CD, PC-FX: Not sure how well that would work with disc images, since MAME uses <diskarea> and chds there
#Atari 7800, NES, Master System, Pokemon Mini, Neo Geo Pocket, Vectrex and N64 could make use of software lists, but they have their own modules, and the former two have custom headers and the latter would take 5 hours (especially when 7zipped)
#Uzebox: .uze files have a header, need to get onto those actually
#ZX Spectrum: All +3 software in MAME is in .ipf format, which seems hardly ever used in all honesty

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
	game.metadata.publisher = consistentify_manufacturer(software.findtext('publisher'))
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
	game.metadata.developer = get_software_info(software, 'author')

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

def add_msx_info(game):
	#I'll use this for MSX2 as well for now
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)	
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper

def add_pc88_info(game):
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#TODO: Get the relevant part and get its feature > part_id. Of course, because I'm intelligent and good at forward thinking, I just return the whole software, so now I don't know which part I've just matched, unless I want to re-hash the disk and look for it again.

def add_sg1000_info(game):
	#Input info is mostly just the standard 2-button gamepad, but maybe there was other peripherals?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#There doesn't seem to be a way to know if software is a SC-3000 cart, unless I just say whichever one has the .sc extension. Maybe Uranai Angel Cutie is just compatible anyway? I forgot
		#TOO: Get feature > peripheral = "tablet" in part to get input info

def add_sharp_x1_info(game):
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#TODO: Get the relevant part and get its feature > part_id. Of course, because I'm intelligent and good at forward thinking, I just return the whole software, so now I don't know which part I've just matched, unless I want to re-hash the disk and look for it again.

def add_sharp_x68k_info(game):
	#Many games are known to have SaveType.Floppy, but can't tell programmatically...
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#TODO: Get the relevant part and get its feature > part_id. Of course, because I'm intelligent and good at forward thinking, I just return the whole software, so now I don't know which part I've just matched, unless I want to re-hash the disk and look for it again.

def add_tomy_tutor_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_vc4000_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

#-- Beyond this point, there may be unexplored things which may result in these systems being spun off into their own module. Maybe. It just seems likely.

def add_pce_info(game):
	#Input could be 2 buttons or 6 buttons, usually the former. Might be other types too?
	#Some games should have saving via TurboBooster-Plus (Wii U VC seems to let me save in Neutopia anyway without passwords or savestates), which I guess would be SaveType.Internal
	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#Other info: alt_title, release (that seems to be a date, I'm not sure if it always is though)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_game_com_info(game):
	#Could have its own header. I think it does, but like.. who's gonna document such a thing? The wide community of Game.com enthusiasts?
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #A B C D
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 3 #Menu Sound Pause
	
	#Might have saving, actually. I'm just not sure about how it works.

	software = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#This will tell you that nothing is supported. I think that sometimes the MAME devs are too hard on themselves. Someone needs to cheer them up a bit.
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_lynx_info(game):
	#TODO .lnx files should have a header with something in them, so eventually, Lynx will get its own module here
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 1 #Pause
	#Because of that aforementioned header, we can't really look up software... unless I get off my lazy ass and skip the 128 bytes
