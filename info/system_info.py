import os

from common_types import ConfigValueType, MediaType
from common_paths import data_dir

class SpecificConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type, default_value, description):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class SystemInfo():
	def __init__(self, mame_driver, mame_software_lists, emulators, file_types=None, specific_configs=None, is_virtual=False):
		self.mame_driver = mame_driver
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators
		self.file_types = file_types if file_types else {}
		self.specific_configs = specific_configs if specific_configs else {}
		self.is_virtual = is_virtual #Maybe needs better name

	def is_valid_file_type(self, extension):
		return any([extension in extensions for _, extensions in self.file_types.items()])

	def get_media_type(self, extension):
		for media_type, extensions in self.file_types.items():
			if extension in extensions:
				return media_type
		return None

	@property
	def is_unsupported(self):
		return False

class UnsupportedSystemInfo(SystemInfo):
	@property
	def is_unsupported(self):
		return True

mame_cdrom_formats = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']

#File formats seem to be common between C64/VIC-20/PET/etc
commodore_disk_formats = ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m', 'dsk', 'ipf', 'nib']
#Would be better to just use crt everywhere, but sometimes that just doesn't happen and so the load address has to be stored in the extension
commodore_cart_formats = ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin']
#There is also .cu which is some Harmony Cart format which might not work so easily… .ar is actually Supercharger which also might be different
atari_2600_cartridge_extensions = ['2k', '4k', 'f8', 'ef', 'efs', 'f4', 'f4s', 'fa', 'fe', '3f', '3e', 'e0', 'f8s', 'f6', 'f6s', 'e7', 'cv', 'ua', 'ar', 'dpc', '084']


#All known possible CD-ROM formats, for use with file_types and MediaType.OpticalDisc; of course emulator support may vary
cdrom_formats = mame_cdrom_formats + ['cdi', 'ccd']

