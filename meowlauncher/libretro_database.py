#!/usr/bin/env python3

import functools
import os
import re
from typing import Any, Optional, Sequence, Union

from meowlauncher.config.main_config import main_config

#TODO: Probs should be using dataclasses or whatever for this
RomType = dict[str, str]
GameType = dict[str, Union[int, str, Sequence[RomType]]]

rom_line = re.compile(r'(?<=\(|\s)(?P<attrib>\w+)\s+(?:"(?P<value>[^"]+)"|(?P<rawvalue>\S+))(?:\s+|\))')
def parse_rom_line(line: str) -> Optional[dict[str, str]]:
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
def parse_libretro_dat(path: str) -> tuple[dict[str, Union[int, str]], Sequence[GameType]]:
	games: list[GameType] = []
	header: dict[str, Union[int, str]] = {}
	with open(path, 'rt') as file:
		lines = [line.strip() for line in file.readlines()]
		game: GameType = {}
		inside_header = False
		rom_giant_line = None #Just concat everything in between rom ( ) on multiple lines so we can parse it that way
		roms: list[RomType] = []
		for line in lines:
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

			rom_match = parse_rom_line(line)

			if rom_match:
				roms.append(rom_match)
				continue
		if game:
			game['roms'] = roms
			games.append(game)
	return header, games

@functools.lru_cache(maxsize=None)
def parse_all_dats_for_system(name: str, use_serial: bool):
	relevant_dats = []

	libretro_database_path = main_config.libretro_database_path
	if not libretro_database_path:
		return None
	dat_folder = os.path.join(main_config.libretro_database_path, 'dat')
	metadat_folder = os.path.join(main_config.libretro_database_path, 'metadat')
	
	if os.path.isdir(dat_folder):
		for file in os.listdir(dat_folder):
			if file == name + '.dat':
				path = os.path.join(dat_folder, file)
				relevant_dats.append(path)
	if os.path.isdir(metadat_folder):
		for root, _, files in os.walk(metadat_folder):
			for file in files:
				if file == name + '.dat':
					path = os.path.join(root, file)
					if os.path.isfile(path):
						relevant_dats.append(path)
	
	if not relevant_dats:
		print('Megan is a dork error:', name)
		return None

	games = {}

	for dat in relevant_dats:
		parsed = parse_libretro_dat(dat)
		for game in parsed[1]:
			roms = game.get('roms')
			if not roms:
				#Well that shouldn't happen surely
				#print("Well that shouldn't happen surely", dat, game)
				#Narrator: It does happen
				continue
			for rom in roms:
				if use_serial:
					key = rom.get('serial')
				else:
					key = int(rom.get('crc', '0'), 16)
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
