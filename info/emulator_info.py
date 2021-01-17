from enum import Enum

import info.emulator_command_lines as command_lines
from info.emulator_command_line_helpers import mame_driver_callable, mednafen_module_callable #It would be infeasible to create a function in emulator_command_lines for everything, I guess
from common_types import ConfigValueType

from .format_info import (atari_2600_cartridge_extensions,
                          generic_cart_extensions, mame_cdrom_formats,
                          mame_floppy_formats)

class EmulatorConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type, default_value, description):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class EmulatorStatus(Enum):
	#I have not actually thought of concrete definitions for what these mean
	Good = 6
	Imperfect = 5
	ExperimentalButSeemsOkay = 4
	Experimental = 3
	Janky = 2 #Weird to set up or launch normally
	Borked = 1

class EmulatorInfo():
	def __init__(self, status, default_exe_name, launch_params_func, supported_extensions, supported_compression, configs=None):
		self.status = status
		self.default_exe_name = default_exe_name
		self.get_launch_params = launch_params_func
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression
		self.configs = configs if configs else {}

class MednafenModule(EmulatorInfo):
	def __init__(self, status, module, supported_extensions, params_func=None, configs=None):
		if not params_func:
			params_func = mednafen_module_callable(module)
		EmulatorInfo.__init__(self, status, 'mednafen', params_func, supported_extensions, ['zip', 'gz'], configs)

class MameDriver(EmulatorInfo):
	def __init__(self, status, launch_params, supported_extensions, configs=None):
		if configs is None:
			configs = {}
		configs.update({
			'software_compatibility_threshold': EmulatorConfigValue(ConfigValueType.Integer, 1, '0 = broken 1 = imperfect 2 = working other value = ignore; anything in the software list needs this to be considered compatible or -1 to ignore'),
			'skip_unknown_stuff': EmulatorConfigValue(ConfigValueType.Bool, False, "Skip anything that doesn't have a match in the software list"),
		})
		
		EmulatorInfo.__init__(self, status, 'mame', launch_params, supported_extensions, ['7z', 'zip'], configs)

class ViceEmulator(EmulatorInfo):
	def __init__(self, status, default_exe_name, params):
		#Also does z and zoo compression but I haven't done those in archives.py yet
		#WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
		#Does support compressed tapes/disks (gz/bz2/zip/tgz) but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here. So for now we pretend it supports no compression so we end up getting 7z to put the thing in a temporarily folder regardless
		EmulatorInfo.__init__(self, status, default_exe_name, params, ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m'] + ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin'] + ['p00', 'prg', 'tap', 't64'], [])

