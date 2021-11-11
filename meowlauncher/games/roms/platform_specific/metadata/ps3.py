import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional, cast
from xml.etree import ElementTree

from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.pc_common_metadata import \
    try_and_detect_engine_from_folder
from meowlauncher.games.roms.rom import FolderROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Metadata

from .common.gametdb import TDB, add_info_from_tdb
from .common.playstation_common import parse_param_sfo, parse_product_code


def load_tdb() -> Optional[TDB]:
	if 'PS3' not in platform_configs:
		return None

	tdb_path = platform_configs['PS3'].options.get('tdb_path')
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError) as blorp:
		if main_config.debug:
			print('Oh no failed to load PS3 TDB because', blorp)
		return None
tdb = load_tdb()

def add_game_folder_metadata(rom: FolderROM, metadata: Metadata):
	ps3game_subfolder = rom.get_subfolder('PS3_GAME')
	param_sfo_path: Optional[Path]
	if ps3game_subfolder:
		param_sfo_path = rom.path.joinpath('PS3_GAME', 'PARAM.SFO')
		icon0_path = rom.path.joinpath('PS3_GAME', 'ICON0.PNG')
		if os.path.isfile(icon0_path):
			metadata.images['Banner'] = icon0_path
		icon1_path = rom.path.joinpath('PS3_GAME', 'ICON1.PNG')
		if os.path.isfile(icon1_path):
			metadata.images['Icon-1'] = icon1_path
		pic0_path = rom.path.joinpath('PS3_GAME', 'PIC0.PNG')
		if os.path.isfile(pic0_path):
			metadata.images['Overlay-Image'] = pic0_path
		pic1_path = rom.path.joinpath('PS3_GAME', 'PIC1.PNG')
		if os.path.isfile(pic1_path):
			metadata.images['Background-Image'] = pic1_path
		#PIC2.PNG is for 4:3 instead of 16:9 go away nerds
		if rom.path.joinpath('PS3_GAME', 'TROPDIR').is_dir():
			metadata.specific_info['Supports-Trophies'] = True
		usrdir = ps3game_subfolder.joinpath('USRDIR')
		if usrdir.is_dir(): #Should always be there but who knows
			engine = try_and_detect_engine_from_folder(str(usrdir), metadata)
			if engine:
				metadata.specific_info['Engine'] = engine
	else:
		param_sfo_path = rom.get_file('PARAM.SFO')
		metadata.images['Banner'] = rom.get_file('ICON0.PNG', True)
		metadata.images['Icon-1'] = rom.get_file('ICON1.PNG', True)
		metadata.images['Overlay-Image'] = rom.get_file('PIC0.PNG', True)
		metadata.images['Background-Image'] = rom.get_file('PIC1.PNG', True)
		if rom.has_subfolder('TROPDIR'):
			metadata.specific_info['Supports-Trophies'] = True
		engine = try_and_detect_engine_from_folder(rom.get_subfolder('USRDIR'), metadata)
		if engine:
			metadata.specific_info['Engine'] = engine

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
		
class RPCS3Compatibility(Enum):
	Loadable = 1
	Intro = 2
	Ingame = 3
	Playable = 4

def get_rpcs3_compat(product_code: str) -> Optional[RPCS3Compatibility]:
	compat_db_path = os.path.expanduser('~/.config/rpcs3/GuiConfigs/compat_database.dat')
	if hasattr(get_rpcs3_compat, 'db'):
		db = get_rpcs3_compat.db #type: ignore[attr-defined]
	else:
		try:
			with open(compat_db_path, 'rb') as f:
				db = get_rpcs3_compat.db = json.load(f) #type: ignore[attr-defined]
		except OSError:
			return None
	try:
		game = db['results'][product_code]
		status = game.get('status', 'Unknown')
		
		try:
			return RPCS3Compatibility[status]
		except KeyError:
			pass
	except KeyError:
		pass
	return None
	
def add_cover(metadata: Metadata, product_code: str):
	#Intended for the covers database from GameTDB
	try:
		covers_path = platform_configs['PS3'].options['covers_path']
	except KeyError:
		return
	if not covers_path:
		return
	cover_path = os.path.join(covers_path, product_code)
	for ext in ('png', 'jpg'):
		if os.path.isfile(cover_path + os.extsep + ext):
			metadata.images['Cover'] = cover_path + os.extsep + ext
			break

def add_ps3_metadata(game: ROMGame):
	if game.rom.is_folder:
		add_game_folder_metadata(cast(FolderROM, game.rom), game.metadata)

	if game.metadata.product_code:
		parse_product_code(game.metadata, game.metadata.product_code)
		compat = get_rpcs3_compat(game.metadata.product_code)
		if compat:
			game.metadata.specific_info['RPCS3-Compatibility'] = compat

		add_info_from_tdb(tdb, game.metadata, game.metadata.product_code)
		add_cover(game.metadata, game.metadata.product_code)
