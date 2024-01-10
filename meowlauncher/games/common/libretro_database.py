#!/usr/bin/env python3

import contextlib
import functools
import logging
import os
import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import cast

from meowlauncher.config import main_config

logger = logging.getLogger(__name__)

#TODO: Probs should be using dataclasses or whatever for this
RomType = Mapping[str, str]
GameValueType = int | str | Sequence[RomType]
GameType = Mapping[str, GameValueType]
_MutableGameType = MutableMapping[str, GameValueType]
LibretroDatabaseType = Mapping[int | str, GameType]
_MutableLibretroDatabaseType = MutableMapping[int | str, _MutableGameType]

_rom_line = re.compile(r'(?<=\(|\s)(?P<attrib>\w+)\s+(?:"(?P<value>[^"]+)"|(?P<rawvalue>\S+))(?:\s+|\))')
def _parse_rom_line(line: str) -> RomType | None:
	start = line[:5]
	if start != 'rom (':
		return None

	rom = {}
	for submatch in _rom_line.finditer(line[4:]):
		value = submatch['value']
		if not value:
			rawvalue = submatch['rawvalue']
			value = rawvalue

		rom[submatch['attrib']] = value

	return rom

_attribute_line = re.compile(r'(?P<key>\w+)\s+(?:"(?P<value>[^"]*)"|(?P<intvalue>\d+))')
def parse_libretro_dat(path: Path) -> tuple[Mapping[str, int | str], Sequence[GameType]]:
	#TODO: Probably split this up in two methods, one to parse the header and one to parse the rest of it, once we have that much lines
	games: MutableSequence[GameType] = []
	header: MutableMapping[str, int | str] = {}
	with path.open('rt', encoding='utf-8') as file:
		game: _MutableGameType = {}
		inside_header = False
		rom_giant_line: str | None = None #Just concat everything in between rom ( ) on multiple lines so we can parse it that way
		roms: MutableSequence[RomType] = []
		for line in file:
			line = line.strip()
			rom_match = None
			if not line:
				continue

			if line == 'clrmamepro (':
				inside_header = True
				continue
			if inside_header:
				if line == ')':
					inside_header = False
				else:
					attrib_match = _attribute_line.match(line)
					if attrib_match:
						value = attrib_match['value']
						intvalue = attrib_match['intvalue']
						if value:
							header[attrib_match['key']] = value
						elif intvalue is not None:
							header[attrib_match['key']] = intvalue
				
				continue
			if rom_giant_line:
				rom_giant_line += ' ' + line
				if line == ')':
					line = rom_giant_line
					rom_giant_line = None
				else:
					continue
			elif line.lstrip() == 'rom (':
				rom_giant_line = line
				continue

			if line == 'game (':
				game = {}
				roms = []
				continue
			if line == ')':
				game['roms'] = roms
				games.append(game)
				game = {}
				continue

			#Assume we are in the middle
			if not line:
				continue
			attrib_match = _attribute_line.match(line)
			if attrib_match:
				value = attrib_match['value']
				intvalue = attrib_match['intvalue']
				if value:
					game[attrib_match['key']] = value
				elif intvalue is not None:
					game[attrib_match['key']] = intvalue
				continue

			rom_match = _parse_rom_line(line)

			if rom_match:
				roms.append(rom_match)
				continue
		if game:
			game['roms'] = roms
			games.append(game)
	return header, games

@functools.cache
def parse_all_dats_for_system(name: str, use_serial: bool) -> LibretroDatabaseType | None:
	relevant_dats = []

	libretro_database_path = main_config.libretro_database_path
	if not libretro_database_path:
		return None
	dat_folder = Path(libretro_database_path, 'dat')
	metadat_folder = Path(libretro_database_path, 'metadat')
	
	with contextlib.suppress(OSError):
		relevant_dats += [file for file in dat_folder.iterdir() if file.stem == name and file.suffix == '.dat']
	if metadat_folder.is_dir():
		for root, _, files in os.walk(metadat_folder):
			for filename in files:
				path = Path(root, filename)
				if path.stem == name and path.suffix == '.dat' and path.is_file():
					relevant_dats.append(path)
	
	if not relevant_dats:
		logger.info('Megan is a dork error: %s', name)
		return None

	games: _MutableLibretroDatabaseType = {}

	for dat in relevant_dats:
		parsed = parse_libretro_dat(dat)
		for game in parsed[1]:
			roms = game.get('roms')
			if not roms:
				continue
			for rom in cast(Sequence[RomType], roms):
				key: int | str | None = rom.get('serial') if use_serial else int(rom.get('crc', '0'), 16)
				if key is None:
					continue

				this_game = games.setdefault(key, {})
				for k, v in game.items():
					if k != 'rom':
						this_game[k] = v

	return games