emulators = {
	'A7800': EmulatorInfo(EmulatorStatus.Good, 'a7800', command_lines.a7800, ['bin', 'a78'], ['7z', 'zip']),
	#Forked directly from MAME with alterations to a7800.cpp driver, so will more or less work the same way as that
	#Executable name might be a7800.Linux-x86_64 depending on how it's installed... hmm
	'bsnes': EmulatorInfo(EmulatorStatus.Good, 'bsnes', command_lines.bsnes, ['sfc', 'smc', 'st', 'bs', 'gb', 'gbc'], ['zip', '7z'], {
		'sgb_incompatible_with_gbc': EmulatorConfigValue(ConfigValueType.Bool, True, 'Consider Super Game Boy as incompatible with carts with any GBC compatibility, even if they are DMG compatible'),
		'sgb_enhanced_only': EmulatorConfigValue(ConfigValueType.Bool, False, 'Consider Super Game Boy to only support games that are specifically enhanced for it'),
	}),
	'cxNES': EmulatorInfo(EmulatorStatus.Good, 'cxnes', command_lines.cxnes, ['nes', 'fds', 'unf', 'unif'], ['7z', 'zip']),
	#Or is it good? Have not tried it in a fair bit
	'Dolphin': EmulatorInfo(EmulatorStatus.Good, 'dolphin-emu', command_lines.dolphin, ['iso', 'ciso', 'gcm', 'gcz', 'tgc', 'elf', 'dol', 'wad', 'wbfs', 'm3u', 'wia', 'rvz'], []),
	'DuckStation': EmulatorInfo(EmulatorStatus.Good, 'duckstation-qt', command_lines.duckstation, ['bin', 'img', 'cue', 'chd', 'exe', 'm3u', 'iso'], [], {
		'compatibility_xml_path': EmulatorConfigValue(ConfigValueType.FilePath, None, 'Path to where compatibility.xml is installed'), #Because DuckStation's not always installed in any particular location…
		'compatibility_threshold': EmulatorConfigValue(ConfigValueType.Integer, 2, "Don't try and launch any game with this compatibility rating or lower"),
		'consider_unknown_games_incompatible': EmulatorConfigValue(ConfigValueType.Bool, False, "Consider games incompatible if they aren't in the compatibility database at all")
	}),
	'Flycast': EmulatorInfo(EmulatorStatus.Good, 'flycast', command_lines.flycast, ['gdi', 'cdi', 'chd', 'cue'], [], {
		'force_opengl_version': EmulatorConfigValue(ConfigValueType.Bool, False, 'Hack to force Mesa OpenGL version by environment variable if you need it')
	}),
	'FS-UAE': EmulatorInfo(EmulatorStatus.Good, 'fs-uae', command_lines.fs_uae, ['iso', 'cue', 'adf', 'ipf'], []),
	#Note that .ipf files need a separately downloadable plugin. We could detect the presence of that, I guess
	'Gambatte': EmulatorInfo(EmulatorStatus.Good, 'gambatte_qt', command_lines.gambatte, ['gb', 'gbc'], ['zip']),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations, but that would probably require a specific thing that notes some GBC games are incompatible with GBA mode (Pocket Music) or GB incompatible with GBC (R-Type, also Pocket Sonar but that wouldn't work anyway)
	'GBE+': EmulatorInfo(EmulatorStatus.Good, 'gbe_plus_qt', command_lines.gbe_plus, ['gb', 'gbc', 'gba'], []),
	#Also in theory recognizes any extension and assumes Game Boy if not .gba or .nds, but that would be screwy
	'Kega Fusion': EmulatorInfo(EmulatorStatus.Good, 'kega-fusion', command_lines.kega_fusion, ['bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', 'sc', '32x'], ['zip']),
	#May support other CD formats for Mega CD other than iso, cue? Because it's closed source, can't really have a look, but I'm just going to presume it's only those two
	'mGBA': EmulatorInfo(EmulatorStatus.Good, 'mgba-qt', command_lines.mgba, ['gb', 'gbc', 'gba', 'srl', 'bin', 'mb', 'gbx'], ['7z', 'zip']),
	#Doesn't really do GBX but it will ignore the footer
	'melonDS': EmulatorInfo(EmulatorStatus.Good, 'melonDS', command_lines.melonds, ['nds', 'srl'], []), #Supports .dsi too, but I'm acting as though it doesn't, because it's too screwy
	'Mupen64Plus': EmulatorInfo(EmulatorStatus.Good, 'mupen64plus', command_lines.mupen64plus, ['z64', 'v64', 'n64'], []),
	'PCSX2': EmulatorInfo(EmulatorStatus.Good, 'PCSX2', command_lines.pcsx2, ['iso', 'cso', 'bin'], ['gz']),
	#Takes some time to load the interface so at first it might look like it's not working; take out --fullboot if it forbids any homebrew stuff (but it should be fine, and certain games might need it).  ELF seems to not work, though it'd need a different command line anyway. Only reads the bin of bin/cues and not the cue
	'PokeMini': EmulatorInfo(EmulatorStatus.Janky, 'PokeMini', command_lines.pokemini, ['min'], ['zip']),
	#Puts all the config files in the current directory, which is why there's a wrapper below which you probably want to use instead of this
	#Should I even have this as opposed to just having the wrapper?
	'PokeMini (wrapper)': EmulatorInfo(EmulatorStatus.Good, 'PokeMini', command_lines.pokemini_wrapper, ['min'], ['zip']),
	'PPSSPP': EmulatorInfo(EmulatorStatus.Good, 'ppsspp-qt', command_lines.ppsspp, ['iso', 'pbp', 'cso'], []),
	'Reicast': EmulatorInfo(EmulatorStatus.Good, 'reicast', command_lines.reicast, ['gdi', 'cdi', 'chd'], [], {
		'force_opengl_version': EmulatorConfigValue(ConfigValueType.Bool, False, 'Hack to force Mesa OpenGL version by environment variable if you need it')
	}),
	'SimCoupe': EmulatorInfo(EmulatorStatus.Good, 'simcoupe', command_lines.simcoupe, ['mgt', 'sad', 'dsk', 'sbt'], ['zip', 'gz']),
	'Snes9x': EmulatorInfo(EmulatorStatus.Good, 'snes9x-gtk', command_lines.snes9x, ['sfc', 'smc', 'swc'], ['zip', 'gz']),
	#Can't set fullscreen mode from the command line so you have to set up that yourself (but it will do that automatically); GTK port can't do Sufami Turbo or Satellaview from command line due to lacking multi-cart support that Windows has (Unix non-GTK doesn't like being in fullscreen etc)
	'Stella': EmulatorInfo(EmulatorStatus.Good, 'stella', command_lines.stella, ['a26', 'bin', 'rom'] + atari_2600_cartridge_extensions, ['gz', 'zip']),
	'PrBoom+': EmulatorInfo(EmulatorStatus.Imperfect, 'prboom-plus', command_lines.prboom_plus, ['wad'], []),
	#Joystick support not so great, otherwise it plays perfectly well with keyboard + mouse; except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay

	'VICE (C64)': ViceEmulator(EmulatorStatus.Good, 'x64sc', command_lines.vice_c64),
	#x64 and x64sc have the same command line structure, just different exe names
	'VICE (C64 Fast)': ViceEmulator(EmulatorStatus.Good, 'x64', command_lines.vice_c64),
	'VICE (VIC-20)': ViceEmulator(EmulatorStatus.Good, 'xvic', command_lines.vice_vic20),
	'VICE (Commodore PET)': ViceEmulator(EmulatorStatus.Good, 'xpet', command_lines.vice_pet),
	'VICE (Plus/4)': ViceEmulator(EmulatorStatus.Good, 'xplus4', command_lines.vice_plus4),
	'VICE (C128)': ViceEmulator(EmulatorStatus.Good, 'x128', command_lines.vice_c128),

	'Mednafen (Apple II)': MednafenModule(EmulatorStatus.Good, 'apple2', ['woz', 'dsk', 'po', 'do', 'd13'], command_lines.mednafen_apple_ii),
	#Seems fine but no Apple IIe/128K?
	'Mednafen (Lynx)': MednafenModule(EmulatorStatus.Good, 'lynx', ['lnx', 'lyx', 'o'], command_lines.mednafen_lynx),
	#Based on Handy, but that hasn't been updated in 14 years, so I guess this probably has some more updates
	'Mednafen (Neo Geo Pocket)': MednafenModule(EmulatorStatus.Good, 'ngp', ['ngp', 'npc', 'ngc']),
	#Based off NeoPop, which hasn't been updated in 15 years, so presumably with improvements. Does say that this is unsuitable for homebrew development (due to lack of accuracy) and MAME is more suitable for that, so believe that if you want
	'Mednafen (NES)': MednafenModule(EmulatorStatus.Good, 'nes', ['nes', 'fds', 'unf'], command_lines.mednafen_nes),
	#Based off FCEU, so not quite cycle-accurate but it works
	'Mednafen (PC Engine)': MednafenModule(EmulatorStatus.Good, 'pce', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	'Mednafen (PC-FX)': MednafenModule(EmulatorStatus.Good, 'pcfx', ['iso', 'cue', 'toc', 'ccd', 'm3u']), #Do NOT specify a FX-SCSI BIOS
	'Mednafen (PlayStation)': MednafenModule(EmulatorStatus.Good, 'psx', ['iso', 'cue', 'exe', 'toc', 'ccd', 'm3u', 'psx']),
	'Mednafen (Virtual Boy)': MednafenModule(EmulatorStatus.Good, 'vb', ['bin', 'vb', 'vboy']),
	'Mednafen (WonderSwan)': MednafenModule(EmulatorStatus.Good, 'wswan', ['ws', 'wsc', 'bin', 'pc2']),
	#Based on Cygne, definitely heavily modified by now

	'MAME (Amstrad GX4000)': MameDriver(EmulatorStatus.Imperfect, mame_driver_callable('gx4000', 'cart'), ['bin', 'cpr']),
	#MT06201 (issue with emulated monochrome monitor), MT6509 lists various compatibility issues
	'MAME (APF-MP1000)': MameDriver(EmulatorStatus.Good, mame_driver_callable('apfm1000', 'cart'), ['bin']),
	'MAME (Apple II)': MameDriver(EmulatorStatus.Good, command_lines.mame_apple_ii, mame_floppy_formats + ['do', 'po', 'woz']),
	'MAME (Apple IIgs)': MameDriver(EmulatorStatus.Good, mame_driver_callable('apple2gsr1', 'flop3', {'gameio': 'joy'}, has_keyboard=True), mame_floppy_formats + ['2mg', '2img', 'dc']),
	#Rev 1 is needed because some stuff doesn't work on rev 3 (happens in real life), flop1 and flop2 are for Apple II-not-GS software
	#ramsize can go up to 8M if need be and there are a lot of slot options (4play might be useful for our 1337 pro gaming purposes? arcbd sounds cool?)
	'MAME (Apple III)': MameDriver(EmulatorStatus.Good, mame_driver_callable('apple3', 'flop1', has_keyboard=True), mame_floppy_formats + ['do', 'po']),
	'MAME (Arcadia 2001)': MameDriver(EmulatorStatus.Good, mame_driver_callable('arcadia', 'cart'), ['bin']),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all
	#MT06642: Wrong background colours
	'MAME (Astrocade)': MameDriver(EmulatorStatus.Good, mame_driver_callable('astrocde', 'cart', {'exp': 'rl64_ram'}), ['bin']),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	'MAME (Atari 2600)': MameDriver(EmulatorStatus.Good, command_lines.mame_atari_2600, ['bin', 'a26']),
	'MAME (Atari 5200)': MameDriver(EmulatorStatus.Imperfect, mame_driver_callable('a5200', 'cart'), ['bin', 'rom', 'car', 'a52']),
	#Could use -sio casette -cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory (or is that just there because Atari 8-bit computers can do that)
	#MT06972: Nondescript input issues; MT07248: Galaxian doesn't work
	'MAME (Atari 7800)': MameDriver(EmulatorStatus.Good, command_lines.mame_atari_7800, ['bin', 'a78']),
	'MAME (Atari 8-bit)': MameDriver(EmulatorStatus.Good, command_lines.mame_atari_8bit, ['bin', 'rom', 'car', 'atr', 'dsk']),
	#Has issues with XEGS carts that it should be able to load (because they do run on the real system) but it says it doesn't because they should be run on XEGS instead, and then doesn't support a few cart types anyway; otherwise fine
	'MAME (Bandai Super Vision 8000)': MameDriver(EmulatorStatus.Good, mame_driver_callable('sv8000', 'cart'), ['bin']),
	'MAME (BBC Bridge Companion)': MameDriver(EmulatorStatus.Good, mame_driver_callable('bbcbc', 'cart'), ['bin']),
	'MAME (C64)': MameDriver(EmulatorStatus.Good, command_lines.mame_c64, ['80', 'a0', 'e0', 'crt']),
	'MAME (Casio PV-1000)': MameDriver(EmulatorStatus.Good, mame_driver_callable('pv1000', 'cart'), ['bin']),
	'MAME (Champion 2711)': MameDriver(EmulatorStatus.Good, mame_driver_callable('unichamp', 'cart'), generic_cart_extensions),
	'MAME (Channel F)': MameDriver(EmulatorStatus.Good, mame_driver_callable('channelf', 'cart'), ['bin', 'chf']),
	'MAME (ColecoVision)': MameDriver(EmulatorStatus.Good, command_lines.mame_colecovision, ['bin', 'col', 'rom']),
	#MT06554: Roller controller is inaccurate
	'MAME (Coleco Adam)': MameDriver(EmulatorStatus.Good, command_lines.mame_coleco_adam, ['wav', 'ddp'] + mame_floppy_formats),
	#Both disks and tapes autoboot. Woohoo!
	'MAME (Entex Adventure Vision)': MameDriver(EmulatorStatus.Imperfect, mame_driver_callable('advision', 'cart'), ['bin']),
	'MAME (FM-7)': MameDriver(EmulatorStatus.Good, mame_driver_callable('fm77av', 'flop1', has_keyboard=True), mame_floppy_formats),
	#Tapes work, but they require run"" and then pressing play on the tape, the latter not being Lua-autoboot-scriptable yet.
	#Difference between fm7 and fmnew7 seems to be that the latter boots into BASIC by default (there's dip switches involved) instead of DOS, which seems to be required for tapes to work; and disks just autoboot anyway. FM-77AV is used here despite its allegedly imperfect graphics as there are games which won't work on earlier systems and there doesn't seem to be a programmatic way to tell, and it seems backwards compatibility is fine
	#Joystick only works with fm7/fmnew7 -centronics dsjoy... whoops; not sure what the builtin joystick does then
	'MAME (G7400)': MameDriver(EmulatorStatus.Good, mame_driver_callable('g7400', 'cart'), ['bin', 'rom']),
	#There is also an unreleased odyssey3 prototype if that is useful for USA (presumably unreleased) games, also jotac for France
	#Should this be merged with Odyssey 2 if it's compatible like that?
	'MAME (Gamate)': MameDriver(EmulatorStatus.Good, mame_driver_callable('gamate', 'cart'), ['bin']),
	'MAME (Game Boy)': MameDriver(EmulatorStatus.Imperfect, command_lines.mame_game_boy, ['bin', 'gb', 'gbc'], {
		'use_gbc_for_dmg': EmulatorConfigValue(ConfigValueType.Bool, True, 'Use MAME GBC driver for DMG games'),
		'prefer_sgb_over_gbc': EmulatorConfigValue(ConfigValueType.Bool, False, 'If a game is both SGB and GBC enhanced, use MAME SGB driver instead of GBC'),
	}),
	#This supports some bootleg mappers that other emus tend to not; fails on really fancy tricks like the Demotronic trick (it does run the demo, but the effect doesn't look right); and has sound issues with GBC (MT06441, MT04949)
	#There are comments in the source file that point out that Super Game Boy should be part of the snes driver with the BIOS cart inserted, rather than a separate system, so that might not exist in the future
	'MAME (Game.com)': MameDriver(EmulatorStatus.Good, mame_driver_callable('gamecom', 'cart1'), ['bin', 'tgc']),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything.
	'MAME (Game Gear)': MameDriver(EmulatorStatus.Good, command_lines.mame_game_gear, ['bin', 'gg']),
	'MAME (Epoch Game Pocket Computer)': MameDriver(EmulatorStatus.Good, mame_driver_callable('gamepock', 'cart'), ['bin']),
	'MAME (GBA)': MameDriver(EmulatorStatus.Good, mame_driver_callable('gba', 'cart'), ['bin', 'gba']),
	#Does not let you do GBA-enhanced GBC games
	'MAME (IBM PCjr)': MameDriver(EmulatorStatus.Good, command_lines.mame_ibm_pcjr, mame_floppy_formats + ['img', 'bin', 'jrc']),
	'MAME (Intellivision)': MameDriver(EmulatorStatus.Good, command_lines.mame_intellivision, ['bin', 'int', 'rom', 'itv']),
	'MAME (Jupiter Ace)': MameDriver(EmulatorStatus.Good, mame_driver_callable('jupace', 'dump', {'ramsize': '48K'}, has_keyboard=True), ['ace']),
	'MAME (Lynx)': MameDriver(EmulatorStatus.Good, command_lines.mame_lynx, ['lnx', 'lyx', 'o']),
	#Could be weird where rotation is involved
	'MAME (Magnavox Odyssey²)': MameDriver(EmulatorStatus.Good, command_lines.mame_odyssey2, ['bin', 'rom']),
	'MAME (Master System)': MameDriver(EmulatorStatus.Good, command_lines.mame_master_system, ['bin', 'sms']),
	'MAME (Mattel Juice Box)': MameDriver(EmulatorStatus.Good, mame_driver_callable('juicebox', 'memcard'), ['smc']),
	'MAME (Mega Drive)': MameDriver(EmulatorStatus.Good, command_lines.mame_megadrive, ['bin', 'md', 'smd', 'gen']),
	'MAME (Mega Duck)': MameDriver(EmulatorStatus.Good, mame_driver_callable('megaduck', 'cart'), ['bin']),
	'MAME (Memorex VIS)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vis', 'cdrom'), mame_cdrom_formats),
	'MAME (MSX)': MameDriver(EmulatorStatus.Good, command_lines.mame_msx1, generic_cart_extensions + mame_floppy_formats),
	'MAME (MSX2)': MameDriver(EmulatorStatus.Good, command_lines.mame_msx2, generic_cart_extensions + mame_floppy_formats),
	'MAME (MSX2+)': MameDriver(EmulatorStatus.Good, command_lines.mame_msx2plus, generic_cart_extensions + mame_floppy_formats),
	'MAME (Neo Geo CD)': MameDriver(EmulatorStatus.Good, mame_driver_callable('neocdz', 'cdrom'), mame_cdrom_formats),
	#Don't think it has region lock so I should never need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	'MAME (Neo Geo Pocket)': MameDriver(EmulatorStatus.Good, mame_driver_callable('ngpc', 'cart'), ['bin', 'ngp', 'npc', 'ngc']),
	'MAME (NES)': MameDriver(EmulatorStatus.Good, command_lines.mame_nes, ['nes', 'unf', 'unif', 'fds']),
	#Supports a lot of mappers actually, probably not as much as Mesen or puNES would, but it's up there; also a lot of cool peripherals
	'MAME (Nichibutsu My Vision)': MameDriver(EmulatorStatus.Good, mame_driver_callable('myvision', 'cart'), ['bin']),
	'MAME (PC Engine)': MameDriver(EmulatorStatus.Good, command_lines.mame_pc_engine, ['pce', 'bin', 'sgx']),
	'MAME (SAM Coupe)': MameDriver(EmulatorStatus.Good, mame_driver_callable('samcoupe', 'flop1', autoboot_script='sam_coupe', has_keyboard=True), mame_floppy_formats),
	'MAME (SG-1000)': MameDriver(EmulatorStatus.Good, command_lines.mame_sg1000, ['bin', 'sg', 'sc', 'sf', 'sf7'] + mame_floppy_formats),
	'MAME (Sharp X1)': MameDriver(EmulatorStatus.Good, mame_driver_callable('x1turbo40', 'flop1', has_keyboard=True), mame_floppy_formats + ['2d']),
	#x1turbo doesn't work, and I'm not sure what running x1 over x1turbo40 would achieve (hope there's no compatibility shenanigans)
	'MAME (Sharp X68000)': MameDriver(EmulatorStatus.Good, command_lines.mame_sharp_x68000, mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim', 'm3u']),
	#It doesn't	really support m3u, but I'm going to make it so it does (multi-disk games seem fairly common)
	#All the other models of X68000 (x68030, x68ksupr, x68kxvi) don't work yet
	'MAME (SNES)': MameDriver(EmulatorStatus.Good, command_lines.mame_snes, ['sfc', 'bs', 'st', 'smc', 'swc']),
	'MAME (Sord M5)': MameDriver(EmulatorStatus.Good, command_lines.mame_sord_m5, ['bin']),
	'MAME (Super Cassette Vision)': MameDriver(EmulatorStatus.Good, command_lines.mame_super_cassette_vision, ['bin']),
	'MAME (SVI-3x8)': MameDriver(EmulatorStatus.Good, mame_driver_callable('svi328', 'cart'), ['bin', 'rom']),
	'MAME (Squale)': MameDriver(EmulatorStatus.Good, mame_driver_callable('squale', 'cart', has_keyboard=True), ['bin']),
	'MAME (Tandy CoCo)': MameDriver(EmulatorStatus.Good, mame_driver_callable('coco3', 'cart', has_keyboard=True), ['ccc', 'rom', 'bin']),
	#There is a coco3p, but it apparently runs at 60Hz too, so I'm not sure if it's needed
	'MAME (Thomson MO5)': MameDriver(EmulatorStatus.Good, mame_driver_callable('mo5', 'flop1', has_keyboard=True), ['fd', 'sap'] + mame_floppy_formats),
	#Cartridges do not work (or on MO6) but floppies do autoboot, cassettes do not like to load either (would need to type LOAD and enter but then it plays it for you, but then stops because I guess it's broken) (MO6 is broken as well); qd would not work without setting the floppy type to quad density in Machine Configuration which we cannot do programmatically
	#Use mo5e for export version or mo5nr for network version (I don't know what they would be useful for)
	'MAME (Tomy Tutor)': MameDriver(EmulatorStatus.Good, mame_driver_callable('tutor', 'cart', has_keyboard=True, autoboot_script='tomy_tutor'), ['bin']),
	#There is pyuuta if you want to read Japanese instead
	'MAME (TRS-80)': MameDriver(EmulatorStatus.Good, mame_driver_callable('trs80l2', 'quik', has_keyboard=True), ['cmd']),
	#trs80 only has tapes I guess, there are lots of clones of trs80l2
	#I didn't manage to figure out disks, tapes of course require typing non-programmatically-typeable things
	#TRS-80 Model 3 is there but sound seems to not work for backwards compatibility so like I dunno, still need to figure out if I want it as a separate system entirely
	'MAME (VC 4000)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vc4000', 'cart'), ['bin', 'rom']),
	#There's like 30 different clones of this, and most of them aren't even clones in the MAME sense, they're literally hardware clones. But they're apparently all software-compatible, although the cartridges aren't hardware-compatible, they just contain the same software... so this all gets confusing. Anyway, the software list with all these is named "vc4000" so I guess that's the "main" one, so we'll use that. Seems that all models use 50Hz display so there shouldn't need to be model switching based on TV type
	#TODO: Quickload slot (.pgm, .tvc)
	'MAME (Vectrex)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vectrex', 'cart'), ['bin', 'gam', 'vec']),
	#Includes overlays as selectable artwork, but that has to be done by the user from the menu
	'MAME (VIC-10)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), ['crt', '80', 'e0']),
	#More similar to the C64 (works and performs just as well as that driver) than the VIC-20, need to plug a joystick into both ports because once again games can use either port and thanks I hate it. At least there's only one TV type
	#Sometimes I see this called the Commodore MAX Machine or Ultimax or VC-10, but... well, I'm not sure where the VIC-10 name comes from other than that's what the driver's called
	'MAME (VIC-20)': MameDriver(EmulatorStatus.Good, command_lines.mame_vic_20, ['20', '40', '60', '70', 'a0', 'b0', 'crt']),
	'MAME (V.Smile)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vsmile', 'cart'), generic_cart_extensions),
	'MAME (V.Smile Motion)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vsmilem', 'cart'), generic_cart_extensions),
	#No motion controls, but the games are playable without them
	'MAME (VZ-200)': MameDriver(EmulatorStatus.Good, mame_driver_callable('vz200', 'dump', {'io': 'joystick', 'mem': 'laser_64k'}, True), ['vz']),
	#In the Laser 200/Laser 210 family, but Dick Smith variant should do.
	#Joystick interface doesn't seem to be used by any games, but I guess it does more than leaving the IO slot unfilled. That sucks, because otherwise no game ever uses the keyboard consistently, because of course not. Even modern homebrew games. Why y'all gotta be like that?
	#Some games will need you to type RUN to run them, not sure how to detect that.
	'MAME (Watara Supervision)': MameDriver(EmulatorStatus.Good, mame_driver_callable('svision', 'cart'), ['bin', 'ws', 'sv']),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes the colours look even worse (they're all inverted and shit)
	'MAME (WonderSwan)': MameDriver(EmulatorStatus.Good, mame_driver_callable('wscolor', 'cart'), ['ws', 'wsc', 'bin', 'pc2']),
	#Could also be weird where rotation is involved, but at least it selects the right way around on startup
	'MAME (ZX Spectrum)': MameDriver(EmulatorStatus.Good, command_lines.mame_zx_spectrum, ['ach', 'frz', 'plusd', 'prg', 'sem', 'sit', 'sna', 'snp', 'snx', 'sp', 'z80', 'zx', 'bin', 'rom', 'raw', 'scr'] + mame_floppy_formats),
	#.trd would be doable with -exp beta128, but that only autoboots on Spectrum 48K (128K needs 128 Basic > "randomize usr 15616" > j > enter) and everything is designed for 128K
	#.opu .opd might work with -exp opus, but that seems to only work on 48K and one must type "run"

	#----- The experimental section. The emulators are still here, it's just so you, the fabulous and wonderful end user, can have more information on how to manage expectations. Or something like that.

	#--These experimental emulators seem to work more often than they don't, but still describe themselves as experimental:
	'Citra': EmulatorInfo(EmulatorStatus.ExperimentalButSeemsOkay, 'citra-qt', command_lines.citra, ['3ds', 'cxi', '3dsx'], []),
	#No fullscreen from command line
	'Medusa': EmulatorInfo(EmulatorStatus.ExperimentalButSeemsOkay, 'medusa-emu-qt', command_lines.medusa, ['nds', 'gb', 'gbc', 'gba'], ['7z', 'zip']),
	'Yuzu': EmulatorInfo(EmulatorStatus.ExperimentalButSeemsOkay, 'yuzu', command_lines.yuzu, ['xci', 'nsp', 'nro', 'nso', 'nca', 'elf', 'kip'], []),

	'Mednafen (Game Boy)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'gb', ['gb', 'gbc'], command_lines.mednafen_gb),
	#Based off an old version of VisualBoyAdvance
	'Mednafen (Game Gear)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'gg', ['gg'], command_lines.mednafen_game_gear),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes". This is based off SMS Plus
	'Mednafen (GBA)': MednafenModule('gba', ['gba'], command_lines.mednafen_gba),
	#Based off an old version of VisualBoyAdvance
	'Mednafen (Master System)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'sms', ['sms', 'bin']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes". Based off SMS Plus
	'Mednafen (Mega Drive)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'md', ['md', 'bin', 'gen', 'smd', 'sgd'], command_lines.mednafen_megadrive),
	#Based off Genesis Plus and an older GPL version of Genesis Plus GX, with all GPL-incompatible cores replaced with alternatives (sound chip emulation from Gens, Z80 from FUSE). Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
	'Mednafen (PC Engine Fast)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'pce_fast', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	#Forked from 0.8.x pce with speed-accuracy tradeoffs
	'Mednafen (Saturn)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'ss', ['cue', 'toc', 'ccd', 'm3u']),
	#Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not
	'Mednafen (SNES)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'snes', ['sfc', 'smc', 'swc']),
	#Based on bsnes v0.059; appears it doesn't do Sufami Turbo or Satellaview
	'Mednafen (SNES-Faust)': MednafenModule(EmulatorStatus.ExperimentalButSeemsOkay, 'snes_faust', ['sfc', 'smc', 'swc'], command_lines.mednafen_snes_faust),

	'MAME (32X)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_32x, ['32x', 'bin']),
	#Higher host CPU requirements than what you might expect
	'MAME (Amstrad PCW)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_amstrad_pcw, mame_floppy_formats),
	'MAME (Casio PV-2000)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('pv2000', 'cart', has_keyboard=True), ['bin']),
	#Not the same as the PV-1000, albeit similar. Driver marked as non-working but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a gamepad to map to emulated cursor keys) which maybe is why
	'MAME (CD-i)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('cdimono1', 'cdrom'), mame_cdrom_formats), #This is the only CD-i model that works according to wisdom passed down the ages (is it still true or does other stuff work now?), and it says it's imperfect graphics/sound, no digital video stuff
	'MAME (Dreamcast VMU)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('svmu', 'quik', {'bios': 'dev1004'}), ['vms', 'bin']),
	#This doesn't save the RTC so you have to set that every time you boot it up, which would be too annoying… but this development BIOS instantly boots up whatever game is in the flash; claims to have no sound but it does do the sound? Unless it's supposed to have more sound than just beep
	'MAME (FM Towns)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_fm_towns, mame_cdrom_formats + mame_floppy_formats + ['bin']),
	'MAME (FM Towns Marty)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_fm_towns_marty, mame_cdrom_formats + mame_floppy_formats + ['bin']),
	#As it says right there in the fmtowns.cpp comments: "Issues: Video emulation is far from complete." and still marked not working, but it seems okay for a few games actually; creating floppies (for games that make you do that) seems like a weird time
	'MAME (Gachinko Contest! Slot Machine TV)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('gcslottv', 'cart'), generic_cart_extensions),
	#Not working and imperfect sound
	'MAME (GameKing)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('gameking', 'cart'), ['bin', 'gk']),
	'MAME (GameKing 3)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('gamekin3', 'cart'), ['bin', 'gk3']),
	'MAME (GP32)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('gp32', 'memc'), ['smc'],),
	#Bad performance (60-ish% on i5-9600kf) but otherwise might kinda work?
	'MAME (Hartung Game Master)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('gmaster', 'cart'), ['bin']),
	#Hmm... says not working and imperfect sound. I guess it does run the games, though
	'MAME (Microbee)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, command_lines.mame_microbee, ['mwb', 'com', 'bee'] + mame_floppy_formats),
	'MAME (PC-6001)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('pc6001', 'cart1', has_keyboard=True), ['bin', 'rom']),
	#Preliminary and notes in source file comments it doesn't load tapes yet (the cart2 slot seems to be a hack that does that)
	#Use pc6001a for USA version if needed, pc6001mk2 and pc6001sr might also do something, pc6601 should have a floppy drive but doesn't yet
	'MAME (PC-88)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('pc8801', 'flop1', has_keyboard=True), mame_floppy_formats),
	#TODO: Tapes, and potentially look into other models. All the PC-88 models claim to be broken, but the base one plays the games, so that's good enough in my book
	'MAME (Sharp MZ-2000)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('mz2200', 'flop1', has_keyboard=True), mame_floppy_formats + ['2d']),
	#Autoboots floppies unless they have more than one thing to boot on them, which I guess makes sense
	#Apparently not working (mz2000 is not either), so I dunno
	'MAME (Sony SMC-777)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('smc777', 'flop1', has_keyboard=True), mame_floppy_formats + ['1dd']),
	'MAME (Uzebox)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('uzebox', 'cart'), ['bin', 'uze']),
	'MAME (V.Tech Socrates)': MameDriver(EmulatorStatus.ExperimentalButSeemsOkay, mame_driver_callable('socrates', 'cart'), ['bin']),
	#Marked as not working + imperfect sound, possibly because of missing speech (also mouse is missing)
	
	#--Stuff that might not work with most things, or otherwise has known issues
	'MAME (Amiga CD32)': MameDriver(EmulatorStatus.Experimental, command_lines.mame_amiga_cd32, mame_cdrom_formats),
	#Hmm boots only a few things I guess
	'MAME (CreatiVision)': MameDriver(EmulatorStatus.Janky, mame_driver_callable('crvision', 'cart', has_keyboard=True), ['bin', 'rom']),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it; anyway it works
	'MAME (Dreamcast)': MameDriver(EmulatorStatus.Experimental, command_lines.mame_dreamcast, mame_cdrom_formats),
	#Sloooow, marked as non-working + imperfect sound
	'MAME (IBM PC)': MameDriver(EmulatorStatus.Janky, mame_driver_callable('ibm5150', 'flop1', {'isa5': 'sblaster1_5'}, has_keyboard=True), mame_floppy_formats + ['img']),
	#Sound Blaster 1.5 is added here primarily just to give this a joystick, but then that seems to not work anyway... also, there's DIP switches you might need to set in order for video output to work (it's set to monochrome by default and not CGA)
	'MAME (Jaguar)': MameDriver(EmulatorStatus.Experimental, command_lines.mame_atari_jaguar, ['j64', 'rom', 'bin', 'abs', 'cof', 'jag', 'prg']),
	#Hmm. Mostly not working. Some stuff does though
	'MAME (KC-85)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('kc85_3', 'quik'), ['kcc']),
	#All marked as MACHINE_NOT_WORKING (some stuff doesn't seem to have sound or boot)
	'MAME (Mattel Aquarius)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('aquarius', 'cart', has_keyboard=True), ['bin', 'rom']),
	#Controllers aren't emulated yet (and they're necessary for a lot of things)
	'MAME (Mattel HyperScan)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('hyprscan', 'cdrom'), mame_cdrom_formats),
	#Not going to bother about handling the cards, since logically you want to use those in the middle of the game and so you'd swap those in and out with the MAME file management menu
	#No sound and a bit slow (the latter is made worse with this console having shit loading speed)
	'MAME (Mega CD)': MameDriver(EmulatorStatus.Experimental, command_lines.mame_mega_cd, mame_cdrom_formats),
	#Hmm sometimes works and sometimes does not (when does it not? Elaborate, past self)
	'MAME (Microtan 65)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('mt65', 'dump', has_keyboard=True), ['dmp', 'm65']),
	#System name was "microtan" prior to 0.212
	#Aagggh, none of these inputs seem to be working properly (to the point where I can't just assume the games were like that)... maybe I'm doing it wrong, I don't know…
	'MAME (Microvision)': MameDriver(EmulatorStatus.Janky, mame_driver_callable('microvsn', 'cart'), generic_cart_extensions),
	#You probably want to use the software list for this so it can detect controls properly, also needs artwork that doesn't seem to be available anywhere
	'MAME (N64)': MameDriver(EmulatorStatus.Experimental, command_lines.mame_n64, ['v64', 'z64', 'rom', 'n64', 'bin']),
	#Emulates a NTSC console only so PAL games will probably tell you off or otherwise not work properly; also no rumble/mempak/etc for you. Very slow on even modern systems. Marked as non-working + imperfect graphics
	'MAME (Pokemon Mini)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('pokemini', 'cart'), ['bin', 'min']),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life, also some stuff doesn't work
	'MAME (Saturn)': MameDriver(EmulatorStatus.Experimental, command_lines.mame_saturn, mame_cdrom_formats),
	#Non-working, imperfect sound; crashes on quite a few games and hangs to white screen sometimes
	'MAME (Sega Pico)': MameDriver(EmulatorStatus.Janky, command_lines.mame_pico, ['bin', 'md']),
	#Seems like a lot of stuff doesn't get anywhere? Probably needs the book part
	'MAME (Select-a-Game)': MameDriver(EmulatorStatus.Janky, mame_driver_callable('sag', 'cart'), ['bin']),
	#Is now a separate system as of 0.221 instead of sag_whatever individual machines
	#See also Microvision, is similarly janky with needing artwork
	"MAME (Super A'Can)": MameDriver(EmulatorStatus.Experimental, mame_driver_callable('supracan', 'cart'), ['bin']),
	#Some things work, except with no sound, so... nah
	'MAME (V.Smile Baby)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('vsmileb', 'cart'), ['u1', 'u3', 'bin']),
	#Seems to crash on some titles, also everything in software list is supported=no?
	'MAME (VideoBrain)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('vidbrain', 'cart', has_keyboard=True), ['bin']),
	#Has some hella glitchy graphics and I'm not gonna call it a playable experience at this point (also it does say not working)
	'MAME (Videoton TVC)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('tvc64', 'cart', has_keyboard=True), ['bin', 'rom', 'crt']),
	'MAME (Virtual Boy)': MameDriver(EmulatorStatus.Experimental, mame_driver_callable('vboy', 'cart'), ['bin', 'vb']),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there and a lot of software list items are unsupported
	#TODO PlayStation: Would require proper region code detection, which would require looking at ISO9660 stuff properly. Anyway it is MACHINE_NOT_WORKING and often doesn't play the games (see https://mametesters.org/view.php?id=7127)

	#Just here for future use or the fun of creating launchers really; these straight up don't work:
	'MAME (3DO)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('3do', 'cdrom'), mame_cdrom_formats), #Should switch to 3do_pal when needed, but it doesn't really matter at this point
	'MAME (Bandai RX-78)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('rx78', 'cart', has_keyboard=True), ['bin', 'rom']),
	#Does boot things from software list, but not from fullpath, and doesn't really work too well
	'MAME (Buzztime Home Trivia System)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('buzztime', 'cart'), ['bin']),
	#Inputs are not defined and it just spams random inputs (the game plays itself!!!1)
	'MAME (Casio Loopy)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('casloopy', 'cart'), ['bin']),
	#Just shows corrupted graphics (and has no controls defined), basically just a skeleton even if it looks like it isn't
	'MAME (Commodore CDTV)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('cdtv', 'cdrom'), mame_cdrom_formats),
	#This one works less than CD32; just takes you to the default boot screen like no CD was inserted
	'MAME (Copera)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('copera', 'cart'), ['bin', 'md']),
	#Displays the logo and then displays nothing
	'MAME (GoGo TV Video Vision)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('tvgogo', 'cart'), ['bin']),
	'MAME (Jaguar CD)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('jaguarcd', 'cdrom'), mame_cdrom_formats), #Also has cartridge port, as it is a Jaguar addon
	'MAME (Koei PasoGo)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('pasogo', 'cart'), ['bin']),
	#No sound yet, and apparently the rest doesn't work either (I'll take their word for it so I don't have to play weird board games I don't understand)
	'MAME (Tomy Prin-C)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('princ', 'cart'), ['bin']),
	#Skeleton driver that displays a green background and then doesn't go anywhere
	
	#Doesn't even display graphics, I'm just feeling like adding stuff at this point
	'MAME (Advanced Pico Beena)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('beena', 'cart'), ['bin']), #Segfaults
	'MAME (C2 Color)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('c2color', 'cart'), ['bin']),
	'MAME (Didj)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('didj', 'cart'), ['bin']),
	'MAME (Konami Picno)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('picno', 'cart'), ['bin']),
	'MAME (LeapPad)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('leappad', 'cart'), ['bin']),
	'MAME (Leapster)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('leapster', 'cart'), ['bin']), #Sometimes crashes, appears to be executing the CPU and printing debug stuff
	'MAME (MobiGo)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('mobigo', 'cart'), ['bin']),
	'MAME (Monon Color)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('mononcol', 'cart'), ['bin']),
	'MAME (My First LeapPad)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('mfleappad', 'cart'), ['bin']),
	'MAME (Pippin)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('pippin', 'cdrom'), mame_cdrom_formats),
	'MAME (Pocket Challenge W)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('pockchal', 'cart'), ['bin', 'pcw']),
	'MAME (V.Reader)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('vreader', 'cart'), ['bin']),
	'MAME (V.Smile Pro)': MameDriver(EmulatorStatus.Borked, mame_driver_callable('vsmilpro', 'cdrom'), mame_cdrom_formats),

	#TODO: Comments from system_info that indicate I feel the need to create an autoboot for stuff (because I guess typing arcane shit just sucks too much, and yeah it does make me think that some tapes_are_okay or menus_are_okay option is needed)
	#z88: 	#Marked as not working due to missing expansion interface and serial port and other things, not sure how important that would be... anyway, I'd need to do an autoboot thing to press the key to start the thing, because otherwise it's annoying to navigate every time, and then... hmm, I guess I dunno what actually is a function of things not working yet
	#mo6: #Floppies work (and cassettes and carts have same problem as MO5), but this time we need to press the F1 key and I don't waaaanna do that myself
	#to7/to8: 	#Fuck I hate this. Carts need to press 1 on TO7 or press the button with the lightpen on TO8/9 and also they suck, floppies need BASIC cart inserted on TO7 (and then the same method to boot that cart) or press B on TO8/9, tapes are a shitload of fuck right now (same broken as MO5/MO6), not all of this seems to be cross compatible so might need to separate systems or work out what's going on there
	#ti99_4a: 	#Carts need to press the any key and then 2 to actually load them. Floppies are the most asinine irritating thing ever fuck it Actually if we can detect that a floppy has Extended BASIC autoboot that could work with an autoboot script in the same way that cartridges work
	#studio2: #This console sucks and I hate it, anyway; I'd need to make multiple autoboot scripts that press F3 and then combinations of buttons depending on software list > usage somehow? God fuck I hate this console so much. PAL games (and some homebrew stuff) need mpt02
	#bbcb: The key combination to boot a floppy is Shift+Break which is rather awkward to press, so I want an autoboot script
	#electron: Same
	#galaxy/galaxyp:  #This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why. Anyway, we'd go with those and make an autoboot script (maybe just -autoboot_command '\n' would work with suitable delay). galaxy is regular system, galaxyp is an upgraded one which appears to be completely backwards compatible
	#abc80: #Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	#pdp1: MAME needs us to press control panel key + read in, and then it does the thing and all is well
	#zx81: 	#Gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing baaggghghh which is why I haven't bothered trying more of this
	#einstein: Works fine but you need to type in the name of the program (this isn't in the usage field of SL)

	#Have not gotten around to trying:
	#atom
	#CPC/CPC+, maybe CPC+ and GX4000 should be merged?
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

class MacEmulator():
	def __init__(self, launch_params):
		self.launch_params = launch_params

	def get_launch_params(self, app, system_config):
		if callable(self.launch_params):
			return self.launch_params(app, system_config)

		return self.launch_params

mac_emulators = {
	'BasiliskII': MacEmulator(command_lines.basilisk_ii),
	#TODO: Add SheepShaver here, even if we would have to do the vm.mmap thingy
}

class DOSEmulator():
	def __init__(self, launch_params):
		self.launch_params = launch_params

	def get_launch_params(self, app, system_config):
		if callable(self.launch_params):
			return self.launch_params(app, system_config)

		return self.launch_params

dos_emulators = {
	'DOSBox': DOSEmulator(command_lines.dosbox),
	'DOSBox-X': DOSEmulator(command_lines.dosbox_x)
}
