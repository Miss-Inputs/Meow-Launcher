#TODO: I want this to be in root of specific_behaviour but that causes a circular import right now, no can do buddy

from collections.abc import Callable, Mapping, Sequence
from typing import Optional

from meowlauncher.games.specific_behaviour.simple_filename_info import add_atari_st_info

from ._3ds import add_3ds_custom_info
from .amiga import add_amiga_custom_info
from .apple_ii import add_apple_ii_rom_file_info, add_apple_ii_software_info
from .atari_8_bit import add_atari_8bit_custom_info
from .atari_2600 import add_atari_2600_custom_info
from .atari_5200 import add_atari_5200_footer_garbage_info
from .atari_7800 import add_atari_7800_custom_info
from .commodore_64 import add_commodore_64_custom_info
from .dreamcast import add_dreamcast_custom_info
from .ds import add_ds_custom_info
from .game_boy import add_game_boy_custom_info
from .game_com import add_game_com_header_info
from .gamecube import add_gamecube_custom_info
from .gba import add_gba_rom_file_info
from .intellivision import add_intellivision_custom_info
from .lynx import add_lynx_custom_info
from .master_system import (add_sms_gg_rom_file_info,
                            add_sms_gg_software_list_info)
from .megadrive import (add_megadrive_custom_info,
                        find_equivalent_mega_drive_arcade)
from .misc_platforms import (add_colecovision_software_info,
                             add_ibm_pcjr_custom_info, add_pet_custom_info,
                             add_vic10_custom_info, add_vic20_custom_info,
                             find_equivalent_pc_engine_arcade)
from .n64 import add_n64_custom_info
from .nes import add_nes_custom_info, find_equivalent_nes_arcade
from .ps1 import add_ps1_custom_info
from .ps2 import add_ps2_custom_info
from .ps3 import add_ps3_custom_info
from .psp import add_psp_custom_info
from .saturn import add_saturn_custom_info
from .simple_rom_info import *
from .simple_software_info import *
from .snes import (add_snes_rom_header_info, add_snes_software_list_metadata,
                   find_equivalent_snes_arcade)
from .static_platform_info import *
from .switch import add_switch_rom_file_info
from .uzebox import add_uzebox_custom_info
from .virtual_boy import add_virtual_boy_rom_info
from .wii import add_wii_custom_info
from .wii_u import add_wii_u_custom_info
from .wonderswan import add_wonderswan_header_info
from .zx_spectrum import add_speccy_custom_info

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.machine import Machine
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

__doc__ = """Dispatches to whatever module in specific_behaviour is appropriate, depending on platform

Stuff that can be extracted from the ROM but we haven't done that because it's not worth doing:
ColecoVision: Year (unreliable, from copyright string on title screen), author (also unreliable and from copyright string; and in uppercase so you'd probably wanna call .titlecase() or whatsitcalled or something), title
APF: Menu text
Vectrex: Title screen text
Konami Picno: Product code
Xbox: Publisher, year/month/day; albeit just for executables and not discs, so I'm not gonna bother since we only launch discs right now

If I had them emulated/added to system info there can be metadatum extracted, but there's no point implementing them here yet:
64DD: Publisher, product code, version
e-Reader: Hmm. Not a lot actually, but which "region" (Japan, export, Japan+) would end up being necessary I think
RCA Studio 2 (community-developed .st2 header): developer, product code
Xbox 360: Publisher, icon (for XBLA), number of players (for XBLA), genre (for XBLA)"""

