import json
import logging
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from meowlauncher.games.common.generic_info import add_generic_software_info
from meowlauncher.settings.emulator_config import emulator_configs
from meowlauncher.util.region_info import get_language_by_english_name

if TYPE_CHECKING:
	from collections.abc import Collection, Mapping

	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)
_duckstation_config = emulator_configs.get('DuckStation')

class DuckStationCompatibility(IntEnum):
	"""DuckStation compatibility as defined by compatibility database"""
	NoIssues = 5
	GraphicalOrAudioIssues = 4
	CrashesInGame = 3
	CrashesInIntro = 2
	DoesNotBoot = 1
	Unknown = 0

@dataclass
class DuckStationCompatibilityEntry:
	"""Represents DuckStation database <compatibility> element"""
	compatibility: DuckStationCompatibility
	comments: str | None
	upscaling_issues: str | None

@lru_cache(maxsize=1)
def _get_duckstation_compat_xml() -> 'ElementTree.ElementTree | None':
	assert _duckstation_config, 'We already checked before calling'
	compat_xml_path = _duckstation_config.options.get('compatibility_xml_path')
	if not compat_xml_path:
		return None

	try:
		return ElementTree.parse(compat_xml_path)
	except OSError:
		logger.exception('oh dear')
		return None
	
def _find_duckstation_compat_info(product_code: str) -> DuckStationCompatibilityEntry | None:
	compat_xml = _get_duckstation_compat_xml()
	if not compat_xml:
		return None
	entry = compat_xml.find(f'entry[@code="{product_code}"]')
	if entry is not None:
		try:
			compatibility = entry.attrib.get('compatibility')
			if compatibility:
				return DuckStationCompatibilityEntry(DuckStationCompatibility(int(compatibility)), entry.findtext('comments'), entry.findtext('upscaling-issues'))
		except ValueError:
			pass
	return None

@lru_cache(maxsize=1)
def _get_duckstation_db() -> 'Collection[Mapping[Any, Any]]':
	assert _duckstation_config, 'We already checked before calling'
	gamedb_path = _duckstation_config.options.get('gamedb_path')
	if not gamedb_path:
		return []
	try:
		return json.loads(gamedb_path.read_bytes())
	except OSError:
		logger.exception('oh bother')
		return []

def _get_duckstation_db_info(product_code: str) -> 'Mapping[Any, Any] | None':
	return next((db_entry for db_entry in _get_duckstation_db() if db_entry.get('serial') == product_code), None)

def _add_duckstation_db_info(db_entry: 'Mapping[Any, Any]', metadata: 'GameInfo') -> None:
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

def add_info_from_product_code(product_code: str, metadata: 'GameInfo') -> None:
	"""If DuckStation is configured, add info from its database, otherwise do nothing"""
	if _duckstation_config:
		compat = _find_duckstation_compat_info(product_code)
		if compat:
			metadata.specific_info['DuckStation Compatibility'] = compat.compatibility
			metadata.specific_info['DuckStation Compatibility Comments'] = compat.comments
			metadata.specific_info['DuckStation Upscaling Issues'] = compat.upscaling_issues
		db_entry = _get_duckstation_db_info(product_code)
		if db_entry:
			_add_duckstation_db_info(db_entry, metadata)

def add_ps1_custom_info(game: 'ROMGame') -> None:
	"""Adds info from the software list entry and product code."""
	try:
		software = game.get_software_list_entry()
		if software:
			add_generic_software_info(software, game.info)
	except NotImplementedError:
		pass

	if game.info.product_code:
		add_info_from_product_code(game.info.product_code, game.info)
