from collections.abc import Collection, MutableSequence
from typing import TYPE_CHECKING, Union

import meowlauncher.games.specific_behaviour.emulator_command_lines as command_lines
from meowlauncher.config_types import ConfigValueType, RunnerConfigValue
from meowlauncher.emulated_game import EmulatedGame
from meowlauncher.emulator import (Emulator, EmulatorStatus, LibretroCore,
                                   LibretroFrontend, MAMEDriver,
                                   MednafenModule, StandardEmulator,
                                   ViceEmulator)
from meowlauncher.games.common.emulator_command_line_helpers import (
    SimpleMednafenModule, simple_emulator, simple_gb_emulator,
    simple_mame_driver, simple_md_emulator)
from meowlauncher.launch_command import rom_path_argument
from meowlauncher.runner import HostPlatform, Runner

from .format_info import (atari_2600_cartridge_extensions,
                          generic_cart_extensions, mame_cdrom_formats,
                          mame_floppy_formats)

if TYPE_CHECKING:
	from meowlauncher.games.mame.mame_game import MAMEGame

_bsnes_options = {
	#All versions would use this
	'sgb_incompatible_with_gbc': RunnerConfigValue(ConfigValueType.Bool, True, 'Consider Super Game Boy as incompatible with carts with any GBC compatibility, even if they are DMG compatible'),
	'sgb_enhanced_only': RunnerConfigValue(ConfigValueType.Bool, False, 'Consider Super Game Boy to only support games that are specifically enhanced for it'),
}

