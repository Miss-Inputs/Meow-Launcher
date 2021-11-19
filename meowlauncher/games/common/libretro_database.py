#!/usr/bin/env python3

import functools
import os
import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Optional, Union, cast

from meowlauncher.config.main_config import main_config

#TODO: Probs should be using dataclasses or whatever for this
RomType = Mapping[str, str]
GameValueType = Union[int, str, Sequence[RomType]]
GameType = Mapping[str, GameValueType]
_MutableGameType = MutableMapping[str, GameValueType]
LibretroDatabaseType = Mapping[Union[int, str], GameType]
_MutableLibretroDatabaseType = MutableMapping[Union[int, str], _MutableGameType]

rom_line = re.compile(r'(?<=\(|\s)(?P<attrib>\w+)\s+(?:"(?P<value>[^"]+)"|(?P<rawvalue>\S+))(?:\s+|\))')
def _parse_rom_line(line: str) -> Optional[RomType]:
	start = line[:5]
	if start != 'rom (':
		return None

	rom = {}
	for submatch in rom_line.finditer(line[4:]):
		value = submatch['value']
		if not value:
			rawvalue = submatch['rawvalue']
			if rawvalue is None:
				continue
			value = rawvalue

		rom[submatch['attrib']] = value

	return rom

attribute_line = re.compile(r'(?P<key>\w+)\s+(?:"(?P<value>[^"]*)"|(?P<intvalue>\d+))')
def parse_libretro_dat(path: Path) -> tuple[Mapping[str, Union[int, str]], Sequence[GameType]]:
	#TODO: Probably split this up in two methods, one to parse the header and one to parse the rest of it, once we have that much lines
	games: MutableSequence[GameType] = []
	header: MutableMapping[str, Union[int, str]] = {}
	with open(path, 'rt', encoding='utf-8') as file:
		game: _MutableGameType = {}
		inside_header = False
		rom_giant_line = None #Just concat everything in between rom ( ) on multiple lines so we can parse it that way
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
					attrib_match = attribute_line.match(line)
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
			attrib_match = attribute_line.match(line)
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

@functools.lru_cache(maxsize=None)
def parse_all_dats_for_system(name: str, use_serial: bool) -> Optional[LibretroDatabaseType]:
	relevant_dats = []

	libretro_database_path = main_config.libretro_database_path
	if not libretro_database_path:
		return None
	dat_folder = Path(main_config.libretro_database_path, 'dat')
	metadat_folder = Path(main_config.libretro_database_path, 'metadat')
	
	try:
		for file in dat_folder.iterdir():
			if file.name == name + '.dat':
				relevant_dats.append(file)
	except OSError:
		pass
	if metadat_folder.is_dir():
		for root, _, files in os.walk(metadat_folder):
			for filename in files:
				path = Path(root, filename)
				if path.stem == name and path.suffix == '.dat':
					if path.is_file():
						relevant_dats.append(path)
	
	if not relevant_dats:
		print('Megan is a dork error:', name)
		return None

	games: _MutableLibretroDatabaseType = {}

	for dat in relevant_dats:
		parsed = parse_libretro_dat(dat)
		for game in parsed[1]:
			roms = game.get('roms')
			if not roms:
				#Well that shouldn't happen surely
				#print("Well that shouldn't happen surely", dat, game)
				#Narrator: It does happen
				continue
			for rom in cast(Sequence[RomType], roms):
				key: Union[int, str, None] = rom.get('serial') if use_serial else int(rom.get('crc', '0'), 16)
				if not key: #crc should never be 0 so it's okay to not just check for none
					#print("Surely this also should not happen", dat, game)
					#Ah… this happens with PS1 hacks which use the crc of the whole bin
					continue

				if key not in games:
					games[key] = {}
				this_game = games[key]
				for k, v in game.items():
					if k != 'rom':
						this_game[k] = v

	return games
