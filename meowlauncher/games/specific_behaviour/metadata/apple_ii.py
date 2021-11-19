
from typing import TYPE_CHECKING, cast

from meowlauncher.config.main_config import main_config
from meowlauncher.games.mame_common.mame_utils import \
    consistentify_manufacturer
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.metadata import Date, Metadata
from meowlauncher.platform_types import AppleIIHardware
from meowlauncher.util.region_info import get_language_by_english_name

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame

def parse_woz_info_chunk(metadata: Metadata, chunk_data: bytes):
	info_version = chunk_data[0]
	#1: Disk type = 5.25" if 1 else 3.25 if 2
	#2: 1 if write protected
	if info_version == 2:
		compatible_hardware = int.from_bytes(chunk_data[40:42], 'little')
		if compatible_hardware:
			machines = set()
			if compatible_hardware & 1:
				machines.add(AppleIIHardware.AppleII)
			if compatible_hardware & 2:
				machines.add(AppleIIHardware.AppleIIPlus)
			if compatible_hardware & 4:
				machines.add(AppleIIHardware.AppleIIE)
			if compatible_hardware & 8:
				machines.add(AppleIIHardware.AppleIIC)
			if compatible_hardware & 16:
				machines.add(AppleIIHardware.AppleIIEEnhanced)
			if compatible_hardware & 32:
				machines.add(AppleIIHardware.AppleIIgs)
			if compatible_hardware & 64:
				machines.add(AppleIIHardware.AppleIICPlus)
			if compatible_hardware & 128:
				machines.add(AppleIIHardware.AppleIII)
			if compatible_hardware & 256:
				machines.add(AppleIIHardware.AppleIIIPlus)
			metadata.specific_info['Machine'] = machines
		minimum_ram = int.from_bytes(chunk_data[42:44], 'little')
		if minimum_ram:
			metadata.specific_info['Minimum RAM'] = minimum_ram

woz_meta_machines = {
	'2': AppleIIHardware.AppleII,
	'2+': AppleIIHardware.AppleIIPlus,
	'2e': AppleIIHardware.AppleIIE,
	'2c': AppleIIHardware.AppleIIC,
	'2e+': AppleIIHardware.AppleIIEEnhanced,
	'2gs': AppleIIHardware.AppleIIgs,
	'2c+': AppleIIHardware.AppleIICPlus,
	'3': AppleIIHardware.AppleIII,
	'3+': AppleIIHardware.AppleIIIPlus,
}

def parse_woz_kv(rompath: str, metadata: Metadata, key: str, value: str):
	#rompath is just here for making warnings look better which is a bit silly I think… hm
	if key in {'side', 'side_name', 'contributor', 'image_date', 'collection', 'requires_platform'}:
		#No use for these
		#"collection" is not part of the spec but it shows up and it just says where the image came from
		#requires_platform is not either, it just seems to be "apple2" so far and I don't get it
		return

	if key == 'version':
		#Note that this is free text
		if not value.startswith('v'):
			value = 'v' + value
		metadata.specific_info['Version'] = value
	elif key == 'title':
		metadata.add_alternate_name(value, 'Header Title')
	elif key == 'subtitle':
		metadata.specific_info['Subtitle'] = value
	elif key == 'requires_machine':
		if metadata.specific_info.get('Machine'):
			#Trust the info from the INFO chunk more if it exists
			return
		machines = set()
		for machine in value.split('|'):
			if machine in woz_meta_machines:
				machines.add(woz_meta_machines[machine])
			else:
				print('Unknown compatible machine in Woz META chunk', rompath, machine)
		metadata.specific_info['Machine'] = machines
	elif key == 'requires_ram':
		#Should be in INFO chunk, but sometimes isn't
		if value[-1].lower() == 'k':
			value = value[:-1]
		try:
			metadata.specific_info['Minimum RAM'] = int(value)
		except ValueError:
			pass
	elif key == 'publisher':
		metadata.publisher = consistentify_manufacturer(value)
	elif key == 'developer':
		metadata.developer = consistentify_manufacturer(value)
	elif key == 'copyright':
		metadata.specific_info['Copyright'] = value
		try:
			metadata.release_date = Date(value)
		except ValueError:
			pass
	elif key == 'language':
		#TODO: Proper nested comprehension…
		metadata.languages = {lang for lang in {get_language_by_english_name(lang_name) for lang_name in value.split('|')} if lang}
	elif key == 'genre':
		#This isn't part of the specification, but I've seen it
		if value == 'rpg':
			metadata.genre = 'RPG'
		else:
			metadata.genre = value.capitalize() if value.islower() else value
	elif key == 'notes':
		#This isn't part of the specification, but I've seen it
		metadata.add_notes(value)
	else:
		if main_config.debug:
			print('Unknown Woz META key', rompath, key, value)

