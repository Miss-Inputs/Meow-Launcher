from enum import Enum, auto
from typing import TYPE_CHECKING, cast

from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.metadata import Date
from meowlauncher.platform_types import SaturnRegionCodes
from meowlauncher.util.cd_read import get_first_data_cue_track, read_mode_1_cd
from meowlauncher.util.utils import load_dict

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

_licensee_codes = load_dict(None, 'sega_licensee_codes')

class SaturnPeripheral(Enum):
	StandardController = auto()
	AnalogController = auto() #Or "3D Control Pad" if you prefer
	LightGun = auto()
	Keyboard = auto()
	Mouse = auto()
	Wheel = auto()

_standard_controller = input_metadata.NormalController()
_standard_controller.face_buttons = 6 # A B C X Y Z #yeah I had to count them because I have 0 brain cells sorry
_standard_controller.shoulder_buttons = 2 #L R
_standard_controller.dpads = 1

_analog_controller = input_metadata.NormalController()
_analog_controller.face_buttons = 6 # A B C X Y Z
_analog_controller.analog_triggers = 2
_analog_controller.analog_sticks = 1
_analog_controller.dpads = 1

_mission_stick_main_part = input_metadata.NormalController()
_mission_stick_main_part.analog_sticks = 1
_mission_stick_main_part.face_buttons = 10 #The usual + L and R are located there instead of what would be considered a shoulder button, plus 2 extra on the stick
_throttle_wheel = input_metadata.Dial()
_mission_stick = input_metadata.CombinedController([_mission_stick_main_part, _throttle_wheel])

_virtua_gun = input_metadata.LightGun()
_virtua_gun.buttons = 1 #Also start and I dunno if offscreen shot would count as a button

_keyboard = input_metadata.Keyboard()
_keyboard.keys = 101
#Japan keyboard has 89 keys... bleh, it doesn't seem to say which keyboard it refers to

_mouse = input_metadata.Mouse()
_mouse.buttons = 3

def _parse_peripherals(metadata: 'Metadata', peripherals: str) -> None:
	for peripheral in peripherals:
		if peripheral == 'J':
			metadata.input_info.add_option(_standard_controller)
		elif peripheral == 'E':
			metadata.input_info.add_option(_analog_controller)
			metadata.specific_info['Uses 3D Control Pad?'] = True
		elif peripheral == 'A':
			metadata.input_info.add_option(_mission_stick)
			metadata.specific_info['Uses Mission Stick?'] = True
		elif peripheral == 'G':
			metadata.input_info.add_option(_virtua_gun)
			metadata.specific_info['Uses Gun?'] = True
		elif peripheral == 'K':
			metadata.input_info.add_option(_keyboard)
			metadata.specific_info['Uses Keyboard?'] = True
		elif peripheral == 'M':
			metadata.input_info.add_option(_mouse)
			metadata.specific_info['Uses Mouse?'] = True
		elif peripheral == 'S':
			metadata.input_info.add_option(input_metadata.SteeringWheel())
			metadata.specific_info['Uses Steering Wheel?'] = True
		elif peripheral == 'T':
			metadata.specific_info['Supports Multitap?'] = True
		elif peripheral == 'F':
			#Hmm... it might be possible that a game saves to both floppy and backup RAM etc
			metadata.save_type = SaveType.Floppy
		elif peripheral == 'W':
			#Doesn't specify if it needs 1MB or 4MB... some games (e.g. KOF 96) supposedly only do 1MB
			metadata.specific_info['Requires RAM Cartridge?'] = True
		elif peripheral == 'Y':
			metadata.specific_info['Uses MIDI?'] = True
			#TODO Input info for the MIDI keyboard
		elif peripheral == 'Q':
			metadata.specific_info['Uses Pachinko Controller?'] = True
			#TODO Input info (known as Sankyo FF, but I can't find anything about what it actually does other than it exists)
		elif peripheral == 'R':
			metadata.specific_info['Uses ROM Cartridge?'] = True
			#KoF 95 and Ultraman: Hikari no Kyojin Densetsu, although they aren't interchangable, they both use the same peripheral code here
		#else:
		#	print('Unknown Saturn peripheral', game.rom.path, peripheral)
		#D = Modem? (Anywhere X is but also SegaSaturn Internet)
		#X = Duke Nukem 3D, Daytona CCE Net Link Edition, Puyo Puyo Sun for SegaNet (something to do with NetLink, but what is the difference with D?)
		#U = Sonic Z-Treme?
		#Z = Game Basic for SegaSaturn (PC connectivity?)

