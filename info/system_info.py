from enum import Enum, auto

from common_types import ConfigValueType

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

class SpecificConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type, default_value, description):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class System():
	def __init__(self, mame_driver, mame_software_lists, emulators, file_types=None, specific_configs=None):
		self.mame_driver = mame_driver
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators
		self.file_types = file_types if file_types else {}
		self.specific_configs = specific_configs if specific_configs else {}

	def is_valid_file_type(self, extension):
		return any([extension in extensions for _, extensions in self.file_types.items()])

	def get_media_type(self, extension):
		for media_type, extensions in self.file_types.items():
			if extension in extensions:
				return media_type
		return None

mame_cdrom_formats = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']

#File formats seem to be common between C64/VIC-20/PET/etc
commodore_disk_formats = ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m', 'dsk', 'ipf', 'nib']
#Would be better to just use crt everywhere, but sometimes that just doesn't happen and so the load address has to be stored in the extension
commodore_cart_formats = ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin']

#All known possible CD-ROM formats, for use with file_types and MediaType.OpticalDisc; of course emulator support may vary
cdrom_formats = mame_cdrom_formats + ['cdi', 'ccd', 'toc']

systems = {
	#Note that this is organized into different sections for no rememberable reason, and also contains my rambling sometimes and I also forgot why that is
	#But who am I to remove comments and code formatting

	'3DS': System(None, [], ['Citra'], {MediaType.Cartridge: ['3ds'], MediaType.Digital: ['cxi'], MediaType.Executable: ['3dsx']}),
	'Atari 2600': System('a2600', ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)'], {MediaType.Cartridge: ['a26', 'rom', 'bin']}),
	'Atari 5200': System('a5200', ['a5200'], ['MAME (Atari 5200)'], {MediaType.Cartridge: ['a52', 'car', 'rom', 'bin'], MediaType.Tape: ['wav']}),
	'Atari 7800': System('a7800', ['a7800'], ['A7800', 'MAME (Atari 7800)'], {MediaType.Cartridge: ['a78', 'bin']}),
	'CD-i': System('cdimono1', ['cdi'], ['MAME (CD-i)'], {MediaType.OpticalDisc: cdrom_formats}),
	'ColecoVision': System('coleco', ['coleco'], ['MAME (ColecoVision)'], {MediaType.Cartridge: ['col', 'bin', 'rom']}),
	'Dreamcast': System('dc', ['dc'], ['Reicast'], {MediaType.OpticalDisc: cdrom_formats}),
	'DS': System('nds', [], ['Medusa'], {MediaType.Cartridge: ['nds', 'dsi', 'ids']}),
	'Game Boy': System('gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gb', 'gbc', 'gbx', 'sgb']},
		{'use_gbc_for_dmg': SpecificConfigValue(ConfigValueType.Bool, True, 'Use MAME GBC driver for DMG games'), 'prefer_sgb_over_gbc': SpecificConfigValue(ConfigValueType.Bool, False, 'If a game is both SGB and GBC enhanced, use MAME SGB driver instead of GBC')}),
	'GameCube': System('gcjp', [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz'], MediaType.Executable: ['dol', 'elf']}),
	'Game Gear': System('gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'GBA': System('gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gba', 'bin', 'srl'], MediaType.Executable: ['elf', 'mb']}),
	'Intellivision': System('intv', ['intv', 'intvecs'], ['MAME (Intellivision)'], {MediaType.Cartridge: ['bin', 'int', 'rom', 'itv']}),
	'Lynx': System('lynx', ['lynx'], ['Mednafen (Lynx)'], {MediaType.Cartridge: ['lnx', 'lyx'], MediaType.Executable: ['o']}),
	'Master System': System('sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'Mega Drive': System('megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)'], {MediaType.Cartridge: ['bin', 'gen', 'md', 'smd', 'sgd']}),
	'N64': System('n64', ['n64'], ['Mupen64Plus'], {MediaType.Cartridge: ['z64', 'v64', 'n64', 'bin']}, {'prefer_controller_pak_over_rumble': SpecificConfigValue(ConfigValueType.Bool, True, 'If a game can use both the Controller Pak and the Rumble Pak, use the Controller Pak')}),
	'Neo Geo Pocket': System('ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'], {MediaType.Cartridge: ['ngp', 'npc', 'ngc', 'bin']}),
	'NES': System('nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)'], {MediaType.Cartridge: ['nes', 'unf', 'unif'], MediaType.Floppy: ['fds']}),
	'PC Engine': System('pce', ['pce', 'sgx', 'tg16'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.Cartridge: ['pce', 'sgx', 'bin']}),
	'PlayStation': System('psj', ['psx'], ['Mednafen (PlayStation)'], {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: ['exe', 'psx']}),
	'PS2': System('ps2', [], ['PCSX2'], {MediaType.OpticalDisc: cdrom_formats + ['cso', 'bin'], MediaType.Executable: ['elf']}),
	'PSP': System(None, [], ['PPSSPP'], {MediaType.OpticalDisc: cdrom_formats + ['cso'], MediaType.Executable: ['pbp']}),
	'Saturn': System('saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)'], {MediaType.OpticalDisc: cdrom_formats}),
	'SNES': System('snes', ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)'], {MediaType.Cartridge: ['sfc', 'swc', 'smc', 'bs', 'st', 'bin']}, {'sufami_turbo_bios_path': SpecificConfigValue(ConfigValueType.Path, None, 'Path to Sufami Turbo BIOS, required to run Sufami Turbo carts'), 'bsx_bios_path': SpecificConfigValue(ConfigValueType.Path, None, 'Path to BS-X BIOS, required to run Satellaview games')}),
	'Wii': System(None, [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz'], MediaType.Executable: ['dol', 'elf'], MediaType.Digital: ['wad']}),
	'WonderSwan': System('wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['ws', 'wsc', 'bin']}),
	#Rotates around so that sometimes the dpad becomes buttons and vice versa and there's like two dpads??? but if you use Mednafen's rotation auto-adjust thing it kinda works

	#Obscure systems (<1M units sold), just for the sake of making that list less messy
	#Uzebox is a homebrew thing and not really a commercial product, so it doesn't really have numbers. But it probably counts as obscure.
	#Can't really find numbers on Atari 7800 and Neo Geo Pocket, but they aren't obscure... right?
	'Amiga CD32': System('cd32', ['cd32'], ['FS-UAE'], {MediaType.OpticalDisc: cdrom_formats}),
	'Amstrad GX4000': System('gx4000', ['gx4000'], ['MAME (Amstrad GX4000)', 'MAME (Amstrad CPC+)'], {MediaType.Cartridge: ['bin', 'cpr']}),
	'APF-MP1000': System('apfm1000', ['apfm1000'], ['MAME (APF-MP1000)'], {MediaType.Cartridge: ['bin']}),
	'Arcadia 2001': System('arcadia', ['arcadia'], ['MAME (Arcadia 2001)'], {MediaType.Cartridge: ['bin']}),
	'Astrocade': System('astrocde', ['astrocde'], ['MAME (Astrocade)'], {MediaType.Cartridge: ['bin']}),
	'Bandai Super Vision 8000': System('sv8000', ['sv8000'], ['MAME (Bandai Super Vision 8000)'], {MediaType.Cartridge: ['bin']}),
	'Benesse Pocket Challenge V2': System(None, ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['pc2', 'bin']}),
	#Controls are mapped even worse than regular WonderSwan games, even with rotation auto-adjust you still end up using a stick/dpad as buttons and it gets weird, also the module must be forced or else it won't be recognized. But it works though
	'BBC Bridge Companion': System('bbcbc', ['bbcbc'], ['MAME (BBC Bridge Companion)'], {MediaType.Cartridge: ['bin']}),
	'Casio PV-1000': System('pv1000', ['pv1000'], ['MAME (Casio PV-1000)'], {MediaType.Cartridge: ['bin']}),
	'Channel F': System('channelf', ['channelf'], ['MAME (Channel F)'], {MediaType.Cartridge: ['chf', 'bin']}),
	#It has some sort of knob that you twist up and down or something? What the fuck
	'Commodore CDTV': System('cdtv', ['cdtv'], ['FS-UAE'], {MediaType.OpticalDisc: cdrom_formats}),
	'Entex Adventure Vision': System('advision', ['advision'], ['MAME (Entex Adventure Vision)'], {MediaType.Cartridge: ['bin']}),
	'Epoch Game Pocket Computer': System('gamepock', ['gamepock'], ['MAME (Epoch Game Pocket Computer)'], {MediaType.Cartridge: ['bin']}),
	'Gamate': System('gamate', ['gamate'], ['MAME (Gamate)'], {MediaType.Cartridge: ['bin']}),
	'Game.com': System('gamecom', ['gamecom'], ['MAME (Game.com)'], {MediaType.Cartridge: ['tgc', 'bin']}),
	'Hartung Game Master': System('gmaster', ['gmaster'], ['MAME (Hartung Game Master)'], {MediaType.Cartridge: ['bin']}),
	'Mattel Juice Box': System('juicebox', ['juicebox'], ['MAME (Mattel Juice Box)'], {MediaType.Cartridge: ['smc']}),
	#Now for those who actually do know what this is, you may be thinking: But doesn't that just play videos? Isn't this really pointless? And the answer is yes, yes it is. I love pointless.
	'Mega Duck': System('megaduck', ['megaduck'], ['MAME (Mega Duck)'], {MediaType.Cartridge: ['bin']}),
	'Neo Geo CD': System('neocdz', ['neocd'], ['MAME (Neo Geo CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Nichibutsu My Vision': System('myvision', ['myvision'], ['MAME (Nichibutsu My Vision)'], {MediaType.Cartridge: ['bin']}),
	'PC-FX': System('pcfx', ['pcfx'], ['Mednafen (PC-FX)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Pokemon Mini': System('pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)'], {MediaType.Cartridge: ['min', 'bin']}),
	'SG-1000': System('sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)'], {MediaType.Cartridge: ['sg', 'bin', 'sc'], MediaType.Tape: ['wav', 'bit'], MediaType.Floppy: mame_floppy_formats + ['sf7']}),
	'Super Cassette Vision': System('scv', ['scv'], ['MAME (Super Cassette Vision)'], {MediaType.Cartridge: ['bin']}),
	'Uzebox': System('uzebox', ['uzebox'], ['MAME (Uzebox)'], {MediaType.Executable: ['bin', 'uze']}),
	'VC 4000': System('vc4000', ['vc4000'], ['MAME (VC 4000)'], {MediaType.Cartridge: ['bin', 'rom']}),
	'Vectrex': System('vectrex', ['vectrex'], ['MAME (Vectrex)'], {MediaType.Cartridge: ['vec', 'gam', 'bin']}),
	'Virtual Boy': System('vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'], {MediaType.Cartridge: ['vb', 'vboy', 'bin']}),
	'Watara Supervision': System('svision', ['svision'], ['MAME (Watara Supervision)'], {MediaType.Cartridge: ['ws', 'sv', 'bin']}),

	#Systems that are treated as though they were whole separate things, but they're addons for other systems with their own distinct set of software
	'32X': System('32x', ['32x'], ['Kega Fusion'], {MediaType.Cartridge: ['32x', 'bin']}),
	'Mega CD': System('megacdj', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion'], {MediaType.OpticalDisc: cdrom_formats}),
	'PC Engine CD': System('pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.OpticalDisc: cdrom_formats}),

	#Computers
	'Amiga': System('a1200', ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'], ['FS-UAE'], {MediaType.Floppy: ['adf', 'ipf', 'dms']}, {'default_chipset': SpecificConfigValue(ConfigValueType.String, 'AGA', 'Default chipset to use if a game doesn\'t specify what chipset it should use (AGA, OCS, ECS)')}),
	'Apple II': System('apple2', ['apple2', 'apple2_cass'], ['MAME (Apple II)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib'], MediaType.Tape: ['wav']}),
	'Apple III': System('apple3', ['apple3'], ['MAME (Apple III)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib']}),
	'Atari 8-bit': System('a800', ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)'], {MediaType.Cartridge: ['bin', 'rom', 'car'], MediaType.Tape: ['wav']}),
	#TODO: MediaType.Floppy: ['atr', 'dsk'], MediaType.Executable: ['xex', 'bas'],
	'C64': System('c64', ['c64_cart', 'c64_cass', 'c64_flop'], ['MAME (C64)', 'VICE (SDL2)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	, {'use_fast_c64': SpecificConfigValue(ConfigValueType.Bool, False, 'Use VICE\'s fast but less accurate C64 emulation')}),
	'C128': System('c128', ['c128_cart', 'c128_flop', 'c128_rom'], ['VICE (SDL2)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'Casio PV-2000': System('pv2000', ['pv2000'], ['MAME (Casio PV-2000)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Coleco Adam': System('adam', ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)'], {MediaType.Cartridge: ['col', 'bin'], MediaType.Tape: ['wav', 'ddp'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['lbr', 'com']}),
	'Commodore PET': System('pet4032', ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], ['VICE (SDL2)'], {MediaType.Floppy: commodore_disk_formats, MediaType.Cartridge: ['bin', 'rom'], MediaType.Executable: ['prg', 'p00'], MediaType.Tape: ['wav', 'tap']}),
	#Unsure which one the "main" driver is, or if some of them count as separate systems...
	#TODO: This can work with MAME by using -quik and autoboot, and... there's cartridges? Huh?
	'FM-7': System('fm7', ['fm7_cass', 'fm7_disk', 'fm77av'], ['MAME (FM-7)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav', 't77']}),
	'IBM PCjr': System('ibmpcjr', ['ibmpcjr_cart'], ['MAME (IBM PCjr)'], {MediaType.Cartridge: ['bin', 'jrc'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#For the carts, because otherwise we'd just call the software DOS or PC Booter.
	'MSX': System('svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX1)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'MSX2': System('fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop'], ['MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'PC-88': System('pc8801', ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'Plus/4': System('c16', ['plus4_cart', 'plus4_cass', 'plus4_flop'], ['VICE (SDL2)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	#Family also includes C16 and C116
	'Sharp X1': System('x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)'], {MediaType.Floppy: ['2d'] + mame_floppy_formats, MediaType.Tape: ['wav', 'tap']}),
	'Sharp X68000': System('x68000', ['x68k_flop'], ['MAME (Sharp X68000)'], {MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	'SAM Coupe': System('samcoupe', ['samcoupe_cass', 'samcoupe_flop'], ['SimCoupe'], {MediaType.Floppy: ['mgt', 'sad', 'dsk', 'sdf'], MediaType.Executable: ['sbt']}),
	'Sord M5': System('m5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)'], {MediaType.Cartridge: ['bin'], MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	'Tomy Tutor': System('tutor', ['tutor'], ['MAME (Tomy Tutor)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'VIC-10': System('vic10', ['vic10'], ['MAME (VIC-10)'], {MediaType.Cartridge: ['crt', 'bin', '80', 'e0'], MediaType.Tape: ['wav', 'tap', 't64']}),
	'VIC-20': System('vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)', 'VICE (SDL2)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['wav', 'tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'VZ-200': System('vz200', ['vz_cass'], ['MAME (VZ-200)'], {MediaType.Snapshot: ['vz'], MediaType.Tape: ['wav', 'cas']}),
	#There are many different systems in this family, but I'll go with this one, because the software list is named after it
	'ZX Spectrum': System('spectrum', ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)'], {MediaType.Snapshot: ['z80', 'sna'], MediaType.Tape: ['wav', 'cas', 'tap', 'tzx'], MediaType.Executable: ['raw', 'scr'], MediaType.Floppy: ['dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi'], MediaType.Cartridge: ['bin', 'rom']}),
	#Joystick interface is non-standard so not all games support it and might decide to use the keyboard instead, but eh. It works I guess.
	#There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

}

#Unsupported (yet) systems beyond this point, these won't be listed in any config files by default; just here to make it easier for me to add new systems later as I document what they are and what holds them back, sometimes just because I have nothing better to do I guess

unsupported_systems = {
	#Theoretically supported, but not supported enough to be considered playable, you'd have to put them into systems yourself until I figure out a better way to handle that
	'FM Towns Marty': System('fmtmarty', ['fmtowns_cd', 'fmtowns_flop'], ['MAME (FM Towns Marty)'], {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}),
	'Jaguar': System('jaguar', ['jaguar'], ['MAME (Jaguar)'], {MediaType.Cartridge: ['j64', 'bin', 'rom'], MediaType.Executable: ['abs', 'cof', 'jag', 'prg']}),
	'Magnavox Odyssey²': System('odyssey2', ['odyssey2'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	#O2EM doesn't really work; MAME isn't completely broken but a lot of games have broken graphics so like... ehh
	#TODO: Move comments to emulator_info, do thing which selects g7000/odyssey2 automatically
	'G7400': System('g7400', ['g7400'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	#just has the same problems as Odyssey 2...
	'PC Booter': System('ibm5150', ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#This one is a bit tricky... both MAME and PCem have issues emulating a joystick. Do the games actually just suck like that? _All of them_? I don't know. The majority of these games assume a 4.77MHz CPU, of course. The software list is ibm5150 but that has some DOS games too, just to be confusing (but usage == 'PC booter' where it is a PC booter).
	"Super A'Can": System('supracan', ['supracan'], ["MAME (Super A'Can)"], {MediaType.Cartridge: ['bin']}),

	#No emulators that are cool enough on Linux (any available are too preliminary to work). Yet. Maybe? That I know of. They're here for completeness. Or no emulators at all.
	#They are also here to remind me to check up on them every now and again to make sure they indeed don't work or if I was just being stupid all along
	'3DO': System('3do', [], [], {MediaType.OpticalDisc: cdrom_formats}),
	#4DO doesn't like Wine and has no native Linux version (just libretro and meh), Phoenix Emu has no command line support; so both are unusable for our purposes. MAME driver just kinda hangs at the 3DO logo at the moment
	'3DO M2': System('3do_m2', ['3do_m2'], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Was never actually released, but prototypes exist
	'Action Max': System(None, [], [], {}),
	#No emulators, no dumps (probably nobody has decided the best way to preserve VHS games), no nothing
	'Apple Lisa': System('lisa', ['lisa'], [], {MediaType.Floppy: mame_floppy_formats + ['dc', 'dc42']}),
	#Preliminary MAME driver doesn't seem to boot anything; LisaEm doesn't seem to work with newer OSes and hasn't been updated since
	'Bandai Playdia': System(None, [], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Casio Loopy': System('casloopy', ['casloopy'], [], {MediaType.Cartridge: ['bin']}),
	'Coleco Telstar Arcade': System(None, [], [], {}),
	'Copera': System('copera', ['copera'], [], {MediaType.Cartridge: ['bin', 'md']}),
	#Kega Fusion emulates the Pico well enough to show the message telling you the Copera software won't work on a Pico, at least; otherwise no known emulation
	'GameKing': System('gameking', ['gameking'], [], {MediaType.Cartridge: ['bin']}),
	'GameKing 3': System('gamekin3', ['gameking3'], [], {MediaType.Cartridge: ['bin']}),
	'Gakken TV Boy': System(None, [], [], {}),
	#No MAME driver or anything, although it's mentioned on an old MESS 'to be dumped' page; apparently CPU is inside the carts
	'GP32': System('gp32', ['gp32'], [], {MediaType.Cartridge: ['smc'], MediaType.Executable: ['gxb', 'sxf', 'bin', 'gxf', 'fxe']}),
	#Runs too slow to verify if anything else works, but all documentation points to not
	'Jaguar CD': System('jaguarcd', [], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Unlike the lack of CD, this does not work at all on anything, doesn't even have a software list yet
	'Koei PasoGo': System('pasogo', ['pasogo'], [], {MediaType.Cartridge: ['bin']}),
	#No sound in MAME yet, and apparently the rest doesn't work either (I'll take their word for it)
	'Konami Picno': System('picno', ['picno'], [], {MediaType.Cartridge: ['bin']}),
	'Leapster': System('leapster', ['leapster'], [], {MediaType.Cartridge: ['bin']}),
	'Mattel HyperScan': System('hs', ['hyperscan'], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Microvision': System('microvsn', ['microvision'], [], {MediaType.Cartridge: ['bin']}),
	#Cartridges boot, but seem to do nothing...
	'N-Gage': System(None, [], [], {}), #File types are.. folders I think. That could get weird. Anyway, all emulators at this stage seem to be super-preliminary
	'Nuon': System(None, [], [], {}),
	'Pippin': System('pippin', ['pippin', 'pippin_flop'], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Games don't just boot in a PPC Mac, unfortunately. No PPC Mac emulator has branched off into specific Pippin emulation yet
	'Pocket Challenge W': System('pockchal', ['pockchalw'], [], {MediaType.Cartridge: ['bin']}),
	'Sawatte Pico': System('sawatte', ['sawatte'], [], {}),
	#Similar to the Sega Pico but with different software (may or may not also use Megadrive ROM header?), but is completely unemulated. Not sure if dump format is identical
	'Tomy Prin-C': System('princ', ['princ'], [], {MediaType.Cartridge: ['bin']}), #MAME has skeleton driver that displays a green background and then doesn't go anywhere
	'V.Smile': System('vsmile', ['vsmile_cart', 'vsmile_cd', 'vsmileb_cart', 'vsmilem_cart'], [], {MediaType.Cartridge: ['bin'], MediaType.OpticalDisc: cdrom_formats}), #MAME will boot the carts, but seemingly not proceed any further than title screens (doesn't seem to have input)
	'Video Challenger': System([], [], {}),
	'Xbox': System('xbox', [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xbe']}),
	#Cxbx-Reloaded will only run on Windows; XQEMU isn't ready yet
	'Xbox 360': System(None, [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xex']}),
	#Xenia requires Windows 8 + Vulkan, somehow I don't think it'd ever run under Wine either
	'ZAPit GameWave': System(None, [], [], {MediaType.OpticalDisc: ['iso']}),

	#My computer isn't cool enough to emulate these systems, so I can't verify how they work or how well they work just yet
	'Wii U': System(None, [], [], {MediaType.OpticalDisc: ['iso', 'wud'], MediaType.Executable: ['rpx', 'elf']}),
	#Decaf requires OpenGL 4.5 (even for software rendering it seems)

	#Things that have usability issues that make things unsuitable for launchering purposes at this point in time, but otherwise would work if you're just here because you're wondering what emulators work
	'64DD': System('n64dd', ['n64dd'], {MediaType.Floppy: ['ndd', 'ddd']}),
	#Mupen64Plus would work, but right now it has issues with usability that it says right in the readme (so it's not just me picking on them, they say it themselves). Basically you have to have a cart inserted which has the same properties as the 64DD software you want to emulate, and that wouldn't work for our launchering purposes. MAME doesn't seem to work with .ndd format dumps
	'Apple I': System('apple1', ['apple1'], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['snp']}),
	#Loading tapes would require parsing software list usage to figure out where to put load addresses and things to make an autoboot script, because otherwise it's just way too messy to warrant being in a frontend. Snapshots supposedly exist, but I haven't seen any evidence they actually do, so... whoops
	'C64DTV': System('c64dtv', [], []),
	#Commodore 64 plug and play system that has its own unique software, apparently. MAME driver is skeleton, and VICE doesn't seem to boot anything (it is noted as being WIP/experimental)
	'Commodore 65': System('c65', ['c65_flop'], []),
	#This was actually never released, but there's software for it anyway. However, this is only supported by MAME, and it seems it only supports loading by software lists (there are no media slots), which won't work for our purposes at this point in time
	'Cybiko': System('cybikov1', [], [], {MediaType.Digital: ['app']}),
	#Quickload slot doesn't seem to actually quickload anything, and seems to require setup each time. V2 and Extreme have same problems
	'Dreamcast VMU': System('svmu', ['svmu'], [], {MediaType.Executable: ['bin'], MediaType.Digital: ['vms']}),
	#Makes you set time and date each time; also supposed to have sound apparently but I don't hear any
	'e-Reader': System(None, ['gba_ereader'], [], {MediaType.Barcode: ['bin', 'raw', 'bmp']}),
	#VBA-M works (nothing else emulates e-Reader that I know of), but you have to swipe the card manually, which doesn't really work for a nice launcher thing... and there's not really a way around that at this point in time.
	'Luxor ABC80': System('abc80', ['abc80_cass', 'abc80_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['bac']}),
	#Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	'Neo Geo AES': System('aes', ['neogoeo'], [], {MediaType.Cartridge: ['bin']}),
	#Theoretically this works, but fullpath loading only works as a single .bin file which nothing ever is dumped as. This would only ever be useful with software list support. As for separate Neo Geo emulators... well, they all only seem interested in MVS and CD
	'Oric': System('orica', [], []),
	#MAME has oric1 as well... either way, they don't seem to actually load anything I've tried. There's no software lists, so nothing that says anything is supposed to work
	#Oricutron loads things automatically and other nice things, but has issues with fullscreen
	'PC-6001': System('pc6001', [], []),
	#MAME driver is preliminary and notes in source file comments it doesn't load tapes yet; PC6001VX doesn't do command line arguments so un-launcherable
	'PocketStation': System('pockstat', [], [], {MediaType.Digital: ['gme']}),
	#Makes you set time and date each time
	'RCA Studio 2': System('studio2', ['studio2'], [], {MediaType.Cartridge: ['st2', 'bin', 'rom']}),
	#Due to the console's terrible design, asinine keypad sequences are needed to boot games any further than weird static or a black screen. They're so asinine that even if I look at the info usage in the software list, and do the thing, it still doesn't work. So if it's that complicated that I can't work it out manually, how can I do it programmatically? So yeah, shit
	'SVI-3x8': System('svi328', ['svi318_cart', 'svi318_cass', 'svi318_flop'], [], {MediaType.Tape: ['wav', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	#Works well, just needs to autoboot tapes, and that might be tricky because you have BLOAD and CLOAD (and how does one even tell the difference programmatically)
	'ZX81': System('zx81', ['zx80_cass', 'zx81_cass'], [], {MediaType.Tape: ['wav', 'cas', 'p', '81', 'tzx']}),
	#Not even gonna try testing any more software without autobooting it, though I'm not sure it does work from the one I did. Anyway, gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing, and even then it's like.... meh....
	'Radio 86-RK': System('radio86', ['radio86_cart', 'radio86_cass'], []),
	#These and the other USSR systems below are all sorta the same (but might not be software-compatible?) anyway they only have tapes for software, and are mostly only emulated by MAME which has tape annoyances, or that online thing which is online and not suitable for a launcher
	'Mikrosha': System('mikrosha', ['mikrosha_cart', 'mikrosha_cass'], []),
	'Apogey BK-01': System('apogee', ['apogee'], []),
	'Partner 01.01': System('partner', ['partner_cass', 'partner_flop'], []),
	'Orion-128': System('orion128', ['orion_cart', 'orion_cass', 'orion_flop'], []),

	#Things that have other weird usability issues
	'Apple IIgs': System('apple2gs', ['apple2gs'], [], {MediaType.Floppy: mame_floppy_formats + ['2mg']}),
	#Some games require a hard disk with an OS install and they won't tell you this because of course not, and if you want to autoboot the floppies with a hard drive still in there you have to set it to always boot from slot 5 and it's really annoying and I hate it
	'CreatiVision': System('crvision', ['crvision'], [], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it
	'Mattel Aquarius': System('aquarius', ['aquarius'], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	#Controllers aren't emulated yet (and they're necessary for a lot of things)
	'Sega Pico': System('pico', ['pico'], [], {MediaType.Cartridge: ['bin', 'md']}),
	#Emulation works in Kega Fusion and MAME, but they don't display the actual book, which would be needed for most of the software to make any sense. Kega Fusion doesn't even have controls to turn the pages, which is needed for stuff

	#TODO: Me being lazy, need to check if these actually work or not:
	'Acorn Atom': System('atom', ['atom_cass', 'atom_flop', 'atom_rom'], []),
	'Amstrad CPC': System('cpc464', ['cpc_cass', 'cpc_flop'], []),
	#The not-plus one (probably will need to switch to cpc664/cpc6128 for flopppy stuff)
	'APF Imagination Machine': System('apfimag', ['apfimag_cass', 'apfm1000'], []),
	#Considered separate from APF-M1000 (same predicament as Coleco Adam)
	'Atari Portfolio': System('pofo', ['pofo'], []),
	#Nothing is dumped, so I think it's safe to say nothing will work, but still. Apparently it's supposed to be a PC clone, but doesn't support any PC software lists...
	'Atari ST': System('st', ['st_flop', 'st_cart'], []),
	#MAME is known to not work here, and Hatari is known to have usability issues... is there anything else?
	'BBC Master': System('bbcm', ['bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'], []),
	'Epoch Sorcerer': System('sorcerer', ['sorcerer_cart', 'sorcerer_cass', 'sorcerer_flop'],
		{MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav', 'tape']}),
	#Would need automated tape loading to do anything interesting (carts and floppies are just BASIC/OS stuff, also what even is the file type for floppies?) and apparently there's a .snp snapshot and .bin quickload so maybe those do something
	'Goldstar FC-100': System('fc100', [], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas']}),
	#No software list, some kind of PC-6001 clone or something
	'Memotech MTX': System('mtx512', ['mtx_cart', 'mtx_cass', 'mtx_rom'], []),
	'Sharp MZ-700': System('mz700', ['mz700'], []),
	'Sharp MZ-800': System('mz800', ['mz800'], []),
	'Sharp MZ-2000': System('mz2000', ['mz2000_cass', 'mz2000_flop'], []),
	'Squale': System('squale', ['squale_cart'], []),
	#What's interesting is that the XML for the driver says it's compatible with a software list simply called "squale", but that's not in the default hash directory
	'Tandy CoCo': System('coco3', ['coco_cart', 'coco_flop'], []),
	#Did I want coco/coco2 instead? Hmm. Those seem to work but coco3 seems to not autoboot. It looks like carts >128K require coco3, or if the software list says so

	#TODO: Me being lazy, I know if these work or not but they require effort:
	'Acorn Electron': System('electron', ['electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'], []),
	#Seems to require the same Shift+Break to boot as BBC Micro, so... dang
	'BBC Micro': System('bbcb', ['bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig', 'bbc_flop_65c102', 'bbc_flop_6502', 'bbc_flop_32016', 'bbc_flop_68000', 'bbc_flop_80186', 'bbc_flop_arm', 'bbc_flop_torch', 'bbc_flop_z80'], []),
	#The key combination to boot a floppy is Shift+Break which is rather awkward to press especially every time you just want to use some software, so I'm not going anywhere without an autoboot script
	#Otherwise, it does seem to boot floppies..
	'Cambridge Z88': System('z88', ['z88_cart'], []),
	#Marked as not working due to missing expansion interface and serial port and other things, not sure how important that would be... anyway, I'd need to do an autoboot thing to press the key to start the thing, because otherwise it's annoying to navigate every time, and then... hmm, I guess I dunno what actually is a function of things not working yet
	'Galaksija': System('galaxyp', ['galaxy'], [], {MediaType.Snapshot: ['gal'], MediaType.Tape: ['wav', 'gtp']}),
	#This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why. Anyway, we'd go with those and make an autoboot script (maybe just -autoboot_command '\n' would work with suitable delay). galaxy is regular system, galaxyp is an upgraded one which appears to be completely backwards compatible

	#Other todos, often just me not knowing which something actually is or being too lazy to organize it even into the "too lazy to look into right now" list:
	#Which of TI calculators are software compatible with which?
	#Thomson MO: Is MO5 or MO6 the main system? (latter has exclusive software lists, but is compatible with MO5)
	#Thomson MO: Is TO5 or TO8 the main system? (latter has exclusive software lists, but is compatible with TO7)
	#Which TRS-80 model is which?
	#Bandai Super Note Club: Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
	#Dragon 64 part of CoCo or nah?
	#Which PC-98 system is which?
	#Videoton TVC: Which is main system? TV64?
	#Acorn Archimedes stuff (could this end up being amongst dos_mac_common?)
	#Jupiter Ace (ZX Spectrum clone but has different compatibility?)
	#TI-99: Main kerfluffle seems to be .rpk file format needed for -cart loading, but everything else is in .c and .g and who knows what else; -ioport peb -ioport:peb:slot2 32kmem -ioport:peb:slot3 speech might be needed?
	#CBM-II (VIC-II and CRTC models)

	#Epoch (not Super) Casette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
	#Coleco Quiz Wiz Challenge might require its own thing: The software cartridges contain no ROMs, just different pinouts, you need the software list to select which one
	#Memotech VIS: Just Windows 3.1?
	#Pioneer LaserActive probably just counts as Mega CD and PC Engine CD except with Laserdisc instead of CD, but I'll worry about that when emulation for it becomes a thing
}

class GameWithEngine():
	def __init__(self, name, engines, uses_folders, specific_configs=None):
		self.name = name
		self.engines = engines
		self.uses_folders = uses_folders
		self.specific_configs = specific_configs if specific_configs else {}

games_with_engines = {
	'Doom': GameWithEngine('Doom', ['PrBoom+'], False, {'save_dir': SpecificConfigValue(ConfigValueType.Path, None, 'Folder to put save files in')}),
	'Quake': GameWithEngine('Quake', ['Darkplaces'], True),
}
#TODO: There should be a Z-Machine interpreter that runs nicely with modern sensibilities, I should look into that
#Duke Nukem 3D and Wolfenstein 3D definitely have various source ports too, just need to find one that works. Should try Theme Hospital (CorsixTH) and Morrowind (OpenMW) too. Enigma might be able to take original Oxyd data files, thus counting as an engine for that?

class ComputerSystem():
	#Need a better name for this shit
	def __init__(self, specific_configs):
		self.specific_configs = specific_configs if specific_configs else {}

computer_systems = {
	'Mac': ComputerSystem({'shared_folder': SpecificConfigValue(ConfigValueType.Path, None, 'Path to shared folder on host that guest can see. This is mandatory for all this Mac stuff to work'), 'default_width': SpecificConfigValue(ConfigValueType.String, 1920, 'Emulated screen width to run at if a game doesn\'t need a specific screen resolution'), 'default_height': SpecificConfigValue(ConfigValueType.String, 1080, 'Emulated screen height to run at if a game doesn\'t need a specific screen resolution')}),
	'DOS': ComputerSystem({'slow_cpu_cycles': SpecificConfigValue(ConfigValueType.String, 477, 'CPU cycles to run at for games only designed to run at 4.77 MHz clock speed')})
}

#TODO: Add these as well (or should I? Maybe I should just leave it to emulator_info):
#Arcade: I guess it's not an array, it's just MAME
#Virtual environment-but-not-quite-type-system-things: J2ME, Flash (but once those have nicer emulators, until then never mind, or maybe I could pretend they're emulated systems)
#This allows us to organize supported emulators easily and such
