from enum import Enum
from xml.etree import ElementTree
import json

from info.region_info import get_language_by_english_name
from config.main_config import main_config
from config.emulator_config import emulator_configs

from .minor_systems import add_generic_info

duckstation_config = emulator_configs.get('DuckStation')

class DuckStationCompatibility(Enum):
	NoIssues = 5
	GraphicalOrAudioIssues = 4
	CrashesInGame = 3
	CrashesInIntro = 2
	DoesNotBoot = 1
	Unknown = 0

def add_duckstation_compat_info(metadata):
	compat_xml_path = duckstation_config.options.get('compatibility_xml_path')
	if not compat_xml_path:
		return

	if not hasattr(add_duckstation_compat_info, 'compat_xml'):
		try:
			add_duckstation_compat_info.compat_xml = ElementTree.parse(compat_xml_path)
		except OSError as oserr:
			if main_config.debug:
				print('Oh dear we have an OSError trying to load compat_xml', oserr)
			return

	entry = add_duckstation_compat_info.compat_xml.find('entry[@code="{0}"]'.format(metadata.product_code))
	if entry is not None:
		try:
			compatibility = int(entry.attrib.get('compatibility'))
			if compatibility:
				metadata.specific_info['DuckStation-Compatibility'] = DuckStationCompatibility(compatibility)
		except ValueError:
			pass
	
def add_duckstation_db_info(metadata):
	gamedb_path = duckstation_config.options.get('gamedb_path')
	if not gamedb_path:
		return

	if not hasattr(add_duckstation_db_info, 'gamedb'):
		try:
			with open(gamedb_path, 'rb') as f:
				add_duckstation_db_info.gamedb = json.load(f)
		except OSError as oserr:
			if main_config.debug:
				print('Oh dear we have an OSError trying to load gamedb', oserr)
			return

	game = None
	for db_game in add_duckstation_db_info.gamedb:
		if db_game.get('serial') == metadata.product_code:
			game = db_game
			break
	if game:
		metadata.add_alternate_name(game['name'], 'DuckStation-Database-Name')
		languages = game.get('languages')
		if languages:
			metadata.languages = [get_language_by_english_name(lang) for lang in languages]
		if game.get('publisher') and not metadata.publisher:
			metadata.publisher = game.get('publisher')
		if game.get('developer') and not metadata.developer:
			metadata.publisher = game.get('developer')
		if game.get('releaseDate'):
			metadata.publisher = game.get('releaseDate')
		#TODO: Genre, but should this take precedence over libretro database if that is used too
		#TODO: minBlocks and maxBlocks might indicate save type? But why is it sometimes 0
		#TODO: minPlayers and maxPlayers
		if game.get('vibration'):
			metadata.specific_info['Force-Feedback'] = True
		if game.get('multitap'):
			metadata.specific_info['Supports-Multitap'] = True
		if game.get('linkCable'):
			metadata.specific_info['Supports-Link-Cable'] = True
		controllers = game.get('controllers')
		if controllers:
			metadata.specific_info['Compatible-Controllers'] = controllers
			metadata.specific_info['Supports-Analog'] = 'AnalogController' in controllers


def add_ps1_metadata(game):
	add_generic_info(game)
	if game.metadata.product_code and duckstation_config:
		add_duckstation_compat_info(game.metadata)
		add_duckstation_db_info(game.metadata)