custom_info_funcs: Mapping[str, Callable[['ROMGame'], None]] = {
	#TODO: Ideally we should work out a way to dismantle all of these

	#Where do we even begin here… these are going to stay custy for a while, sorry
	#TDB trickiness… how we gonna do that without causing a platform_configs circular import, I think we'd need a get_key_for_tdb as well
	'3DS': add_3ds_custom_info,
	'DS': add_ds_custom_info,
	'GameCube': add_gamecube_custom_info,
	'PS3': add_ps3_custom_info,
	'Wii U': add_wii_u_custom_info,
	'Wii': add_wii_custom_info,
	#Switch has a GameTDB as well? But we can't get the product code we use it out of the ROM or anywhere else… unless we search by name I guess, so for our purposes it doesn't
	'N64': add_n64_custom_info, #Internal header, byteswap shenanigans, custom database (Mupen64Plus, by md5), tries to be helpful by reading entire cart to get md5, generic software
	'NES': add_nes_custom_info, #uhhhh fuckin what doesn't this one have
	'PSP': add_psp_custom_info, #Info from product code, inbuilt controls, internal info (pbp, iso (ideally cso too but it doesn't yet)), folder check, info for file in folder (pbp inside homebrew)
	
	#TODO: Will need to have a think about how to arrange this in a more generic way inside roms_metadata etc (but also mame_software later)
	'Atari 2600': add_atari_2600_custom_info, #Software, custom database (Stella output, by md5), reads the whole cart as an optimization for both, but it could just not
	'Game Boy': add_game_boy_custom_info, #Internal header, footer shenanigans (.gbx), software, inbuilt controls
	'Intellivision': add_intellivision_custom_info, #Fucky custom software getter

	#TODO: I think we can make filename tags work as a start (when less tired)
	'Amiga': add_amiga_custom_info, #Software, filename tags
	'Commodore PET': add_pet_custom_info, #Software, filename tags
	'ZX Spectrum': add_speccy_custom_info, #Internal info (z80), generic software, filename tags (but we don't want to overwrite info we detected from z80)

	#TODO: Getting info from product code after we've done the software/rom info could be straightforward enough too
	'PS2': add_ps2_custom_info, #Info from product code, internal info inside .iso (we want to get .cue discs too but it does not yet)
	'PlayStation': add_ps1_custom_info, #Generic software, custom database (DuckStation) by product code (needs emulator_configs DuckStation)
	
	#TODO: Hmm… how will we solve header shenanigans, and might we need a might_have_header hint in EmulatedStandardPlatform or something
	'VIC-10': add_vic10_custom_info, #Annoying 2-byte header, otherwise generic software
	'VIC-20': add_vic20_custom_info, #Software, 2 byte header

	#TODO: Header stuff, but with metadata in it
	'Atari 7800': add_atari_7800_custom_info, #Header (.a78), software that checks if it needs to skip 128 bytes
	'Atari 8-bit': add_atari_8bit_custom_info, #Software, header shenanigans, filename tags
	'C64': add_commodore_64_custom_info, #Header shenanigans, software
	'IBM PCjr': add_ibm_pcjr_custom_info, #Generic software (that can potentially be not generic), header shenanigans
	'Lynx': add_lynx_custom_info, #Header, software that is otherwise generic but dependent on header length, inbuilt controls
	'Uzebox': add_uzebox_custom_info, #Header, almost generic software
	
	#TODO: Hmm CD stuff needs a rewrite I think
	'Mega CD': add_megadrive_custom_info,
	'Dreamcast': add_dreamcast_custom_info, #Internal header, generic software, we also need to refactor the GDI stuff outta there, but also the cue sheet stuff
	'Saturn': add_saturn_custom_info, #Internal header, generic software, but with disc shenanigans

	'Mega Drive': add_megadrive_custom_info, #Internal header (for CDs too; needs refactoring I guess), software, equivalent arcade (just using ROM name, and metadata alt names)
	'32X': add_megadrive_custom_info,
	'Sega Pico': add_megadrive_custom_info,
}