def parse_woz_meta_chunk(rompath: str, metadata: Metadata, chunk_data: bytes):
	rows = chunk_data.split(b'\x0a')
	for row in rows:
		try:
			key, value = row.decode('utf-8').split('\t', maxsplit=1)
		except ValueError: #Oh I guess this includes UnicodeDecodeError
			continue

		parse_woz_kv(rompath, metadata, key, value)

def parse_woz_chunk(rom: FileROM, metadata: Metadata, position: int) -> int:
	chunk_header = rom.read(seek_to=position, amount=8)
	chunk_id = chunk_header[0:4].decode('ascii', errors='ignore')
	chunk_data_size = int.from_bytes(chunk_header[4:8], 'little')

	if chunk_id == 'INFO':
		chunk_data = rom.read(seek_to=position+8, amount=chunk_data_size)
		parse_woz_info_chunk(metadata, chunk_data)
	elif chunk_id == 'META':
		chunk_data = rom.read(seek_to=position+8, amount=chunk_data_size)
		parse_woz_meta_chunk(str(rom.path), metadata, chunk_data)

	return position + chunk_data_size + 8

def add_woz_metadata(rom: FileROM, metadata: Metadata):
	#https://applesaucefdc.com/woz/reference1/
	#https://applesaucefdc.com/woz/reference2/
	magic = rom.read(amount=8)
	if magic == b'WOZ1\xff\n\r\n':
		metadata.specific_info['ROM Format'] = 'WOZ v1'
	elif magic == b'WOZ2\xff\n\r\n':
		metadata.specific_info['ROM Format'] = 'WOZ v2'
	else:
		print('Weird .woz magic', rom.path, magic)
		return

	position = 12
	size = rom.get_size()
	while position:
		position = parse_woz_chunk(rom, metadata, position)
		if position >= size:
			break
	if 'Header-Title' in metadata.names and 'Subtitle' in metadata.specific_info:
		metadata.add_alternate_name(metadata.names['Header Title'] + ': ' + metadata.specific_info['Subtitle'], 'Header Title with Subtitle')

def add_apple_ii_metadata(game: 'ROMGame'):
	if game.rom.extension == 'woz':
		add_woz_metadata(cast(FileROM, game.rom), game.metadata)

	#Possible input info: Keyboard and joystick by default, mouse if mouse card exists

	software = game.get_software_list_entry()
	if software:
		software.add_standard_metadata(game.metadata)
		usage = software.get_info('usage')
		if usage == 'Works with Apple II Mouse Card in slot 4: -sl4 mouse':
			#Not setting up input_info just yet because I don't know if it uses joystick/keyboard as well. I guess I probably never will, but like... well.... dang
			game.metadata.specific_info['Uses Mouse?'] = True
		elif usage:
			game.metadata.add_notes(usage)
		
		if software.software_list.name == 'apple2_flop_orig' and software.name == 'arkanoid':
			game.metadata.specific_info['Uses Mouse?'] = True

		if not game.metadata.specific_info.get('Machine'):
			compat = software.compatibility
			if compat:
				machines = set()
				for machine in compat:
					if machine == 'A2':
						machines.add(AppleIIHardware.AppleII)
					if machine == 'A2P':
						machines.add(AppleIIHardware.AppleIIPlus)
					if machine == 'A2E':
						machines.add(AppleIIHardware.AppleIIE)
					if machine == 'A2EE':
						machines.add(AppleIIHardware.AppleIIEEnhanced)
					if machine == 'A2C':
						machines.add(AppleIIHardware.AppleIIC)
					if machine == 'A2GS':
						machines.add(AppleIIHardware.AppleIIgs)
					#Apple IIc+ doesn't show up in this list so far
				game.metadata.specific_info['Machine'] = machines
