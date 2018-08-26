from info.region_info import TVSystem
from metadata import PlayerInput, InputType

#I don't know why I have to import things from myself. Why? That sucks.
#Well, I guess if that's the only thing that sucks, it could be worse... but still, this _really_ sucks. This can't be right, can it? Surely there's some trick that nobody thought to put in documentation
from platform_metadata._3ds import add_3ds_metadata
from platform_metadata.atari_2600 import add_atari_2600_metadata
from platform_metadata.atari_7800 import add_atari_7800_metadata
from platform_metadata.atari_8_bit import add_atari_8bit_metadata
from platform_metadata.commodore_64 import add_commodore_64_metadata
from platform_metadata.dreamcast import add_dreamcast_metadata
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
from platform_metadata.saturn import add_saturn_metadata
from platform_metadata.snes import add_snes_metadata
from platform_metadata.vectrex import add_vectrex_metadata
from platform_metadata.virtual_boy import add_virtual_boy_metadata
from platform_metadata.wii import add_wii_metadata
from platform_metadata.wonderswan import add_wonderswan_metadata

from platform_metadata.minor_systems import *

#For roms.py, gets metadata in ways specific to certain platforms
#I guess this is duplicating a lot of ROMniscience code, huh? Well, it's my project, and I'll use it for reference for my other project if I want. But I guess there is duplication there. I mean, it's C# and Python, so I can't really combine them directly, but it makes me think... it makes me overthink. That's the best kind of think.

#TODO: Stuff I know we can get due to being implemented in ROMniscience
#Atari 5200: Year (unreliable, has Y2K bug. It's actually just the 3rd and 4th digit stored as 5200 characters, and then printing 19 + those characters)
#ColecoVision: Year (unreliable, from copyright string on title screen), author (also unreliable and from copyright string; and in uppercase so you'd probably wanna call .titlecase() or whatsitcalled or something)
#PSP homebrew: Uhh, product code I guess; retail discs would need me to parse ISO9660 filesystems

#If I had them emulated there can be metadatum extracted, but there's no point implementing them here yet:
#64DD: Publisher, product code, version
#e-Reader: Hmm. Not a lot actually, but which "region" (Japan, export, Japan+) would end up being necessary I think
#Konami Picno: Product code
#RCA Studio 2 (community-developed .st2 header): developer, product code
#Sega Pico (same as Megadrive)
#Wii U: Publisher, icon (if Pillow can do .tga or if that can just be put in .desktop files as an icon natively)
#Xbox: Publisher, year/month/day; albeit just for executables and not discs
#Xbox 360: Publisher, icon (for XBLA), number of players (for XBLA), genre (for XBLA)

helpers = {
	'3DS': add_3ds_metadata,
	'Atari 2600': add_atari_2600_metadata,
	'Atari 7800': add_atari_7800_metadata,
	'Atari 8-bit': add_atari_8bit_metadata,
	'C64': add_commodore_64_metadata,
	'Dreamcast': add_dreamcast_metadata,
	'DS': add_ds_metadata,
	'Game Boy': add_gameboy_metadata,
	'GameCube': add_gamecube_metadata,
	'GBA': add_gba_metadata,
	'Master System': get_sms_metadata,
	'Mega Drive': add_megadrive_metadata,
	'N64': add_n64_metadata,
	'Neo Geo Pocket': add_ngp_metadata,
	'NES': add_nes_metadata,
	'Pokemon Mini': add_pokemini_metadata,
	'PSP': add_psp_metadata,
	'Saturn': add_saturn_metadata,
	'SNES': add_snes_metadata,
	'Vectrex': add_vectrex_metadata,
	'Virtual Boy': add_virtual_boy_metadata,
	'Wii': add_wii_metadata,
	'WonderSwan': add_wonderswan_metadata,

	#These just re-use some other system's header
	'32X': add_megadrive_metadata,
	'Benesse Pocket Challenge V2': add_wonderswan_metadata,
	'Game Gear': get_sms_metadata,
	'Mega CD': add_megadrive_metadata,

	#Just get basic system info and software list stuff for now (see minor_systems.py). Not as fun as the others.
	'APF-MP1000': add_apfm1000_info,
	'Arcadia 2001': add_arcadia_info,
	'Astrocade': add_astrocade_info,
	'Atari 5200': add_atari_5200_info,
	'Casio PV-1000': add_casio_pv1000_info,
	'Casio PV-2000': add_casio_pv2000_info,
	'Channel F': add_channel_f_info,
	'Entex Adventure Vision': add_entex_adventure_vision_info,
	'Epoch Game Pocket Computer': add_game_pocket_computer_info,
	'Gamate': add_gamate_info,
	'Game.com': add_game_com_info,
	'Lynx': add_lynx_info,
	'Mattel Juice Box': add_juicebox_info,
	'Mega Duck': add_mega_duck_info,
	'MSX': add_msx_info,
	'MSX2': add_msx_info,
	'PC Engine': add_pce_info,
	'PC-88': add_pc88_info,
	'Sord M5': add_sord_m5_info,
	'SG-1000': add_sg1000_info,
	'Sharp X1': add_sharp_x1_info,
	'Sharp X68000': add_sharp_x68k_info,
	'Tomy Tutor': add_tomy_tutor_info,
	'Uzebox': add_uzebox_info,
	'VC 4000': add_vc4000_info,
	'VIC-10': add_vic10_info,
	'Watara Supervision': add_watara_supervision_info,
}
