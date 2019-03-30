import os

import info.emulator_command_lines as command_lines
from .system_info import mame_floppy_formats, mame_cdrom_formats

class Emulator():
	def __init__(self, exe_name, args, supported_extensions, supported_compression, wrap_in_shell=False):
		self.exe_name = exe_name
		self.args = args
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression
		self.wrap_in_shell = wrap_in_shell

	def get_command_line(self, game, specific_config):
		exe_name = self.exe_name

		#You might think sine I have game.rom here, I should just insert the path into the command line here too. I don't though, in case the final path that gets passed to the emulator needs to be different than the ROM's path (in case of temporary extracted files for emulators not supporting compression, for example)
		if callable(self.args):
			args = self.args(game, specific_config)
			if isinstance(args, tuple):
				exe_name, args = args
		else:
			args = self.args

		return exe_name, args

class MednafenModule(Emulator):
	def __init__(self, module, supported_extensions, args=None):
		if not args:
			args = command_lines.make_mednafen_command_line(module)
		Emulator.__init__(self, 'mednafen', args, supported_extensions, ['zip', 'gz'])

class MameSystem(Emulator):
	def __init__(self, args, supported_extensions):
		Emulator.__init__(self, 'mame', args, supported_extensions, ['7z', 'zip'])

class ViceEmulator(Emulator):
	def __init__(self, exe_name, args):
		#Also does z and zoo compression but I haven't done those in archives.py yet
		#WARNING! Will write back changes to your disk images unless they are compressed or actually write protected on the file system
		#FIXME: Does support compressed tapes/disks but doesn't support compressed cartridges (seemingly). This would require changing all kinds of stuff with how compression is handled here.
		Emulator.__init__(self, exe_name, args, ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m'] + ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin'] + ['p00', 'prg', 'tap', 't64'], ['gz', 'bz2', 'zip', 'tgz'])

