from enum import Enum, auto

class MediaType(Enum):
	Cartridge = auto()
	Digital = auto()
	Executable = auto()
	Floppy = auto()
	OpticalDisc = auto()
	Tape = auto()
	Snapshot = auto()
	Barcode = auto()
	Standalone = auto()

class System():
	def __init__(self, name, mame_driver, mame_software_lists, emulators, file_types=None):
		self.name = name
		self.mame_driver = mame_driver
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators
		self.file_types = file_types if file_types else {}

	def is_valid_file_type(self, extension):
		return any([extension in extensions for _, extensions in self.file_types.items()])

	def get_media_type(self, extension):
		for media_type, extensions in self.file_types.items():
			if extension in extensions:
				return media_type
		return None

def get_system_by_name(name):
	for system in systems:
		if system.name == name:
			return system

	for k, v in games_with_engines.items():
		if k == name:
			return v

	return None

def get_mame_driver_by_system_name(name):
	for system in systems:
		if system.name == name:
			return system.mame_driver

	return None

def get_mame_software_list_names_by_system_name(name):
	for system in systems:
		if system.name == name:
			return system.mame_software_lists

	return None

mame_cdrom_formats = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']

#All known possible CD-ROM formats, for use with file_types and MediaType.OpticalDisc; of course emulator support may vary
cdrom_formats = mame_cdrom_formats + ['cdi', 'ccd', 'toc']

