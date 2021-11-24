import json
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast
from xml.etree import ElementTree

from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.common.engine_detect import \
    try_and_detect_engine_from_folder
from meowlauncher.games.roms.rom import FolderROM

from .common.gametdb import TDB, add_info_from_tdb
from .common.playstation_common import parse_param_sfo, parse_product_code

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

def _load_tdb() -> Optional[TDB]:
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
_tdb = _load_tdb()

def add_game_folder_metadata(rom: FolderROM, metadata: 'Metadata'):
	param_sfo_path = rom.relevant_files['PARAM.SFO']
	usrdir = rom.relevant_files['USRDIR']

	subfolder = param_sfo_path.parent
	icon0_path = subfolder / 'ICON0.PNG'
	if icon0_path.is_file():
		metadata.images['Banner'] = icon0_path
	icon1_path = subfolder / 'ICON1.PNG'
	if icon1_path.is_file():
		metadata.images['Icon 1'] = icon1_path
	pic0_path = subfolder / 'PIC0.PNG'
	if pic0_path.is_file():
		metadata.images['Overlay Image'] = pic0_path
	pic1_path = subfolder / 'PIC1.PNG'
	pic2_path = subfolder / 'PIC2.PNG'
	if pic1_path.is_file():
		metadata.images['Background Image'] = pic1_path
	elif pic2_path.is_file():
		#For 4:3 instead of 16:9?
		metadata.images['Background Image'] = pic2_path
	
	if subfolder.joinpath('TROPDIR').is_dir():
		metadata.specific_info['Has Achievements?'] = True

	if usrdir.is_dir():
		engine = try_and_detect_engine_from_folder(usrdir, metadata)
		if engine:
			metadata.specific_info['Engine'] = engine
		#EXE name should be EBOOT.BIN in here?
	elif main_config.debug:
		print('How interesting!', rom.path, 'has no USRDIR')

	with param_sfo_path.open('rb') as f:
		parse_param_sfo(str(rom.path), metadata, f.read())

	is_installed_to_rpcs3_hdd = rom.path.parent == Path('~/.config/rpcs3/dev_hdd0/game').expanduser()
	#Messy hack time
	if is_installed_to_rpcs3_hdd and metadata.names:
		#If we found a banner title, etc then use that instead
		rom.ignore_name = True
	if metadata.product_code == rom.name:
		rom.ignore_name = True
		#Internal to some game folder, but if it is on the RPCS3 hard drive then it is just in a folder called "game" under "dev_hdd0" which contains no useful information
		if not is_installed_to_rpcs3_hdd:
			metadata.add_alternate_name(rom.path.parent.name, 'Name')
		
class RPCS3Compatibility(Enum):
	Loadable = 1
	Intro = 2
	Ingame = 3
	Playable = 4
	#There is no perfect? Not yet comfy saying anything is I guess

def get_rpcs3_compat(product_code: str) -> Optional[RPCS3Compatibility]:
	compat_db_path = Path('~/.config/rpcs3/GuiConfigs/compat_database.dat').expanduser()
	if hasattr(get_rpcs3_compat, 'db'):
		db = get_rpcs3_compat.db #type: ignore[attr-defined]
	else:
		try:
			with compat_db_path.open('rb') as f:
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
	
def add_cover(metadata: 'Metadata', product_code: str):
	#Intended for the covers database from GameTDB
	try:
		covers_path = platform_configs['PS3'].options['covers_path']
	except KeyError:
		return
	if not covers_path:
		return
	cover_path = covers_path.joinpath(product_code)
	for ext in ('png', 'jpg'):
		potential_cover_path = cover_path.with_suffix(os.extsep + ext)
		if potential_cover_path.is_file():
			metadata.images['Cover'] = potential_cover_path
			break

def add_ps3_custom_info(game: 'ROMGame'):
	if game.rom.is_folder:
		add_game_folder_metadata(cast(FolderROM, game.rom), game.metadata)

	if game.metadata.product_code:
		parse_product_code(game.metadata, game.metadata.product_code)
		compat = get_rpcs3_compat(game.metadata.product_code)
		if compat:
			game.metadata.specific_info['RPCS3 Compatibility'] = compat

		add_info_from_tdb(_tdb, game.metadata, game.metadata.product_code)
		add_cover(game.metadata, game.metadata.product_code)
