from info.region_info import TVSystem
from metadata import PlayerInput, InputType

#I don't know why I have to import things from myself. Why? That sucks.
#Well, I guess if that's the only thing that sucks, it could be worse... but still, this _really_ sucks. This can't be right, can it? Surely there's some trick that nobody thought to put in documentation
from platform_metadata._3ds import add_3ds_metadata
from platform_metadata.atari_2600 import add_atari_2600_metadata
from platform_metadata.atari_7800 import add_atari7800_metadata
from platform_metadata.atari_8_bit import add_atari_8bit_metadata
from platform_metadata.commodore_64 import add_commodore_64_metadata
from platform_metadata.ds import add_ds_metadata
from platform_metadata.game_boy import add_gameboy_metadata
from platform_metadata.gamecube import add_gamecube_metadata
from platform_metadata.gba import add_gba_metadata
from platform_metadata.master_system import get_sms_metadata
from platform_metadata.megadrive import add_megadrive_metadata
from platform_metadata.n64 import add_n64_metadata
from platform_metadata.neo_geo_pocket import add_ngp_metadata
from platform_metadata.nes import add_nes_metadata
from platform_metadata.pokemon_mini import add_pokemini_metadata
from platform_metadata.psp import add_psp_metadata
from platform_metadata.snes import add_snes_metadata
from platform_metadata.vectrex import add_vectrex_metadata
from platform_metadata.virtual_boy import add_virtual_boy_metadata
from platform_metadata.wii import add_wii_metadata
from platform_metadata.wonderswan import add_wonderswan_metadata

#For roms.py, gets metadata in ways specific to certain platforms
#I guess this is duplicating a lot of ROMniscience code, huh? Well, it's my project, and I'll use it for reference for my other project if I want. But I guess there is duplication there. I mean, it's C# and Python, so I can't really combine them directly, but it makes me think... it makes me overthink. That's the best kind of think.

#TODO: Stuff I know we can get due to being implemented in ROMniscience
#Atari 5200: Year (unreliable, has Y2K bug. It's actually just the 3rd and 4th digit stored as 5200 characters, and then printing 19 + those characters)
#ColecoVision: Year (unreliable, from copyright string on title screen), author (also unreliable and from copyright string; and in uppercase so you'd probably wanna call .titlecase() or whatsitcalled or something)

#Stuff which would require robust CD handling:
#Saturn: Input method (normal/analog/mouse/keyboard/wheel, multiple supported), region, author, product code, year
#Mega CD: Reuse Megadrive stuff

def nothing_interesting(game):
	#TODO: Gonna have to dismantle this to add number of buttons
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	game.metadata.input_info.players.append(player)

helpers = {
	'32X': add_megadrive_metadata,
	'3DS': add_3ds_metadata,
	'Atari 2600': add_atari_2600_metadata,
	'Atari 7800': add_atari7800_metadata,
	'Atari 8-bit': add_atari_8bit_metadata,
	'Benesse Pocket Challenge V2': add_wonderswan_metadata,
	'C64': add_commodore_64_metadata,
	'DS': add_ds_metadata,
	'Epoch Game Pocket Computer': nothing_interesting,
	'Gamate': nothing_interesting,
	'Game Boy': add_gameboy_metadata,
	'GameCube': add_gamecube_metadata,
	'Game Gear': get_sms_metadata,
	'GBA': add_gba_metadata,
	'Master System': get_sms_metadata,
	'Mega Drive': add_megadrive_metadata,
	'Mega Duck': nothing_interesting,
	'N64': add_n64_metadata,
	'Neo Geo Pocket': add_ngp_metadata,
	'NES': add_nes_metadata,
	'Pokemon Mini': add_pokemini_metadata,
	'PSP': add_psp_metadata,
	'SNES': add_snes_metadata,
	'Vectrex': add_vectrex_metadata,
	'Virtual Boy': add_virtual_boy_metadata,
	'Watara Supervision': nothing_interesting,
	'Wii': add_wii_metadata,
	'WonderSwan': add_wonderswan_metadata,
}
