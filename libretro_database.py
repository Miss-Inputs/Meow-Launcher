#!/usr/bin/env python3

import functools
import os
import re

from config.main_config import main_config

rom_line = re.compile(r'(?<=\(|\s)(?P<attrib>\w+)\s+(?:"(?P<value>[^"]+)"|(?P<hexvalue>[0-9A-Fa-f]+))(?:\s+|\))')
def parse_rom_line(line):
	start = line[:5]
	if start != 'rom (':
		return None

	rom = {}
	for submatch in rom_line.finditer(line[4:]):
		value = submatch['value']
		if not value:
			hexvalue = submatch['hexvalue']
			if hexvalue is None:
				continue
			value = hexvalue

		rom[submatch['attrib']] = value

	return rom

attribute_line = re.compile(r'(?P<key>\w+)\s+(?:"(?P<value>[^"]*)"|(?P<intvalue>\d+))')
def parse_dat(path):
	games = []
	with open(path, 'rt') as file:
		lines = [line.strip() for line in file.readlines()]
		game = {}
		inside_header = False
		rom_giant_line = None #Just concat everything in between rom ( ) on multiple lines so we can parse it that way
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
				continue
			if line == ')':
				games.append(game)
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
				game['rom'] = rom_match
				#name, size, crc, serial, sha1, md5, image
				continue
				
	return games

@functools.lru_cache(maxsize=None)
def parse_all_dats_for_system(name, use_serial):
	relevant_dats = []

	libretro_database_path = main_config.libretro_database_path
	if not libretro_database_path:
		return None
	metadat_folder = os.path.join(main_config.libretro_database_path, 'metadat')
	if not os.path.isdir(metadat_folder):
		return None

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
		parsed = parse_dat(dat)
		for game in parsed:
			rom = game.get('rom')
			if not rom:
				#Well that shouldn't happen surely
				#print("Well that shouldn't happen surely", dat, game)
				#Narrator: It does happen
				continue
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
