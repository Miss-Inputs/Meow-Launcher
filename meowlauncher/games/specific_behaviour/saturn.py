import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, cast

from meowlauncher import input_info
from meowlauncher.common_types import SaveType
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.info import Date
from meowlauncher.platform_types import SaturnRegionCodes
from meowlauncher.util.cd_read import get_first_data_cue_track, read_mode_1_cd
from meowlauncher.util.utils import load_dict

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

_licensee_codes = load_dict(None, 'sega_licensee_codes')

class SaturnPeripheral(Enum):
	StandardController = auto()
	AnalogController = auto() #Or "3D Control Pad" if you prefer
	LightGun = auto()
	Keyboard = auto()
	Mouse = auto()
	Wheel = auto()

_standard_controller = input_info.NormalController()
_standard_controller.face_buttons = 6 # A B C X Y Z #yeah I had to count them because I have 0 brain cells sorry
_standard_controller.shoulder_buttons = 2 #L R
_standard_controller.dpads = 1

_analog_controller = input_info.NormalController()
_analog_controller.face_buttons = 6 # A B C X Y Z
_analog_controller.analog_triggers = 2
_analog_controller.analog_sticks = 1
_analog_controller.dpads = 1

_mission_stick_main_part = input_info.NormalController()
_mission_stick_main_part.analog_sticks = 1
_mission_stick_main_part.face_buttons = 10 #The usual + L and R are located there instead of what would be considered a shoulder button, plus 2 extra on the stick
_throttle_wheel = input_info.Dial()
_mission_stick = input_info.CombinedController([_mission_stick_main_part, _throttle_wheel])

_virtua_gun = input_info.LightGun()
_virtua_gun.buttons = 1 #Also start and I dunno if offscreen shot would count as a button

_keyboard = input_info.Keyboard()
_keyboard.keys = 101
#Japan keyboard has 89 keys... bleh, it doesn't seem to say which keyboard it refers to

_mouse = input_info.Mouse()
_mouse.buttons = 3

def _parse_peripherals(game_info: 'GameInfo', peripherals: str, rom_path_for_warning: Any=None) -> None:
	for peripheral in peripherals:
		if peripheral == 'J':
			game_info.input_info.add_option(_standard_controller)
		elif peripheral == 'E':
			game_info.input_info.add_option(_analog_controller)
			game_info.specific_info['Uses 3D Control Pad?'] = True
		elif peripheral == 'A':
			game_info.input_info.add_option(_mission_stick)
			game_info.specific_info['Uses Mission Stick?'] = True
		elif peripheral == 'G':
			game_info.input_info.add_option(_virtua_gun)
			game_info.specific_info['Uses Gun?'] = True
		elif peripheral == 'K':
			game_info.input_info.add_option(_keyboard)
			game_info.specific_info['Uses Keyboard?'] = True
		elif peripheral == 'M':
			game_info.input_info.add_option(_mouse)
			game_info.specific_info['Uses Mouse?'] = True
		elif peripheral == 'S':
			game_info.input_info.add_option(input_info.SteeringWheel())
			game_info.specific_info['Uses Steering Wheel?'] = True
		elif peripheral == 'T':
			game_info.specific_info['Supports Multitap?'] = True
		elif peripheral == 'F':
			#Hmm... it might be possible that a game saves to both floppy and backup RAM etc
			game_info.save_type = SaveType.Floppy
		elif peripheral == 'W':
			#Doesn't specify if it needs 1MB or 4MB... some games (e.g. KOF 96) supposedly only do 1MB
			game_info.specific_info['Requires RAM Cartridge?'] = True
		elif peripheral == 'Y':
			game_info.specific_info['Uses MIDI?'] = True
			#TODO Input info for the MIDI keyboard
		elif peripheral == 'Q':
			game_info.specific_info['Uses Pachinko Controller?'] = True
			#TODO Input info (known as Sankyo FF, but I can't find anything about what it actually does other than it exists)
		elif peripheral == 'R':
			game_info.specific_info['Uses ROM Cartridge?'] = True
			#KoF 95 and Ultraman: Hikari no Kyojin Densetsu, although they aren't interchangable, they both use the same peripheral code here
		else:
			logger.debug('Unknown Saturn peripheral %s in %s', peripheral, rom_path_for_warning)
		#D = Modem? (Anywhere X is but also SegaSaturn Internet)
		#X = Duke Nukem 3D, Daytona CCE Net Link Edition, Puyo Puyo Sun for SegaNet (something to do with NetLink, but what is the difference with D?)
		#U = Sonic Z-Treme?
		#Z = Game Basic for SegaSaturn (PC connectivity?)

