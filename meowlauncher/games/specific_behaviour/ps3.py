import json
import logging
import os
from collections.abc import Mapping
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from xml.etree import ElementTree

from meowlauncher.games.common.engine_detect import try_and_detect_engine_from_folder
from meowlauncher.games.roms.rom import FolderROM
from meowlauncher.settings.platform_config import platform_configs

from .common.gametdb import TDB, add_info_from_tdb
from .common.playstation_common import parse_param_sfo, parse_product_code

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

def _load_tdb() -> TDB | None:
	if 'PS3' not in platform_configs:
		return None

	tdb_path = cast(Path | None, platform_configs['PS3'].options.get('tdb_path'))
	if not tdb_path:
		return None

	try:
		return TDB(ElementTree.parse(tdb_path))
	except (ElementTree.ParseError, OSError):
		logger.exception('Oh no failed to load PS3 TDB')
		return None
_tdb = _load_tdb()

rpcs3_vfs_config_path = Path('~/.config/rpcs3/vfs.yml').expanduser()

def add_game_folder_info(rom: FolderROM, game_info: 'GameInfo') -> None:
	param_sfo_path = rom.relevant_files['PARAM.SFO']
	usrdir = rom.relevant_files['USRDIR']

	subfolder = param_sfo_path.parent
	icon0_path = subfolder / 'ICON0.PNG'
	if icon0_path.is_file():
		game_info.images['Banner'] = icon0_path
	icon1_path = subfolder / 'ICON1.PNG'
	if icon1_path.is_file():
		game_info.images['Icon 1'] = icon1_path
	pic0_path = subfolder / 'PIC0.PNG'
	if pic0_path.is_file():
		game_info.images['Overlay Image'] = pic0_path
	pic1_path = subfolder / 'PIC1.PNG'
	pic2_path = subfolder / 'PIC2.PNG'
	if pic1_path.is_file():
		game_info.images['Background Image'] = pic1_path
	elif pic2_path.is_file():
		#For 4:3 instead of 16:9?
		game_info.images['Background Image'] = pic2_path
	
	if subfolder.joinpath('TROPDIR').is_dir():
		game_info.specific_info['Has Achievements?'] = True

	if usrdir.is_dir():
		engine = try_and_detect_engine_from_folder(usrdir, game_info)
		if engine:
			game_info.specific_info['Engine'] = engine
		#EXE name should be EBOOT.BIN in here?
	else:
		logger.info('How interesting! %s has no USRDIR', rom)

	parse_param_sfo(rom.path, game_info, param_sfo_path.read_bytes())

	rpcs3_hdd_path = Path('~/.config/rpcs3/dev_hdd0/').expanduser()
	try:
		if rpcs3_vfs_config_path.is_file():
			for line in rpcs3_vfs_config_path.read_text(encoding='utf-8').splitlines():
				if line.startswith('/dev_hdd0/: '):
					rpcs3_hdd_path = Path(line.rstrip().split(': ', 1)[1])
					break
	except OSError:
		pass

	is_installed_to_rpcs3_hdd = rom.path.parent == rpcs3_hdd_path.joinpath('game')
	#Messy hack time
	if is_installed_to_rpcs3_hdd and game_info.names:
		#If we found a banner title, etc then use that instead
		rom.ignore_name = True
	if game_info.product_code == rom.name:
		rom.ignore_name = True
		#Internal to some game folder, but if it is on the RPCS3 hard drive then it is just in a folder called "game" under "dev_hdd0" which contains no useful information
		if not is_installed_to_rpcs3_hdd:
			game_info.add_alternate_name(rom.path.parent.name, 'Name')
		
class RPCS3Compatibility(Enum):
	Loadable = 1
	Intro = 2
	Ingame = 3
	Playable = 4
	#There is no perfect? Not yet comfy saying anything is I guess

@lru_cache(maxsize=1)
def _get_rpcs3_compatibility_db() -> Mapping[str, Any]:
	compat_db_path = Path('~/.config/rpcs3/GuiConfigs/compat_database.dat').expanduser()
	return json.loads(compat_db_path.read_bytes())

def _get_rpcs3_compat(product_code: str) -> RPCS3Compatibility | None:
	"""Looks up this serial in RPCS3's compatibility database, if it is there in the config folder (needs to be downloaded from within RPCS3)"""
	try:
		game = _get_rpcs3_compatibility_db()['results'][product_code]
		status = game.get('status', 'Unknown')
		
		try:
			return RPCS3Compatibility[status]
		except KeyError:
			pass
	except KeyError:
		pass
	return None
	
def add_cover(game_info: 'GameInfo', product_code: str) -> None:
	"""Intended for the covers database from GameTDB"""
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
			game_info.images['Cover'] = potential_cover_path
			break

def add_ps3_custom_info(game: 'ROMGame') -> None:
	if game.rom.is_folder:
		add_game_folder_info(cast(FolderROM, game.rom), game.info)

	if game.info.product_code:
		parse_product_code(game.info, game.info.product_code)
		compat = _get_rpcs3_compat(game.info.product_code)
		if compat:
			game.info.specific_info['RPCS3 Compatibility'] = compat

		add_info_from_tdb(_tdb, game.info, game.info.product_code)
		add_cover(game.info, game.info.product_code)
