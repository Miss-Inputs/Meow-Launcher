import json
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.util.region_info import get_language_by_english_name

if TYPE_CHECKING:
	from collections.abc import Mapping
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

logger = logging.getLogger(__name__)
_duckstation_config = emulator_configs.get('DuckStation')

class DuckStationCompatibility(Enum):
	NoIssues = 5
	GraphicalOrAudioIssues = 4
	CrashesInGame = 3
	CrashesInIntro = 2
	DoesNotBoot = 1
	Unknown = 0

def find_duckstation_compat_info(product_code: str) -> DuckStationCompatibility | None:
	compat_xml_path = _duckstation_config.options.get('compatibility_xml_path')
	if not compat_xml_path:
		return None

	if not hasattr(find_duckstation_compat_info, 'compat_xml'):
		try:
			find_duckstation_compat_info.compat_xml = ElementTree.parse(compat_xml_path) #type: ignore[attr-defined]
		except OSError:
			logger.exception('Oh dear we have an OSError trying to load compat_xml')
			return None

	entry = find_duckstation_compat_info.compat_xml.find(f'entry[@code="{product_code}"]') #type: ignore[attr-defined]
	if entry is not None:
		try:
			compatibility = int(entry.attrib.get('compatibility'))
			if compatibility:
				return DuckStationCompatibility(compatibility)
		except ValueError:
			pass
	return None

def get_duckstation_db_info(product_code: str) -> 'Mapping[Any, Any]' | None:
	gamedb_path = _duckstation_config.options.get('gamedb_path')
	if not gamedb_path:
		return None

	if not hasattr(get_duckstation_db_info, 'gamedb'):
		try:
			get_duckstation_db_info.gamedb = json.loads(gamedb_path.read_bytes()) #type: ignore[attr-defined]
		except OSError:
			if not getattr(get_duckstation_db_info, 'error', False):
				logger.exception('Oh dear we have an OSError trying to load gamedb')
				get_duckstation_db_info.error = True #type: ignore[attr-defined]
			return None

	for db_game in get_duckstation_db_info.gamedb: #type: ignore[attr-defined]
		if db_game.get('serial') == product_code:
			return db_game
	return None

def _add_duckstation_db_info(db_entry: Mapping[Any, Any], metadata: 'Metadata') -> None:
	metadata.add_alternate_name(db_entry['name'], 'DuckStation Database Name')
	languages = db_entry.get('languages')
	if languages:
		metadata.languages = {lang for lang in (get_language_by_english_name(lang_name) for lang_name in languages) if lang}
	if db_entry.get('publisher') and not metadata.publisher:
		metadata.publisher = db_entry.get('publisher')
	if db_entry.get('developer') and not metadata.developer:
		metadata.publisher = db_entry.get('developer')
	if db_entry.get('releaseDate'):
		metadata.publisher = db_entry.get('releaseDate')
	#TODO: Genre, but should this take precedence over libretro database if that is used too
	#TODO: minBlocks and maxBlocks might indicate save type? But why is it sometimes 0
	#TODO: minPlayers and maxPlayers
	if db_entry.get('vibration'):
		metadata.specific_info['Force Feedback?'] = True
	if db_entry.get('multitap'):
		metadata.specific_info['Supports Multitap?'] = True
	if db_entry.get('linkCable'):
		metadata.specific_info['Supports Link Cable?'] = True
	controllers = db_entry.get('controllers')
	if controllers:
		metadata.specific_info['Compatible Controllers'] = controllers
		metadata.specific_info['Supports Analog?'] = 'AnalogController' in controllers

def add_info_from_product_code(product_code: str, metadata: 'Metadata') -> None:
	if _duckstation_config:
		compat = find_duckstation_compat_info(product_code)
		if compat:
			metadata.specific_info['DuckStation Compatibility'] = compat
		db_entry = get_duckstation_db_info(product_code)
		if db_entry:
			_add_duckstation_db_info(db_entry, metadata)

def add_ps1_custom_info(game: 'ROMGame') -> None:
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.metadata)
	except NotImplementedError:
		pass

	if game.metadata.product_code:
		add_info_from_product_code(game.metadata.product_code, game.metadata)
