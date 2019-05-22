from enum import Enum, auto

from config import main_config
from mame_helpers import consistentify_manufacturer
from info.region_info import get_language_by_english_name
from software_list_info import get_software_list_entry

class AppleIIHardware(Enum):
	AppleII = auto()
	AppleIIPlus = auto()
	AppleIIE = auto()
	AppleIIC = auto()
	AppleIIEEnhanced = auto()
	AppleIIgs = auto()
	AppleIICPlus = auto()
	AppleIII = auto()
	AppleIIIPlus = auto()

def parse_woz_info_chunk(game, chunk_data):
	info_version = chunk_data[0]
	#1: Disk type = 5.25" if 1 else 3.25 if 2
	#2: 1 if write protected
	if info_version == 2:
		compatible_hardware = int.from_bytes(chunk_data[40:42], 'little')
		if compatible_hardware:
			machines = []
			if compatible_hardware & 1:
				machines.append(AppleIIHardware.AppleII)
			if compatible_hardware & 2:
				machines.append(AppleIIHardware.AppleIIPlus)
			if compatible_hardware & 4:
				machines.append(AppleIIHardware.AppleIIE)
			if compatible_hardware & 8:
				machines.append(AppleIIHardware.AppleIIC)
			if compatible_hardware & 16:
				machines.append(AppleIIHardware.AppleIIEEnhanced)
			if compatible_hardware & 32:
				machines.append(AppleIIHardware.AppleIIgs)
			if compatible_hardware & 64:
				machines.append(AppleIIHardware.AppleIICPlus)
			if compatible_hardware & 128:
				machines.append(AppleIIHardware.AppleIII)
			if compatible_hardware & 256:
				machines.append(AppleIIHardware.AppleIIIPlus)
			game.metadata.specific_info['Machine'] = machines
		minimum_ram = int.from_bytes(chunk_data[42:44], 'little')
		if minimum_ram:
			game.metadata.specific_info['Minimum-RAM'] = minimum_ram

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

def parse_woz_meta_chunk(game, chunk_data):
	rows = chunk_data.split(b'\x0a')
	for row in rows:
		try:
			key, value = row.decode('utf-8').split('\t', maxsplit=1)
		except ValueError: #Oh I guess this includes UnicodeDecodeError
			continue

		if key in ('version', 'side', 'side_name', 'contributor', 'image_date', 'collection'):
			#No use for these
			#"collection" is not part of the spec but it shows up and it just says where the image came from
			pass
		elif key == 'title':
			game.metadata.specific_info['Title'] = value
		elif key == 'subtitle':
			game.metadata.specific_info['Subtitle'] = value
		elif key == 'requires_machine':
			if game.metadata.specific_info.get('Machine'):
				#Trust the info from the INFO chunk more if it exists
				continue
			machines = []
			for machine in value.split('|'):
				if machine in woz_meta_machines:
					machines.append(woz_meta_machines[machine])
				else:
					print('Unknown compatible machine in Woz META chunk', game.rom.path, machine)
			game.metadata.specific_info['Machine'] = machines
		elif key == 'requires_ram':
			#Should be in INFO chunk, but sometimes isn't
			if value[-1].lower() == 'k':
				value = value[:-1]
			try:
				game.metadata.specific_info['Minimum-RAM'] = int(value)
			except ValueError:
				pass
		elif key == 'publisher':
			game.metadata.publisher = consistentify_manufacturer(value)
		elif key == 'developer':
			game.metadata.developer = consistentify_manufacturer(value)
		elif key == 'copyright':
			#TODO: Catch values like "1989 Cool Corporation"
			try:
				game.metadata.year = int(value)
			except ValueError:
				pass
		elif key == 'language':
			game.metadata.languages = []
			for lang in value.split('|'):
				language = get_language_by_english_name(lang)
				if language:
					game.metadata.languages.append(language)
		elif key == 'genre':
			#This isn't part of the specification, but I've seen it
			if value == 'rpg':
				game.metadata.genre = 'RPG'
			else:
				game.metadata.genre = value.capitalize() if value.islower() else value
		elif key == 'notes':
			#This isn't part of the specification, but I've seen it
			game.metadata.notes = value
		else:
			if main_config.debug:
				print('Unknown Woz META key', game.rom.path, key, value)

def parse_woz_chunk(game, position):
	chunk_header = game.rom.read(seek_to=position, amount=8)
	chunk_id = chunk_header[0:4].decode('ascii', errors='ignore')
	chunk_data_size = int.from_bytes(chunk_header[4:8], 'little')

	if chunk_id == 'INFO':
		chunk_data = game.rom.read(seek_to=position+8, amount=chunk_data_size)
		parse_woz_info_chunk(game, chunk_data)
	elif chunk_id == 'META':
		chunk_data = game.rom.read(seek_to=position+8, amount=chunk_data_size)
		parse_woz_meta_chunk(game, chunk_data)

	return position + chunk_data_size + 8

def add_woz_metadata(game):
	#https://applesaucefdc.com/woz/reference1/
	#https://applesaucefdc.com/woz/reference2/
	magic = game.rom.read(amount=8)
	if magic == b'WOZ1\xff\n\r\n':
		game.metadata.specific_info['ROM-Format'] = 'WOZ v1'
	elif magic == b'WOZ2\xff\n\r\n':
		game.metadata.specific_info['ROM-Format'] = 'WOZ v2'
	else:
		print(game.rom.path, magic)
		return

	position = 12
	size = game.rom.get_size()
	while position:
		position = parse_woz_chunk(game, position)
		if position >= size:
			break

def add_apple_ii_metadata(game):
	if game.metadata.extension == 'woz':
		add_woz_metadata(game)

	#Possible input info: Keyboard and joystick by default, mouse if mouse card exists

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		usage = software.get_info('usage')
		if usage == 'Works with Apple II Mouse Card in slot 4: -sl4 mouse':
			#Not setting up input_info just yet because I don't know if it uses joystick/keyboard as well. I guess I probably never will, but like... well.... dang
			game.metadata.specific_info['Uses-Mouse'] = True
		elif usage:
			if game.metadata.notes:
				game.metadata.notes += ';' + usage
			else:
				game.metadata.notes = usage

		if not game.metadata.specific_info.get('Machine'):
			compat = software.get_shared_feature('compatibility')
			if compat:
				machines = []
				for machine in compat.split(','):
					if machine == 'A2':
						machines.append(AppleIIHardware.AppleII)
					if machine == 'A2P':
						machines.append(AppleIIHardware.AppleIIPlus)
					if machine == 'A2E':
						machines.append(AppleIIHardware.AppleIIE)
					if machine == 'A2EE':
						machines.append(AppleIIHardware.AppleIIEEnhanced)
					if machine == 'A2C':
						machines.append(AppleIIHardware.AppleIIC)
					if machine == 'A2GS':
						machines.append(AppleIIHardware.AppleIIgs)
					#Apple IIc+ doesn't show up in this list so far
				game.metadata.specific_info['Machine'] = machines