systems = {
	#Note that this is organized into different sections for no rememberable reason, and also contains my rambling sometimes and I also forgot why that is
	#But who am I to remove comments and code formatting

	'3DS': SystemInfo(None, [], ['Citra'], {MediaType.Cartridge: ['3ds'], MediaType.Digital: ['cxi'], MediaType.Executable: ['3dsx']}),
	'Atari 2600': SystemInfo('a2600', ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)'], {MediaType.Cartridge: ['a26', 'rom', 'bin'] + atari_2600_cartridge_extensions}),
	'Atari 5200': SystemInfo('a5200', ['a5200'], ['MAME (Atari 5200)'], {MediaType.Cartridge: ['a52', 'car', 'rom', 'bin'], MediaType.Tape: ['wav']}),
	'Atari 7800': SystemInfo('a7800', ['a7800'], ['A7800', 'MAME (Atari 7800)'], {MediaType.Cartridge: ['a78', 'bin']}),
	'CD-i': SystemInfo('cdimono1', ['cdi'], ['MAME (CD-i)'], {MediaType.OpticalDisc: cdrom_formats}),
	'ColecoVision': SystemInfo('coleco', ['coleco'], ['MAME (ColecoVision)'], {MediaType.Cartridge: ['col', 'bin', 'rom']}),
	'Dreamcast': SystemInfo('dc', ['dc'], ['Reicast', 'Flycast', 'MAME (Dreamcast)'], {MediaType.OpticalDisc: cdrom_formats}, {'force_opengl_version': SpecificConfigValue(ConfigValueType.Bool, False, 'Add environment variable to force Mesa OpenGL version, which is probably a bad idea')}),
	'DS': SystemInfo('nds', [], ['Medusa'], {MediaType.Cartridge: ['nds', 'dsi', 'ids']}),
	'Game Boy': SystemInfo('gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gb', 'gbc', 'gbx', 'sgb']},
		{'use_gbc_for_dmg': SpecificConfigValue(ConfigValueType.Bool, True, 'Use MAME GBC driver for DMG games'), 'prefer_sgb_over_gbc': SpecificConfigValue(ConfigValueType.Bool, False, 'If a game is both SGB and GBC enhanced, use MAME SGB driver instead of GBC')}),
	'GameCube': SystemInfo('gcjp', [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz'], MediaType.Executable: ['dol', 'elf']}),
	'Game Gear': SystemInfo('gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'GBA': SystemInfo('gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gba', 'bin', 'srl'], MediaType.Executable: ['elf', 'mb']}),
	'Intellivision': SystemInfo('intv', ['intv', 'intvecs'], ['MAME (Intellivision)'], {MediaType.Cartridge: ['bin', 'int', 'rom', 'itv']}),
	'Lynx': SystemInfo('lynx', ['lynx'], ['Mednafen (Lynx)', 'MAME (Lynx)'], {MediaType.Cartridge: ['lnx', 'lyx'], MediaType.Executable: ['o']}),
	'Master System': SystemInfo('sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)', 'MAME (Master System)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'Mega Drive': SystemInfo('megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)', 'MAME (Mega Drive)'], {MediaType.Cartridge: ['bin', 'gen', 'md', 'smd', 'sgd']}),
	'N64': SystemInfo('n64', ['n64'], ['Mupen64Plus', 'MAME (N64)'], {MediaType.Cartridge: ['z64', 'v64', 'n64', 'bin']}, {'prefer_controller_pak_over_rumble': SpecificConfigValue(ConfigValueType.Bool, True, 'If a game can use both the Controller Pak and the Rumble Pak, use the Controller Pak')}),
	'Neo Geo Pocket': SystemInfo('ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'], {MediaType.Cartridge: ['ngp', 'npc', 'ngc', 'bin']}),
	'NES': SystemInfo('nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)', 'cxNES'], {MediaType.Cartridge: ['nes', 'unf', 'unif'], MediaType.Floppy: ['fds']}),
	'PC Engine': SystemInfo('pce', ['pce', 'sgx', 'tg16'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)', 'MAME (PC Engine)'], {MediaType.Cartridge: ['pce', 'sgx', 'bin']}),
	'PlayStation': SystemInfo('psj', ['psx'], ['Mednafen (PlayStation)', 'PCSX2'], {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: ['exe', 'psx']}),
	'PS2': SystemInfo('ps2', [], ['PCSX2'], {MediaType.OpticalDisc: cdrom_formats + ['cso', 'bin'], MediaType.Executable: ['elf']}),
	'PSP': SystemInfo(None, [], ['PPSSPP'], {MediaType.OpticalDisc: cdrom_formats + ['cso'], MediaType.Executable: ['pbp']}),
	'Saturn': SystemInfo('saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)', 'MAME (Saturn)'], {MediaType.OpticalDisc: cdrom_formats}),
	'SNES': SystemInfo('snes', ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)'], {MediaType.Cartridge: ['sfc', 'swc', 'smc', 'bs', 'st', 'bin']}, {'sufami_turbo_bios_path': SpecificConfigValue(ConfigValueType.FilePath, None, 'Path to Sufami Turbo BIOS, required to run Sufami Turbo carts'), 'bsx_bios_path': SpecificConfigValue(ConfigValueType.FilePath, None, 'Path to BS-X BIOS, required to run Satellaview games')}),
	'Switch': SystemInfo(None, [], ['Yuzu'], {MediaType.Cartridge: ['xci'], MediaType.Digital: ['nsp', 'nca'], MediaType.Executable: ['nro', 'nso', 'elf']}),
	'V.Smile': SystemInfo('vsmile', ['vsmile_cart'], ['MAME (V.Smile)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	'Wii': SystemInfo(None, [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'wbfs'], MediaType.Executable: ['dol', 'elf'], MediaType.Digital: ['wad']}),
	'WonderSwan': SystemInfo('wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['ws', 'wsc', 'bin']}),
	#Rotates around so that sometimes the dpad becomes buttons and vice versa and there's like two dpads??? but if you use Mednafen's rotation auto-adjust thing it kinda works

	#Obscure systems (<1M units sold), just for the sake of making that list less messy (maybe I should just like... not do things that way)
	#Uzebox is a homebrew thing and not really a commercial product, so it doesn't really have numbers. But it probably counts as obscure.
	#Can't really find numbers on Atari 7800 and Neo Geo Pocket, but they aren't obscure... right?
	'Amiga CD32': SystemInfo('cd32', ['cd32'], ['FS-UAE', 'MAME (Amiga CD32)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Amstrad GX4000': SystemInfo('gx4000', ['gx4000'], ['MAME (Amstrad GX4000)'], {MediaType.Cartridge: ['bin', 'cpr']}),
	'APF-MP1000': SystemInfo('apfm1000', ['apfm1000'], ['MAME (APF-MP1000)'], {MediaType.Cartridge: ['bin']}),
	'Arcadia 2001': SystemInfo('arcadia', ['arcadia'], ['MAME (Arcadia 2001)'], {MediaType.Cartridge: ['bin']}),
	'Astrocade': SystemInfo('astrocde', ['astrocde'], ['MAME (Astrocade)'], {MediaType.Cartridge: ['bin']}),
	'Bandai Super Vision 8000': SystemInfo('sv8000', ['sv8000'], ['MAME (Bandai Super Vision 8000)'], {MediaType.Cartridge: ['bin']}),
	'Benesse Pocket Challenge V2': SystemInfo(None, ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['pc2', 'bin']}),
	#Controls are mapped even worse than regular WonderSwan games, even with rotation auto-adjust you still end up using a stick/dpad as buttons and it gets weird, also the module must be forced or else it won't be recognized. But it works though
	'BBC Bridge Companion': SystemInfo('bbcbc', ['bbcbc'], ['MAME (BBC Bridge Companion)'], {MediaType.Cartridge: ['bin']}),
	'Casio PV-1000': SystemInfo('pv1000', ['pv1000'], ['MAME (Casio PV-1000)'], {MediaType.Cartridge: ['bin']}),
	'Channel F': SystemInfo('channelf', ['channelf'], ['MAME (Channel F)'], {MediaType.Cartridge: ['chf', 'bin']}),
	#It has some sort of knob that you twist up and down or something? What the fuck
	'Commodore CDTV': SystemInfo('cdtv', ['cdtv'], ['FS-UAE', 'MAME (Commodore CDTV)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Entex Adventure Vision': SystemInfo('advision', ['advision'], ['MAME (Entex Adventure Vision)'], {MediaType.Cartridge: ['bin']}),
	'Epoch Game Pocket Computer': SystemInfo('gamepock', ['gamepock'], ['MAME (Epoch Game Pocket Computer)'], {MediaType.Cartridge: ['bin']}),
	'Gamate': SystemInfo('gamate', ['gamate'], ['MAME (Gamate)'], {MediaType.Cartridge: ['bin']}),
	'Game.com': SystemInfo('gamecom', ['gamecom'], ['MAME (Game.com)'], {MediaType.Cartridge: ['tgc', 'bin']}),
	'Hartung Game Master': SystemInfo('gmaster', ['gmaster'], ['MAME (Hartung Game Master)'], {MediaType.Cartridge: ['bin']}),
	'Mattel Juice Box': SystemInfo('juicebox', ['juicebox'], ['MAME (Mattel Juice Box)'], {MediaType.Cartridge: ['smc']}),
	#Now for those who actually do know what this is, you may be thinking: But doesn't that just play videos? Isn't this really pointless? And the answer is yes, yes it is. I love pointless.
	'Mega Duck': SystemInfo('megaduck', ['megaduck'], ['MAME (Mega Duck)'], {MediaType.Cartridge: ['bin']}),
	'Memorex VIS': SystemInfo('vis', [], ['MAME (Memorex VIS)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Neo Geo CD': SystemInfo('neocdz', ['neocd'], ['MAME (Neo Geo CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Nichibutsu My Vision': SystemInfo('myvision', ['myvision'], ['MAME (Nichibutsu My Vision)'], {MediaType.Cartridge: ['bin']}),
	'PC-FX': SystemInfo('pcfx', ['pcfx'], ['Mednafen (PC-FX)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Pokemon Mini': SystemInfo('pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)'], {MediaType.Cartridge: ['min', 'bin']}),
	'SG-1000': SystemInfo('sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)'], {MediaType.Cartridge: ['sg', 'bin', 'sc'], MediaType.Tape: ['wav', 'bit'], MediaType.Floppy: mame_floppy_formats + ['sf7']}),
	'Super Cassette Vision': SystemInfo('scv', ['scv'], ['MAME (Super Cassette Vision)'], {MediaType.Cartridge: ['bin']}),
	'Uzebox': SystemInfo('uzebox', ['uzebox'], ['MAME (Uzebox)'], {MediaType.Executable: ['bin', 'uze']}),
	'VC 4000': SystemInfo('vc4000', ['vc4000', 'database'], ['MAME (VC 4000)'], {MediaType.Cartridge: ['bin', 'rom']}),
	'Vectrex': SystemInfo('vectrex', ['vectrex'], ['MAME (Vectrex)'], {MediaType.Cartridge: ['vec', 'gam', 'bin']}),
	'Virtual Boy': SystemInfo('vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'], {MediaType.Cartridge: ['vb', 'vboy', 'bin']}),
	'Watara Supervision': SystemInfo('svision', ['svision'], ['MAME (Watara Supervision)'], {MediaType.Cartridge: ['ws', 'sv', 'bin']}),

	#Systems that are treated as though they were whole separate things, but they're addons for other systems with their own distinct set of software
	'32X': SystemInfo('32x', ['32x'], ['Kega Fusion', 'MAME (32X)'], {MediaType.Cartridge: ['32x', 'bin']}),
	'Mega CD': SystemInfo('megacdj', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion', 'MAME (Mega CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'PC Engine CD': SystemInfo('pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.OpticalDisc: cdrom_formats}),

	#Computers
	'Amiga': SystemInfo('a500', ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'], ['FS-UAE'], {MediaType.Floppy: ['adf', 'ipf', 'dms']}, {'default_chipset': SpecificConfigValue(ConfigValueType.String, 'AGA', 'Default chipset to use if a game doesn\'t specify what chipset it should use (AGA, OCS, ECS)')}),
	'Apple II': SystemInfo('apple2', ['apple2', 'apple2_cass', 'apple2_flop_orig', 'apple2_flop_clcracked', 'apple2_flop_misc'], ['MAME (Apple II)', 'Mednafen (Apple II)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz', 'shk', 'bxy'], MediaType.Tape: ['wav']}),
	'Apple IIgs': SystemInfo('apple2gs', ['apple2gs'], ['MAME (Apple IIgs)'], {MediaType.Floppy: mame_floppy_formats + ['2mg', '2img', 'dc', 'shk', 'bxy']}),
	'Apple III': SystemInfo('apple3', ['apple3'], ['MAME (Apple III)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz']}),
	'Atari 8-bit': SystemInfo('a800', ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)'], {MediaType.Floppy: ['atr', 'dsk', 'xfd', 'dcm'], MediaType.Executable: ['xex', 'bas', 'com'], MediaType.Cartridge: ['bin', 'rom', 'car'], MediaType.Tape: ['wav']}, {'basic_path': SpecificConfigValue(ConfigValueType.FilePath, None, 'Path to BASIC ROM for floppy software which requires that')}),
	'C64': SystemInfo('c64', ['c64_cart', 'c64_cass', 'c64_flop'], ['MAME (C64)', 'VICE (C64)', 'VICE (C64 Fast)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}),
	'C128': SystemInfo('c128', ['c128_cart', 'c128_flop', 'c128_rom'], ['VICE (C128)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'Casio PV-2000': SystemInfo('pv2000', ['pv2000'], ['MAME (Casio PV-2000)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Coleco Adam': SystemInfo('adam', ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)'], {MediaType.Cartridge: ['col', 'bin'], MediaType.Tape: ['wav', 'ddp'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['lbr', 'com']}),
	'Commodore PET': SystemInfo('pet2001', ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], ['VICE (Commodore PET)'], {MediaType.Floppy: commodore_disk_formats, MediaType.Cartridge: ['bin', 'rom'], MediaType.Executable: ['prg', 'p00'], MediaType.Tape: ['wav', 'tap']}),
	#Unsure which one the "main" driver is, or if some of them count as separate systems...
	#TODO: This can work with MAME by using -quik and autoboot, and... there's cartridges? Huh?
	'FM-7': SystemInfo('fm7', ['fm7_cass', 'fm7_disk', 'fm77av'], ['MAME (FM-7)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav', 't77']}),
	'FM Towns': SystemInfo('fmtmarty', ['fmtowns_cd', 'fmtowns_flop'], ['MAME (FM Towns Marty)'], {MediaType.Floppy: mame_floppy_formats + ['bin'], MediaType.OpticalDisc: cdrom_formats}),
	#Not bothering adding the FM Towns Not-Marty MAME driver as it just makes some things not work (if they're non-bootable disks)
	'IBM PCjr': SystemInfo('ibmpcjr', ['ibmpcjr_cart'], ['MAME (IBM PCjr)'], {MediaType.Cartridge: ['bin', 'jrc'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#For the carts, because otherwise we'd just call the software DOS or PC Booter.
	'MSX': SystemInfo('svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'MSX2': SystemInfo('fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop', 'msx2p_flop'], ['MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'PC-88': SystemInfo('pc8801', ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'Plus/4': SystemInfo('c16', ['plus4_cart', 'plus4_cass', 'plus4_flop'], ['VICE (Plus/4)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	#Family also includes C16 and C116
	'Sharp X1': SystemInfo('x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)'], {MediaType.Floppy: ['2d'] + mame_floppy_formats, MediaType.Tape: ['wav', 'tap']}),
	'Sharp X68000': SystemInfo('x68000', ['x68k_flop'], ['MAME (Sharp X68000)'], {MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim'], MediaType.HardDisk: ['hdf']}),
	'SAM Coupe': SystemInfo('samcoupe', ['samcoupe_cass', 'samcoupe_flop'], ['SimCoupe', 'MAME (SAM Coupe)'], {MediaType.Floppy: ['mgt', 'sad', 'dsk', 'sdf'], MediaType.Executable: ['sbt']}),
	'Sord M5': SystemInfo('m5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)'], {MediaType.Cartridge: ['bin'], MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	'Squale': SystemInfo('squale', ['squale_cart'], ['MAME (Squale)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin']}),
	#What's interesting is that the XML for the driver says it's compatible with a software list simply called "squale", but that doesn't exist
	'SVI-3x8': SystemInfo('svi328', ['svi318_cart', 'svi318_cass', 'svi318_flop'], ['MAME (SVI-3x8)'], {MediaType.Tape: ['wav', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'Tandy CoCo': SystemInfo('coco3', ['coco_cart', 'coco_flop'], ['MAME (Tandy CoCo)'], {MediaType.Cartridge: ['ccc', 'rom', 'bin'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats + ['dmk', 'jvc']}),
	#Also has .vhd hard disks
	'Thomson MO5': SystemInfo('mo5', ['mo5_cart', 'mo5_cass', 'mo5_flop', 'mo5_qd'], ['MAME (Thomson MO5)'], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}),
	'Tomy Tutor': SystemInfo('tutor', ['tutor'], ['MAME (Tomy Tutor)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'VIC-10': SystemInfo('vic10', ['vic10'], ['MAME (VIC-10)'], {MediaType.Cartridge: ['crt', 'bin', '80', 'e0'], MediaType.Tape: ['wav', 'tap', 't64']}),
	'VIC-20': SystemInfo('vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)', 'VICE (VIC-20)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['wav', 'tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'VZ-200': SystemInfo('vz200', ['vz_cass', 'vz_snap'], ['MAME (VZ-200)'], {MediaType.Snapshot: ['vz'], MediaType.Tape: ['wav', 'cas']}),
	#There are many different systems in this family, but I'll go with this one, because the software list is named after it
	'ZX Spectrum': SystemInfo('spectrum', ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)'], {MediaType.Snapshot: ['z80', 'sna'], MediaType.Tape: ['wav', 'cas', 'tap', 'tzx'], MediaType.Executable: ['raw', 'scr'], MediaType.Floppy: ['dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi', 'opd', 'opu'], MediaType.Cartridge: ['bin', 'rom']}),
	#Joystick interface is non-standard so not all games support it and might decide to use the keyboard instead, but eh. It works I guess.
	#There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

	#Stuff that isn't really a game system but we can pretend it is one
	'Doom': SystemInfo(None, [], ['PrBoom+'], {MediaType.Digital: ['wad']}, {'save_dir': SpecificConfigValue(ConfigValueType.FolderPath, None, 'Folder to put save files in')}, is_virtual=True),
}

#Unsupported (yet) systems beyond this point, these won't be listed in any config files by default; just here to make it easier for me to add new systems later as I document what they are and what holds them back, sometimes just because I have nothing better to do I guess

systems.update({
	#Theoretically supported, but not supported enough to be considered playable (see emulator_info for commentary there), but you can manually add them to systems.ini if you really want
	'GameKing': UnsupportedSystemInfo('gameking', ['gameking'], ['MAME (GameKing)'], {MediaType.Cartridge: ['bin', 'gk']}),
	#Still no sound
	'GameKing 3': UnsupportedSystemInfo('gamekin3', ['gameking3'], ['MAME (GameKing 3)'], {MediaType.Cartridge: ['bin', 'gk3']}),
	'Jaguar': UnsupportedSystemInfo('jaguar', ['jaguar'], ['MAME (Jaguar)'], {MediaType.Cartridge: ['j64', 'bin', 'rom'], MediaType.Executable: ['abs', 'cof', 'jag', 'prg']}),
	'Magnavox Odyssey²': UnsupportedSystemInfo('odyssey2', ['odyssey2'], ['MAME (Magnavox Odyssey²)', 'MAME (G7400)'], {MediaType.Cartridge: ['bin', 'rom']}),
	'G7400': UnsupportedSystemInfo('g7400', ['g7400'], ['MAME (G7400)'], {MediaType.Cartridge: ['bin', 'rom']}),
	'PC Booter': UnsupportedSystemInfo('ibm5150', ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)'], {MediaType.Floppy: mame_floppy_formats + ['img'], MediaType.Executable: ['exe', 'com', 'bat']}),
	#This one is a bit tricky... both MAME and PCem have issues emulating a joystick. Do the games actually just suck like that? _All of them_? I don't know. The majority of these games assume a 4.77MHz CPU, of course. The software list is ibm5150 but that has some DOS games too, just to be confusing (but usage == 'PC booter' where it is a PC booter).
	"Super A'Can": UnsupportedSystemInfo('supracan', ['supracan'], ["MAME (Super A'Can)"], {MediaType.Cartridge: ['bin']}),
	'V.Smile Baby': SystemInfo('vsmileb', ['vsmileb_cart'], ['MAME (V.Smile Baby)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	'CreatiVision': UnsupportedSystemInfo('crvision', ['crvision'], ['MAME (CreatiVision)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}),
	'Mattel Aquarius': UnsupportedSystemInfo('aquarius', ['aquarius'], ['MAME (Mattel Aquarius)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav', 'caq']}),
	'Microtan 65': UnsupportedSystemInfo('mt65', ['mt65_snap'], ['MAME (Microtan 65)'], {MediaType.Tape: ['wav'], MediaType.Executable: ['hex'], MediaType.Snapshot: ['dmp', 'm65']}), #MAME driver was "microtan" prior to 0.212
	'Videoton TVC': UnsupportedSystemInfo('tvc64', ['tvc_cart', 'tvc_cass', 'tvc_flop'], ['MAME (Videoton TVC)'], {MediaType.Cartridge: ['bin', 'rom', 'crt'], MediaType.Tape: ['wav', 'cas']}),
	'KC-85': UnsupportedSystemInfo('kc85_5', ['kc_cart', 'kc_cass', 'kc_flop'], ['MAME (KC-85)'], {MediaType.Executable: ['kcc'], MediaType.Tape: ['wav', 'kcb', 'tap', '853', '854', '855', 'tp2', 'kcm', 'sss'], MediaType.Cartridge: ['bin']}),
	#kcc might also be a tape format?? ehhhh???
	'Amstrad PCW': UnsupportedSystemInfo('pcw10', ['pcw'], ['MAME (Amstrad PCW)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['com']}),
	'PC-6001': UnsupportedSystemInfo('pc6001', [], ['MAME (PC-6001)'], {MediaType.Tape: ['cas', 'p6'], MediaType.Cartridge: ['bin', 'rom']}),
	'Sharp MZ-2000': UnsupportedSystemInfo('mz2000', ['mz2000_cass', 'mz2000_flop'], ['MAME (Sharp MZ-2000)'], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt'], MediaType.Floppy: ['2d'] + mame_floppy_formats}),

	#No emulators that are cool enough on Linux (any available are too preliminary to work). Yet. Maybe? That I know of. They're here for completeness. Or no emulators at all.
	#They are also here to remind me to check up on them every now and again to make sure they indeed don't work or if I was just being stupid all along

	#Stuff with skeleton/borked MAME drivers:
	'3DO': UnsupportedSystemInfo('3do', [], ['MAME (3DO)'], {MediaType.OpticalDisc: cdrom_formats}),
	#4DO doesn't like Wine and has no native Linux version (just libretro and meh), Phoenix Emu has no command line support; so both are unusable for our purposes. MAME driver just kinda hangs at the 3DO logo at the moment
	'Advanced Pico Beena': UnsupportedSystemInfo('beena', ['sega_beena_cart'], ['MAME (Advanced Pico Beena)'], {MediaType.Cartridge: ['bin']}),
	'Apple Lisa': UnsupportedSystemInfo('lisa', ['lisa'], [], {MediaType.Floppy: mame_floppy_formats + ['dc', 'dc42']}),
	#Preliminary MAME driver doesn't seem to boot anything; LisaEm doesn't seem to work with newer OSes and hasn't been updated since
	'Atari Portfolio': UnsupportedSystemInfo('pofo', ['pofo'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	'Atari ST': UnsupportedSystemInfo('st', ['st_flop', 'st_cart'], [], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats + ['st', 'stx', 'msa']}),
	#MAME seems to boot some things but not respond to input (the driver is marked solidly MACHINE_NOT_WORKING), need to find a standalone emulator that cooperates with fullscreen mode and such
	'Bandai RX-78': UnsupportedSystemInfo('rx78', ['rx78'], ['MAME (Bandai RX-78)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}),
	#Does boot things from software list, but not from fullpath, and doesn't really work too well
	'C2 Color': UnsupportedSystemInfo('c2color', ['c2color_cart'], ['MAME (C2 Color)'], {MediaType.Cartridge: ['bin']}),
	'Casio Loopy': UnsupportedSystemInfo('casloopy', ['casloopy'], ['MAME (Casio Loopy)'], {MediaType.Cartridge: ['bin']}),
	#MAME driver just shows corrupted graphics (and has no controls defined), basically just a skeleton even if it looks like it isn't
	'ClickStart': UnsupportedSystemInfo('clikstrt', ['clickstart_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Copera': UnsupportedSystemInfo('copera', ['copera'], ['MAME (Copera)'], {MediaType.Cartridge: ['bin', 'md']}),
	#Kega Fusion emulates the Pico well enough to show the message telling you the Copera software won't work on a Pico, at least
	'Gizmondo': UnsupportedSystemInfo('gizmondo', [], [], {}), #Uses folders seemingly, so that may be weird with the file types
	'GP32': UnsupportedSystemInfo('gp32', ['gp32'], ['MAME (GP32)'], {MediaType.Cartridge: ['smc'], MediaType.Executable: ['gxb', 'sxf', 'bin', 'gxf', 'fxe']}),
	#Runs too slow to verify if anything else works, but all documentation points to not
	'Jaguar CD': UnsupportedSystemInfo('jaguarcd', [], ['MAME (Jaguar CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	#Unlike the lack of CD, this does not work at all on anything, doesn't even have a software list yet
	'Koei PasoGo': UnsupportedSystemInfo('pasogo', ['pasogo'], ['MAME (Koei PasoGo)'], {MediaType.Cartridge: ['bin']}),
	#No sound in MAME yet, and apparently the rest doesn't work either (I'll take their word for it)
	'Konami Picno': UnsupportedSystemInfo('picno', ['picno'], ['MAME (Konami Picno)'], {MediaType.Cartridge: ['bin']}),
	'LeapPad': UnsupportedSystemInfo('leappad', ['leapfrog_leappad_cart'], ['MAME (LeapPad)'], {MediaType.Cartridge: ['bin']}),
	'Leapster': UnsupportedSystemInfo('leapster', ['leapster'], ['MAME (Leapster)'], {MediaType.Cartridge: ['bin']}),
	'Mattel HyperScan': UnsupportedSystemInfo('hs', ['hyperscan'], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Microvision': UnsupportedSystemInfo('microvsn', ['microvision'], ['MAME (Microvision)'], {MediaType.Cartridge: ['bin']}),
	#Cartridges boot, but seem to do nothing...
	'Monon Color': UnsupportedSystemInfo('mononcol', ['monon_color'], ['MAME (Monon Color)'], {MediaType.Cartridge: ['bin']}),
	#Only a skeleton MAME driver with no sound or video or inputs
	'My First LeapPad': UnsupportedSystemInfo('mfleappad', ['leapfrog_mfleappad_cart'], ['MAME (My First LeapPad)'], {MediaType.Cartridge: ['bin']}),
	'Panasonic JR-200': UnsupportedSystemInfo('jr200', [], []),
	'Pippin': UnsupportedSystemInfo('pippin', ['pippin', 'pippin_flop'], ['MAME (Pippin)'], {MediaType.OpticalDisc: cdrom_formats}),
	#Games don't just boot in a PPC Mac, unfortunately. No PPC Mac emulator has branched off into specific Pippin emulation yet
	'Pocket Challenge W': UnsupportedSystemInfo('pockchal', ['pockchalw'], ['MAME (Pocket Challenge W)'], {MediaType.Cartridge: ['bin']}),
	'Robotron Z1013': UnsupportedSystemInfo('z1013', [], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['z80']}),
	'Sawatte Pico': UnsupportedSystemInfo('sawatte', ['sawatte'], [], {}),
	#Similar to the Sega Pico but with different software (may or may not also use Megadrive ROM header?), but is completely unemulated. Not sure if dump format is identical
	'Sharp MZ-800': UnsupportedSystemInfo('mz800', ['mz800'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sinclair QL': UnsupportedSystemInfo('ql', ['ql_cart', 'ql_cass', 'ql_flop'], [], {MediaType.Tape: ['mdv'], MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats}),
	'Tomy Prin-C': UnsupportedSystemInfo('princ', ['princ'], ['MAME (Tomy Prin-C)'], {MediaType.Cartridge: ['bin']}), #MAME has skeleton driver that displays a green background and then doesn't go anywhere
	'V.Reader': UnsupportedSystemInfo('vreader', ['vtech_storio_cart'], ['MAME (V.Reader)'], {MediaType.Cartridge: ['bin']}), #Skeleton driver, apparently also known as Storio, or something like that
	'V.Smile Motion': UnsupportedSystemInfo('vsmilem', ['vsmilem_cart'], ['MAME (V.Smile Motion)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	#Games boot, but the actual motion part is not implemented, so you can't do anything (you can also boot these in normal vsmile it seems, but that also won't respond to input; I forgot if the two systems were supposed to be cross-compatible in real life?)
	'V.Smile Pro': UnsupportedSystemInfo('vsmilpro', ['vsmile_cd'], ['MAME (V.Smile Pro)'], {MediaType.OpticalDisc: cdrom_formats}),
	'VideoBrain': UnsupportedSystemInfo('vidbrain', ['vidbrain'], ['MAME (VideoBrain)'], {MediaType.Cartridge: ['bin']}),
	#MAME has some hella glitchy graphics and I'm not gonna call it a playable experience at this point (also it does say not working)
	'Video Challenger': UnsupportedSystemInfo('vidchal', [], [], {}),
	#From hh_cop400.cpp comments: Needs screen, gun cursor, VHS player device, and software list for tapes; at the moment displays a score counter and has one button input (supposed to be the gun) which makes a "pew" sound
	#.cas is also quickload? I donut understand
	'Xbox': UnsupportedSystemInfo('xbox', [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xbe']}),
	#Cxbx-Reloaded will only run on Windows; XQEMU isn't ready yet; not even gonna look at the MAME driver at this point in time

	#Too cool for MAME:
	'3DO M2': UnsupportedSystemInfo(None, ['3do_m2'], [], {MediaType.OpticalDisc: cdrom_formats}),
	#Was never actually released, but prototypes exist
	'Arduboy': UnsupportedSystemInfo(None, [], [], {MediaType.Digital: ['arduboy'], MediaType.Executable: ['hex']}),
	'N-Gage': UnsupportedSystemInfo(None, [], [], {}), #File types are.. folders I think. That could get weird. Anyway, all emulators at this stage seem to be super-preliminary
	'Nuon': UnsupportedSystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso']}),
	#There once was an emulator out there somewhere… for Windows
	'Wii U': UnsupportedSystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso', 'wud'], MediaType.Executable: ['rpx', 'elf']}),
	#Decaf seems to not work on Linux at the moment
	'Xbox 360': UnsupportedSystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xex']}),
	#Xenia requires Windows 8 + Vulkan, somehow I don't think it'd ever run under Wine either

	#Too cool for anyone at all so we can't get much info there and there is not really any point in me doing this other than either smartarsery or boredom:
	'Action Max': UnsupportedSystemInfo(None, [], [], {}),
	#No emulators, no dumps (probably nobody has decided the best way to preserve VHS games), no nothing
	'Arcadia Skeet Shoot': UnsupportedSystemInfo(None, [], [], {}), #VHS?
	'Bandai Playdia': UnsupportedSystemInfo(None, [], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Buzztime Home Trivia System':  UnsupportedSystemInfo(None, [], [], {}),
	'Coleco Telstar Arcade': UnsupportedSystemInfo(None, [], [], {}),
	'Design Master Senshi Mangajukuu': UnsupportedSystemInfo(None, [], [], {}),
	'Gakken TV Boy': UnsupportedSystemInfo(None, [], [], {}),
	#No MAME driver or anything, although it's mentioned on an old MESS 'to be dumped' page; apparently CPU is inside the carts
	'Tapwave Zodiac': UnsupportedSystemInfo(None, [], [], {}),
	#File type is like, kinda .prc but kinda not (the device runs spicy PalmOS, would it be considered part of that if any of that was emulated?)
	'Terebikko': UnsupportedSystemInfo(None, [], [], {}), #VHS
	'View-Master Interactive Vision': UnsupportedSystemInfo(None, [], [], {}), #VHS
	'ZAPit Game Wave': UnsupportedSystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso']}),
	#An SDK with emulator exists according to some company's website but yeah nah

	#Stuff that at the moment is only useful in mame_software.py, but it is here for reference or if some other emulator shows up
	'Commodore 65': UnsupportedSystemInfo('c65', ['c65_flop'], [], {MediaType.Floppy: commodore_disk_formats}),
	#This was actually never released, but there's software for it anyway. However, this is only supported by MAME, and it seems it only supports loading by software lists (there are no media slots), which won't work for our purposes at this point in time
	'Neo Geo AES': UnsupportedSystemInfo('aes', ['neogoeo'], [], {MediaType.Cartridge: ['bin']}),
	#Theoretically this works, but fullpath loading only works as a single .bin file which nothing ever is dumped as. This would only ever be useful with software list support. As for separate Neo Geo emulators... well, they all only seem interested in MVS and CD
	
	#Things that have usability issues that make things unsuitable for launchering purposes at this point in time, but otherwise might well work
	'64DD': UnsupportedSystemInfo('n64dd', ['n64dd'], [], {MediaType.Floppy: ['ndd', 'ddd']}),
	#Mupen64Plus would work, but right now it has issues with usability that it says right in the readme (so it's not just me picking on them, they say it themselves). Basically you have to have a cart inserted which has the same properties as the 64DD software you want to emulate, and that wouldn't work for our launchering purposes. MAME doesn't seem to work with .ndd format dumps
	'Acorn Archimedes': UnsupportedSystemInfo('aa310', ['archimedes'], [], {MediaType.Floppy: mame_floppy_formats + ['adf']}),
	#MAME driver is marked not working anyway, but also there's not really a way to get this to autoboot, so you have to click the icon on the thing and I don't wanna
	'Android': UnsupportedSystemInfo(None, [], [], {MediaType.Digital: ['apk']}),
	#Probably no emulators that will work nicely for us at this point (the emus that do exist tend to be virtual machines and/or closed source Windows only)
	'Apple I': UnsupportedSystemInfo('apple1', ['apple1'], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['snp']}),
	#Loading tapes would require parsing software list usage to figure out where to put load addresses and things to make an autoboot script, because otherwise it's just way too messy to warrant being in a frontend. Snapshots supposedly exist, but I haven't seen any evidence they actually do, so... whoops
	'Camputers Lynx': UnsupportedSystemInfo('lynx128k', ['camplynx_cass', 'camplynx_flop'], [], {MediaType.Floppy: mame_floppy_formats + ['ldf'], MediaType.Tape: ['wav', 'tap']}),
	#Convinced that whoever invented this system and the way it loads programs personally hates me, even though I wasn't born when it was made and so that's not really possible
	'C64DTV': UnsupportedSystemInfo('c64dtv', [], [], {MediaType.Floppy: commodore_disk_formats, MediaType.Executable: ['prg']}),
	#Commodore 64 plug and play UnsupportedSystem that has its own unique software, apparently. MAME driver is skeleton, and VICE doesn't seem to boot anything (it is noted as being WIP/experimental)
	'Cybiko': UnsupportedSystemInfo('cybikov1', [], [], {MediaType.Digital: ['app']}),
	#Quickload slot doesn't seem to actually quickload anything, and seems to require setup each time. V2 and Extreme have same problems
	'Cybiko Xtreme': UnsupportedSystemInfo('cybikoxt', [], [], {MediaType.Digital: ['app']}),
	'Dreamcast VMU': UnsupportedSystemInfo('svmu', ['svmu'], [], {MediaType.Executable: ['bin'], MediaType.Digital: ['vms']}),
	#Makes you set time and date each time; also supposed to have sound apparently but I don't hear any
	'e-Reader': UnsupportedSystemInfo('gba', ['gba_ereader'], [], {MediaType.Barcode: ['bin', 'raw', 'bmp']}),
	#VBA-M works (nothing else emulates e-Reader that I know of), but you have to swipe the card manually, which doesn't really work for a nice launcher thing... and there's not really a way around that at this point in time.
	'Electronika BK': UnsupportedSystemInfo('bk0011m', ['bk0010'], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: mame_floppy_formats, MediaType.HardDisk: ['hdi'], MediaType.Executable: ['bin']}),
	#Preliminary driver and only supports .wav tapes as media
	'Interact': UnsupportedSystemInfo('interact', ['interact'], [], {MediaType.Tape: ['wav', 'k7', 'cin', 'for']}),
	#Eww, tapes (otherwise works I guess)
	'Luxor ABC80': UnsupportedSystemInfo('abc80', ['abc80_cass', 'abc80_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['bac']}),
	#Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	'Oric': UnsupportedSystemInfo('orica', [], [], {MediaType.Tape: ['wav', 'tap']}),
	#MAME has oric1 as well... either way, they don't seem to actually load anything I've tried. There's no software lists, so nothing that says anything is supposed to work
	#Oricutron loads things automatically and other nice things, but has issues with fullscreen
	'PMD 85': UnsupportedSystemInfo('pmd853', ['pmd85_cass'], [], {MediaType.Tape: ['wav', 'pmd', 'tap', 'ptp']}),
	#This has quite a few variants and apparently works, pmd85.cpp has todos/notes. Notably, floppy interface and speaker apparently not there yet. Anyway, boo tapes
	'PocketStation': UnsupportedSystemInfo('pockstat', [], [], {MediaType.Digital: ['gme']}),
	#Makes you set time and date each time
	'PS3': UnsupportedSystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Digital: ['pkg'], MediaType.Executable: ['self', 'elf', 'bin']}),
	'Sharp MZ-700': UnsupportedSystemInfo('mz700', ['mz700'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'ZX81': UnsupportedSystemInfo('zx81', ['zx80_cass', 'zx81_cass'], [], {MediaType.Tape: ['wav', 'cas', 'p', '81', 'tzx']}),
	#Not even gonna try testing any more software without autobooting it, though I'm not sure it does work from the one I did. Anyway, gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing, and even then it's like.... meh....
	'Radio 86-RK': UnsupportedSystemInfo('radio86', ['radio86_cart', 'radio86_cass'], [], {MediaType.Tape: ['wav', 'rk', 'rkr', 'gam', 'g16', 'pki']}),
	#These and the other USSR systems below are all sorta the same (but might not be software-compatible?) anyway they only have tapes for software other than system stuff, and are mostly only emulated by MAME which has the ol' tape problems of having to type in weird commands, or that online thing which is online and not suitable for a launcher
	'Mikrosha': UnsupportedSystemInfo('mikrosha', ['mikrosha_cart', 'mikrosha_cass'], [], {MediaType.Tape: ['wav', 'rkm'], MediaType.Cartridge: ['bin', 'rom']}),
	'Apogey BK-01': UnsupportedSystemInfo('apogee', ['apogee'], [], {MediaType.Tape: ['wav', 'rka']}),
	'Partner 01.01': UnsupportedSystemInfo('partner', ['partner_cass', 'partner_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi']}),
	'Orion-128': UnsupportedSystemInfo('orion128', ['orion_cart', 'orion_cass', 'orion_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi'], MediaType.Cartridge: ['bin']}),
	'PC-98': UnsupportedSystemInfo('pc9801f', ['pc98', 'pc98_cd'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}),

	#Things that have other weird usability issues
	'Sega Pico': UnsupportedSystemInfo('pico', ['pico'], ['Kega Fusion', 'MAME (Sega Pico)'], {MediaType.Cartridge: ['bin', 'md']}),
	#Neither emulator displays the actual book, which would be needed for anything to make sense… Kega Fusion doesn't even have decrement/increment page controls

	#TODO: Me being lazy, need to check if these actually work or not:
	'Acorn Atom': UnsupportedSystemInfo('atom', ['atom_cass', 'atom_flop', 'atom_rom'], [], {MediaType.Floppy: ['40t', 'dsk'], MediaType.Tape: ['wav', 'tap', 'csw', 'uef'], MediaType.Executable: ['atm'], MediaType.Cartridge: ['bin', 'rom']}),
	'Amstrad CPC': UnsupportedSystemInfo('cpc464', ['cpc_cass', 'cpc_flop'], [], {MediaType.Snapshot: ['sna'], MediaType.Tape: ['wav', 'cdt'], MediaType.Floppy: mame_floppy_formats}),
	#The not-plus one (probably will need to switch to cpc664/cpc6128 for flopppy stuff)
	#CPC+: Use cpc6128p, this uses the gx4000 software list (as well as original cpc_cass and cpc_flop) so I should probably consider these to be the same platform
	'Amstrad PCW16': UnsupportedSystemInfo('pcw16', ['pcw16'], [], {MediaType.Floppy: mame_floppy_formats}),
	#Marked as MACHINE_NOT_WORKING and MAME pcw.cpp mentions needing an OS rescue disk, probably doesn't work conveniently or at all
	'APF Imagination Machine': UnsupportedSystemInfo('apfimag', ['apfimag_cass', 'apfm1000'], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas', 'cpf', 'apt'], MediaType.Floppy: mame_floppy_formats}),
	#Considered separate from APF-M1000 (same predicament as Coleco Adam)
	'BBC Master': UnsupportedSystemInfo('bbcm', ['bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'ima', 'ufi', '360'] + mame_floppy_formats, MediaType.Cartridge: ['rom', 'bin']}),
	'Exidy Sorcerer': UnsupportedSystemInfo('sorcerer', ['sorcerer_cart', 'sorcerer_cass', 'sorcerer_flop'],
		{MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav', 'tape'], MediaType.Snapshot: ['snp']}),
	#Would need automated tape loading to do anything interesting (carts and floppies are just BASIC/OS stuff, also what even is the file type for floppies?) hnmn
	'Goldstar FC-100': UnsupportedSystemInfo('fc100', [], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas']}),
	#No software list, some kind of PC-6001 clone or something
	'Memotech MTX': UnsupportedSystemInfo('mtx512', ['mtx_cart', 'mtx_cass', 'mtx_rom'], [], {MediaType.Snapshot: ['mtx'], MediaType.Executable: ['run'], MediaType.Tape: ['wav'], MediaType.Cartridge: ['bin', 'rom']}),
	'TRS-80': UnsupportedSystemInfo('trs80m3', [], [], {MediaType.Executable: ['cmd'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats}),
	'Vector-06C': UnsupportedSystemInfo('vector06', ['vector06_cart', 'vector06_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin', 'emr']}),
	#MAME driver is marked as working but clones are not; needs to hold F2 then press F11 then F12 to boot from cartridge so that may be wacky; and I can't get that working, not sure if floppies/tapes do work
	'Tandy MC-10': UnsupportedSystemInfo('mc10', ['mc10'], [], {MediaType.Tape: ['wav', 'cas']}),
	#Hmm... tapes...
	'Alice 32': UnsupportedSystemInfo('alice32', ['alice32', 'alice90'], [], {MediaType.Tape: ['wav', 'cas', 'c10', 'k7']}),
	#Tapes again... not having high hopes that this will be a smooth experience. Alice 90 is an upgraded Alice 32, Alice without a number is an unrelated machine by the same manufacturer which is a clone of the MC-10
	'Central Data 2650': UnsupportedSystemInfo('cd2650', [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'Instructor 50': UnsupportedSystemInfo('instruct', [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'PipBug': UnsupportedSystemInfo('pipbug', [], [], {MediaType.Executable: ['pgm']}),
	'V.Tech Socrates': UnsupportedSystemInfo('socrates', ['socrates'], [], {MediaType.Cartridge: ['bin']}),
	#Emulation status = preliminary... hh (but sound is imperfect, and not completely borked)
	'TI-99': UnsupportedSystemInfo('ti99_4', ['ti99_cart'], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	#Main kerfluffle seems to be .rpk file format needed for -cart loading, but everything else is in .c and .g and who knows what else; -ioport peb -ioport:peb:slot2 32kmem -ioport:peb:slot3 speech might be needed? What is the difference between TI-99/2 TI99/4 TI99/8


	#TODO: Me being lazy, I know if these work or not but they require effort:
	'Acorn Electron': UnsupportedSystemInfo('electron', ['electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl']}),
	#Seems to require the same Shift+Break to boot as BBC Micro, so... dang
	'BBC Micro': UnsupportedSystemInfo('bbcb', ['bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig', 'bbc_flop_65c102', 'bbc_flop_6502', 'bbc_flop_32016', 'bbc_flop_68000', 'bbc_flop_80186', 'bbc_flop_arm', 'bbc_flop_torch', 'bbc_flop_z80'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'dsk', 'ima', 'ufi', '360'], MediaType.Cartridge: ['rom', 'bin']}),
	#The key combination to boot a floppy is Shift+Break which is rather awkward to press especially every time you just want to use some software, so I'm not going anywhere without an autoboot script
	#Otherwise, it does seem to boot floppies..
	'Cambridge Z88': UnsupportedSystemInfo('z88', ['z88_cart'], [], {MediaType.Cartridge: ['epr', 'bin']}),
	#Marked as not working due to missing expansion interface and serial port and other things, not sure how important that would be... anyway, I'd need to do an autoboot thing to press the key to start the thing, because otherwise it's annoying to navigate every time, and then... hmm, I guess I dunno what actually is a function of things not working yet
	'Galaksija': UnsupportedSystemInfo('galaxyp', ['galaxy'], [], {MediaType.Snapshot: ['gal'], MediaType.Tape: ['wav', 'gtp']}),
	#This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why. Anyway, we'd go with those and make an autoboot script (maybe just -autoboot_command '\n' would work with suitable delay). galaxy is regular system, galaxyp is an upgraded one which appears to be completely backwards compatible
	'RCA Studio 2': UnsupportedSystemInfo('studio2', ['studio2'], [], {MediaType.Cartridge: ['st2', 'bin', 'rom']}),
	#This console sucks and I hate it, anyway; I'd need to make multiple autoboot scripts that press F3 and then combinations of buttons depending on software list > usage. God fuck I hate this console so much. PAL games (and some homebrew stuff) need mpt02
	'Thomson MO6': UnsupportedSystemInfo('mo6', ['mo6_cass', 'mo6_flop'], [], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}),
	#MO6 is an upgraded model, Prodest PC 128 is an Italian MO6
	#Floppies work (and cassettes and carts have same problem as MO5), but this time we need to press the F1 key and I don't waaaanna do that myself
	'Thomson TO': UnsupportedSystemInfo('to8', ['to7_cart', 'to7_cass', 'to7_qd', 'to8_cass', 'to8_qd', 'to770a_cart', 'to770_cart'], [], {MediaType.Tape: ['wav', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m7', 'bin', 'rom']}),
	#Fuck I hate this. Carts need to press 1 on TO7 or press the button with the lightpen on TO8/9 and also they suck, floppies need BASIC cart inserted on TO7 (and then the same method to boot that cart) or press B on TO8/9, tapes are a shitload of fuck right now (same broken as MO5/MO6), not all of this seems to be cross compatible so might need to separate systems or work out what's going on there

	#Other todos, often just me not knowing which something actually is or being too lazy to organize it even into the "too lazy to look into right now" list:
	#Which of TI calculators are software compatible with which (and hence which ones would be considered individual systems)?
		#TI-73, 81, 82, 83x, 84x, 85, 86 are Z80; 89, 92x are M68K; folders here are 83, 84+, 86, 89 but I might need to reorganize them...
	#Bandai Super Note Club: Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
	#Dragon 64 part of CoCo or nah?
	#Jupiter Ace (ZX Spectrum clone but has different compatibility?)
	#CBM-II (VIC-II and CRTC models)
	#PalmOS: Not sure if there would be something which can just run .prc files or whatsitcalled
	#Amstrad PC20/Sinclair PC200: Is this just IBM PC compatible stuff? Have one demoscene prod which claims to be for it specifically
	#Epoch (not Super) Cassette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
	#Pioneer LaserActive probably just counts as Mega CD and PC Engine CD except with Laserdisc instead of CD, but I'll worry about that when emulation for it becomes a thing
})

class ComputerSystem():
	#Need a better name for this shit
	def __init__(self, specific_configs):
		self.specific_configs = specific_configs if specific_configs else {}

computer_systems = {
	'Mac': ComputerSystem({
		'shared_folder': SpecificConfigValue(ConfigValueType.FolderPath, None, 'Path to shared folder on host that guest can see. This is mandatory for all this Mac stuff to work'),
		'default_width': SpecificConfigValue(ConfigValueType.String, 1920, 'Emulated screen width to run at if a game doesn\'t need a specific screen resolution'), 'default_height': SpecificConfigValue(ConfigValueType.String, 1080, 'Emulated screen height to run at if a game doesn\'t need a specific screen resolution')
	}),
	'DOS': ComputerSystem({
		'slow_cpu_cycles': SpecificConfigValue(ConfigValueType.String, 477, 'CPU cycles to run at for games only designed to run at 4.77 MHz clock speed'),
		'dosbox_configs_path': SpecificConfigValue(ConfigValueType.FolderPath, os.path.join(data_dir, 'dosbox_configs'), 'Folder to store DOSBox per-application configuration files'),
		'dosbox_x_configs_path': SpecificConfigValue(ConfigValueType.FolderPath, os.path.join(data_dir, 'dosbox_configs'), 'Folder to store DOSBox-X per-application configuration files'),
	})
}

#One day add these as well (or should I? Maybe I should just leave it to emulator_info):
#Arcade: I guess it's not an array, it's just MAME (for now... but this will be complicated, I think)
#Virtual environment-but-not-quite-type-system-things: J2ME, Flash (but once those have nicer emulators, until then never mind, or maybe I could pretend they're emulated systems)
#This allows us to organize supported emulators easily and such