def add_saturn_info(rom_path_for_warning: str, metadata: 'Metadata', header: bytes) -> None:
	hardware_id = header[0:16].decode('ascii', errors='ignore')
	if hardware_id != 'SEGA SEGASATURN ':
		#Won't boot on a real Saturn, also if this is some emulator only thing then nothing in the header can be considered valid
		metadata.specific_info['Hardware ID'] = hardware_id
		metadata.specific_info['Invalid Hardware ID?'] = True
		return

	try:
		maker = header[16:32].decode('ascii').rstrip()
		if maker.startswith('SEGA TP '):
			#"Sega Third Party", I guess
			maker_code = maker.removeprefix('SEGA TP ')
			if maker_code.startswith('T '):
				#You're not supposed to do that, stop that
				maker_code = 'T-' + maker_code[2:]
			if maker_code in _licensee_codes:
				metadata.publisher = _licensee_codes[maker_code]
		elif maker == 'SEGA ENTERPRISES':
			metadata.publisher = 'Sega'
		else:
			metadata.publisher = maker
	except UnicodeDecodeError:
		pass

	try:
		metadata.product_code = header[32:42].decode('ascii').rstrip()
	except UnicodeDecodeError:
		pass

	try:
		version = header[42:48].decode('ascii').rstrip()
		if version[0] == 'V' and version[2] == '.':
			metadata.specific_info['Version'] = 'v' + version[1:]
	except UnicodeDecodeError:
		pass

	release_date = header[48:56].decode('ascii', errors='backslashreplace').rstrip()

	if not release_date.startswith('0') and '-' not in release_date:
		#If it starts with 0 the date format is WRONG stop it because I know the Saturn wasn't invented yet before 1000 AD
		#Also sometimes it's formatted with dashes which means there are 2 bytes that shouldn't be there and are technically part of device info? Weird
		try:
			year = release_date[0:4]
			month = release_date[4:6]
			day = release_date[6:8]
			metadata.specific_info['Header Date'] = Date(year, month, day)
			guessed = Date(year, month, day, True)
			if guessed.is_better_than(metadata.release_date):
				metadata.release_date = guessed
		except IndexError:
			if main_config.debug:
				print(rom_path_for_warning, 'has invalid date in header:', release_date)
		except ValueError:
			pass

	device_info = header[56:64].decode('ascii', errors='ignore').rstrip()
	if device_info.startswith('CD-'):
		#CART16M is seen here instead of "CD-1/1" on some protos?
		disc_number, _, disc_total = device_info[3:].partition('/')
		try:
			metadata.disc_number = int(disc_number)
			metadata.disc_total = int(disc_total)
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

	metadata.specific_info['Region Code'] = region_codes

	peripherals = header[80:96].decode('ascii', errors='backslashreplace').rstrip()
	_parse_peripherals(metadata, peripherals)

	internal_name = header[96:208].decode('ascii', errors='backslashreplace').rstrip()
	#Sometimes / : - are used as delimiters, and there can also be J:JapaneseNameU:USAName
	if internal_name:
		metadata.specific_info['Internal Title'] = internal_name

def add_saturn_custom_info(game: 'ROMGame') -> None:
	if game.rom.extension == 'cue':
		first_track_and_sector_size = get_first_data_cue_track(game.rom.path)
		if not first_track_and_sector_size:
			print(game.rom.path, 'has invalid cuesheet')
			return
		first_track, sector_size = first_track_and_sector_size

		if not first_track.is_file():
			print(game.rom.path, 'has invalid cuesheet')
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

	add_saturn_info(str(game.rom.path), game.metadata, header)

	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass
