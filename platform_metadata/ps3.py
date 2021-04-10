import os
import json
from .playstation_common import parse_param_sfo, parse_product_code

def add_game_folder_metadata(rom, metadata):
	if rom.has_subfolder('PS3_GAME'):
		param_sfo_path = os.path.join(rom.path, 'PS3_GAME', 'PARAM.SFO')
		icon0_path = os.path.join(rom.path, 'PS3_GAME', 'ICON0.PNG')
		if os.path.isfile(icon0_path):
			metadata.images['Banner'] = icon0_path
		icon1_path = os.path.join(rom.path, 'PS3_GAME', 'ICON1.PNG')
		if os.path.isfile(icon1_path):
			metadata.images['Icon-1'] = icon1_path
		pic0_path = os.path.join(rom.path, 'PS3_GAME', 'PIC0.PNG')
		if os.path.isfile(pic0_path):
			metadata.images['Overlay-Image'] = pic0_path
		pic1_path = os.path.join(rom.path, 'PS3_GAME', 'PIC1.PNG')
		if os.path.isfile(pic1_path):
			metadata.images['Background-Image'] = pic1_path
		#PIC2.PNG is for 4:3 instead of 16:9 go away nerds
		if os.path.isdir(os.path.join(rom.path, 'PS3_GAME', 'TROPDIR')):
			metadata.specific_info['Supports-Trophies'] = True
	else:
		param_sfo_path = rom.get_file('PARAM.SFO')
		metadata.images['Banner'] = rom.get_file('ICON0.PNG', True)
		metadata.images['Icon-1'] = rom.get_file('ICON1.PNG', True)
		metadata.images['Overlay-Image'] = rom.get_file('PIC0.PNG', True)
		metadata.images['Background-Image'] = rom.get_file('PIC1.PNG', True)
		if rom.has_subfolder('TROPDIR'):
			metadata.specific_info['Supports-Trophies'] = True

	is_installed_to_rpcs3_hdd = os.path.dirname(rom.path) == os.path.expanduser('~/.config/rpcs3/dev_hdd0/game')
	
	if param_sfo_path:
		with open(param_sfo_path, 'rb') as f:
			parse_param_sfo(rom, metadata, f.read())

	#Messy hack time
	if is_installed_to_rpcs3_hdd and metadata.names:
		rom.ignore_name = True
	if metadata.product_code == rom.name:
		rom.ignore_name = True
		if not is_installed_to_rpcs3_hdd:
			metadata.add_alternate_name(os.path.basename(os.path.dirname(rom.path)), 'Name')
		
def check_rpcs3_compat(metadata):
	compat_db_path = os.path.expanduser('~/.config/rpcs3/GuiConfigs/compat_database.dat')
	if hasattr(check_rpcs3_compat, 'db'):
		db = check_rpcs3_compat.db
	else:
		try:
			with open(compat_db_path, 'rb') as f:
				db = check_rpcs3_compat.db = json.load(f)
		except OSError:
			return
	try:
		game = db['results'][metadata.product_code]
		metadata.specific_info['RPCS3-Compatibility'] = game.get('status', 'Unknown')
	except KeyError:
		return

def add_ps3_metadata(game):
	if game.rom.is_folder:
		add_game_folder_metadata(game.rom, game.metadata)

	if game.metadata.product_code:
		parse_product_code(game.metadata)
		check_rpcs3_compat(game.metadata)