static_info_funcs: Mapping[str, Callable[['Metadata'], None]] = {
	#Stuff that has nothing to do with the game at all
	#Generally just InputInfo… but also SaveType if we assume it's Nothing, maybe we shouldn't
	#TODO: Feel like this should be moved to being held by EmulatedPlatform
	#Maybe something like an inbuilt_controls field that holds a func returning InputInfo or maybe InputOption, or just put the data in there; and a assume_save_type_nothing field
	'Amiga CD32': add_cd32_info,
	'Arcadia 2001': add_arcadia_info,
	'Astrocade': add_astrocade_info,
	'BBC Bridge Companion': add_bbc_bridge_companion_info,
	'Bandai Super Vision 8000': add_bandai_sv8000_info,
	'Benesse Pocket Challenge V2': add_benesse_v2_info,
	'Casio PV-1000': add_casio_pv1000_info,
	'Entex Adventure Vision': add_entex_adventure_vision_info,
	'Epoch Game Pocket Computer': add_game_pocket_computer_info,
	'Gamate': add_gamate_info,
	'Game Gear': add_game_gear_info,
	'Game.com': add_gamecom_info,
	'GBA': add_gba_info,
	'Hartung Game Master': add_hartung_game_master_info,
	'Mattel Juice Box': add_juicebox_info,
	'Mega Duck': add_mega_duck_info,
	'Neo Geo CD': add_neogeo_cd_info,
	'Neo Geo Pocket': add_ngp_info,
	'Nichibutsu My Vision': add_nichibutsu_my_vision_info,
	'Pokemon Mini': add_pokemini_info,
	'Super A\'Can': add_super_acan_info,
	'Super Cassette Vision': add_super_cassette_vision_info,
	'V.Smile Baby': add_vsmile_babby_info,
	'V.Smile': add_vsmile_info,
	'VC 4000': add_vc4000_info,
	'VZ-200': add_vz200_info,
	'Vectrex': add_vectrex_info,
	'Virtual Boy': add_virtual_boy_info,
	'Watara Supervision': add_watara_supervision_info,
	'WonderSwan': add_wonderswan_info,
}

rom_file_info_funcs: Mapping[str, Callable[['FileROM', 'Metadata'], None]] = {
	'Apple II': add_apple_ii_rom_file_info,
	'Atari 5200': add_atari_5200_footer_garbage_info,
	'Benesse Pocket Challenge V2': add_wonderswan_header_info,
	'Doom': add_doom_rom_file_info, #Just detects file type, which maybe should go somewhere else - maybe a file_type_detector that roms.py or EmulatedStandardPlatform uses
	'Game Gear': add_sms_gg_rom_file_info,
	'Game.com': add_game_com_header_info,
	'GBA': add_gba_rom_file_info, #Reads the entire cart, which may be good to know - if nothing else it would mean it would be handy if we could detect this and set should_read_entire_file to True already
	'Master System': add_sms_gg_rom_file_info,
	'Neo Geo Pocket': add_ngp_header_info,
	'Pokemon Mini': add_pokemini_rom_file_info,
	'SNES': add_snes_rom_header_info,
	'Switch': add_switch_rom_file_info,
	'Vectrex': add_vectrex_header_info,
	'Virtual Boy': add_virtual_boy_rom_info,
	'WonderSwan': add_wonderswan_header_info,
}

software_info_funcs: Mapping[str, Callable[['Software', 'Metadata'], None]] = {
	'Amstrad PCW': add_amstrad_pcw_software_info,
	'Apple II': add_apple_ii_software_info,
	'Atari 5200': add_atari_5200_software_info,
	'ColecoVision': add_colecovision_software_info,
	'FM Towns': add_fm_towns_software_info,
	'Game Gear': add_sms_gg_software_list_info,
	'Master System': add_sms_gg_software_list_info,
	'MSX': add_msx_software_info,
	'MSX2': add_msx_software_info,
	'MSX2+': add_msx_software_info,
	'Microtan 65': add_microtan_65_software_info,
	'PC Booter': add_pc_booter_software_info,
	'PC Engine CD': add_pc_engine_cd_software_info,
	'SG-1000': add_sg1000_software_info,
	'SNES': add_snes_software_list_metadata,
	'Sord M5': add_sord_m5_software_info,
	'Super Cassette Vision': add_super_cassette_vision_software_info,
	'Virtual Boy': add_virtual_boy_software_info,
}