_standalone_emulators: Collection[StandardEmulator] = {
	StandardEmulator('A7800', EmulatorStatus.Good, 'a7800', command_lines.a7800, {'bin', 'a78'}, {'7z', 'zip'}),
	#Forked directly from MAME with alterations to a7800.cpp driver, so will more or less work the same way as that
	#Executable name might be a7800.Linux-x86_64 depending on how it's installed... hmm
	StandardEmulator('bsnes', EmulatorStatus.Good, 'bsnes', command_lines.bsnes, {'sfc', 'smc', 'st', 'bs', 'gb', 'gbc'}, {'zip', '7z'}, _bsnes_options),
	StandardEmulator('cxNES', EmulatorStatus.Good, 'cxnes', command_lines.cxnes, {'nes', 'fds', 'unf', 'unif'}, {'7z', 'zip'}),
	#Or is it good? Have not tried it in a fair bit
	StandardEmulator('Dolphin', EmulatorStatus.Good, 'dolphin-emu', command_lines.dolphin, {'iso', 'ciso', 'gcm', 'gcz', 'tgc', 'elf', 'dol', 'wad', 'wbfs', 'm3u', 'wia', 'rvz', '/'}),
	StandardEmulator('DuckStation', EmulatorStatus.Good, 'duckstation-qt', command_lines.duckstation, {'bin', 'img', 'cue', 'chd', 'exe', 'm3u', 'iso'}, configs={
		'compatibility_xml_path': RunnerConfigValue(ConfigValueType.FilePath, None, 'Path to where compatibility.xml is installed'), #Because DuckStation's not always installed in any particular location…
		'gamedb_path': RunnerConfigValue(ConfigValueType.FilePath, None, 'Path to where gamedb.json is installed'),
		'compatibility_threshold': RunnerConfigValue(ConfigValueType.Integer, 2, "Don't try and launch any game with this compatibility rating or lower"),
		'consider_unknown_games_incompatible': RunnerConfigValue(ConfigValueType.Bool, False, "Consider games incompatible if they aren't in the compatibility database at all")
	}),
	StandardEmulator('Flycast', EmulatorStatus.Good, 'flycast', simple_emulator(['-config', 'window:fullscreen=yes', rom_path_argument]), {'gdi', 'cdi', 'chd', 'cue'}, []),
	StandardEmulator('FS-UAE', EmulatorStatus.Good, 'fs-uae', command_lines.fs_uae, {'iso', 'cue', 'adf', 'ipf', 'lha'}),
	#Note that .ipf files need a separately downloadable plugin. We could detect the presence of that, I guess
	StandardEmulator('Gambatte', EmulatorStatus.Good, 'gambatte_qt', 
	simple_gb_emulator(['--full-screen', rom_path_argument], {'MBC1', 'MBC2', 'MBC3', 'HuC1', 'MBC5'}, {'MBC1 Multicart'}), {'gb', 'gbc'}, {'zip'}),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations, but that would probably require a specific thing that notes some GBC games are incompatible with GBA mode (Pocket Music) or GB incompatible with GBC (R-Type, also Pocket Sonar but that wouldn't work anyway)
	#I guess MBC1 Multicart only works if you tick the "Multicart compatibility" box
	#MMM01 technically works but only boots the first game instead of the menu, so it doesn't really work work
	StandardEmulator('GBE+', EmulatorStatus.Good, 'gbe_plus_qt', command_lines.gbe_plus, {'gb', 'gbc', 'gba'}),
	#In theory, only this should support Pocket Sonar (so far), but there's not really a way to detect that since it just claims to be MBC1 in the header...
	#Also in theory recognizes any extension and assumes Game Boy if not .gba or .nds, but that would be screwy
	StandardEmulator('Kega Fusion', EmulatorStatus.Good, 'kega-fusion', 
	simple_md_emulator(['-fullscreen', rom_path_argument], {'aqlian', 'sf002', 'sf004', 'smw64', 'topf', 'kof99', 'cjmjclub', 'pokestad', 'soulb', 'chinf3'}), 
	{'bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', 'sc', '32x'}, {'zip'}),
	#rom_kof99: Pocket Monsters does work (game-specific hack, probably?), which is why in platform_metadata/megadrive I've treated it specially and called it rom_kof99_pokemon
	#May support other CD formats for Mega CD other than iso, cue? Because it's closed source, can't really have a look, but I'm just going to presume it's only those two
	StandardEmulator('mGBA', EmulatorStatus.Good, 'mgba-qt', command_lines.mgba, {'gb', 'gbc', 'gba', 'srl', 'bin', 'mb', 'gbx'}, {'7z', 'zip'}),
	#Doesn't really do GBX but it will ignore the footer
	StandardEmulator('melonDS', EmulatorStatus.Good, 'melonDS', command_lines.melonds, {'nds', 'srl'}), #Supports .dsi too, but I'm acting as though it doesn't, because it's too screwy
	StandardEmulator('Mupen64Plus', EmulatorStatus.Good, 'mupen64plus', command_lines.mupen64plus, {'z64', 'v64', 'n64'}),
	StandardEmulator('PCSX2', EmulatorStatus.Good, 'pcsx2', command_lines.pcsx2, {'iso', 'cso', 'bin', 'elf', 'irx', 'chd'}, {'gz'}),
	#Only reads the bin of bin/cues and not the cue
	StandardEmulator('Pico-8', EmulatorStatus.Good, 'pico8', simple_emulator(['-windowed', '0', '-run', rom_path_argument]), {'p8', 'p8.png'}),
	StandardEmulator('PokeMini', EmulatorStatus.Good, 'PokeMini', command_lines.pokemini, {'min'}, {'zip'}), #Normally just puts the config files in the current directory, so this cd's to ~/.config/PokeMini first
	StandardEmulator('PPSSPP', EmulatorStatus.Good, 'ppsspp-qt', command_lines.ppsspp, {'iso', 'pbp', 'cso', '/'}),
	StandardEmulator('Reicast', EmulatorStatus.Good, 'reicast', command_lines.reicast, {'gdi', 'cdi', 'chd'}),
	StandardEmulator('Ruffle', EmulatorStatus.Imperfect, 'ruffle', simple_emulator(), {'swf'}),
	#No way to start off in fullscreen…
	StandardEmulator('SimCoupe', EmulatorStatus.Good, 'simcoupe', simple_emulator(['-fullscreen', 'yes', rom_path_argument]), {'mgt', 'sad', 'dsk', 'sbt'}, {'zip', 'gz'}),
	StandardEmulator('Snes9x', EmulatorStatus.Good, 'snes9x-gtk', command_lines.snes9x, {'sfc', 'smc', 'swc'}, {'zip', 'gz'}),
	#Can't set fullscreen mode from the command line so you have to set up that yourself (but it will do that automatically); GTK port can't do Sufami Turbo or Satellaview from command line due to lacking multi-cart support that Windows has (Unix non-GTK doesn't like being in fullscreen etc)
	StandardEmulator('Stella', EmulatorStatus.Good, 'stella', simple_emulator(['-fullscreen', '1', rom_path_argument]), {'a26', 'bin', 'rom'}.union(atari_2600_cartridge_extensions), {'gz', 'zip'}),
	StandardEmulator('PrBoom+', EmulatorStatus.Imperfect, 'prboom-plus', command_lines.prboom_plus, {'wad'}),
	#Joystick support not so great, otherwise it plays perfectly well with keyboard.union(mouse); except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay

	StandardEmulator('Cemu', EmulatorStatus.Experimental, 'Cemu.exe', command_lines.cemu, {'wud', 'wux', 'rpx', '/'}, host_platform=HostPlatform.Windows),
	StandardEmulator('Citra', EmulatorStatus.ExperimentalButSeemsOkay, 'citra-qt', command_lines.citra, {'3ds', 'cxi', '3dsx'}),
	#No fullscreen from command line
	StandardEmulator('Medusa', EmulatorStatus.ExperimentalButSeemsOkay, 'medusa-emu-qt', command_lines.medusa, {'nds', 'gb', 'gbc', 'gba'}, {'7z', 'zip'}),
	StandardEmulator('RPCS3', EmulatorStatus.ExperimentalButSeemsOkay, 'rpcs3', command_lines.rpcs3, {'/', 'elf', 'self', 'bin'}, configs={
		'require_compat_entry': RunnerConfigValue(ConfigValueType.Bool, False, 'Do not make launchers for games which are not in the compatibility database at all'),
		'compat_threshold': RunnerConfigValue(ConfigValueType.Integer, 0, 'Games that are under this level of compatibility will not get launchers made; 1 = Loadable 2 = Intro 3 = Ingame 4 = Playable (all the way through)'),
	}),
	StandardEmulator('Xemu', EmulatorStatus.Experimental, 'xemu', command_lines.xemu, {'iso'}), #Requires the game partition to be separated out of the disc image
	StandardEmulator('Yuzu', EmulatorStatus.ExperimentalButSeemsOkay, 'yuzu', command_lines.yuzu, {'xci', 'nsp', 'nro', 'nso', 'nca', 'elf', 'kip'}),


	ViceEmulator('C64', EmulatorStatus.Good, 'x64sc', command_lines.vice_c64),
	#x64 and x64sc have the same command line structure, just different exe names
	ViceEmulator('C64 Fast', EmulatorStatus.Good, 'x64', command_lines.vice_c64),
	ViceEmulator('VIC-20', EmulatorStatus.Good, 'xvic', command_lines.vice_vic20),
	ViceEmulator('Commodore PET', EmulatorStatus.Good, 'xpet', command_lines.vice_pet),
	ViceEmulator('Plus/4', EmulatorStatus.Good, 'xplus4', command_lines.vice_plus4),
	ViceEmulator('C128', EmulatorStatus.Good, 'x128', command_lines.vice_c128),

	MednafenModule('Apple II', EmulatorStatus.Good, {'woz', 'dsk', 'po', 'do', 'd13', '2mg'}, command_lines.mednafen_apple_ii),
	#Seems fine but no Apple IIe/128K?
	MednafenModule('Lynx', EmulatorStatus.Good, {'lnx', 'o'}, command_lines.mednafen_lynx),
	#Based on Handy, but that hasn't been updated in 14 years, so I guess this probably has some more updates
	SimpleMednafenModule('Neo Geo Pocket', EmulatorStatus.Good, 'ngp', {'ngp', 'npc', 'ngc'}),
	#Based off NeoPop, which hasn't been updated in 15 years, so presumably with improvements. Does say that this is unsuitable for homebrew development (due to lack of accuracy) and MAME is more suitable for that, so believe that if you want
	MednafenModule('NES', EmulatorStatus.Good, {'nes', 'fds', 'unf'}, command_lines.mednafen_nes),
	#Based off FCEU, so not quite cycle-accurate but it works
	SimpleMednafenModule('PC Engine', EmulatorStatus.Good, 'pce', {'pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u'}),
	SimpleMednafenModule('PC-FX', EmulatorStatus.Good, 'pcfx', {'iso', 'cue', 'toc', 'ccd', 'm3u'}), #Do NOT specify a FX-SCSI BIOS
	SimpleMednafenModule('PlayStation', EmulatorStatus.Good, 'psx', {'iso', 'cue', 'exe', 'toc', 'ccd', 'm3u', 'psx'}),
	SimpleMednafenModule('Virtual Boy', EmulatorStatus.Good, 'vb', {'bin', 'vb', 'vboy'}),
	SimpleMednafenModule('WonderSwan', EmulatorStatus.Good, 'wswan', {'ws', 'wsc', 'bin', 'pc2'}),
	#Based on Cygne, definitely heavily modified by now

	MAMEDriver('Amstrad GX4000', EmulatorStatus.Imperfect, simple_mame_driver('gx4000', 'cart'), {'bin', 'cpr'}),
	#MT06201 (issue with emulated monochrome monitor), MT6509 lists various compatibility issues
	MAMEDriver('APF-MP1000', EmulatorStatus.Good, simple_mame_driver('apfm1000', 'cart'), {'bin'}),
	MAMEDriver('Apple II', EmulatorStatus.Good, command_lines.mame_apple_ii, mame_floppy_formats.union({'nib', 'do', 'po', 'woz', '2mg'})), #nib support only >= 0.229
	MAMEDriver('Apple IIgs', EmulatorStatus.Good, simple_mame_driver('apple2gsr1', 'flop3', {'gameio': 'joy'}, has_keyboard=True), mame_floppy_formats.union({'2mg', '2img', 'dc', 'woz'})),
	#Rev 1 is needed because some stuff doesn't work on rev 3 (happens in real life), flop1 and flop2 are for Apple II-not-GS software
	#ramsize can go up to 8M if need be and there are a lot of slot options (4play might be useful for our 1337 pro gaming purposes? arcbd sounds cool?)
	MAMEDriver('Apple III', EmulatorStatus.Good, simple_mame_driver('apple3', 'flop1', has_keyboard=True), mame_floppy_formats.union({'do', 'po'})),
	MAMEDriver('Arcadia 2001', EmulatorStatus.Good, simple_mame_driver('arcadia', 'cart'), {'bin'}),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all
	#MT06642: Wrong background colours
	MAMEDriver('Astrocade', EmulatorStatus.Good, simple_mame_driver('astrocde', 'cart', {'exp': 'rl64_ram'}), {'bin'}),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	MAMEDriver('Atari 2600', EmulatorStatus.Good, command_lines.mame_atari_2600, {'bin', 'a26'}),
	MAMEDriver('Atari 5200', EmulatorStatus.Imperfect, simple_mame_driver('a5200', 'cart'), {'bin', 'rom', 'car', 'a52'}),
	#Could use -sio casette -cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory (or is that just there because Atari 8-bit computers can do that)
	#MT06972: Nondescript input issues; MT07248: Galaxian doesn't work
	MAMEDriver('Atari 7800', EmulatorStatus.Good, command_lines.mame_atari_7800, {'a78'}),
	MAMEDriver('Atari 8-bit', EmulatorStatus.Good, command_lines.mame_atari_8bit, {'bin', 'rom', 'car', 'atr', 'dsk'}),
	#Has issues with XEGS carts that it should be able to load (because they do run on the real system) but it says it doesn't because they should be run on XEGS instead, and then doesn't support a few cart types anyway; otherwise fine
	MAMEDriver('Bandai Super Vision 8000', EmulatorStatus.Good, simple_mame_driver('sv8000', 'cart'), {'bin'}),
	MAMEDriver('BBC Bridge Companion', EmulatorStatus.Good, simple_mame_driver('bbcbc', 'cart'), {'bin'}),
	MAMEDriver('Casio PV-1000', EmulatorStatus.Good, simple_mame_driver('pv1000', 'cart'), {'bin'}),
	MAMEDriver('Champion 2711', EmulatorStatus.Good, simple_mame_driver('unichamp', 'cart'), generic_cart_extensions),
	MAMEDriver('Channel F', EmulatorStatus.Good, simple_mame_driver('channelf', 'cart'), {'bin', 'chf'}),
	MAMEDriver('ColecoVision', EmulatorStatus.Good, command_lines.mame_colecovision, {'bin', 'col', 'rom'}),
	#MT06554: Roller controller is inaccurate
	MAMEDriver('Coleco Adam', EmulatorStatus.Good, command_lines.mame_coleco_adam, {'wav', 'ddp'}.union(mame_floppy_formats)),
	#Both disks and tapes autoboot. Woohoo!
	MAMEDriver('Entex Adventure Vision', EmulatorStatus.Imperfect, simple_mame_driver('advision', 'cart'), {'bin'}),
	MAMEDriver('FM-7', EmulatorStatus.Good, simple_mame_driver('fm77av', 'flop1', has_keyboard=True), mame_floppy_formats),
	#Tapes work, but they require run"" and then pressing play on the tape, the latter not being Lua-autoboot-scriptable yet.
	#Difference between fm7 and fmnew7 seems to be that the latter boots into BASIC by default (there's dip switches involved) instead of DOS, which seems to be required for tapes to work; and disks just autoboot anyway. FM-77AV is used here despite its allegedly imperfect graphics as there are games which won't work on earlier systems and there doesn't seem to be a programmatic way to tell, and it seems backwards compatibility is fine
	#Joystick only works with fm7/fmnew7 -centronics dsjoy... whoops; not sure what the builtin joystick does then
	MAMEDriver('G7400', EmulatorStatus.Good, simple_mame_driver('g7400', 'cart'), {'bin', 'rom'}),
	#There is also an unreleased odyssey3 prototype if that is useful for USA (presumably unreleased) games, also jotac for France
	#Should this be merged with Odyssey 2 if it's compatible like that?
	MAMEDriver('Gamate', EmulatorStatus.Good, simple_mame_driver('gamate', 'cart'), {'bin'}),
	MAMEDriver('Game Boy', EmulatorStatus.Imperfect, command_lines.mame_game_boy, {'bin', 'gb', 'gbc'}, {
		'use_gbc_for_dmg': RunnerConfigValue(ConfigValueType.Bool, True, 'Use MAME GBC driver for DMG games'),
		'prefer_sgb_over_gbc': RunnerConfigValue(ConfigValueType.Bool, False, 'If a game is both SGB and GBC enhanced, use MAME SGB driver instead of GBC'),
	}),
	#This supports some bootleg mappers that other emus tend to not; fails on really fancy tricks like the Demotronic trick (it does run the demo, but the effect doesn't look right); and has sound issues with GBC (MT06441, MT04949)
	#There are comments in the source file that point out that Super Game Boy should be part of the snes driver with the BIOS cart inserted, rather than a separate system, so that might not exist in the future
	MAMEDriver('Game.com', EmulatorStatus.Good, simple_mame_driver('gamecom', 'cart1'), {'bin', 'tgc'}),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything.
	MAMEDriver('Game Gear', EmulatorStatus.Good, command_lines.mame_game_gear, {'bin', 'gg'}),
	MAMEDriver('Epoch Game Pocket Computer', EmulatorStatus.Good, simple_mame_driver('gamepock', 'cart'), {'bin'}),
	MAMEDriver('GBA', EmulatorStatus.Good, simple_mame_driver('gba', 'cart'), {'bin', 'gba'}),
	#Does not let you do GBA-enhanced GBC games
	MAMEDriver('IBM PCjr', EmulatorStatus.Good, command_lines.mame_ibm_pcjr, mame_floppy_formats.union({'img', 'bin', 'jrc'})),
	MAMEDriver('Intellivision', EmulatorStatus.Good, command_lines.mame_intellivision, {'bin', 'int', 'rom', 'itv'}),
	MAMEDriver('Jupiter Ace', EmulatorStatus.Good, simple_mame_driver('jupace', 'dump', {'ramsize': '48K'}, has_keyboard=True), {'ace'}),
	MAMEDriver('Lynx', EmulatorStatus.Good, command_lines.mame_lynx, {'lnx', 'lyx', 'o'}),
	#Could be weird where rotation is involved
	MAMEDriver('Magnavox Odyssey²', EmulatorStatus.Good, command_lines.mame_odyssey2, {'bin', 'rom'}),
	MAMEDriver('Master System', EmulatorStatus.Good, command_lines.mame_master_system, {'bin', 'sms'}),
	MAMEDriver('Mattel Juice Box', EmulatorStatus.Good, simple_mame_driver('juicebox', 'memcard'), {'smc'}),
	MAMEDriver('Mega Drive', EmulatorStatus.Good, command_lines.mame_megadrive, {'bin', 'md', 'smd', 'gen'}),
	MAMEDriver('Mega Duck', EmulatorStatus.Good, simple_mame_driver('megaduck', 'cart'), {'bin'}),
	MAMEDriver('Memorex VIS', EmulatorStatus.Good, simple_mame_driver('vis', 'cdrom'), mame_cdrom_formats),
	MAMEDriver('MSX', EmulatorStatus.Good, command_lines.mame_msx1, generic_cart_extensions.union(mame_floppy_formats)),
	MAMEDriver('MSX2', EmulatorStatus.Good, command_lines.mame_msx2, generic_cart_extensions.union(mame_floppy_formats)),
	MAMEDriver('MSX2+', EmulatorStatus.Good, command_lines.mame_msx2plus, generic_cart_extensions.union(mame_floppy_formats)),
	MAMEDriver('Neo Geo CD', EmulatorStatus.Good, simple_mame_driver('neocdz', 'cdrom'), mame_cdrom_formats),
	#Don't think it has region lock so I should never need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	MAMEDriver('Neo Geo Pocket', EmulatorStatus.Good, simple_mame_driver('ngpc', 'cart'), {'bin', 'ngp', 'npc', 'ngc'}),
	MAMEDriver('NES', EmulatorStatus.Good, command_lines.mame_nes, {'nes', 'unf', 'unif', 'fds'}),
	#Supports a lot of mappers actually, probably not as much as Mesen or puNES would, but it's up there; also a lot of cool peripherals
	MAMEDriver('Nichibutsu My Vision', EmulatorStatus.Good, simple_mame_driver('myvision', 'cart'), {'bin'}),
	MAMEDriver('PC Engine', EmulatorStatus.Good, command_lines.mame_pc_engine, {'pce', 'bin', 'sgx'}),
	MAMEDriver('SAM Coupe', EmulatorStatus.Good, simple_mame_driver('samcoupe', 'flop1', autoboot_script='sam_coupe', has_keyboard=True), mame_floppy_formats),
	MAMEDriver('SG-1000', EmulatorStatus.Good, command_lines.mame_sg1000, {'bin', 'sg', 'sc', 'sf', 'sf7'}.union(mame_floppy_formats)),
	MAMEDriver('Sharp X1', EmulatorStatus.Good, simple_mame_driver('x1turbo40', 'flop1', has_keyboard=True), mame_floppy_formats.union({'2d'})),
	#x1turbo doesn't work, and I'm not sure what running x1 over x1turbo40 would achieve (hope there's no compatibility shenanigans)
	MAMEDriver('Sharp X68000', EmulatorStatus.Good, command_lines.mame_sharp_x68000, mame_floppy_formats.union({'xdf', 'hdm', '2hd', 'dim', 'm3u'})),
	#It doesn't	really support m3u, but I'm going to make it so it does (multi-disk games seem fairly common)
	#All the other models of X68000 (x68030, x68ksupr, x68kxvi) don't work yet
	MAMEDriver('SNES', EmulatorStatus.Good, command_lines.mame_snes, {'sfc', 'bs', 'st', 'smc', 'swc'}),
	MAMEDriver('Sord M5', EmulatorStatus.Good, command_lines.mame_sord_m5, {'bin'}),
	MAMEDriver('Super Cassette Vision', EmulatorStatus.Good, command_lines.mame_super_cassette_vision, {'bin'}),
	MAMEDriver('SVI-3x8', EmulatorStatus.Good, simple_mame_driver('svi328', 'cart'), {'bin', 'rom'}),
	MAMEDriver('Squale', EmulatorStatus.Good, simple_mame_driver('squale', 'cart', has_keyboard=True), {'bin'}),
	MAMEDriver('Tandy CoCo', EmulatorStatus.Good, simple_mame_driver('coco3', 'cart', has_keyboard=True), {'ccc', 'rom', 'bin'}),
	#There is a coco3p, but it apparently runs at 60Hz too, so I'm not sure if it's needed
	MAMEDriver('Thomson MO5', EmulatorStatus.Good, simple_mame_driver('mo5', 'flop1', has_keyboard=True), {'fd', 'sap'}.union(mame_floppy_formats)),
	#Cartridges do not work (or on MO6) but floppies do autoboot, cassettes do not like to load either (would need to type LOAD and enter but then it plays it for you, but then stops because I guess it's broken) (MO6 is broken as well); qd would not work without setting the floppy type to quad density in Machine Configuration which we cannot do programmatically
	#Use mo5e for export version or mo5nr for network version (I don't know what they would be useful for)
	MAMEDriver('Tomy Tutor', EmulatorStatus.Good, simple_mame_driver('tutor', 'cart', has_keyboard=True, autoboot_script='tomy_tutor'), {'bin'}),
	#There is pyuuta if you want to read Japanese instead
	MAMEDriver('VC 4000', EmulatorStatus.Good, simple_mame_driver('vc4000', 'cart'), {'bin', 'rom'}),
	#There's like 30 different clones of this, and most of them aren't even clones in the MAME sense, they're literally hardware clones. But they're apparently all software-compatible, although the cartridges aren't hardware-compatible, they just contain the same software... so this all gets confusing. Anyway, the software list with all these is named "vc4000" so I guess that's the "main" one, so we'll use that. Seems that all models use 50Hz display so there shouldn't need to be model switching based on TV type
	#TODO: Quickload slot (.pgm, .tvc)
	MAMEDriver('Vectrex', EmulatorStatus.Good, simple_mame_driver('vectrex', 'cart'), {'bin', 'gam', 'vec'}),
	#Includes overlays as selectable artwork, but that has to be done by the user from the menu
	MAMEDriver('VIC-10', EmulatorStatus.Good, simple_mame_driver('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), {'crt', '80', 'e0'}),
	#More similar to the C64 (works and performs just as well as that driver) than the VIC-20, need to plug a joystick into both ports because once again games can use either port and thanks I hate it. At least there's only one TV type
	#Sometimes I see this called the Commodore MAX Machine or Ultimax or VC-10, but... well, I'm not sure where the VIC-10 name comes from other than that's what the driver's called
	MAMEDriver('VIC-20', EmulatorStatus.Good, command_lines.mame_vic_20, {'20', '40', '60', '70', 'a0', 'b0', 'crt'}),
	MAMEDriver('V.Smile', EmulatorStatus.Good, simple_mame_driver('vsmile', 'cart'), generic_cart_extensions),
	MAMEDriver('V.Smile Motion', EmulatorStatus.Good, simple_mame_driver('vsmilem', 'cart'), generic_cart_extensions),
	#No motion controls, but the games are playable without them
	MAMEDriver('VZ-200', EmulatorStatus.Good, simple_mame_driver('vz200', 'dump', {'io': 'joystick', 'mem': 'laser_64k'}, True), {'vz'}),
	#In the Laser 200/Laser 210 family, but Dick Smith variant should do.
	#Joystick interface doesn't seem to be used by any games, but I guess it does more than leaving the IO slot unfilled. That sucks, because otherwise no game ever uses the keyboard consistently, because of course not. Even modern homebrew games. Why y'all gotta be like that?
	#Some games will need you to type RUN to run them, not sure how to detect that.
	MAMEDriver('Watara Supervision', EmulatorStatus.Good, simple_mame_driver('svision', 'cart'), {'bin', 'ws', 'sv'}),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes the colours look even worse (they're all inverted and shit)
	MAMEDriver('WonderSwan', EmulatorStatus.Good, simple_mame_driver('wscolor', 'cart'), {'ws', 'wsc', 'bin', 'pc2'}),
	#Could also be weird where rotation is involved, but at least it selects the right way around on startup
	MAMEDriver('ZX Spectrum', EmulatorStatus.Good, command_lines.mame_zx_spectrum, {'ach', 'frz', 'plusd', 'prg', 'sem', 'sit', 'sna', 'snp', 'snx', 'sp', 'z80', 'zx', 'bin', 'rom', 'raw', 'scr'}.union(mame_floppy_formats)),
	#.trd would be doable with -exp beta128, but that only autoboots on Spectrum 48K (128K needs 128 Basic > "randomize usr 15616" > j > enter) and everything is designed for 128K
	#.opu .opd might work with -exp opus, but that seems to only work on 48K and one must type "run"

	#----- The experimental section. The emulators are still here, it's just so you, the fabulous and wonderful end user, can have more information on how to manage expectations. Or something like that.

	MednafenModule('Game Boy', EmulatorStatus.ExperimentalButSeemsOkay, {'gb', 'gbc'}, command_lines.mednafen_gb),
	#Based off an old version of VisualBoyAdvance
	MednafenModule('Game Gear', EmulatorStatus.ExperimentalButSeemsOkay, {'gg'}, command_lines.mednafen_game_gear),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes". This is based off SMS Plus
	MednafenModule('GBA', EmulatorStatus.Imperfect, {'gba'}, command_lines.mednafen_gba),
	#Based off an old version of VisualBoyAdvance
	SimpleMednafenModule('Master System', EmulatorStatus.ExperimentalButSeemsOkay, 'sms', {'sms', 'bin'}),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes". Based off SMS Plus
	MednafenModule('Mega Drive', EmulatorStatus.ExperimentalButSeemsOkay, {'md', 'bin', 'gen', 'smd', 'sgd'}, command_lines.mednafen_megadrive),
	#Based off Genesis Plus and an older GPL version of Genesis Plus GX, with all GPL-incompatible cores replaced with alternatives (sound chip emulation from Gens, Z80 from FUSE). Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
	SimpleMednafenModule('PC Engine Fast', EmulatorStatus.ExperimentalButSeemsOkay, 'pce_fast', {'pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u'}),
	#Forked from 0.8.x pce with speed-accuracy tradeoffs
	SimpleMednafenModule('Saturn', EmulatorStatus.ExperimentalButSeemsOkay, 'ss', {'cue', 'toc', 'ccd', 'm3u'}),
	#Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not
	SimpleMednafenModule('SNES', EmulatorStatus.ExperimentalButSeemsOkay, 'snes', {'sfc', 'smc', 'swc'}),
	#Based on bsnes v0.059; appears it doesn't do Sufami Turbo or Satellaview
	MednafenModule('SNES-Faust', EmulatorStatus.ExperimentalButSeemsOkay, {'sfc', 'smc', 'swc'}, command_lines.mednafen_snes_faust),

	MAMEDriver('32X', EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_32x, {'32x', 'bin'}),
	#Higher host CPU requirements than what you might expect
	MAMEDriver('Amstrad PCW', EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_amstrad_pcw, mame_floppy_formats),
	MAMEDriver('Bandai RX-78', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('rx78', 'cart', has_keyboard=True), {'bin', 'rom'}), #Supports savestate but otherwise emulation = preliminary
	MAMEDriver('Casio PV-2000', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('pv2000', 'cart', has_keyboard=True), {'bin'}),
	#Not the same as the PV-1000, albeit similar. Driver marked as non-working but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a gamepad to map to emulated cursor keys) which maybe is why
	MAMEDriver('CD-i', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('cdimono1', 'cdrom'), mame_cdrom_formats), #This is the only CD-i model that works according to wisdom passed down the ages (is it still true or does other stuff work now?), and it says it's imperfect graphics/sound, no digital video stuff
	MAMEDriver('Dreamcast VMU', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('svmu', 'quik', {'bios': 'dev1004'}), {'vms', 'bin'}),
	#This doesn't save the RTC so you have to set that every time you boot it up, which would be too annoying… but this development BIOS instantly boots up whatever game is in the flash; claims to have no sound but it does do the sound? Unless it's supposed to have more sound than just beep
	MAMEDriver('FM Towns', EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_fm_towns, mame_cdrom_formats.union(mame_floppy_formats).union({'bin'})),
	MAMEDriver('FM Towns Marty', EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_fm_towns_marty, mame_cdrom_formats.union(mame_floppy_formats).union({'bin'})),
	#As it says right there in the fmtowns.cpp comments: "Issues: Video emulation is far from complete." and still marked not working, but it seems okay for a few games actually; creating floppies (for games that make you do that) seems like a weird time
	MAMEDriver('Gachinko Contest! Slot Machine TV', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('gcslottv', 'cart'), generic_cart_extensions),
	#Not working and imperfect sound
	MAMEDriver('GameKing', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('gameking', 'cart'), {'bin', 'gk'}),
	MAMEDriver('GameKing 3', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('gamekin3', 'cart'), {'bin', 'gk3'}),
	MAMEDriver('GP32', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('gp32', 'memc'), {'smc'},),
	#Bad performance (60-ish% on i5-9600kf) but otherwise might kinda work?
	MAMEDriver('Hartung Game Master', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('gmaster', 'cart'), {'bin'}),
	#Hmm... says not working and imperfect sound. I guess it does run the games, though
	MAMEDriver('Microbee', EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_microbee, {'mwb', 'com', 'bee'}.union(mame_floppy_formats)),
	MAMEDriver('PC-6001', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('pc6001', 'cart1', has_keyboard=True), {'bin', 'rom'}),
	#Preliminary and notes in source file comments it doesn't load tapes yet (the cart2 slot seems to be a hack that does that)
	#Use pc6001a for USA version if needed, pc6001mk2 and pc6001sr might also do something, pc6601 should have a floppy drive but doesn't yet
	MAMEDriver('PC-88', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('pc8801', 'flop1', has_keyboard=True), mame_floppy_formats),
	#TODO: Tapes, and potentially look into other models. All the PC-88 models claim to be broken, but the base one plays the games, so that's good enough in my book
	MAMEDriver('Sharp MZ-2000', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('mz2200', 'flop1', has_keyboard=True), mame_floppy_formats.union({'2d'})),
	#Autoboots floppies unless they have more than one thing to boot on them, which I guess makes sense
	#Apparently not working (mz2000 is not either), so I dunno
	MAMEDriver('Sony SMC-777', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('smc777', 'flop1', has_keyboard=True), mame_floppy_formats.union({'1dd'})),
	MAMEDriver('Uzebox', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('uzebox', 'cart'), {'bin', 'uze'}),
	MAMEDriver('V.Tech Socrates', EmulatorStatus.ExperimentalButSeemsOkay, simple_mame_driver('socrates', 'cart'), {'bin'}),
	#Marked as not working.union(imperfect) sound, possibly because of missing speech (also mouse is missing)
	
	MAMEDriver('Amiga CD32', EmulatorStatus.Experimental, command_lines.mame_amiga_cd32, mame_cdrom_formats),
	#Hmm boots only a few things I guess
	MAMEDriver('CreatiVision', EmulatorStatus.Janky, simple_mame_driver('crvision', 'cart', has_keyboard=True), {'bin', 'rom'}),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it; anyway it works
	MAMEDriver('Dreamcast', EmulatorStatus.Experimental, command_lines.mame_dreamcast, mame_cdrom_formats),
	#Sloooow, marked as non-working.union(imperfect) sound
	MAMEDriver('IBM PC', EmulatorStatus.Janky, simple_mame_driver('ibm5150', 'flop1', {'isa5': 'sblaster1_5'}, has_keyboard=True), mame_floppy_formats.union({'img'})),
	#Sound Blaster 1.5 is added here primarily just to give this a joystick, but then that seems to not work anyway... also, there's DIP switches you might need to set in order for video output to work (it's set to monochrome by default and not CGA)
	MAMEDriver('Jaguar', EmulatorStatus.Experimental, command_lines.mame_atari_jaguar, {'j64', 'rom', 'bin', 'abs', 'cof', 'jag', 'prg'}),
	#Hmm. Mostly not working. Some stuff does though
	MAMEDriver('KC-85', EmulatorStatus.Experimental, simple_mame_driver('kc85_3', 'quik'), {'kcc'}),
	#All marked as MACHINE_NOT_WORKING (some stuff doesn't seem to have sound or boot)
	MAMEDriver('Mattel Aquarius', EmulatorStatus.Experimental, simple_mame_driver('aquarius', 'cart', has_keyboard=True), {'bin', 'rom'}),
	#Controllers aren't emulated yet (and they're necessary for a lot of things)
	MAMEDriver('Mattel HyperScan', EmulatorStatus.Experimental, simple_mame_driver('hyprscan', 'cdrom'), mame_cdrom_formats),
	#Not going to bother about handling the cards, since logically you want to use those in the middle of the game and so you'd swap those in and out with the MAME file management menu
	#No sound and a bit slow (the latter is made worse with this console having shit loading speed)
	MAMEDriver('Mega CD', EmulatorStatus.Experimental, command_lines.mame_mega_cd, mame_cdrom_formats),
	#Hmm sometimes works and sometimes does not (when does it not? Elaborate, past self)
	MAMEDriver('Microtan 65', EmulatorStatus.Experimental, simple_mame_driver('mt65', 'dump', has_keyboard=True), {'dmp', 'm65'}),
	#System name was "microtan" prior to 0.212
	#Aagggh, none of these inputs seem to be working properly (to the point where I can't just assume the games were like that)... maybe I'm doing it wrong, I don't know…
	MAMEDriver('Microvision', EmulatorStatus.Janky, simple_mame_driver('microvsn', 'cart'), generic_cart_extensions),
	#You probably want to use the software list for this so it can detect controls properly, also needs artwork that doesn't seem to be available anywhere
	MAMEDriver('N64', EmulatorStatus.Experimental, command_lines.mame_n64, {'v64', 'z64', 'rom', 'n64', 'bin'}),
	#Emulates a NTSC console only so PAL games will probably tell you off or otherwise not work properly; also no rumble/mempak/etc for you. Very slow on even modern systems. Marked as non-working.union(imperfect) graphics
	MAMEDriver('Pokemon Mini', EmulatorStatus.Experimental, simple_mame_driver('pokemini', 'cart'), {'bin', 'min'}),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life, also some stuff doesn't work
	MAMEDriver('Saturn', EmulatorStatus.Experimental, command_lines.mame_saturn, mame_cdrom_formats),
	#Non-working, imperfect sound; crashes on quite a few games and hangs to white screen sometimes
	MAMEDriver('Sega Pico', EmulatorStatus.Janky, command_lines.mame_pico, {'bin', 'md'}),
	#Seems like a lot of stuff doesn't get anywhere? Probably needs the book part
	MAMEDriver('Select-a-Game', EmulatorStatus.Janky, simple_mame_driver('sag', 'cart'), {'bin'}),
	#Is now a separate system as of 0.221 instead of sag_whatever individual machines
	#See also Microvision, is similarly janky with needing artwork
	MAMEDriver('Super A\'Can', EmulatorStatus.Experimental, simple_mame_driver('supracan', 'cart'), {'bin'}),
	#Some things work, except with no sound, so... nah
	MAMEDriver('TRS-80', EmulatorStatus.Experimental, simple_mame_driver('trs80l2', 'quik', has_keyboard=True), {'cmd'}),
	#trs80 only has tapes I guess, there are lots of clones of trs80l2
	#I didn't manage to figure out disks, tapes of course require typing non-programmatically-typeable things
	#TRS-80 Model 3 is there but sound seems to not work for backwards compatibility so like I dunno, still need to figure out if I want it as a separate system entirely
	MAMEDriver('V.Smile Baby', EmulatorStatus.Experimental, simple_mame_driver('vsmileb', 'cart'), {'u1', 'u3', 'bin'}),
	#Seems to crash on some titles, also everything in software list is supported=no?
	MAMEDriver('VideoBrain', EmulatorStatus.Experimental, simple_mame_driver('vidbrain', 'cart', has_keyboard=True), {'bin'}),
	#Has some hella glitchy graphics and I'm not gonna call it a playable experience at this point (also it does say not working)
	MAMEDriver('Videoton TVC', EmulatorStatus.Experimental, simple_mame_driver('tvc64', 'cart', has_keyboard=True), {'bin', 'rom', 'crt'}),
	MAMEDriver('Virtual Boy', EmulatorStatus.Experimental, simple_mame_driver('vboy', 'cart'), {'bin', 'vb'}),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there and a lot of software list items are unsupported
	#TODO PlayStation: Would require proper region code detection, which would require looking at ISO9660 stuff properly. Anyway it is MACHINE_NOT_WORKING and often doesn't play the games (see https://mametesters.org/view.php?id=7127)

	#Just here for future use or the fun of creating launchers really; these straight up don't work:
	MAMEDriver('3DO', EmulatorStatus.Borked, simple_mame_driver('3do', 'cdrom'), mame_cdrom_formats), #Should switch to 3do_pal when needed, but it doesn't really matter at this point
	MAMEDriver('Buzztime Home Trivia System', EmulatorStatus.Borked, simple_mame_driver('buzztime', 'cart'), {'bin'}),
	#Inputs are not defined and it just spams random inputs (the game plays itself!!!1)
	MAMEDriver('C64', EmulatorStatus.Borked, command_lines.mame_c64, {'80', 'a0', 'e0', 'crt'}), #Doesn't load carts anymore
	MAMEDriver('Casio Loopy', EmulatorStatus.Borked, simple_mame_driver('casloopy', 'cart'), {'bin'}),
	#Just shows corrupted graphics (and has no controls defined), basically just a skeleton even if it looks like it isn't
	MAMEDriver('Commodore CDTV', EmulatorStatus.Borked, simple_mame_driver('cdtv', 'cdrom'), mame_cdrom_formats),
	#This one works less than CD32; just takes you to the default boot screen like no CD was inserted
	MAMEDriver('Copera', EmulatorStatus.Borked, simple_mame_driver('copera', 'cart'), {'bin', 'md'}),
	#Displays the logo and then displays nothing
	MAMEDriver('GoGo TV Video Vision', EmulatorStatus.Borked, simple_mame_driver('tvgogo', 'cart'), {'bin'}),
	MAMEDriver('Jaguar CD', EmulatorStatus.Borked, simple_mame_driver('jaguarcd', 'cdrom'), mame_cdrom_formats), #Also has cartridge port, as it is a Jaguar addon
	MAMEDriver('Koei PasoGo', EmulatorStatus.Borked, simple_mame_driver('pasogo', 'cart'), {'bin'}),
	#No sound yet, and apparently the rest doesn't work either (I'll take their word for it so I don't have to play weird board games I don't understand)
	MAMEDriver('Tomy Prin-C', EmulatorStatus.Borked, simple_mame_driver('princ', 'cart'), {'bin'}),
	#Skeleton driver that displays a green background and then doesn't go anywhere
	
	#Doesn't even display graphics, I'm just feeling like adding stuff at this point
	MAMEDriver('Advanced Pico Beena', EmulatorStatus.Borked, simple_mame_driver('beena', 'cart'), {'bin'}), #Segfaults
	MAMEDriver('C2 Color', EmulatorStatus.Borked, simple_mame_driver('c2color', 'cart'), {'bin'}),
	MAMEDriver('Didj', EmulatorStatus.Borked, simple_mame_driver('didj', 'cart'), {'bin'}),
	MAMEDriver('Konami Picno', EmulatorStatus.Borked, simple_mame_driver('picno', 'cart'), {'bin'}),
	MAMEDriver('LeapPad', EmulatorStatus.Borked, simple_mame_driver('leappad', 'cart'), {'bin'}),
	MAMEDriver('Leapster', EmulatorStatus.Borked, simple_mame_driver('leapster', 'cart'), {'bin'}), #Sometimes crashes, appears to be executing the CPU and printing debug stuff
	MAMEDriver('MobiGo', EmulatorStatus.Borked, simple_mame_driver('mobigo', 'cart'), {'bin'}),
	MAMEDriver('Monon Color', EmulatorStatus.Borked, simple_mame_driver('mononcol', 'cart'), {'bin'}),
	MAMEDriver('My First LeapPad', EmulatorStatus.Borked, simple_mame_driver('mfleappad', 'cart'), {'bin'}),
	MAMEDriver('Pippin', EmulatorStatus.Borked, simple_mame_driver('pippin', 'cdrom'), mame_cdrom_formats),
	MAMEDriver('Pocket Challenge W', EmulatorStatus.Borked, simple_mame_driver('pockchal', 'cart'), {'bin', 'pcw'}),
	MAMEDriver('V.Reader', EmulatorStatus.Borked, simple_mame_driver('vreader', 'cart'), {'bin'}),
	MAMEDriver('V.Smile Pro', EmulatorStatus.Borked, simple_mame_driver('vsmilpro', 'cdrom'), mame_cdrom_formats),

	#TODO: Comments from systems that indicate I feel the need to create an autoboot for stuff (because I guess typing arcane shit just sucks too much, and yeah it does make me think that some tapes_are_okay or menus_are_okay option is needed)
	#z88: 	#Marked as not working due to missing expansion interface and serial port and other things, not sure how important that would be... anyway, I'd need to do an autoboot thing to press the key to start the thing, because otherwise it's annoying to navigate every time, and then... hmm, I guess I dunno what actually is a function of things not working yet
	#mo6: #Floppies work (and cassettes and carts have same problem as MO5), but this time we need to press the F1 key and I don't waaaanna do that myself
	#to7/to8: 	#Fuck I hate this. Carts need to press 1 on TO7 or press the button with the lightpen on TO8/9 and also they suck, floppies need BASIC cart inserted on TO7 (and then the same method to boot that cart) or press B on TO8/9, tapes are a shitload of fuck right now (same broken as MO5/MO6), not all of this seems to be cross compatible so might need to separate systems or work out what's going on there
	#ti99_4a: 	#Carts need to press the any key and then 2 to actually load them. Floppies are the most asinine irritating thing ever fuck it Actually if we can detect that a floppy has Extended BASIC autoboot that could work with an autoboot script in the same way that cartridges work
	#studio2: #This console sucks and I hate it, anyway; I'd need to make multiple autoboot scripts that press F3 and then combinations of buttons depending on software list > usage somehow? God fuck I hate this console so much. PAL games (and some homebrew stuff) need mpt02
	#bbcb: The key combination to boot a floppy is Shift+Break which is rather awkward to press, so I want an autoboot script
	#electron: Same
	#galaxy/galaxyp:  #This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why. Anyway, we'd go with those and make an autoboot script (maybe just -autoboot_command '\n' would work with suitable delay). galaxy is regular system, galaxyp is an upgraded one which appears to be completely backwards compatible
	#abc80: #Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	#pdp1: MAME needs us to press control panel key.union(read) in, and then it does the thing and all is well
	#zx81: 	#Gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing baaggghghh which is why I haven't bothered trying more of this
	#einstein: Works fine but you need to type in the name of the program (this isn't in the usage field of SL)

	#Have not gotten around to trying:
	#atom
	#CPC/CPC+
	#pcw16 	#Marked as MACHINE_NOT_WORKING and MAME pcw.cpp mentions needing an OS rescue disk, probably doesn't work conveniently or at all
	#apfimag
	#bbcm
	#sorcerer:	#Would need automated tape loading to do anything interesting (carts and floppies are just BASIC/OS stuff, also what even is the file type for floppies?) hnmn so probably not
	#fc100
	#mtx512
	#vector06: 	#MAME driver is marked as working but clones are not; needs to hold F2 then press F11 then F12 to boot from cartridge so that may be wacky; and I can't get that working, not sure if floppies/tapes do work
	#mc10 hmm tapes tho
	#cd2650
	#instruct
	#pipbug
	#nascom/nascom2c
	#cgenie
	#CBM-II
	#compis
	#ep128 #hhhhh needs isdos from software list for floppies I think
	#dragon64
	#elfii

	#Have not gotten around to trying and don't feel like it (give me games or give me death)
	#x07 (video expansion is not there)
	#zorba
	#wmbullet

	#Do the thing idiot:
	#TODO: Commodore PET can work with MAME by using -quik and autoboot, apparently?
	#TODO PC-98 does somewhat work, but I probably want to filter out stuff that requires HDD install (only some stuff autoboots from floppy)
	#TODO: Put Acorn Archimedes MAME driver in there anyway, even if I need to click the thing, I think that is not too unreasonable
}

_libretro_cores = {
	LibretroCore('81', EmulatorStatus.Good, '81', None, {'p', 'tzx', 't81'}),
	LibretroCore('Beetle Cygne', EmulatorStatus.Good, 'mednafen_cygne', None, {'ws', 'wsc', 'pc2'}),
	LibretroCore('Beetle NeoPop', EmulatorStatus.Good, 'mednafen_ngp', None, {'ngp', 'ngc', 'ngpc', 'npc'}),
	LibretroCore('Beetle PCE Fast', EmulatorStatus.Good, 'mednafen_pce_fast', None, {'pce', 'cue', 'ccd', 'toc', 'm3u', 'chd'}),
	LibretroCore('Beetle PCE', EmulatorStatus.Good, 'mednafen_pce', None, {'pce', 'cue', 'ccd', 'sgx', 'toc', 'm3u', 'chd'}),
	LibretroCore('Beetle PC-FX', EmulatorStatus.Good, 'mednafen_pcfx', None, {'cue', 'ccd', 'toc', 'chd', 'm3u'}),
	LibretroCore('Beetle PSX HW', EmulatorStatus.Good, 'mednafen_psx_hw', None, {'cue', 'chd', 'ccd', 'toc', 'm3u', 'exe', 'pbp'}), #needs_fullpath=true
	LibretroCore('Beetle Saturn', EmulatorStatus.Good, 'mednafen_saturn', None, {'cue', 'chd', 'ccd', 'toc', 'm3u'}), #needs_fullpath=true
	LibretroCore('Beetle VB', EmulatorStatus.Good, 'mednafen_vb', None, {'vb', 'vboy', 'bin'}),
	LibretroCore('BlastEm', EmulatorStatus.Good, 'blastem', command_lines.blastem, {'md', 'bin', 'smd', 'gen', 'sms'}), #Does not claim to support Master System in info file, but does
	LibretroCore('blueMSX', EmulatorStatus.Good, 'bluemsx', None, {'dsk', 'rom', 'ri', 'mx1', 'mx2', 'col', 'cas', 'sg', 'sc', 'm3u'}), #Turbo-R does not work, also does not do any dual cartridge shenanigans, or battery saves; needs_fullpath=true
	LibretroCore('bsnes', EmulatorStatus.Good, 'bsnes', command_lines.bsnes_libretro, {'sfc', 'smc', 'gb', 'gbc', 'bs'}, _bsnes_options),
	LibretroCore('bsnes-hd beta', EmulatorStatus.Good, 'bsnes_hd_beta', command_lines.bsnes_libretro, {'sfc', 'smc', 'gb', 'gbc', 'bs'}, _bsnes_options), #Does not claim to support .bs, but does
	LibretroCore('Caprice32', EmulatorStatus.Good, 'cap32', None, {'dsk', 'sna', 'tap', 'cdt', 'voc', 'cpr', 'm3u'}), #cpr will need game override to 6128+, if setting that globally disks won't autoboot; m3u is there to specify load command and not multiple disks; needs_fullpath=true
	LibretroCore('ChaiLove', EmulatorStatus.Good, 'chailove', None, {'chai', 'chailove'}), #needs_fullpath=true
	LibretroCore('Dinothawr', EmulatorStatus.Good, 'dinothawr', None, {'game'}),
	LibretroCore('fMSX', EmulatorStatus.Good, 'fmsx', None, {'rom', 'mx1', 'mx2', 'dsk', 'm3u', 'cas', 'fdi'}),
	LibretroCore('FreeChaF', EmulatorStatus.Good, 'freechaf', None, {'bin', 'chf'}),
	LibretroCore('FreeIntv', EmulatorStatus.Janky, 'freeintv', None, {'int', 'bin', 'rom'}),
	LibretroCore('FreeJ2ME', EmulatorStatus.Imperfect, 'freej2me', None, {'jar'}), #Seems to require a JDK
	LibretroCore('FUSE', EmulatorStatus.Good, 'fuse', None, {'tzx', 'tap', 'z80', 'rzx', 'scl', 'trd', 'dsk'}),
	LibretroCore('Gearboy', EmulatorStatus.Good, 'gearboy', simple_gb_emulator([], {'MBC1', 'MBC2', 'MBC3', 'MBC5'}, {'MBC1 Multicart'}), {'gb', 'dmg', 'gbc', 'cgb', 'sgb'}),
	LibretroCore('Genesis Plus GX', EmulatorStatus.Good, 'genesis_plus_gx', command_lines.genesis_plus_gx, {'mdx', 'md', 'smd', 'gen', 'bin', 'cue', 'iso', 'sms', 'bms', 'gg', 'sg', '68k', 'chd', 'm3u'}), #needs_fullpath=true (but is that just for CD)
	LibretroCore('Hatari', EmulatorStatus.Good, 'hatari', None, {'st', 'msa', 'stx', 'dim', 'm3u'}), #Theoretically supports .ipf but that is not compiled in with the build from the core downloader; needs_fullpath=true
	LibretroCore('LowRes NX', EmulatorStatus.Good, 'lowresnx', None, {'nx'}),
	LibretroCore('Mesen', EmulatorStatus.Good, 'mesen', command_lines.mesen, {'nes', 'fds', 'unf', 'unif'}),
	LibretroCore('melonDS', EmulatorStatus.Good, 'melonds', command_lines.melonds, {'nds'}), #Still no DSi or iQue, OpenGL renderer makes aspect ratio go weird unless using hybrid layout
	LibretroCore('mGBA', EmulatorStatus.Good, 'mgba', command_lines.mgba, {'gb', 'gbc', 'gba'}),
	LibretroCore('Mu', EmulatorStatus.Janky, 'mu', None, {'prc', 'pqa', 'img', 'pdb'}), #Still need to select application manually from emulated menu
	LibretroCore('Mupen64Plus-Next', EmulatorStatus.Good, 'mupen64plus_next', None, {'n64', 'v64', 'z64', 'bin', 'u1'}), #TODO: Command line function to reject roms with no detectable endianness
	LibretroCore('NeoCD', EmulatorStatus.Good, 'neocd', None, {'cue', 'chd'}),
	LibretroCore('O2EM', EmulatorStatus.Good, 'o2em', None, {'bin'}),
	LibretroCore('Opera', EmulatorStatus.Imperfect, 'opera', None, {'iso', 'chd', 'bin', 'cue'}), #needs_fullpath=true
	LibretroCore('PicoDrive', EmulatorStatus.Good, 'picodrive', simple_md_emulator([], {'pokestad', 'lion3'}), {'bin', 'gen', 'smd', 'md', '32x', 'chd', 'cue', 'iso', 'sms', '68k', 'm3u'}), #Lion King 3 is automatically detected but no other games using the same mapper work, so I guess we will pretend it's not a working mapper; needs_fullpath=true (for CDs?)
	LibretroCore('PokeMini', EmulatorStatus.Good, 'pokemini', None, {'min'}),
	LibretroCore('Potator', EmulatorStatus.Good, 'potator', None, {'bin', 'sv'}),
	LibretroCore('ProSystem', EmulatorStatus.Good, 'prosystem', command_lines.prosystem, {'a78', 'bin'}),
	LibretroCore('PUAE', EmulatorStatus.Good, 'puae', None, {'adf', 'adz', 'dms', 'fdi', 'ipf', 'hdf', 'hdz', 'lha', 'slave', 'info', 'cue', 'ccd', 'nrg', 'mds', 'iso', 'chd', 'uae', 'm3u', 'rp9'}), #Does require you to switch between RetroPad and CD32 pad accordingly…; needs_fullpath=true
	LibretroCore('PX68k', EmulatorStatus.Good, 'px68k', None, {'dim', 'img', 'd88', '88d', 'hdm', 'dup', '2hd', 'xdf', 'hdf', 'cmd', 'm3u'}), #needs_fullpath=true (tricky thing is that it might overwrite your uncompressed files if you leave them uncompressed? or something)
	LibretroCore('SameBoy', EmulatorStatus.Good, 'sameboy', simple_gb_emulator([], {'MBC1', 'MBC2', 'MBC3', 'MBC5', 'HuC1', 'HuC3', 'Pocket Camera'}, {'MBC1 Multicart'}), {'gb', 'gbc'}),
	LibretroCore('SameDuck', EmulatorStatus.Good, 'sameduck', None, {'bin'}),
	LibretroCore('Stella', EmulatorStatus.Good, 'stella', None, {'a26', 'bin'}),
	LibretroCore('Uzem', EmulatorStatus.Good, 'uzem', None, {'uze'}),
	LibretroCore('Vecx', EmulatorStatus.Good, 'vecx', None, {'vec', 'bin'}),
	LibretroCore('VeMUlator', EmulatorStatus.Imperfect, 'vemulator', None, {'vms', 'dci', 'bin'}), #Does a heckin bzzzz with a lot of things
	LibretroCore('Virtual Jaguar', EmulatorStatus.Imperfect, 'virtualjaguar', None, {'j64', 'jag', 'rom', 'abs', 'cof', 'bin', 'prg'}),
	LibretroCore('X Millennium', EmulatorStatus.Good, 'x1', None, {'dx1', '2d', '2hd', 'tfd', 'd88', '88d', 'hdm', 'xdf', 'dup', 'cmd'}), #Claims to support tap but doesn't
}

emulators = {standalone_emulator.config_name: standalone_emulator for standalone_emulator in _standalone_emulators}
libretro_cores = {core.name: core for core in _libretro_cores}

_dos_emulators = {
	Emulator('DOSBox Staging', EmulatorStatus.Good, 'dosbox', command_lines.dosbox_staging, {
		'cycles_for_477_mhz': RunnerConfigValue(ConfigValueType.Integer, 245, 'CPU cycles to use to get as close as possible to 4.77MHz'),
		'noautoexec': RunnerConfigValue(ConfigValueType.Bool, False, 'Do not load [autoexec] section in config file'),
		'overlay_path': RunnerConfigValue(ConfigValueType.FolderPath, None, 'If set to something, use a subfolder of this path as an overlay so save games etc are written there'),
	}),
	Emulator('DOSBox-X', EmulatorStatus.Good, 'dosbox-x', command_lines.dosbox_x),
}
_mac_emulators = {
	Emulator('BasiliskII', EmulatorStatus.Janky, 'BasiliskII', command_lines.basilisk_ii, {
		'skip_if_ppc_enhanced': RunnerConfigValue(ConfigValueType.Bool, False, 'If the app has ppc_enhanced = true in its config ie. it performs better or has some extra functionality on PPC, do not use BasiliskII for it')
	}),
	Emulator('SheepShaver', EmulatorStatus.Janky, 'SheepShaver', command_lines.sheepshaver),
	
}
dos_emulators = {emu.name: emu for emu in _dos_emulators}
mac_emulators = {emu.name: emu for emu in _mac_emulators}

_libretro_frontends = {
	LibretroFrontend('RetroArch', EmulatorStatus.Good, 'retroarch', command_lines.retroarch, {'7z', 'zip'}),
}
libretro_frontends = {frontend.name: frontend for frontend in _libretro_frontends}

#Basically this is here for the purpose of generating configs
#TODO: Return an iterator and make a "has config" interface so we don't have to invent _JustHereForConfigValues
#all_emulators: MutableSequence[Union[Emulator, LibretroFrontend]] = _standalone_emulators
all_emulators: MutableSequence[Union[Emulator[EmulatedGame], LibretroFrontend, '_JustHereForConfigValues']] = []
all_emulators += _standalone_emulators
all_emulators += _libretro_cores
all_emulators += _dos_emulators
all_emulators += _mac_emulators
all_emulators += _libretro_frontends
mame: Emulator['MAMEGame'] = Emulator('MAME', EmulatorStatus.Good, 'mame', command_lines.mame)
all_emulators.append(mame)
#Ensure one can have globally defined options for all ViceEmulators or MednafenModules etc
class _JustHereForConfigValues(Runner):
	def __init__(self, name: str, default_exe_name: str='') -> None:
		super().__init__()
		self.config_name = name
		self.default_exe_name = default_exe_name

	@property
	def name(self) -> str:
		return self.config_name
all_emulators.append(_JustHereForConfigValues('Mednafen', 'mednafen'))
all_emulators.append(_JustHereForConfigValues('VICE'))