systems = [
	#TODO: Convert to dict where name = key (but would that work out? hmm)

	System('3DS', None, [], ['Citra'], {MediaType.Cartridge: ['3ds'], MediaType.Digital: ['cxi'], MediaType.Executable: ['3dsx']}),
	System('Atari 2600', 'a2600', ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)'], {MediaType.Cartridge: ['a26', 'rom', 'bin']}),
	System('Atari 5200', 'a5200', ['a5200'], ['MAME (Atari 5200)'], {MediaType.Cartridge: ['a52', 'car', 'rom', 'bin'], MediaType.Tape: ['wav']}),
	System('Atari 7800', 'a7800', ['a7800'], ['MAME (Atari 7800)'], {MediaType.Cartridge: ['a78', 'bin']}),
	System('CD-i', 'cdimono1', ['cdi'], ['MAME (CD-i)'], {MediaType.OpticalDisc: cdrom_formats}),
	System('Colecovision', 'coleco', ['coleco'], ['MAME (ColecoVision)'], {MediaType.Cartridge: ['col', 'bin', 'rom']}),
	System('Dreamcast', 'dc', ['dc'], ['Reicast'], {MediaType.OpticalDisc: cdrom_formats}),
	System('DS', 'nds', [], ['Medusa'], {MediaType.Cartridge: ['nds', 'dsi', 'ids']}),
	System('Game Boy', 'gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa'], {MediaType.Cartridge: ['gb', 'gbc', 'gbx', 'sgb']}),
	System('GameCube', 'gcjp', [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz'], MediaType.Executable: ['dol', 'elf']}),
	System('Game Gear', 'gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	System('GBA', 'gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa'], {MediaType.Cartridge: ['gba', 'bin', 'srl'], MediaType.Executable: ['elf', 'mb']}),
	System('Intellivision', 'intv', ['intv', 'intvecs'], ['MAME (Intellivision)'], {MediaType.Cartridge: ['bin', 'int', 'rom', 'itv']}),
	System('Lynx', 'lynx', ['lynx'], ['Mednafen (Lynx)'], {MediaType.Cartridge: ['lnx', 'lyx'], MediaType.Executable: ['o']}),
	System('Master System', 'sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	System('Mega Drive', 'megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)'], {MediaType.Cartridge: ['bin', 'gen', 'md', 'smd', 'sgd']}),
	System('N64', 'n64', ['n64'], ['Mupen64Plus'], {MediaType.Cartridge: ['z64', 'v64', 'n64', 'bin']}),
	System('Neo Geo Pocket', 'ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'], {MediaType.Cartridge: ['ngp', 'npc', 'ngc', 'bin']}),
	System('NES', 'nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)'], {MediaType.Cartridge: ['nes', 'unf', 'unif'], MediaType.Floppy: ['fds']}),
	System('PC Engine', 'pce', ['pce', 'sgx', 'tg16'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.Cartridge: ['pce', 'sgx', 'bin']}),
	System('PlayStation', 'psj', ['psx'], ['Mednafen (PS1)'], {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: ['exe', 'psx']}),
	System('PS2', 'ps2', [], ['PCSX2'], {MediaType.OpticalDisc: cdrom_formats + ['cso', 'bin'], MediaType.Executable: ['elf']}),
	System('PSP', None, [], ['PPSSPP'], {MediaType.OpticalDisc: cdrom_formats + ['cso'], MediaType.Executable: ['pbp']}),
	System('Saturn', 'saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)'], {MediaType.OpticalDisc: cdrom_formats}),
	System('SNES', 'snes', ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)'], {MediaType.Cartridge: ['sfc', 'swc', 'smc', 'bs', 'st', 'bin']}),
	System('Wii', None, [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz'], MediaType.Executable: ['dol', 'elf'], MediaType.Digital: ['wad']}),
	System('WonderSwan', 'wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['ws', 'wsc', 'bin']}),
	#Rotates around so that sometimes the dpad becomes buttons and vice versa and there's like two dpads??? but if you use Mednafen's rotation auto-adjust thing it kinda works

	#Obscure systems (<1M units sold), just for the sake of making that list less messy
	#Uzebox is a homebrew thing and not really a commercial product, so it doesn't really have numbers. But it probably counts as obscure.
	#Can't really find numbers on Atari 7800 and Neo Geo Pocket, but they aren't obscure... right?
	System('Amiga CD32', 'cd32', ['cd32', 'cdtv'], ['FS-UAE'], {MediaType.OpticalDisc: cdrom_formats}),
	#Meh, I'll consider it a separate thing I guess
	System('Amstrad GX4000', 'gx4000', ['gx4000'], ['MAME (Amstrad GX4000)', 'MAME (Amstrad CPC+)'], {MediaType.Cartridge: ['bin', 'cpr']}),
	System('APF-MP1000', 'apfm1000', ['apfm1000'], ['MAME (APF-MP1000)'], {MediaType.Cartridge: ['bin']}),
	System('Arcadia 2001', 'arcadia', ['arcadia'], ['MAME (Arcadia 2001)'], {MediaType.Cartridge: ['bin']}),
	System('Astrocade', 'astrocde', ['astrocde'], ['MAME (Astrocade)'], {MediaType.Cartridge: ['bin']}),
	System('Benesse Pocket Challenge V2', None, ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['pc2', 'bin']}),
	#Controls are mapped even worse than regular WonderSwan games, even with rotation auto-adjust you still end up using a stick/dpad as buttons and it gets weird, also the module must be forced or else it won't be recognized. But it works though
	System('BBC Bridge Companion', 'bbcbc', ['bbcbc'], ['MAME (BBC Bridge Companion)'], {MediaType.Cartridge: ['bin']}),
	System('Casio PV-1000', 'pv1000', ['pv1000'], ['MAME (PV-1000)'], {MediaType.Cartridge: ['bin']}),
	System('Channel F', 'channelf', ['channelf'], ['MAME (Channel F)'], {MediaType.Cartridge: ['chf', 'bin']}),
	#It has some sort of knob that you twist up and down or something? What the fuck
	System('Entex Adventure Vision', 'advision', ['advision'], ['MAME (Entex Adventure Vision)'], {MediaType.Cartridge: ['bin']}),
	System('Epoch Game Pocket Computer', 'gamepock', ['gamepock'], ['MAME (Game Pocket Computer)'], {MediaType.Cartridge: ['bin']}),
	System('Gamate', 'gamate', ['gamate'], ['MAME (Gamate)'], {MediaType.Cartridge: ['bin']}),
	System('Game.com', 'gamecom', ['gamecom'], ['MAME (Game.com)'], {MediaType.Cartridge: ['tgc', 'bin']}),
	System('Hartung Game Master', 'gmaster', ['gmaster'], ['MAME (Hartung Game Master)'], {MediaType.Cartridge: ['bin']}),
	System('Mattel Juice Box', 'juicebox', ['juicebox'], ['MAME (Juice Box)'], {MediaType.Cartridge: ['smc']}),
	#Now for those who actually do know what this is, you may be thinking: But doesn't that just play videos? Isn't this really pointless? And the answer is yes, yes it is. I love pointless.
	System('Mega Duck', 'megaduck', ['megaduck'], ['MAME (Mega Duck)'], {MediaType.Cartridge: ['bin']}),
	System('Neo Geo CD', 'neocdz', ['neocd'], ['MAME (Neo Geo CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	System('Nichibutsu My Vision', 'myvision', ['myvision'], ['MAME (Nichibutsu My Vision)'], {MediaType.Cartridge: ['bin']}),
	System('PC-FX', 'pcfx', ['pcfx'], ['Mednafen (PC-FX)'], {MediaType.OpticalDisc: cdrom_formats}),
	System('Pokemon Mini', 'pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)'], {MediaType.Cartridge: ['min', 'bin']}),
	System('SG-1000', 'sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)'], {MediaType.Cartridge: ['sg', 'bin', 'sc'], MediaType.Tape: ['wav', 'bit'], MediaType.Floppy: mame_floppy_formats + ['sf7']}),
	System('Uzebox', 'uzebox', ['uzebox'], ['MAME (Uzebox)'], {MediaType.Executable: ['bin', 'uze']}),
	System('VC 4000', 'vc4000', ['vc4000'], ['MAME (VC 4000)'], {MediaType.Cartridge: ['bin', 'rom']}),
	System('Vectrex', 'vectrex', ['vectrex'], ['MAME (Vectrex)'], {MediaType.Cartridge: ['vec', 'gam', 'bin']}),
	System('Virtual Boy', 'vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'], {MediaType.Cartridge: ['vb', 'vboy', 'bin']}),
	System('Watara Supervision', 'svision', ['svision'], ['MAME (Watara Supervision)'], {MediaType.Cartridge: ['ws', 'sv', 'bin']}),

	#Systems that are treated as though they were whole separate things, but they're addons for other systems with their own distinct set of software
	System('32X', '32x', ['32x'], ['Kega Fusion'], {MediaType.Cartridge: ['32x', 'bin']}),
	System('Mega CD', 'megacdj', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion'], {MediaType.OpticalDisc: cdrom_formats}),
	System('PC Engine CD', 'pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.OpticalDisc: cdrom_formats}),

	#Computers!  These actually aren't that bad control-wise because most sensible games would use a simple one-button
	#joystick, and most of the time MAME lets you attach one.  But some of them don't!  And the ones that don't just use
	#any damn keys they want!  And some software might only work properly with particular models of a computer within an
	#allegedly compatible family!  Yaaaay!  But they have games, so let's put them in here
	#I avoid using anything which requires me to input arcane commands or hear arcane sounds here or wait for arcane
	#times, though I suppose I _could_ do that, it just doesn't feel like a nicely organized bunch of launcher scripts if
	#I do that
	System('Amiga', 'a1200', ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'], ['FS-UAE'], {MediaType.Floppy: ['adf', 'ipf', 'dms']}),
	System('Atari 8-bit', 'a800', ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)'], {MediaType.Cartridge: ['bin', 'rom', 'car'], MediaType.Tape: ['wav']}),
	#TODO: MediaType.Floppy: ['atr', 'dsk'], MediaType.Executable: ['xex', 'bas'],
	System('C64', 'c64', ['c64_cart', 'c64_cass', 'c64_flop'], ['MAME (C64)'], {MediaType.Cartridge: ['80', 'a0', 'e0', 'crt', 'bin']}),
	#TODO: , MediaType.Floppy: ['d64', 'g64', 'p64', 'x64', 'nib', 'ipf'], MediaType.Tape: ['t64', 'tap'], MediaType.Executable: ['prg', 'p00']
	System('Casio PV-2000', 'pv2000', ['pv2000'], ['MAME (PV-2000)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	System('Coleco Adam', 'adam', ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)'], {MediaType.Cartridge: ['col', 'bin'], MediaType.Tape: ['wav', 'ddp'], MediaType.Floppy: mame_floppy_formats}),
	System('IBM PCjr', 'ibmpcjr', ['ibmpcjr_cart'], ['MAME (IBM PCjr)'], {MediaType.Cartridge: ['bin', 'jrc'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#For the carts, because otherwise we'd just call the software DOS or PC Booter.
	System('MSX2', 'fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop'], ['MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	System('MSX', 'svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX1)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	System('PC-88', 'pc8801', ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	System('Sharp X1', 'x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)'], {MediaType.Floppy: ['2d'] + mame_floppy_formats, MediaType.Tape: ['wav', 'tap']}),
	System('Sharp X68000', 'x68000', ['x68k_flop'], ['MAME (Sharp X68000)'], {MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	System('Sord M5', 'm5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)'], {MediaType.Cartridge: ['bin'], MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	System('Tomy Tutor', 'tutor', ['tutor'], ['MAME (Tomy Tutor)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	System('VIC-10', 'vic10', ['vic10'], ['MAME (VIC-10)'], {MediaType.Cartridge: ['crt', 'bin', '80', 'e0'], MediaType.Tape: ['wav', 'tap', 't64']}),
	System('VIC-20', 'vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)'], {MediaType.Cartridge: ['20', '40', '60', '70', 'a0', 'b0', 'crt']}),
	#TODO: MediaType.Tape: ['wav', 'tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: ['d64', 'g64', 'p64', 'x64', 'nib', 'ipf']
	System('VZ-200', 'vz200', ['vz_cass'], ['MAME (VZ-200)'], {MediaType.Snapshot: ['vz'], MediaType.Tape: ['wav', 'cas']}),
	#There are many different systems in this family, but I'll go with this one, because the software list is named after it
	System('ZX Spectrum', 'spectrum', ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)'], {MediaType.Snapshot: ['z80', 'sna'], MediaType.Tape: ['wav', 'cas', 'tap', 'tzx'], MediaType.Executable: ['raw', 'scr'], MediaType.Floppy: ['dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi'], MediaType.Cartridge: ['bin', 'rom']}),
	#Joystick interface is non-standard so not all games support it and might decide to use the keyboard instead, but eh. It works I guess.
	#There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

	#Unsupported (yet) systems beyond this point

	#Theoretically supported, but not supported enough to be considered playable, but you could configure them if you wanted (see emulator_info)
	System('FM Towns Marty', 'fmtmarty', ['fmtowns_cd', 'fmtowns_flop'], ['MAME (FM Towns Marty)'], {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}),
	System('Jaguar', 'jaguar', ['jaguar'], ['MAME (Atari Jaguar)'], {MediaType.Cartridge: ['j64', 'bin', 'rom'], MediaType.Executable: ['abs', 'cof', 'jag', 'prg']}),
	System('Magnavox Odyssey²', 'odyssey2', ['odyssey2'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	#O2EM doesn't really work; MAME isn't completely broken but a lot of games have broken graphics so like... ehh
	#TODO: Move comments to emulator_info, do thing which selects g7000/odyssey2 automatically
	System('G7400', 'g7400', ['g7400'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	#just has the same problems as Odyssey 2...
	System('PC Booter', 'ibm5150', ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#This one is a bit tricky... both MAME and PCem have issues emulating a joystick. Do the games actually just suck like that? _All of them_? I don't know. The majority of these games assume a 4.77MHz CPU, of course. The software list is ibm5150 but that has some DOS games too, just to be confusing (but usage == 'PC booter' where it is a PC booter).
	System("Super A'Can", 'supracan', ['supracan'], ['MAME (Super Acan)'], {MediaType.Cartridge: ['bin']}),

	#No emulators that are cool enough on Linux. Yet. Maybe? That I know of. They're here for completeness. Or no emulators at all.
	#They are also here to remind me to check up on them every now and again to make sure they indeed don't work or if I was just being stupid all along
	System('3DO', '3do', [], [], {MediaType.OpticalDisc: cdrom_formats}),
	#4DO doesn't like Wine and has no native Linux version (just libretro and meh), Phoenix Emu has no command line support; so both are unusable for our purposes. MAME driver just kinda hangs at the 3DO logo at the moment
	System('3DO M2', '3do_m2', ['3do_m2'], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Was never actually released, but prototypes exist
	System('Action Max', None, [], [], {}),
	#No emulators, no dumps (probably nobody has decided the best way to preserve VHS games), no nothing
	System('Bandai Playdia', None, [], [], {MediaType.OpticalDisc: cdrom_formats}),
	System('Casio Loopy', 'casloopy', ['casloopy'], [], {MediaType.Cartridge: ['bin']}),
	System('Coleco Telstar Arcade', [], [], {}),
	System('GameKing', 'gameking', ['gameking'], [], {MediaType.Cartridge: ['bin']}),
	System('GameKing 3', 'gamekin3', ['gameking3'], [], {MediaType.Cartridge: ['bin']}),
	System('Gakken TV Boy', None, [], [], {}),
	#No MAME driver or anything, although it's mentioned on an old MESS 'to be dumped' page; apparently CPU is inside the carts
	System('GP32', 'gp32', ['gp32'], [], {MediaType.Cartridge: ['smc'], MediaType.Executable: ['gxb', 'sxf', 'bin', 'gxf', 'fxe']}),
	#Runs too slow to verify if anything else works, but all documentation points to not
	System('Jaguar CD', 'jaguarcd', [], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Unlike the lack of CD, this does not work at all on anything, doesn't even have a software list yet
	System('Koei PasoGo', 'pasogo', ['pasogo'], [], {MediaType.Cartridge: ['bin']}),
	#No sound in MAME yet, and apparently the rest doesn't work either (I'll take their word for it)
	System('Konami Picno', 'picno', ['picno'], [], {MediaType.Cartridge: ['bin']}),
	System('Leapster', 'leapster', ['leapster'], [], {MediaType.Cartridge: ['bin']}),
	System('Mattel HyperScan', 'hs', ['hyperscan'], [], {MediaType.OpticalDisc: cdrom_formats}),
	System('Microvision', 'microvsn', ['microvision'], [], {MediaType.Cartridge: ['bin']}),
	#Cartridges boot, but seem to do nothing...
	System('N-Gage', None, [], [], {}), #File types are.. folders I think
	System('Nuon', None, [], [], {}),
	System('Pippin', 'pippin', ['pippin', 'pippin_flop'], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Games don't just boot in a PPC Mac, unfortunately. No PPC Mac emulator has branched off into specific Pippin emulation yet
	System('Sawatte Pico', 'sawatte', ['sawatte'], [], {}),
	#Similar to the Sega Pico but with different software (may or may not also use Megadrive ROM header?), but is completely unemulated. Not sure if dump format is identical
	System('V.Smile', 'vsmile', ['vsmile_cart', 'vsmile_cd', 'vsmileb_cart', 'vsmilem_cart'], [], {MediaType.Cartridge: ['bin'], MediaType.OpticalDisc: cdrom_formats}),
	System('Video Challenger', [], [], {}),
	System('Xbox 360', None, [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xex']}),
	#Xenia requires Windows 8 + Vulkan, somehow I don't think it'd ever run under Wine either
	System('ZAPit GameWave', None, [], [], {MediaType.OpticalDisc: ['iso']}),

	#My computer isn't cool enough to emulate these systems, so I can't verify how they work or how well they work just yet
	System('Wii U', None, [], [], {MediaType.OpticalDisc: ['iso', 'wud'], MediaType.Executable: ['rpx', 'elf']}),
	#Decaf requires OpenGL 4.5 (even for software rendering it seems)

	#Things that have usability issues that make things unsuitable for launchering purposes at this point in time
	System('64DD', 'n64dd', ['n64dd'], {MediaType.Floppy: ['ndd', 'ddd']}),
	#Mupen64Plus would work, but right now it has issues with usability that it says right in the readme (so it's not just me picking on them, they say it themselves). Basically you have to have a cart inserted which has the same properties as the 64DD software you want to emulate, and that wouldn't work for our launchering purposes. MAME doesn't seem to work with .ndd format dumps
	System('Cybiko', 'cybikov1', [], [], {MediaType.Digital: ['app']}),
	#Quickload slot doesn't seem to actually quickload anything, and seems to require setup each time. V2 and Extreme have same problems
	System('Dreamcast VMU', 'svmu', ['svmu'], [], {MediaType.Executable: ['bin'], MediaType.Digital: ['vms']}),
	#Makes you set time and date each time; also supposed to have sound apparently but I don't hear any
	System('e-Reader', None, ['gba_ereader'], [], {MediaType.Barcode: ['bin', 'raw', 'bmp']}),
	#VBA-M works (nothing else emulates e-Reader that I know of), but you have to swipe the card manually, which doesn't really work for a nice launcher thing... and there's not really a way around that at this point in time.
	System('Luxor ABC80', 'abc80', ['abc80_cass', 'abc80_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['bac']}),
	#Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	System('PocketStation', 'pockstat', [], [], {MediaType.Digital: ['gme']}),
	#Makes you set time and date each time
	System('RCA Studio 2', 'studio2', ['studio2'], [], {MediaType.Cartridge: ['st2', 'bin', 'rom']}),
	#Due to the console's terrible design, asinine keypad sequences are needed to boot games any further than weird static or a black screen. They're so asinine that even if I look at the info usage in the software list, and do the thing, it still doesn't work. So if it's that complicated that I can't work it out manually, how can I do it programmatically? So yeah, shit
	System('SVI-3x8', 'svi328', ['svi318_cart', 'svi318_cass', 'svi318_flop'], [], {MediaType.Tape: ['wav', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	#Works well, just needs to autoboot tapes, and that might be tricky because you have BLOAD and CLOAD
	System('ZX81', 'zx81', ['zx80_cass', 'zx81_cass'], [], {MediaType.Tape: ['wav', 'cas', 'p', '81', 'tzx']}),
	#Not even gonna try testing any more software without autobooting it, though I'm not sure it does work from the one I did. Anyway, gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing, and even then it's like.... meh....

	#Things that have other weird usability issues
	System('Apple IIgs', 'apple2gs', ['apple2gs'], [], {MediaType.Floppy: mame_floppy_formats + ['2mg']}),
	#Some games require a hard disk with an OS install and they won't tell you this because of course not, and if you want to autoboot the floppies with a hard drive still in there you have to set it to always boot from slot 5 and it's really annoying and I hate it
	System('CreatiVision', 'crvision', ['crvision'], [], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it
	System('Mattel Aquarius', 'aquarius', ['aquarius'], []),
	#Controllers aren't emulated yet (and they're necessary for a lot of things)
	System('Sega Pico', 'pico', ['pico'], []),
	#Emulation works in Kega Fusion and MAME, but they don't display the actual book, which would be needed for most of the software to make any sense. Kega Fusion doesn't even have controls to turn the pages, which is needed for stuff
	System('Super Casette Vision', 'scv', ['scv'], [], {MediaType.Cartridge: ['bin']}),
	#Only supports some games (e.g. with RAM enhancements) via software list, there's no way to override the cart type or anything like that.

	#Might just be me doing something wrong, but seemingly doesn't work so I'll just put them here until I figure out if they definitely don't work, or they actually do
	System('Radio 86-RK', 'radio86', ['radio86_cart', 'radio86_cass'], []),
	System('Mikrosha', 'mikrosha', ['mikrosha_cart', 'mikrosha_cass'], []),
	System('Apogey BK-01', 'apogee', ['apogee'], []),
	System('Partner 01.01', 'partner', ['partner_cass', 'partner_flop'], []),
	System('Orion-128', 'orion128', ['orion_cart', 'orion_cass', 'orion_flop'], []),
	System('PC-6001', 'pc6001', [], []),
	System('FM-7', 'fm7', ['fm7_cass', 'fm7_disk', 'fm77av'], []),

	#TODO: Me being lazy, need to check if these actually work or not:
	System('Acorn Atom', 'atom', ['atom_cass', 'atom_flop', 'atom_rom'], []),
	System('Acorn Electron', 'electron', ['electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'], []),
	System('Amstrad CPC', 'cpc464', ['cpc_cass', 'cpc_flop'], []),
	#The not-plus one (probably will need to switch to cpc664/cpc6128 for flopppy stuff)
	System('APF Imagination Machine', 'apfimag', ['apfimag_cass', 'apfm1000'], []),
	#Considered separate from APF-M1000 (same predicament as Coleco Adam)
	System('Apple I', 'apple1', ['apple1'], []),
	System('Apple II', 'apple2', ['apple2', 'apple2_cass'], []),
	System('Apple Lisa', 'lisa', ['lisa'], []),
	System('Apple III', 'apple3', ['apple3'], []),
	System('Atari Portfolio', 'pofo', ['pofo'], []),
	#Nothing is dumped, so I think it's safe to say nothing will work, but still. Apparently it's supposed to be a PC clone, but doesn't support any PC software lists...
	System('Atari ST', 'st', ['st_flop', 'st_cart'], []),
	#MAME is known to not work here, and Hatari is known to have usability issues... is there anything else?
	System('Bandai Super Vision 8000', 'sv8000', ['sv8000'], []),
	System('BBC Master', 'bbcm', ['bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'], []),
	System('BBC Micro', 'bbcb', ['bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig'], []),
	#The key combination to boot a floppy is like Shift+Break or something ridiculous like that, so I'm not going anywhere without an autoboot script
	#TODO: Add the flop software lists that have addon CPUs and stuff
	System('Cambridge Z88', 'z88', ['z88_cart'], []),
	System('Commodore 16', 'c16', ['plus4_cart', 'plus4_cass', 'plus4_flop'], []),
	#Plus/4 and C116 are in the same software family, so those could be used too
	System('Commodore 65', 'c65', ['c65_flop'], []),
	#This was actually never released, but there's software for it anyway
	System('Commodore 128', 'c128', ['c128_cart', 'c128_flop', 'c128_rom'], []),
	System('Memotech MTX', 'mtx512', ['mtx_cart', 'mtx_cass', 'mtx_rom'], []),
	System('Neo Geo AES', 'aes', ['neogoeo'], [], {MediaType.Cartridge: ['bin']}),
	#Hmm... even emulated re-releases (like the stuff on Steam) is the MVS version. Also how it works is a bit tricky, since as a system you load single .bin files through the cart slot, but everything out there is stored as multiple ROMs, even in the software list... so I dunno if this would be usable
	System('Pocket Challenge W', 'pockchal', ['pockchalw'], [], {MediaType.Cartridge: ['bin']}),
	#Everything in that software list says unsupported, so that's not a good sign
	System('Sam Coupe', 'samcoupe', ['samcoupe_cass', 'samcoupe_flop'], []),
	System('Sharp MZ-700', 'mz700', ['mz700'], []),
	System('Sharp MZ-800', 'mz800', ['mz800'], []),
	System('Sharp MZ-2000', 'mz2000', ['mz2000_cass', 'mz2000_flop'], []),
	System('Squale', 'squale', ['squale_cart'], []),
	#What's interesting is that the XML for the driver says it's compatible with a software list simply called "squale", but that's not in the default hash directory
	System('Tandy CoCo', 'coco3', ['coco_cart', 'coco_flop'], []),
	#Did I want coco/coco2 instead? Hmm. Those seem to work but coco3 seems to not autoboot. It looks like carts >128K require coco3, or if the software list says so
	System('Xbox', 'xbox', [], []),
	#MAME definitely isn't ready yet.. do XQEMU or Cxbx-Reloaded work for our purposes yet?

	#TODO: Me being lazy, I know if these work or not:
	System('Commodore PET', 'pet4032', ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], []),
	#Unsure which one the "main" driver is, or if some of them count as separate systems. This will require autoboot scripts to do stuff anyway
	#TODO: This can work with -quik and autoboot though
	System('Galaksija', 'galaxyp', ['galaxy'], []),
	#This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why.

	#Other todos, often just me not knowing which something actually is or being too lazy to organize it even into the "too lazy to look into right now" list:
	#Are Oric-1 and Oric Atmos software compatible or different things?
	#Which of TI calculators are software compatible with which?
	#Thomson MO: Is MO5 or MO6 the main system? (latter has exclusive software lists, but is compatible with MO5)
	#Thomson MO: Is TO5 or TO8 the main system? (latter has exclusive software lists, but is compatible with TO7)
	#Which TRS-80 model is which?
	#Bandai Super Note Club: Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
	#Dragon 64 part of CoCo or nah?
	#Which PC-98 system is which?
	#Videoton TVC: Which is main system? TV64?
	#Acorn Archimedes stuff (could this end up being amongst dos_mac_common?)
	#C64DTV
	#Jupiter Ace (ZX Spectrum clone but has different compatibility?)
	#TI-99: Main kerfluffle seems to be .rpk file format needed for -cart loading, but everything else is in .c and .g and who knows what else; -ioport peb -ioport:peb:slot2 32kmem -ioport:peb:slot3 speech might be needed?

	#Epoch (not Super) Casette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
	#Coleco Quiz Wiz Challenge might require its own thing: The software cartridges contain no ROMs, just different pinouts, you need the software list to select which one
	#Memotech VIS: Just Windows 3.1?
	#Pioneer LaserActive probably just counts as Mega CD and PC Engine CD except with Laserdisc instead of CD, but I'll worry about that when emulation for it becomes a thing
]

class GameWithEngine():
	def __init__(self, name, engines, uses_folders):
		self.name = name
		self.engines = engines
		self.uses_folders = uses_folders
games_with_engines = {
	'Doom': GameWithEngine('Doom', ['PrBoom+'], False),
	'Quake': GameWithEngine('Quake', ['Darkplaces'], True),
}
#TODO: There should be a Z-Machine interpreter that runs nicely with modern sensibilities, I should look into that
#Duke Nukem 3D and Wolfenstein 3D definitely have various source ports too, just need to find one that works. Should try Theme Hospital (CorsixTH) and Morrowind (OpenMW) too. Enigma might be able to take original Oxyd data files, thus counting as an engine for that?

#TODO: Add these as well (or should I? Maybe I should just leave it to emulator_info):
#Arcade: I guess it's not an array, it's just MAME
#Computers: Mac, DOS (well, they're emulated too, but differently than the above systems)
#Virtual environment-but-not-quite-type-things: J2ME, Flash
#This allows us to organize supported emulators easily and such