def add_saturn_info(rom_path_for_warning: Any, game_info: 'GameInfo', header: bytes) -> None:
	hardware_id = header[0:16]
	if hardware_id != b'SEGA SEGASATURN ':
		#Won't boot on a real Saturn, also if this is some emulator only thing then nothing in the header can be considered valid
		game_info.specific_info['Hardware ID'] = hardware_id.decode('ascii', 'backslashreplace')
		game_info.specific_info['Invalid Hardware ID?'] = True
		return

	maker = header[16:32].rstrip(b' ').decode('ascii', 'backslashreplace')
	if maker.startswith('SEGA TP '):
		#"Sega Third Party", I guess
		maker_code = maker.removeprefix('SEGA TP ')
		if maker_code.startswith('T '):
			#You're not supposed to do that, stop that
			maker_code = 'T-' + maker_code[2:]
		game_info.publisher = _licensee_codes.get(maker_code, maker)
	elif maker == 'SEGA ENTERPRISES':
		game_info.publisher = 'Sega'
	else:
		game_info.publisher = maker
	
	game_info.product_code = header[32:42].rstrip(b' ').decode('ascii', 'backslashreplace')
	
	try:
		version = header[42:48].rstrip(b' ').decode('ascii')
		if version[0] == 'V' and version[2] == '.':
			game_info.specific_info['Version'] = 'v' + version[1:]
	except UnicodeDecodeError:
		pass

	release_date = header[48:56].rstrip(b' ').decode('ascii', 'backslashreplace')
	if not release_date.startswith('0') and '-' not in release_date:
		#If it starts with 0 the date format is WRONG stop it because I know the Saturn wasn't invented yet before 1000 AD
		#Also sometimes it's formatted with dashes which means there are 2 bytes that shouldn't be there and are technically part of device info? Weird
		try:
			year = release_date[0:4]
			month = release_date[4:6]
			day = release_date[6:8]
			game_info.specific_info['Header Date'] = Date(year, month, day)
			guessed = Date(year, month, day, True)
			if guessed.is_better_than(game_info.release_date):
				game_info.release_date = guessed
		except IndexError:
			logger.info('%s has invalid date in header: %s', rom_path_for_warning, release_date)
		except ValueError:
			pass

	
	try:
		device_info = header[56:64].rstrip(b' ').decode('ascii')
	except UnicodeDecodeError:
		pass
	else:
		if device_info.startswith('CD-'):
			#CART16M is seen here instead of "CD-1/1" on some protos?
			disc_number, _, disc_total = device_info[3:].partition('/')
			try:
				game_info.disc_number = int(disc_number)
				game_info.disc_total = int(disc_total)
			except ValueError:
				pass

	region_info = header[64:80].rstrip()
	#Only 10 characters are used
	region_codes = set()
	if b'J' in region_info:
		region_codes.add(SaturnRegionCodes.Japan)
	if b'U' in region_info:
		region_codes.add(SaturnRegionCodes.USA)
	if b'E' in region_info:
		region_codes.add(SaturnRegionCodes.Europe)

	#Some other region codes appear sometimes, but I haven't been able to verify _exactly_ what they are, and I don't really wanna make guesses
	#T = Taiwan?
	#K = Korea?
	#B = Brazil?
	#A and L seen on some homebrews and devkits?

	game_info.specific_info['Region Code'] = region_codes

	peripherals = header[80:96].rstrip(b' ').decode('ascii', errors='backslashreplace')
	_parse_peripherals(game_info, peripherals, rom_path_for_warning)

	internal_name = header[96:208].rstrip(b' ').decode('ascii', errors='backslashreplace')
	#Sometimes / : - are used as delimiters, and there can also be J:JapaneseNameU:USAName
	if internal_name:
		game_info.specific_info['Internal Title'] = internal_name

def add_saturn_custom_info(game: 'ROMGame') -> None:
	if game.rom.extension == 'cue':
		first_track_and_sector_size = get_first_data_cue_track(game.rom.path)
		if not first_track_and_sector_size:
			logger.info('%s has invalid cuesheet', game.rom)
			return
		first_track, sector_size = first_track_and_sector_size

		if not first_track.is_file():
			logger.warning('%s has cuesheet with track %s not found', game.rom, first_track)
			return
		try:
			header = read_mode_1_cd(first_track, sector_size, seek_to=0, amount=256)
		except NotImplementedError:
			return
	elif game.rom.extension == 'ccd':
		img_file = game.rom.path.with_suffix('.img')
		#I thiiiiiiiiink .ccd/.img always has 2352-byte sectors?
		try:
			header = read_mode_1_cd(img_file, 2352, seek_to=0, amount=256)
		except NotImplementedError:
			return
	elif game.rom.extension == 'iso':
		header = cast(FileROM, game.rom).read(seek_to=0, amount=256)
	else:
		return

	add_saturn_info(str(game.rom), game.info, header)

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.info)
	except NotImplementedError:
		pass