emulators = {
	'A7800': Emulator('a7800', command_lines.a7800, ['bin', 'a78'], ['7z', 'zip']),
	#Forked directly from MAME with alterations to a7800.cpp driver, so will more or less work the same way as that
	#Executable name might be a7800.Linux-x86_64 depending on how it's installed... hmm
	'cxNES': Emulator('cxnes', command_lines.cxnes, ['nes', 'fds', 'unf', 'unif'], ['7z', 'zip']),
	'Dolphin': Emulator('dolphin-emu', command_lines.dolphin, ['iso', 'gcm', 'gcz', 'tgc', 'elf', 'dol', 'wad', 'wbfs'], []),
	'FS-UAE': Emulator('fs-uae', command_lines.fs_uae, ['iso', 'cue', 'adf', 'ipf'], []),
	#Note that .ipf files need a separately downloadable plugin. We could detect the presence of that, I guess
	'Gambatte': Emulator('gambatte_qt', command_lines.gambatte, ['gb', 'gbc'], ['zip']),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations, but that would probably require a specific thing that notes some GBC games are incompatible with GBA mode (Pocket Music) or GB incompatible with GBC (R-Type, also Pocket Sonar but that wouldn't work anyway)
	'GBE+': Emulator('gbe_plus_qt', command_lines.gbe_plus, ['gb', 'gbc', 'gba'], []),
	#Also in theory recognizes any extension and assumes Game Boy if not .gba or .nds, but that would be screwy
	'Kega Fusion': Emulator('kega-fusion', command_lines.kega_fusion, ['bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', 'sc', '32x'], ['zip']),
	#May support other CD formats for Mega CD other than iso, cue? Because it's closed source, can't really have a look, but I'm just going to presume it's only those two

	'mGBA': Emulator('mgba-qt', command_lines.mgba, ['gb', 'gbc', 'gba', 'srl', 'bin', 'mb'], ['7z', 'zip']),
	'Mupen64Plus': Emulator('mupen64plus', command_lines.mupen64plus, ['z64', 'v64', 'n64'], []),
	'PCSX2': Emulator('PCSX2', ['--nogui', '--fullscreen', '--fullboot', '$<path>'], ['iso', 'cso', 'bin'], ['gz']),
	#Takes some time to load the interface so at first it might look like it's not working; take out --fullboot if it forbids any homebrew stuff (but it should be fine, and Katamari Damacy needs it unless you will experience sound issues that are funny the first time but not subsequently).  ELF seems to not work, though it'd need a different command line anyway. Only reads the bin of bin/cues and not the cue
	#Older versions are "pcsx2" or "PCSX2-linux" so I really need to implement that thing where I make the things selectable
	'PokeMini': Emulator('PokeMini', ['-fullscreen', '$<path>'], ['min'], ['zip']),
	#Puts all the config files in the current directory, which is why there's a wrapper below which you probably want to use instead of this
	'PokeMini (wrapper)': Emulator('PokeMini', [['mkdir', '-p', os.path.expanduser('~/.config/PokeMini')], ['cd', os.path.expanduser('~/.config/PokeMini')], ['$<exe>', '-fullscreen', '$<path>']], ['min'], ['zip'], True),
	'PPSSPP': Emulator('ppsspp-qt', ['$<path>'], ['iso', 'pbp', 'cso'], []),
	'SimCoupe': Emulator('simcoupe', ['-fullscreen', 'yes', '$<path>'], ['mgt', 'sad', 'dsk', 'sbt'], ['zip', 'gz']),
	'Snes9x': Emulator('snes9x-gtk', ['$<path>'], ['sfc', 'smc', 'swc'], ['zip', 'gz']),
	#Can't set fullscreen mode from the command line so you have to set up that yourself (but it will do that automatically); GTK port can't do Sufami Turbo or Satellaview from command line due to lacking multi-cart support that Windows has (Unix non-GTK doesn't like being in fullscreen etc)
	'Stella': Emulator('stella', ['-fullscreen', '1', '$<path>'], ['a26', 'bin', 'rom'], ['gz', 'zip']),

	'VICE (C64)': ViceEmulator('x64sc', command_lines.vice_c64),
	'VICE (C64 Fast)': ViceEmulator('x64', command_lines.vice_c64), #For our purposes, this only differs in exe name
	'VICE (VIC-20)': ViceEmulator('xvic', command_lines.vice_vic20),
	'VICE (Commodore PET)': ViceEmulator('xpet', ['-CRTCfull', '$<path>']),
	#Some programs only run on 4000-series machines (model = '4032'), some do not (model = '3032'), I guess I don't have a way of knowing (MAME software lists just have a comment so it just be like that sometimes)
	'VICE (Plus/4)': ViceEmulator('xplus4', command_lines.vice_plus4),
	'VICE (C128)': ViceEmulator('x128', command_lines.vice_c128),


	'Mednafen (Lynx)': MednafenModule('lynx', ['lnx', 'lyx', 'o'], command_lines.mednafen_lynx),
	#Based on Handy, but that hasn't been updated in 14 years, so I guess this probably has some more updates
	'Mednafen (Neo Geo Pocket)': MednafenModule('ngp', ['ngp', 'npc', 'ngc']),
	#Based off NeoPop, which hasn't been updated in 15 years, so presumably with improvements. Does say that this is unsuitable for homebrew development (due to lack of accuracy) and MAME is more suitable for that, so believe that if you want
	'Mednafen (NES)': MednafenModule('nes', ['nes', 'fds', 'unf'], command_lines.mednafen_nes),
	#Based off FCEU, so not quite cycle-accurate but it works
	'Mednafen (PC Engine)': MednafenModule('pce', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	'Mednafen (PC-FX)': MednafenModule('pcfx', ['iso', 'cue', 'toc', 'ccd', 'm3u']), #Do NOT specify a FX-SCSI BIOS
	'Mednafen (PlayStation)': MednafenModule('psx', ['iso', 'cue', 'exe', 'toc', 'ccd', 'm3u', 'psx']),
	'Mednafen (Virtual Boy)': MednafenModule('vb', ['bin', 'vb', 'vboy']),
	'Mednafen (WonderSwan)': MednafenModule('wswan', ['ws', 'wsc', 'bin', 'pc2']),
	#Based on Cygne, definitely heavily modified by now

	'MAME (Amstrad GX4000)': MameSystem(command_lines.mame_command_line('gx4000', 'cart'), ['bin', 'cpr']),
	#MT06201 (issue with emulated monochrome monitor), MT6509 lists various compatibility issues
	'MAME (APF-MP1000)': MameSystem(command_lines.mame_command_line('apfm1000', 'cart'), ['bin']),
	'MAME (Apple II)': MameSystem(command_lines.mame_apple_ii, mame_floppy_formats + ['do', 'po', 'woz']),
	#Apple II+ is required for autobooting because apparently the original Apple II doesn't do that; not sure if Apple IIe would make much difference but eh
	#There's a lot of slot options but I'm not sure if any would be useful for general purposes
	'MAME (Apple III)': MameSystem(command_lines.mame_command_line('apple3', 'flop1', has_keyboard=True), mame_floppy_formats + ['do', 'po']),
	'MAME (Arcadia 2001)': MameSystem(command_lines.mame_command_line('arcadia', 'cart'), ['bin']),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all
	#MT06642: Wrong background colours
	'MAME (Astrocade)': MameSystem(command_lines.mame_command_line('astrocde', 'cart', {'exp': 'rl64_ram'}), ['bin']),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	'MAME (Atari 2600)': MameSystem(command_lines.mame_atari_2600, ['bin', 'a26']),
	#Doesn't support as much fancy peripherals as Stella, and refuses to even acknowledge various large homebrew roms as even being valid roms, but some argue it's more accurate
	'MAME (Atari 5200)': MameSystem(command_lines.mame_command_line('a5200', 'cart'), ['bin', 'rom', 'car', 'a52']),
	#Could use -sio casette -cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory (or is that just there because Atari 8-bit computers can do that)
	#MT06972: Nondescript input issues; MT07248: Galaxian doesn't work
	'MAME (Atari 7800)': MameSystem(command_lines.mame_atari_7800, ['bin', 'a78']),
	'MAME (Atari 8-bit)': MameSystem(command_lines.mame_atari_8bit, ['bin', 'rom', 'car']),
	#Has issues with XEGS carts that it should be able to load (because they do run on the real system) but it says it doesn't because they should be run on XEGS instead, and then doesn't support a few cart types anyway; otherwise fine
	'MAME (BBC Bridge Companion)': MameSystem(command_lines.mame_command_line('bbcbc', 'cart'), ['bin']),
	'MAME (C64)': MameSystem(command_lines.mame_c64, ['80', 'a0', 'e0', 'crt']),
	'MAME (Channel F)': MameSystem(command_lines.mame_command_line('channelf', 'cart'), ['bin', 'chf']),
	'MAME (ColecoVision)': MameSystem(command_lines.mame_command_line('coleco', 'cart'), ['bin', 'col', 'rom']),
	#Controls are actually fine in-game, just requires a keypad to select levels/start games and that's not consistent at all so good luck with that (but mapping 1 to Start seems to work well).  All carts are either USA or combination USA/Europe and are required by Coleco to run on both regions, so why play in 50Hz when we don't have to
	#MT06554: Roller controller is inaccurate
	'MAME (Coleco Adam)': MameSystem(command_lines.mame_coleco_adam, ['wav', 'ddp'] + mame_floppy_formats),
	#Both disks and tapes autoboot. Woohoo!
	'MAME (Entex Adventure Vision)': MameSystem(command_lines.mame_command_line('advision', 'cart'), ['bin']),
	#Doesn't work with the "Code Red" demo last time I tried
	'MAME (FM-7)': MameSystem(command_lines.mame_command_line('fm77av', 'flop1'), mame_floppy_formats),
	#Tapes work, but they require run"" and then pressing play on the tape, the latter not being Lua-autoboot-scriptable yet.
	#Difference between fm7 and fmnew7 seems to be that the latter boots into BASIC by default (there's dip switches involved) instead of DOS, which seems to be required for tapes to work; and disks just autoboot anyway. FM-77AV is used here despite its allegedly imperfect graphics as there are games which won't work on earlier systems and there doesn't seem to be a programmatic way to tell, and it seems backwards compatibility is fine
	#Joystick only works with fm7/fmnew7 -centronics dsjoy... whoops; not sure what the builtin joystick does then
	'MAME (Gamate)': MameSystem(command_lines.mame_command_line('gamate', 'cart'), ['bin']),
	'MAME (Game Boy)': MameSystem(command_lines.mame_game_boy, ['bin', 'gb', 'gbc']),
	#This supports some bootleg mappers that other emus tend to not; fails on really fancy tricks like the Demotronic trick (it does run the demo, but the effect doesn't look right); and has sound issues with GBC (MT06441, MT04949)
	#There are comments in the source file that point out that Super Game Boy should be part of the snes driver with the BIOS cart inserted, rather than a separate system, so that might not exist in the future
	'MAME (Game.com)': MameSystem(command_lines.mame_command_line('gamecom', 'cart1'), ['bin', 'tgc']),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything.
	'MAME (Game Gear)': MameSystem(command_lines.mame_game_gear, ['bin', 'gg']),
	'MAME (Epoch Game Pocket Computer)': MameSystem(command_lines.mame_command_line('gamepock', 'cart'), ['bin']),
	'MAME (GBA)': MameSystem(command_lines.mame_command_line('gba', 'cart'), ['bin', 'gba']),
	#Does not let you do GBA-enhanced GBC games
	'MAME (IBM PCjr)': MameSystem(command_lines.mame_ibm_pcjr, mame_floppy_formats + ['img', 'bin', 'jrc']),
	'MAME (Intellivision)': MameSystem(command_lines.mame_intellivision, ['bin', 'int', 'rom', 'itv']),
	'MAME (Master System)': MameSystem(command_lines.mame_master_system, ['bin', 'sms']),
	'MAME (Mattel Juice Box)': MameSystem(command_lines.mame_command_line('juicebox', 'memcard'), ['smc']),
	'MAME (Mega Drive)': MameSystem(command_lines.mame_megadrive, ['bin', 'md', 'smd', 'gen']),
	'MAME (Mega Duck)': MameSystem(command_lines.mame_command_line('megaduck', 'cart'), ['bin']),
	'MAME (MSX)': MameSystem(command_lines.mame_command_line('svi738', 'cart1', {'fdc:0': ''}, has_keyboard=True), ['bin', 'rom']),
	#Note that MSX2 is backwards compatible anyway, so there's not much reason to use this, unless you do have some reason. This model in particular is used because it should be completely in English and if anything goes wrong I'd be able to understand it. I still don't know how disks work (they don't autoboot), or if there's even a consistent command to use to boot them.
	'MAME (MSX2)': MameSystem(command_lines.mame_command_line('fsa1wsx', 'cart1', {'fdc:0': ''}, has_keyboard=True), ['bin', 'rom']),
	#This includes MSX2+ because do you really want me to make those two separate things? Turbo-R doesn't work in MAME though, so that'd have to be its own thing. This model is used just because I looked it up and it seems like the best one, the MSX2/MSX2+ systems in MAME are all in Japanese (the systems were only really released in Japan, after all) so you can't avoid that part. Still don't understand disks.
	'MAME (Neo Geo CD)': MameSystem(command_lines.mame_command_line('neocdz', 'cdrom'), mame_cdrom_formats),
	#Don't think it has region lock so I should never need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	'MAME (Neo Geo Pocket)': MameSystem(command_lines.mame_command_line('ngpc', 'cart'), ['bin', 'ngp', 'npc', 'ngc']),
	'MAME (NES)': MameSystem(command_lines.mame_nes, ['nes', 'unf', 'unif', 'fds']),
	#Supports a lot of mappers actually, probably not as much as Mesen or puNES would, but it's up there; also a lot of cool peripherals
	'MAME (Nichibutsu My Vision)': MameSystem(command_lines.mame_command_line('myvision', 'cart'), ['bin']),
	'MAME (Casio PV-1000)': MameSystem(command_lines.mame_command_line('pv1000', 'cart'), ['bin']),
	'MAME (SG-1000)': MameSystem(command_lines.mame_sg1000, ['bin', 'sg', 'sc', 'sf7'] + mame_floppy_formats),
	'MAME (Sharp X1)': MameSystem(command_lines.mame_command_line('x1turbo40', 'flop1', has_keyboard=True), mame_floppy_formats + ['2d']),
	#x1turbo doesn't work, and I'm not sure what running x1 over x1turbo40 would achieve
	'MAME (SNES)': MameSystem(command_lines.mame_snes, ['sfc', 'bs', 'st']),
	#The main advantage here is that it supports multi-slot carts (BS-X and Sufami Turbo) where SNES9x's GTK port does not, otherwise I dunno how well it works
	'MAME (Sord M5)': MameSystem(command_lines.mame_command_line('m5', 'cart1', {'ramsize': '64K', 'upd765:0': ''}, True), ['bin']),
	'MAME (Super Cassette Vision)': MameSystem(command_lines.mame_super_cassette_vision, ['bin']),
	'MAME (Bandai Super Vision 8000)': MameSystem(command_lines.mame_command_line('sv8000', 'cart'), ['bin']),
	'MAME (Tomy Tutor)': MameSystem(command_lines.mame_command_line('tutor', 'cart', has_keyboard=True, autoboot_script='tomy_tutor'), ['bin']),
	#There is pyuuta if you want to read Japanese instead
	'MAME (VC 4000)': MameSystem(command_lines.mame_command_line('vc4000', 'cart'), ['bin', 'rom']),
	#There's like 30 different clones of this, and most of them aren't even clones in the MAME sense, they're literally hardware clones. But they're apparently all software-compatible, although the cartridges aren't hardware-compatible, they just contain the same software... so this all gets confusing. Anyway, the software list with all these is named "vc4000" so I guess that's the "main" one, so we'll use that. I'm not sure if there are any PAL/NTSC differences to worry about.
	#TODO: Quickload slot (.pgm, .tvc)
	'MAME (Vectrex)': MameSystem(command_lines.mame_command_line('vectrex', 'cart'), ['bin', 'gam', 'vec']),
	#Includes overlays as selectable artwork, but that has to be done by the user from the menu
	'MAME (VIC-10)': MameSystem(command_lines.mame_command_line('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), ['crt', '80', 'e0']),
	#More similar to the C64 (works and performs just as well as that driver) than the VIC-20, need to plug a joystick into both ports because once again games can use
	#either port and thanks I hate it. At least there's only one TV type
	#Sometimes I see this called the Commodore MAX Machine or Ultimax or VC-10, but... well, I'm not sure where the VIC-10 name comes from other than that's what the driver's called
	'MAME (VIC-20)': MameSystem(command_lines.mame_vic_20, ['20', '40', '60', '70', 'a0', 'b0', 'crt']),
	'MAME (VZ-200)': MameSystem(command_lines.mame_command_line('vz200', 'dump', {'io': 'joystick', 'mem': 'laser_64k'}, True), ['vz']),
	#In the Laser 200/Laser 210 family, but Dick Smith variant should do.
	#Joystick interface doesn't seem to be used by any games, but I guess it does more than leaving the IO slot unfilled. That sucks, because otherwise no game ever uses the keyboard consistently, because of course not. Even modern homebrew games. Why y'all gotta be like that?
	#Some games will need you to type RUN to run them, not sure how to detect that.
	'MAME (Watara Supervision)': MameSystem(command_lines.mame_command_line('svision', 'cart'), ['bin', 'ws', 'sv']),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes the colours look even worse (they're all inverted and shit)
	'MAME (ZX Spectrum)': MameSystem(command_lines.mame_zx_spectrum, ['ach', 'frz', 'plusd', 'prg', 'sem', 'sit', 'sna', 'snp', 'snx', 'sp', 'z80', 'zx', 'bin', 'rom', 'raw', 'scr'] + mame_floppy_formats),
	#.trd would be doable with -exp beta128, but that only autoboots on Spectrum 48K and everything is designed for 128K
	#.opu .opd might work with -exp opus, but that seems to only work on 48K and one must type "run"

	#Other systems that MAME can do but I'm too lazy to do them yet because they'd need a command line generator function or other:
	#Dreamcast: Region, and also runs slow on my computer so I don't feel like it; doesn't seem like it does Windows CE at this point (something about only emulating the MMU properly for Naomi shows up)
	#PC Engine: Need to select between pce and tg16 depending on region, -cdrom and -cart slots, and sgx accordingly:
	#	.sgx extension is SuperGrafx, needs sgx driver
	#	tg16 can run Japanese games (seemingly) but pce cannot run USA games, so it would be the default if region not specified
	#	CD needs -cart set to CD-ROM System .pce BIOS, and then seems to work with any particular driver (but the TurboGrafx CD System Card will only work with tg16)
	#	Seems to support SF2 and Populous and such, not sure what else would be an edge case
	#	6-button controllers are enabled via Machine Configuration
	#Saturn: Needs region stuff (saturn and saturnjp are software incompatible); otherwise seems to basically work (ctrl1 sets controller) but marked as MACHINE_NOT_WORKING and slow...
	#Stuff that MAME doesn't do so well, but a non-skeleton driver exists:
	#Amiga CD32: I guess it doesn't really work at this point in time
	#Commodore CDTV: Nope
	#PlayStation: Seems to like executables but not discs, dunno if psu will accept Japan discs

	#----- The experimental section. The emulators are still here, it's just so you, the fabulous and wonderful end user, can have more information on how to manage expectations. Or something like that.

	#--Has usability issues that prevent me from considering it a nice experience, but may work anyway
	'MAME (IBM PC)': MameSystem(command_lines.mame_command_line('ibm5150', 'flop1', {'isa5': 'sblaster1_5'}, has_keyboard=True), mame_floppy_formats + ['img']),
	#Sound Blaster 1.5 is added here primarily just to give this a joystick, but then that seems to not work anyway... also, there's DIP switches you might need to set in order for video output to work (it's set to monochrome by default and not CGA)
	'MAME (N64)': MameSystem(command_lines.mame_n64, ['v64', 'z64', 'rom', 'n64', 'bin']),
	#Emulates a NTSC console only so PAL games will probably tell you off or otherwise not work properly; also no rumble/mempak/etc for you. Very slow on even modern systems

	#--These experimental emulators seem to work more often than they don't:
	'Citra': Emulator('citra-qt', command_lines.citra, ['3ds', 'cxi', '3dsx'], []),
	#No fullscreen from command line
	'Medusa': Emulator('medusa-emu-qt', command_lines.medusa, ['nds', 'gb', 'gbc', 'gba'], ['7z', 'zip']),
	'Reicast': Emulator('reicast', command_lines.reicast, ['gdi', 'cdi', 'chd'], []),

	'Mednafen (PC Engine Fast)': MednafenModule('pce_fast', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	#Forked from 0.8.x pce with speed-accuracy tradeoffs
	'Mednafen (Saturn)': MednafenModule('ss', ['cue', 'toc', 'ccd', 'm3u']),
	#Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not

	'MAME (CD-i)': MameSystem(command_lines.mame_command_line('cdimono1', 'cdrom'), mame_cdrom_formats),
	#This is the only CD-i model that works according to wisdom passed down the ages (is it still true?), and it says it's not working, but it seems fine
	'MAME (Hartung Game Master)': MameSystem(command_lines.mame_command_line('gmaster', 'cart'), ['bin']),
	#Hmm... says not working and imperfect sound. I guess it does run the games, though
	'MAME (PC-88)': MameSystem(command_lines.mame_command_line('pc8801', 'flop1', has_keyboard=True), mame_floppy_formats),
	#TODO: Tapes, and potentially look into other models. All the PC-88 models claim to be broken, but the base one plays the games, so that's good enough in my book. Some might use BASIC though so I'd have to specially handle that?
	'MAME (Casio PV-2000)': MameSystem(command_lines.mame_command_line('pv2000', 'cart', has_keyboard=True), ['bin']),
	#Not the same as the PV-1000, albeit similar. Driver marked as non-working but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a gamepad to map to emulated cursor keys) which maybe is why
	'MAME (Sharp X68000)': MameSystem(command_lines.mame_sharp_x68000, mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim', 'm3u']),
	#It doesn't	really support m3u, but I'm going to make it so it does (multi-disk games seem fairly common)
	#All the other models of X68000 don't work yet
	'MAME (Uzebox)': MameSystem(command_lines.mame_command_line('uzebox', 'cart'), ['bin', 'uze']),
	#Runs really slowly, but it does work (other than SD card emulation)
	'MAME (V.Smile)': MameSystem(command_lines.mame_command_line('vsmile', 'cart'), ['u1', 'u3', 'bin']),
	'MAME (Virtual Boy)': MameSystem(command_lines.mame_command_line('vboy', 'cart'), ['bin', 'vb']),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there

	#--These experimental emulators seem to not work more often than they do, but they are here for you to play with if you want to, because maybe other people have better luck than me (everything in my life always goes wrong):
	'MAME (CreatiVision)': MameSystem(command_lines.mame_command_line('crvision', 'cart'), ['bin', 'rom']),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it
	'MAME (G7400)': MameSystem(command_lines.mame_command_line('g7400', 'cart'), ['bin', 'rom']),
	#just has the same graphics problems as Odyssey 2... there's a odyssey3 driver that was never released but I guess it would be for NTSC games. Actually, all the software list items say unsupported... hmm
	'MAME (Jaguar)': MameSystem(command_lines.mame_atari_jaguar, ['j64', 'rom', 'bin', 'abs', 'cof', 'jag', 'prg']),
	#Hmm. Mostly not working. Raiden seems to work, but that's about it; other stuff just hangs at the Jaguar logo or has no sound or what barely resembles graphics is corrupted etc
	'MAME (FM Towns Marty)': MameSystem(command_lines.mame_fm_towns_marty, mame_cdrom_formats + mame_floppy_formats),
	#As it says right there in the fmtowns.cpp comments: "Issues: Video emulation is far from complete." This is apparent, as there are some games that run on the FM Towns Not-Marty but not this; they have heavily corrupted graphics. But to use the FM Towns I'd have to first make sure that it being a computer won't mess with anything usability-wise.
	'MAME (Magnavox Odyssey²)': MameSystem(command_lines.mame_odyssey2, ['bin', 'rom']),
	#Isn't completely broken but a lot of games have broken graphics so like... ehh
	'MAME (Mattel Aquarius)': MameSystem(command_lines.mame_command_line('aquarius', 'cart'), ['bin', 'rom']),
	#Controllers aren't emulated yet (and they're necessary for a lot of things)
	'MAME (Pokemon Mini)': MameSystem(command_lines.mame_command_line('pokemini', 'cart'), ['bin', 'min']),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life
	"MAME (Super A'Can)": MameSystem(command_lines.mame_command_line('supracan', 'cart'), ['bin']),
	#Some things work, except with no sound, so... nah
	'MAME (V.Smile Baby)': MameSystem(command_lines.mame_command_line('vsmileb', 'cart'), ['u1', 'u3', 'bin']),
	#Seems to crash on some titles


	#--These ones may or may not run well, I dunno:
	'Mednafen (Game Boy)': MednafenModule('gb', ['gb', 'gbc'], command_lines.mednafen_gb),
	#Based off an old version of VisualBoyAdvance
	'Mednafen (Game Gear)': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes". This is based off SMS Plus
	'Mednafen (GBA)': MednafenModule('gba', ['gba']),
	#Based off an old version of VisualBoyAdvance
	'Mednafen (Master System)': MednafenModule('sms', ['sms', 'bin']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes". Based off SMS Plus
	'Mednafen (Mega Drive)': MednafenModule('md', ['md', 'bin', 'gen', 'smd', 'sgd'], command_lines.mednafen_megadrive),
	#Based off Genesis Plus and an older GPL version of Genesis Plus GX, with all GPL-incompatible cores replaced with alternatives (sound chip emulation from Gens, Z80 from FUSE). Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
	'Mednafen (SNES)': MednafenModule('snes', ['sfc', 'smc', 'swc']),
	#Based on bsnes v0.059; appears it doesn't do Sufami Turbo or Satellaview
	'Mednafen (SNES-Faust)': MednafenModule('snes_faust', ['sfc', 'smc', 'swc']),
	#Experimental and doesn't support expansion chips

	'MAME (Amstrad CPC+)': MameSystem(command_lines.mame_command_line('cpc6128p', 'cart'), ['bin', 'cpr']),
	#Just in case I change my mind on using GX4000. cpc464p is a different CPC+ model but I'm not sure that would be useful?
	'MAME (Lynx)': MameSystem(command_lines.mame_lynx, ['lnx', 'lyx', 'o']),
	'MAME (WonderSwan)': MameSystem(command_lines.mame_command_line('wscolor', 'cart'), ['ws', 'wsc', 'bin', 'pc2']),
}

class GameEngine():
	#Not really emulators, but files come in and games come out.
	def __init__(self, exe_name, args, is_game_data):
		self.exe_name = exe_name
		self.args = args
		self.is_game_data = is_game_data #This is supposed to be a lambda but I can't figure out how to word it so that's apparent at first glance

	def get_command_line(self, game, specific_config):
		if callable(self.args):
			return self.exe_name, self.args(game, specific_config)

		return self.exe_name, self.args

def is_doom_file(file):
	if file.extension != 'wad':
		return False

	return file.read(amount=4) == b'IWAD'

engines = {
	'PrBoom+': GameEngine('prboom-plus', command_lines.make_prboom_plus_command_line, is_doom_file),
	#Joystick support not so great, otherwise it plays perfectly well with keyboard + mouse; except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay
	'Darkplaces': GameEngine('darkplaces-glx', ['-nostdout', '-fullscreen', '-basedir', '$<path>'], lambda folder: folder.contains_subfolder('id1'))
	#TODO: Make this work with expansion packs and stuff (this will most definitely only work with base Quake), I haven't bought them yet
}

class MacEmulator():
	def __init__(self, exe_name, args):
		self.exe_name = exe_name
		self.args = args

	def get_command_line(self, app, specific_config):
		exe_name = self.exe_name

		if callable(self.args):
			args = self.args(app, specific_config)
			if isinstance(args, tuple):
				#This is all just a load of hack I'm really sorry
				exe_name, args = args
				args = [arg.replace('$<exe>', self.exe_name) for arg in args]
		else:
			args = self.args

		return exe_name, args

mac_emulators = {
	'BasiliskII': MacEmulator('BasiliskII', command_lines.basilisk_ii),
	#TODO: Add SheepShaver here, even if we would have to do the vm.mmap thingy
}

class DOSEmulator():
	def __init__(self, exe_name, args):
		self.exe_name = exe_name
		self.args = args

	def get_command_line(self, app, specific_config):
		if callable(self.args):
			return self.exe_name, self.args(app, specific_config)

		return self.exe_name, self.args

dos_emulators = {
	'DOSBox': DOSEmulator('dosbox', command_lines.dosbox)
}
