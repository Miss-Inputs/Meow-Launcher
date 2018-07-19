import sys
import os
import binascii
import subprocess
import hashlib
import re

from info.region_info import TVSystem

#I don't know why I have to import things from myself. Why? That sucks.
#Well, I guess if that's the only thing that sucks, it could be worse... but still, this _really_ sucks. This can't be right, can it? Surely there's some trick that nobody thought to put in documentation
import platform_metadata._3ds
import platform_metadata.atari_2600
import platform_metadata.atari_7800
import platform_metadata.atari_8_bit
import platform_metadata.commodore_64
import platform_metadata.ds
import platform_metadata.game_boy
import platform_metadata.gamecube
import platform_metadata.gba
import platform_metadata.megadrive
import platform_metadata.n64
import platform_metadata.neo_geo_pocket
import platform_metadata.nes
import platform_metadata.pokemon_mini
import platform_metadata.psp
import platform_metadata.snes
import platform_metadata.vectrex
import platform_metadata.virtual_boy
import platform_metadata.wii
import platform_metadata.wonderswan

debug = '--debug' in sys.argv

#For roms.py, gets metadata in ways specific to certain platforms
#I guess this is duplicating a lot of ROMniscience code, huh? Well, it's my project, and I'll use it for reference for my other project if I want. But I guess there is duplication there. I mean, it's C# and Python, so I can't really combine them directly, but it makes me think... it makes me overthink. That's the best kind of think.

#TODO: Stuff I know we can get due to being implemented in ROMniscience
#Atari 5200: Year (unreliable, has Y2K bug. It's actually just the 3rd and 4th digit stored as 5200 characters, and then printing 19 + those characters)
#ColecoVision: Year (unreliable, from copyright string on title screen), author (also unreliable and from copyright string; and in uppercase so you'd probably wanna call .titlecase() or whatsitcalled or something)
#Master System/Game Gear: Regions/device type (i.e. SMS or GG, Japanese or export or international), product code (official games), author (official Game Gear and homebrew both), year (homebrew)
#WiiWare: Product code, author, region (in terms of region locking)

#Stuff which would require robust CD handling:
#Saturn: Input method (normal/analog/mouse/keyboard/wheel, multiple supported), region, author, product code, year
#Mega CD: Reuse Megadrive stuff

def nothing_interesting(game):
	game.metadata.tv_type = TVSystem.Agnostic
	game.metadata.input_method = 'Normal'

helpers = {
	'32X': megadrive.add_megadrive_metadata,
	'3DS': _3ds.add_3ds_metadata,
	'Atari 2600': atari_2600.add_atari_2600_metadata,
	'Atari 7800': atari_7800.add_atari7800_metadata,
	'Atari 8-bit': atari_8_bit.add_atari_8bit_metadata,
	'C64': commodore_64.add_commodore_64_metadata,
	'DS': ds.add_ds_metadata,
	'Epoch Game Pocket Computer': nothing_interesting,
	'Gamate': nothing_interesting,
	'Game Boy': game_boy.add_gameboy_metadata,
	'GameCube': gamecube.add_gamecube_metadata,
	'GBA': gba.add_gba_metadata,
	'Mega Drive': megadrive.add_megadrive_metadata,
	'Mega Duck': nothing_interesting,
	'N64': n64.add_n64_metadata,
	'Neo Geo Pocket': neo_geo_pocket.add_ngp_metadata,
	'NES': nes.add_nes_metadata,
	'Pokemon Mini': pokemon_mini.add_pokemini_metadata,
	'PSP': psp.add_psp_metadata,
	'SNES': snes.add_snes_metadata,
	'Vectrex': vectrex.add_vectrex_metadata,
	'Virtual Boy': virtual_boy.add_virtual_boy_metadata,
	'Watara Supervision': nothing_interesting,
	'Wii': wii.add_wii_metadata,
	'WonderSwan': wonderswan.add_wonderswan_metadata,
}