filename_tag_info_funcs: Mapping[str, Callable[[Sequence[str], 'Metadata'], None]] = {
	'Atari ST': add_atari_st_info
}

arcade_machine_finders: Mapping[str, Callable[[str], Optional['Machine']]] = {
	'Mega Drive': find_equivalent_mega_drive_arcade,
	'NES': find_equivalent_nes_arcade,
	'PC Engine': find_equivalent_pc_engine_arcade,
	'SNES': find_equivalent_snes_arcade,
}

#Possible software info beyond generic:
	#FM-77
		#Possible input info: Keyboard and joystick but barely anything uses said joystick

		#info usage strings to make use of:
		#"Requires FM77AV40" (unsupported system)
		#"Requires FM-77AV40SX" (unsupported system)
		#"Load F-BASIC first, then LOADM &quot;CALLEB&quot; and RUN &quot;MAIN&quot;"
		#"Type RUN&quot;SD1&quot; or RUN&quot;SD2&quot; in F-BASIC"
		#"Run from F-BASIC"
		#"In F-BASIC, set 1 drive and 0 files, then type LOAD&quot;START&quot;,R"
		#"Type RUN&quot;XXX&quot; with XXX=MAGUS, LIZARD, BLUE.FOX or ナイザー in F-BASIC"
		#Sounds like there's a few disks which don't autoboot...
		#"Type LOADM&quot;&quot;,R to load" is on a few tapes
	#PC-88
			#Input info: Keyboard or joystick
			#Needs BASIC V1 or older
			#Mount both disk A and B to start
			#Needs BASIC V1
			#Mount Main disk and Scenario 1 to start
			#Mount Main disk and Scenario 2 to start
			#Needs CD-ROM support
			#Needs N-BASIC
	#Sharp X1
		#Input info: Keyboard and/or joystick
		#Type FILES then move the cursor to the line of the game and type LOAD (to load) and type RUN when loaded
		#Runs in HuBASIC
		#Load SIRIUS 1 from Extra Hyper
		#Once booted in S-OS, type "L DALK" to load, and "J 9600" to run
		#In BASIC, type FILES to list the disk content
	#Sharp X68K
		#Input info: Keyboard and/or joystick

		#Many games are known to have SaveType.Floppy, but can't tell programmatically...
		#Requires Disk 1 and Disk 3 mounted to boot
		#Use mouse at select screen
		#Requires "Harukanaru Augusta" to work
		#Requires to be installed
		#Requires SX-Windows
		#Use command.x in Human68k OS
		#Type BPHXTST in Human68k OS
		#Type S_MARIO.X in Human68k OS
	#WonderSwan
		#We could get save type from software.has_data_area('sram' or 'eeprom') but I think we can trust the header flags for now, even with BPCv2 carts
		#By the same token we can get screen orientation = vertical if feature rotated = 'yes'

	#Apple III: Possible input info: Keyboard and joystick by default, mouse if mouse card exists
	#Coleco Adam: Input info: Keyboard / Coleco numpad?
	#MSX1/2: Input info: Keyboard or joystick; Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper
	#Jaguar input info: There's the default ugly gamepad and also another ugly gamepad with more buttons which I dunno what's compatible with
	#CD-i: That one controller but could also be the light gun thingo
	#Memorex VIS: 4-button wireless not-quite-gamepad-but-effectively-one-thing (A, B, 1, 2), can have 2-button mouse? There are also 3 and 4 buttons and 2-1-Solo switch that aren't emulated yet
	#The rest are weird computers where we can't tell if they use any kind of optional joystick or not so it's like hhhh whaddya do
