from common_types import ConfigValueType, MediaType

from info.format_info import (atari_2600_cartridge_extensions, cdrom_formats,
                              commodore_cart_formats, commodore_disk_formats,
                              generic_cart_extensions, generic_tape_extensions,
                              mame_floppy_formats)


class SystemConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type, default_value, description):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class SystemInfo():
	def __init__(self, mame_drivers, mame_software_lists, emulators, file_types=None, options=None, is_virtual=False, dat_names=None, dat_uses_serial=False, databases_are_byteswapped=False, autodetect_tv_type=False):
		self.mame_drivers = mame_drivers #Parent drivers that represent this system
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators
		self.file_types = file_types if file_types else {}
		self.options = options if options else {}
		self.is_virtual = is_virtual #Maybe needs better name
		self.dat_names = dat_names if dat_names else [] #For libretro-database
		self.dat_uses_serial = dat_uses_serial
		self.databases_are_byteswapped = databases_are_byteswapped #Arguably I should create two separate parameters for both MAME SL and libretro-database, but so far this is only needed for N64 which has both swapped
		self.autodetect_tv_type = autodetect_tv_type

	def is_valid_file_type(self, extension):
		return any(extension in extensions for extensions in self.file_types.values() if isinstance(extension, str))

	def get_media_type(self, rom):
		for media_type, extensions in self.file_types.items():
			if rom.extension in extensions:
				return media_type
		return None

msxtr_drivers = ['fsa1gt', 'fsa1st'] #Neither of these are working

working_msx2plus_drivers = ['hbf1xv', 'fsa1fx', 'fsa1wxa', 'fsa1wsx', 'hbf1xdj', 'phc70fd2', 'phc35j', 'hbf9sp']
broken_msx2plus_drivers = ['expert3i', 'expert3t', 'expertac', 'expertdx']
msx2plus_drivers = working_msx2plus_drivers + broken_msx2plus_drivers

arabic_msx2_drivers = ['ax350', 'ax370']
korean_msx2_drivers = ['cpc300', 'cpc300e', 'cpc330k', 'cpc400', 'cpc400s', 'cpc61']
japanese_msx2_drivers = ['kmc5000', 'mlg10', 'fs5500f2', 'fs4500', 'fs4700', 'fs5000', 'fs4600', 'fsa1a', 'fsa1mk2', 'fsa1f', 'fsa1fm', 'nms8250j', 'hbf500', 'hbf900a', 'hx33', 'yis604', 'phc23', 'phc55fd2', 'hbf1xd', 'hbf1xdm2']
other_msx2_drivers = ['canonv25', 'canonv30', 'fpc900', 'expert20', 'mlg1', 'mlg3', 'mlg30', 'nms8220a', 'vg8230', 'vg8235', 'vg8240', 'nms8245', 'nms8255', 'nms8280', 'mpc25fd', 'hx34i', 'fstm1', 'hbf5', 'hbf9p', 'hbf500p', 'hbf700p', 'hbg900ap', 'hbg900p', 'tpc310', 'tpp311', 'tps312', 'hx23i', 'cx7m128']
working_msx2_drivers = other_msx2_drivers + arabic_msx2_drivers + korean_msx2_drivers + japanese_msx2_drivers
broken_msx2_drivers = ['cpg120', 'y503iiir', 'y805256', 'mbh70', 'victhc95', 'hotbit20', 'mpc27', 'nms8260', 'mpc2300', 'mpc2500f', 'phc77', 'hbf1', 'hbf12']
msx2_drivers = working_msx2_drivers + broken_msx2_drivers

arabic_msx1_drivers = ['ax150', 'ax170', 'svi738ar']
japanese_msx1_drivers = ['fmx', 'mbh2', 'mbh25', 'mbh50', 'mlf110', 'mlf120', 'cf1200', 'cf2000', 'cf2700', 'cf3000', 'cf3300', 'fs1300', 'fs4000', 'mpc64', 'hb701fd', 'hc7', 'cx5f']
korean_msx1_drivers = ['cpc88', 'dpc200', 'gsfc80u', 'cpc51', 'gfc1080', 'gfc1080a', 'mx64']
other_msx1_drivers = ['svi728', 'svi738', 'canonv8', 'canonv20', 'mx10', 'pv7', 'pv16', 'dpc200e', 'dgnmsx', 'fdpc200', 'fpc500', 'fspc800', 'bruc100', 'gsfc200', 'jvchc7gb', 'mlf48', 'mlf80', 'mlfx1', 'phc2', 'phc28', 'cf2700g', 'perfect1', 'nms801', 'vg8010', 'vg802020', 'piopx7', 'spc800', 'mpc100', 'mpc200', 'phc28l', 'phc28s', 'mpc10', 'hb10p', 'hb101p', 'hb20p', 'hb201p', 'hb501p', 'hb55p', 'hb75p', 'hx10', 'hx20', 'cx5m128', 'yis303', 'yis503', 'yc64', 'expert13', 'expertdp', 'expertpl', 'hotbi13p'] #Anything that isn't one of those other three (which are apparently specifically different or needed in some cases)
working_msx1_drivers = other_msx1_drivers + arabic_msx1_drivers + japanese_msx1_drivers + korean_msx1_drivers
broken_msx1_drivers = ['hx21', 'hx22']
msx1_drivers = working_msx1_drivers + broken_msx1_drivers

systems = {
	#Put all the "most normal people would be interested in" consoles up here, which is completely subjective and not even the same as my own personal view of notable, not to mention completely meaningless because it's a dict and the order shouldn't matter, and even if it did, ROMs are scanned in the order they're listed in systems.ini anyway. I guess it makes this a bit easier to read than having a huge wall of text though
	'3DS': SystemInfo(
		[], [], ['Citra'], {MediaType.Cartridge: ['3ds'], MediaType.Digital: ['cxi'], MediaType.Executable: ['3dsx']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB 3dstdb.xml file (https://www.gametdb.com/3dstdb.zip)'),
		'covers_path': SystemConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after 4-letter product code'),
		}, #There is a Nintendo - Nintendo 3DS.dat that could go in datnames but it is indexed by 4-letter serial so I'd have to do some trickery and then the info is already in GameTDB anyway
	),
	'Atari 2600': SystemInfo(
		['a2600'], ['a2600', 'a2600_cass'], ['Stella', 'Stella (libretro)', 'MAME (Atari 2600)'], {MediaType.Cartridge: ['a26'] + atari_2600_cartridge_extensions + generic_cart_extensions}, autodetect_tv_type=True
	),
	'ColecoVision': SystemInfo(
		['coleco', 'bit90', 'czz50'], ['coleco'], ['blueMSX (libretro)', 'MAME (ColecoVision)'], {MediaType.Cartridge: ['col'] + generic_cart_extensions}, dat_names=['Coleco - ColecoVision']
	),
	'Dreamcast': SystemInfo(
		['dcjp', 'dcdev'], ['dc'], ['Reicast', 'Flycast', 'MAME (Dreamcast)'], {MediaType.OpticalDisc: cdrom_formats}, dat_names=['Sega - Dreamcast'], dat_uses_serial=True
	),
	'DS': SystemInfo(
		['nds'], [], ['melonDS', 'Medusa'], {MediaType.Cartridge: ['nds', 'dsi', 'ids', 'srl']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB dstdb.xml file (https://www.gametdb.com/dstdb.zip)'),
		'covers_path': SystemConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after 4-letter product code'),
		},
		dat_names=['Nintendo - Nintendo DS']
	),
	'Game Boy': SystemInfo(
		['gameboy', 'gbcolor'], ['gameboy', 'gbcolor'], 
		['SameBoy (libretro)', 'Gearboy (libretro)', 'Gambatte', 'mGBA', 'mGBA (libretro)', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa', 'GBE+', 'bsnes', 'bsnes (libretro)', 'bsnes-hd beta (libretro)'], {MediaType.Cartridge: ['gb', 'gbc', 'gbx', 'sgb', 'cgb', 'dmg']},
		{
			'super_game_boy_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to Super Game Boy BIOS to use'),
			'set_gbc_as_different_platform': SystemConfigValue(ConfigValueType.Bool, False, 'Set the platform of GBC games to Game Boy Color instead of leaving them as Game Boy'),
		},
		dat_names=['Nintendo - Game Boy', 'Nintendo - Game Boy Color']
	),
	'GameCube': SystemInfo(
		['gcjp'], [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'ciso', 'rvz'], MediaType.Executable: ['dol', 'elf']}
		#dat_names could be Nintendo - GameCube but that doesn't give us any more info that isn't in GameTDB and also is indexed by 6-character code so I'd have to fiddle around I think
	),
	'Game Gear': SystemInfo(
		['gamegear'], ['gamegear'], ['Genesis Plus GX (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}, dat_names=['Sega - Game Gear']
	),
	'GBA': SystemInfo(
		['gba'], ['gba'],
		['mGBA', 'mGBA (libretro)', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gba', 'bin', 'srl'], MediaType.Executable: ['elf', 'mb']},
		dat_names=['Nintendo - Game Boy Advance']
	),
	'Intellivision': SystemInfo(
		['intv'], ['intv', 'intvecs'], ['MAME (Intellivision)', 'FreeIntv (libretro)'], {MediaType.Cartridge: ['bin', 'int', 'rom', 'itv']}, dat_names=['Mattel - Intellivision'], autodetect_tv_type=True
	),
	'Lynx': SystemInfo(
		['lynx'], ['lynx'],
		['Mednafen (Lynx)', 'MAME (Lynx)'], {MediaType.Cartridge: ['lnx', 'lyx'], MediaType.Executable: ['o']}, dat_names=['Atari - Lynx'] #This will need header removed
	),
	'Master System': SystemInfo(
		['sms'], ['sms'],
		['Genesis Plus GX (libretro)', 'BlastEm (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'Mednafen (Master System)', 'MAME (Master System)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}, dat_names=['Sega - Master System - Mark III'], autodetect_tv_type=True
	),
	'Mega Drive': SystemInfo(
		['genesis', 'gen_nomd'], ['megadriv'],
		['BlastEm (libretro)', 'Genesis Plus GX (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'Mednafen (Mega Drive)', 'MAME (Mega Drive)'], {MediaType.Cartridge: ['bin', 'gen', 'md', 'smd', 'sgd']}, dat_names=['Sega - Mega Drive - Genesis'], autodetect_tv_type=True
	),
	'N64': SystemInfo(
		['n64'], ['n64', 'ique'], ['Mupen64Plus', 'Mupen64Plus-Next (libretro)', 'MAME (N64)'], {MediaType.Cartridge: ['z64', 'v64', 'n64', 'bin']}, 
		{'prefer_controller_pak_over_rumble': SystemConfigValue(ConfigValueType.Bool, True, 'If a game can use both the Controller Pak and the Rumble Pak, use the Controller Pak')}, 
		dat_names=['Nintendo - Nintendo 64'], databases_are_byteswapped=True, autodetect_tv_type=True
	),
	'Neo Geo AES': SystemInfo(
		#For software list usage
		['aes'], ['neogoeo'], [], {MediaType.Cartridge: ['bin']}
	), 
	'Neo Geo Pocket': SystemInfo(
		['ngp'], ['ngp', 'ngpc'],
		['Beetle NeoPop (libretro)', 'Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'], {MediaType.Cartridge: ['ngp', 'npc', 'ngc', 'bin']},
		dat_names=['SNK - Neo Geo Pocket', 'SNK - Neo Geo Pocket Color']
	),
	'NES': SystemInfo(
		['nes', 'famicom', 'iq501', 'sb486'], ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], 
		['Mesen (libretro)', 'Mednafen (NES)', 'MAME (NES)', 'cxNES'], {MediaType.Cartridge: ['nes', 'unf', 'unif'], MediaType.Floppy: ['fds', 'qd']}, 
		{'set_fds_as_different_platform': SystemConfigValue(ConfigValueType.Bool, False, 'Set the platform of FDS games to FDS instead of leaving them as NES')},
		dat_names=['Nintendo - Nintendo Entertainment System', 'Nintendo - Family Computer Disk System'], autodetect_tv_type=True
	),
	'PC Engine': SystemInfo(
		['pce'], ['pce', 'sgx', 'tg16'], ['Beetle PCE (libretro)', 'Beetle PCE Fast (libretro)', 'Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)', 'MAME (PC Engine)'], {MediaType.Cartridge: ['pce', 'sgx', 'bin']},
		dat_names=['NEC - PC Engine - TurboGrafx 16', 'NEC - PC Engine SuperGrafx']
	),
	'PlayStation': SystemInfo(
		['psj'], ['psx'],
		['DuckStation', 'Beetle PSX HW (libretro)', 'Mednafen (PlayStation)', 'PCSX2'], {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: ['exe', 'psx']},
		dat_names=['Sony - PlayStation'], dat_uses_serial=True
	),
	'PS2': SystemInfo(
		['ps2'], [], ['PCSX2'], {MediaType.OpticalDisc: cdrom_formats + ['cso', 'bin'], MediaType.Executable: ['elf', 'irx']},
		dat_names=['Sony - PlayStation 2'], dat_uses_serial=True
	),
	'PS3': SystemInfo(
		#Tech tip: Add ~/.config/rpcs3/dev_hdd0/game to rom paths
		[], [], ['RPCS3'], {MediaType.OpticalDisc: ['iso'], MediaType.Digital: ['pkg'], MediaType.Executable: ['self', 'elf', 'bin']}, dat_names=['Sony - PlayStation 3'], dat_uses_serial=True, options={
			'covers_path': SystemConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after product code'),
			'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB ps3tdb.xml file (https://www.gametdb.com/ps3tdb.zip)'),
		}
	),
	'PSP': SystemInfo(
		[], [], ['PPSSPP'], {MediaType.OpticalDisc: cdrom_formats + ['cso'], MediaType.Executable: ['pbp']}, dat_names=['Sony - PlayStation Portable'], dat_uses_serial=True
	),
	'Saturn': SystemInfo(
		['saturn'], ['saturn', 'sat_cart', 'sat_vccart'], ['Beetle Saturn (libretro)', 'Mednafen (Saturn)', 'MAME (Saturn)'], {MediaType.OpticalDisc: cdrom_formats},
		dat_names=['Sega - Saturn'], dat_uses_serial=True
	),
	'SNES': SystemInfo(
		['snes'], ['snes', 'snes_bspack', 'snes_strom'],
		['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)', 'bsnes', 'bsnes (libretro)', 'bsnes-hd beta (libretro)'], {MediaType.Cartridge: ['sfc', 'swc', 'smc', 'bs', 'st', 'bin']}, 
		{
			'sufami_turbo_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to Sufami Turbo BIOS, required to run Sufami Turbo carts'),
			'bsx_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to BS-X BIOS, required to run Satellaview games'),
		},
		dat_names=['Nintendo - Super Nintendo Entertainment System', 'Nintendo - Satellaview', 'Nintendo - Sufami Turbo'], autodetect_tv_type=True
	),
	'Switch': SystemInfo(
		[], [], ['Yuzu'], {MediaType.Cartridge: ['xci'], MediaType.Digital: ['nsp', 'nca'], MediaType.Executable: ['nro', 'nso', 'elf']}
	),
	'Virtual Boy': SystemInfo(
		['vboy'], ['vboy'], ['Beetle VB (libretro)', 'Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'], {MediaType.Cartridge: ['vb', 'vboy', 'bin']}, dat_names=['Nintendo - Virtual Boy']
	),
	'Vita': SystemInfo(
		[], [], [], {MediaType.Digital: ['vpk']}
	),
	'Xbox': SystemInfo(
		['xbox'], [], ['Xemu'], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xbe']}
	),
	'Xbox 360': SystemInfo(
		[], [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xex']}
	),
	'Wii': SystemInfo([], [], ['Dolphin'], 
		{MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'wbfs', 'ciso', 'wia', 'rvz'], MediaType.Executable: ['dol', 'elf'], MediaType.Digital: ['wad']}, 
		{
			'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB wiitdb.xml file (https://www.gametdb.com/wiitdb.zip), note that GameCube will use this too!'),
			'common_key': SystemConfigValue(ConfigValueType.String, '', 'Wii common key used for decrypting Wii discs which some projects are brave enough to hardcode but I am not'),
			'covers_path': SystemConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after product code, used by GameCube too'),
		},
		dat_names=['Nintendo - Wii'], dat_uses_serial=True #Although WiiWare (Nintendo - Wii (Digital)) uses crc… hm, not important for now since there is not really any metadata
	),
	'Wii U': SystemInfo(
		#See roms_folders for how this mostly works
		[], [], ['Cemu'], {MediaType.OpticalDisc: ['iso', 'wud', 'wux'], MediaType.Executable: ['rpx', 'elf']},
		{
			'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB wiiutdb.xml file (https://www.gametdb.com/wiiutdb.zip)'),
			'covers_path': SystemConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after 4-letter product code (or sometimes 6 letters)'),
		}
	),
	'WonderSwan': SystemInfo(
		['wswan'], ['wswan', 'wscolor'], 
		['Beetle Cygne (libretro)', 'Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['ws', 'wsc', 'bin']}, dat_names=['Bandai - WonderSwan', 'Bandai - WonderSwan Color']
	),
	
	#Less notable stuff goes here
	'3DO': SystemInfo(['3do'], [], ['Opera (libretro)', 'MAME (3DO)'], {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	'Amiga CD32': SystemInfo(['cd32'], ['cd32'], ['PUAE (libretro)', 'FS-UAE', 'MAME (Amiga CD32)'], {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	'Atari 5200': SystemInfo(
		#Does it actually have games on tapes or is MAME listing that as a type just a side effect of it being a spicy Atari 8-bit computer?
		['a5200'], ['a5200'],
		['MAME (Atari 5200)'], {MediaType.Cartridge: ['a52', 'car'] + generic_cart_extensions, MediaType.Tape: generic_tape_extensions}, dat_names=['Atari - 5200']
	), 
	'Atari 7800': SystemInfo(
		['a7800'], ['a7800'], ['ProSystem (libretro)', 'A7800', 'MAME (Atari 7800)'], {MediaType.Cartridge: ['a78'] + generic_cart_extensions}, dat_names=['Atari - 7800'], #Actually headered
		autodetect_tv_type=True
	),
	'Channel F': SystemInfo(
		['channelf', 'channlf2'], ['channelf'],
		['FreeChaF (libretro)', 'MAME (Channel F)'], {MediaType.Cartridge: ['chf'] + generic_cart_extensions}, dat_names=['Fairchild - Channel F'], autodetect_tv_type=True
	),
	'G7400': SystemInfo(['videopacp'], ['videopac'], ['O2EM (libretro)', 'MAME (G7400)'], {MediaType.Cartridge: generic_cart_extensions}, autodetect_tv_type=True, dat_names=['Philips - Videopac+']), #Uses same software list as Odyssey 2 currently, maybe should be considered part of that system?
	'Game.com': SystemInfo(['gamecom'], ['gamecom'], ['MAME (Game.com)'], {MediaType.Cartridge: ['tgc', 'bin']}, dat_names=['Tiger - Game.com']),
	'Jaguar': SystemInfo(
		['jaguar'], ['jaguar'], ['Virtual Jaguar (libretro)', 'MAME (Jaguar)'], 
		{MediaType.Cartridge: ['j64'] + generic_cart_extensions, MediaType.Executable: ['abs', 'cof', 'jag', 'prg']}, dat_names=['Atari - Jaguar'], #j64
		autodetect_tv_type=True
	),
	'Magnavox Odyssey²': SystemInfo(
		['videopac'], ['videopac'], ['O2EM (libretro)', 'MAME (Magnavox Odyssey²)', 'MAME (G7400)'], {MediaType.Cartridge: generic_cart_extensions}, dat_names=['Magnavox - Odyssey2'], autodetect_tv_type=True
	),
	'Microvision': SystemInfo(['microvsn'], ['microvision'], ['MAME (Microvision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Neo Geo CD': SystemInfo(['neocdz'], ['neocd'], ['NeoCD (libretro)', 'MAME (Neo Geo CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'PC-FX': SystemInfo(['pcfx'], ['pcfx'], ['Beetle PC-FX (libretro)', 'Mednafen (PC-FX)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Pokemon Mini': SystemInfo(
		['pokemini'], ['pokemini'], ['PokeMini (libretro)', 'PokeMini', 'MAME (Pokemon Mini)'], {MediaType.Cartridge: ['min', 'bin']}, dat_names=['Nintendo - Pokemon Mini']
	),
	'SG-1000': SystemInfo(
		['sg1000', 'sc3000'], ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'],
		['Genesis Plus GX (libretro)', 'blueMSX (libretro)', 'Kega Fusion', 'MAME (SG-1000)'], {MediaType.Cartridge: ['sg', 'bin', 'sc'], MediaType.Tape: ['wav', 'bit'], MediaType.Floppy: mame_floppy_formats + ['sf', 'sf7']},
		dat_names=['Sega - SG-1000']
	),
	'Vectrex': SystemInfo(['vectrex'], ['vectrex'], ['Vecx (libretro)', 'MAME (Vectrex)'], {MediaType.Cartridge: ['vec', 'gam', 'bin']}, dat_names=['GCE - Vectrex']),
	'Watara Supervision': SystemInfo(['svision'], ['svision'], ['Potator (libretro)', 'MAME (Watara Supervision)'], {MediaType.Cartridge: ['ws', 'sv', 'bin']}, dat_names=['Watara - Supervision']),
	
	#Consoles likely uncared about (I'm being subjective woohoo) just to make the list less of a chungus
	'3DO M2': SystemInfo([], ['3do_m2'], [], {MediaType.OpticalDisc: cdrom_formats}), #Was never actually released, but prototypes exist
	'APF-MP1000': SystemInfo(['apfm1000'], ['apfm1000'], ['MAME (APF-MP1000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Arcadia 2001': SystemInfo(
		['arcadia', 'intmpt03', 'orbituvi', 'ormatu', 'plldium'], ['arcadia'],
		['MAME (Arcadia 2001)'], {MediaType.Cartridge: generic_cart_extensions}, dat_names=['Emerson - Arcadia 2001'], autodetect_tv_type=True
		),
	'Astrocade': SystemInfo(['astrocde'], ['astrocde'], ['MAME (Astrocade)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Bandai Playdia': SystemInfo([], [], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Bandai Super Vision 8000': SystemInfo(['sv8000'], ['sv8000'], ['MAME (Bandai Super Vision 8000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'C2 Color': SystemInfo(['c2color'], ['c2color_cart'], ['MAME (C2 Color)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Casio PV-1000': SystemInfo(['pv1000'], ['pv1000'], ['MAME (Casio PV-1000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Champion 2711': SystemInfo(['unichamp'], ['unichamp'], ['MAME (Champion 2711)'], {MediaType.Cartridge: generic_cart_extensions}),
	'CreatiVision': SystemInfo(
		['crvision', 'lasr2001', 'manager'], ['crvision', 'laser2001_cart'],
		['MAME (CreatiVision)'], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: generic_tape_extensions}, dat_names=['VTech - CreatiVision']
	),
	'Dreamcast VMU': SystemInfo(['svmu'], ['svmu'], ['VeMUlator (libretro)', 'MAME (Dreamcast VMU)'], {MediaType.Executable: ['bin'], MediaType.Digital: ['vms', 'dci']}),
	'Entex Adventure Vision': SystemInfo(['advision'], ['advision'], ['MAME (Entex Adventure Vision)'], {MediaType.Cartridge: generic_cart_extensions}, dat_names=['Entex - Adventure Vision']),
	'Epoch Game Pocket Computer': SystemInfo(['gamepock'], ['gamepock'], ['MAME (Epoch Game Pocket Computer)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Gamate': SystemInfo(['gamate'], ['gamate'], ['MAME (Gamate)'], {MediaType.Cartridge: generic_cart_extensions}),
	'GameKing': SystemInfo(['gameking'], ['gameking'], ['MAME (GameKing)'], {MediaType.Cartridge: ['gk'] + generic_cart_extensions}),
	'GameKing 3': SystemInfo(['gamekin3'], ['gameking3'], ['MAME (GameKing 3)'], {MediaType.Cartridge: ['gk3'] + generic_cart_extensions}),
	'GoGo TV Video Vision': SystemInfo(['tvgogo'], ['tvgogo'], ['MAME (GoGo TV Video Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'GP2X': SystemInfo(['gp2x'], [], [], {}), #TODO: File formats and things
	'GP32': SystemInfo(
		['gp32'], ['gp32'], ['MAME (GP32)'], {MediaType.Cartridge: ['smc'], MediaType.Executable: ['gxb', 'sxf', 'bin', 'gxf', 'fxe']}, dat_names=['GamePark - GP32']
	),
	'Hartung Game Master': SystemInfo(['gmaster'], ['gmaster'], ['MAME (Hartung Game Master)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Mattel HyperScan': SystemInfo(['hyprscan'], ['hyperscan'], ['MAME (Mattel HyperScan)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Mega Duck': SystemInfo(['megaduck', 'mduckspa'], ['megaduck'], ['SameDuck (libretro)', 'MAME (Mega Duck)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Monon Color': SystemInfo(['mononcol'], ['monon_color'], ['MAME (Monon Color)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Nuon': SystemInfo([], ['nuon'], [], {MediaType.OpticalDisc: ['iso']}),
	'PocketStation': SystemInfo(['pockstat'], [], [], {MediaType.Digital: ['gme']}),
	'RCA Studio 2': SystemInfo(['studio2'], ['studio2'], [], {MediaType.Cartridge: ['st2'] + generic_cart_extensions}, dat_names=['RCA - Studio II'], autodetect_tv_type=True), #Headered
	'Select-a-Game': SystemInfo(['sag'], ['entex_sag'], ['MAME (Select-a-Game)'], {MediaType.Cartridge: generic_cart_extensions}),
	"Super A'Can": SystemInfo(['supracan'], ['supracan'], ["MAME (Super A'Can)"], {MediaType.Cartridge: generic_cart_extensions}),
	'Super Cassette Vision': SystemInfo(
		['scv'], ['scv'], ['MAME (Super Cassette Vision)'], {MediaType.Cartridge: generic_cart_extensions}, dat_names=['Epoch - Super Cassette Vision']
	),
	'VC 4000': SystemInfo(['vc4000', '1292apvs', 'database', 'elektor', 'h21', 'krvnjvtv', 'mpt05', 'rwtrntcs'], ['vc4000', 'database'], ['MAME (VC 4000)'], {MediaType.Cartridge: generic_cart_extensions}, autodetect_tv_type=True), #Which one is the "main" system, really, bit of a clusterfuck (well the software list is named vc4000 I guess)
	'ZAPit Game Wave': SystemInfo([], [], [], {MediaType.OpticalDisc: ['iso']}),
	'Zeebo': SystemInfo(['zeebo'], [], [], {}), #Folders with "mif" and "mod"?

	#Homebrew projects or whatever
	'Arduboy': SystemInfo([], [], [], {MediaType.Digital: ['arduboy'], MediaType.Executable: ['hex']}),
	'Uzebox': SystemInfo(['uzebox'], ['uzebox'], ['Uzem (libretro)', 'MAME (Uzebox)'], {MediaType.Executable: ['bin', 'uze']}, dat_names=['Uzebox']),

	#Educational sort-of-game consoles
	'Advanced Pico Beena': SystemInfo(['beena'], ['sega_beena_cart'], ['MAME (Advanced Pico Beena)'], {MediaType.Cartridge: generic_cart_extensions}),
	'ClickStart': SystemInfo(['clikstrt'], ['clickstart_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Copera': SystemInfo(['copera'], ['copera'], ['MAME (Copera)'], {MediaType.Cartridge: ['bin', 'md']}), #Pico-related, but not quite the same (software will show warning message on Pico)
	'Didj': SystemInfo(['didj'], ['leapfrog_didj_cart'], ['MAME (Didj)'], {MediaType.Cartridge: generic_cart_extensions}),
	'InnoTab': SystemInfo(['innotab2'], ['vtech_innotab_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'InnoTV': SystemInfo(['innotv'], ['vtech_innotv_innotabmax_cart'], [], {MediaType.Cartridge: generic_cart_extensions}), #The InnoTab MAX is another system that uses the same cartridges
	'iQuest': SystemInfo(['iquest'], ['leapfrog_iquest_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'LeapPad': SystemInfo(['leappad'], ['leapfrog_leappad_cart'], ['MAME (LeapPad)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Leapster': SystemInfo(['leapster'], ['leapster'], ['MAME (Leapster)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Little Touch LeapPad': SystemInfo(['ltleappad'], ['leapfrog_ltleappad_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'MobiGo': SystemInfo(['mobigo', 'mobigo2'], ['mobigo_cart'], ['MAME (MobiGo)'], {MediaType.Cartridge: generic_cart_extensions}),
	'My First LeapPad': SystemInfo(['mfleappad'], ['leapfrog_mfleappad_cart'], ['MAME (My First LeapPad)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Sawatte Pico': SystemInfo(['sawatte'], ['sawatte'], [], {}),
	'Sega Pico': SystemInfo(['pico'], ['pico'], ['Genesis Plus GX (libretro)', 'Kega Fusion', 'MAME (Sega Pico)'], {MediaType.Cartridge: ['bin', 'md']}, dat_names=['Sega - PICO'], autodetect_tv_type=True),
	'SmarTV Adventures': SystemInfo(['smartvad'], ['smarttv_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Story Reader': SystemInfo(['pi_stry'], ['pi_storyreader_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Story Reader 2': SystemInfo(['pi_stry2'], ['pi_storyreader_v2_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Telestory': SystemInfo(['telestry'], ['telestory_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Tomy Prin-C': SystemInfo(['princ'], ['princ'], ['MAME (Tomy Prin-C)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Turbo Extreme': SystemInfo(['turboex'], ['leapfrog_turboextreme_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Turbo Twist Brain Quest': SystemInfo(['ttwistbq'], ['leapfrog_turbotwistbrainquest_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Turbo Twist Math': SystemInfo(['ttwistm'], ['leapfrog_turbotwistmath_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'V.Baby': SystemInfo(['vbaby'], ['vbaby_cart'], [], {MediaType.Cartridge: generic_cart_extensions}), #Not compatible at all with V.Smile Baby which is confusing
	'V.Reader': SystemInfo(['vreader'], ['vtech_storio_cart'], ['MAME (V.Reader)'], {MediaType.Cartridge: generic_cart_extensions}), 
	#Skeleton driver, apparently also known as Storio, or something like that
	'V.Smile Pro': SystemInfo(['vsmilpro'], ['vsmile_cd'], ['MAME (V.Smile Pro)'], {MediaType.OpticalDisc: cdrom_formats}),
	'V.Smile': SystemInfo(['vsmile'], ['vsmile_cart'], ['MAME (V.Smile)'], {MediaType.Cartridge: generic_cart_extensions}, dat_names=['VTech - V.Smile']),
	'V.Smile Baby': SystemInfo(['vsmileb'], ['vsmileb_cart'], ['MAME (V.Smile Baby)'], {MediaType.Cartridge: generic_cart_extensions}),
	'V.Smile Motion': SystemInfo(['vsmilem'], ['vsmilem_cart'], ['MAME (V.Smile Motion)'], {MediaType.Cartridge: generic_cart_extensions}),
	'V.Tech Socrates': SystemInfo(['socrates'], ['socrates'], ['MAME (V.Tech Socrates)'], {MediaType.Cartridge: generic_cart_extensions}),
	
	#Consoles that barely count as consoles because aren't for gaming or whatever (or games push the definition), but for the purposes of creating a launcher, might as well be consoles
	'BBC Bridge Companion': SystemInfo(['bbcbc'], ['bbcbc'], ['MAME (BBC Bridge Companion)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Benesse Pocket Challenge V2': SystemInfo([], ['pockchalv2'], ['Beetle Cygne (libretro)', 'Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['pc2', 'bin']}), #Sort of WonderSwan with different controls
	'Buzztime Home Trivia System':  SystemInfo(['buzztime'], ['buzztime_cart'], ['MAME (Buzztime Home Trivia System)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Casio Loopy': SystemInfo(['casloopy'], ['casloopy'], ['MAME (Casio Loopy)'], {MediaType.Cartridge: generic_cart_extensions}, dat_names=['Casio - Loopy']),
	'Design Master Denshi Mangajuku': SystemInfo(['bdesignm'], ['bdesignm_design_cart', 'bdesignm_game_cart'], [], {MediaType.Cartridge: generic_cart_extensions}), #This will be interesting because you're supposed to use combinations of different design carts and game carts at the same time
	'Gachinko Contest! Slot Machine TV': SystemInfo(['gcslottv'], ['gcslottv'], ['MAME (Gachinko Contest! Slot Machine TV)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Koei PasoGo': SystemInfo(['pasogo'], ['pasogo'], ['MAME (Koei PasoGo)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Konami Picno': SystemInfo(['picno', 'picno2'], ['picno'], ['MAME (Konami Picno)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Mattel Juice Box': SystemInfo(['juicebox'], ['juicebox'], ['MAME (Mattel Juice Box)'], {MediaType.Cartridge: ['smc']}),
	'Nichibutsu My Vision': SystemInfo(['myvision'], ['myvision'], ['MAME (Nichibutsu My Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Pocket Challenge W': SystemInfo(['pockchal'], ['pockchalw'], ['MAME (Pocket Challenge W)'], {MediaType.Cartridge: ['bin', 'pcw']}),
	
	#Multimedia consoles that also don't like to be classified as game consoles
	'CD-i': SystemInfo(['cdimono1', 'cdimono2', 'cdi490a', 'cdi910'], ['cdi'], ['MAME (CD-i)'], {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	'Commodore CDTV': SystemInfo(['cdtv'], ['cdtv'], ['PUAE (libretro)', 'FS-UAE', 'MAME (Commodore CDTV)'], {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),	
	'Memorex VIS': SystemInfo(['vis'], [], ['MAME (Memorex VIS)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Pippin': SystemInfo(['pippin'], ['pippin', 'pippin_flop'], ['MAME (Pippin)'], {MediaType.OpticalDisc: cdrom_formats}),

	#Addons for other systems that we're going to treat as separate things because it seems to make more sense that way, until it doesn't
	'32X': SystemInfo(['32x'], ['32x'], ['PicoDrive (libretro)', 'Kega Fusion', 'MAME (32X)'], {MediaType.Cartridge: ['32x', 'bin']}, dat_names=['Sega - 32X'], autodetect_tv_type=True),
	'64DD': SystemInfo(['n64dd'], ['n64dd'], [], {MediaType.Floppy: ['ndd', 'ddd']}, dat_names=['Nintendo - Nintendo 64DD']),
	'e-Reader': SystemInfo(['gba'], ['gba_ereader'], [], {MediaType.Barcode: ['bin', 'raw', 'bmp']}),
	'Jaguar CD': SystemInfo(['jaguarcd'], [], ['MAME (Jaguar CD)'], {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	'Mega CD': SystemInfo(
		#LaserActive counts as this for now
		['segacd', '32x_scd', 'cdx', 'segacd2', 'xeye', 'laseract'], ['megacd', 'megacdj', 'segacd'],
		['Genesis Plus GX (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'MAME (Mega CD)'], {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True, dat_names=['Sega - Mega-CD - Sega CD'], dat_uses_serial=True
	),
	'PC Engine CD': SystemInfo(
		['pce'], ['pcecd'], ['Beetle PCE (libretro)', 'Beetle PCE Fast (libretro)', 'Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.OpticalDisc: cdrom_formats}
	),
	'Play-Yan': SystemInfo(['gba'], [], [], {MediaType.Digital: ['asf']}),

	#PDA type things that I don't really wanna put under computers
	'Cybiko': SystemInfo(['cybikov1'], [], [], {MediaType.Digital: ['app']}),
	#'Cybiko Xtreme': SystemInfo('cybikoxt', [], [], {MediaType.Digital: ['app']}), #Does this really qualify as a different thing?
	'Gizmondo': SystemInfo(['gizmondo'], [], [], {}), #Uses folders seemingly, so that may be weird with the file types
	'N-Gage': SystemInfo([], [], [], {MediaType.Digital: ['app']}),
	'Sharp Wizard': SystemInfo(['iq7000'], ['wizard_cart'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Tapwave Zodiac': SystemInfo([], [], [], {}), #File type is like, kinda .prc but kinda not (the device runs spicy PalmOS, would it be considered part of that if any of that was emulated?)
	
	#Computers that most people are here for (wew I'm being subjective again)
	'Acorn Electron': SystemInfo(['electron'], ['electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl']}),
	'Amiga': SystemInfo(
		 #TODO: There should be CD images for this too, albeit I'm not sure how they work
		['a1000', 'a1200', 'a2000', 'a3000', 'a4000', 'a4000t', 'a500', 'a500p', 'a600'], ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'], 
		['PUAE (libretro)', 'FS-UAE'], {MediaType.Floppy: ['adf', 'ipf', 'dms', 'adz', 'fdi'], MediaType.HardDisk: ['hdf', 'hdz'], MediaType.Digital: ['lha', 'slave', 'info']},
		{'default_chipset': SystemConfigValue(ConfigValueType.String, 'AGA', 'Default chipset to use if a game doesn\'t specify what chipset it should use (AGA, OCS, ECS)')}, 
		autodetect_tv_type=True, dat_names=['Commodore - Amiga']
	),
	'Amstrad CPC': SystemInfo(['cpc464', 'cpc6128p', 'gx4000'], ['cpc_cass', 'cpc_flop', 'gx4000'], ['Caprice32 (libretro)', 'MAME (Amstrad GX4000)'], {MediaType.Snapshot: ['sna'], MediaType.Tape: ['wav', 'cdt'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['cpr'] + generic_cart_extensions}, dat_names=['Amstrad - CPC']),
	'Apple II': SystemInfo(['apple2', 'apple2c', 'apple2e', 'cece', 'cecg', 'ceci', 'cecm', 'cec2000'], ['apple2', 'apple2_cass', 'apple2_flop_orig', 'apple2_flop_clcracked', 'apple2_flop_misc'], ['MAME (Apple II)', 'Mednafen (Apple II)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz', 'shk', 'bxy'], MediaType.Tape: generic_tape_extensions}),
	'Apple IIgs': SystemInfo(['apple2gs'], ['apple2gs'], ['MAME (Apple IIgs)'], {MediaType.Floppy: mame_floppy_formats + ['2mg', '2img', 'dc', 'shk', 'bxy', 'woz']}),
	'Atari 8-bit': SystemInfo(
		['a800', 'a400', 'a800xl', 'xegs'], ['a800', 'a800_flop', 'xegs'], 
		['MAME (Atari 8-bit)'], {MediaType.Floppy: ['atr', 'dsk', 'xfd', 'dcm'], MediaType.Executable: ['xex', 'bas', 'com'], MediaType.Cartridge: ['bin', 'rom', 'car'], MediaType.Tape: generic_tape_extensions}, 
		{'basic_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to BASIC ROM for floppy software which requires that, or use "basicc" to use software')
		}, autodetect_tv_type=True),
	'Atari ST': SystemInfo(['st', 'ste', 'tt030', 'falcon30'], ['st_flop', 'st_cart'], ['Hatari (libretro)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats + ['st', 'stx', 'msa', 'dim']}, autodetect_tv_type=True, dat_names=['Atari - ST']),
	'BBC Master': SystemInfo(['bbcm', 'bbcmc'], ['bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'ima', 'ufi', '360'] + mame_floppy_formats, MediaType.Cartridge: ['rom', 'bin']}, autodetect_tv_type=True),
	'BBC Micro': SystemInfo(['bbcb', 'bbcbp'], ['bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig', 'bbc_flop_65c102', 'bbc_flop_6502', 'bbc_flop_32016', 'bbc_flop_68000', 'bbc_flop_80186', 'bbc_flop_arm', 'bbc_flop_torch', 'bbc_flop_z80'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'dsk', 'ima', 'ufi', '360'], MediaType.Cartridge: ['rom', 'bin']}, autodetect_tv_type=True),
	'C64': SystemInfo(
		['c64'], ['c64_cart', 'c64_cass', 'c64_flop', 'c64_flop_clcracked', 'c64_flop_orig', 'c64_flop_misc'], 
		['MAME (C64)', 'VICE (C64)', 'VICE (C64 Fast)'], {MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	),
	'FM Towns': SystemInfo(['fmtowns', 'fmtmarty'], ['fmtowns_cd', 'fmtowns_flop_cracked', 'fmtowns_flop_misc', 'fmtowns_flop_orig'], ['MAME (FM Towns)', 'MAME (FM Towns Marty)'], {MediaType.Floppy: mame_floppy_formats + ['bin'], MediaType.OpticalDisc: cdrom_formats}), #Floppy list was just fmtowns_flop prior to 0.230
	'MSX': SystemInfo(
		msx1_drivers, ['msx1_cart', 'msx1_cass', 'msx1_flop'],
		['blueMSX (libretro)', 'fMSX (libretro)', 'MAME (MSX)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions},
		dat_names=['Microsoft - MSX'], autodetect_tv_type=True
	),
	'MSX2': SystemInfo(
		msx2_drivers, ['msx2_cart', 'msx2_cass', 'msx2_flop'],
		['blueMSX (libretro)', 'fMSX (libretro)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions},
		dat_names=['Microsoft - MSX 2'], autodetect_tv_type=True
	),
	'MSX2+': SystemInfo(
		#Should this be considered the same system as MSX2? Oh dear, I've gotten confused
		msx2plus_drivers, ['msx2p_flop'],
		['blueMSX (libretro)', 'fMSX (libretro)', 'MAME (MSX2+)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions},
		dat_names=['Microsoft - MSX 2'], autodetect_tv_type=True
	),
	'MSX Turbo-R': SystemInfo(msxtr_drivers, ['msxr_flop'], [], {MediaType.Floppy: mame_floppy_formats}),
	'PC-98': SystemInfo(['pc9801f', 'pc9801rs', 'pc9801ux', 'pc9821'], ['pc98', 'pc98_cd'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}, dat_names=['NEC - PC-98']),
	'Sharp X68000': SystemInfo(['x68000'], ['x68k_flop'], ['PX68k (libretro)', 'MAME (Sharp X68000)'], {MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim'], MediaType.HardDisk: ['hdf']}, dat_names=['Sharp - X68000']),
	'Tandy CoCo': SystemInfo(['coco'], ['coco_cart', 'coco_flop'], ['MAME (Tandy CoCo)'], {MediaType.Cartridge: ['ccc', 'rom', 'bin'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats + ['dmk', 'jvc'], MediaType.HardDisk: ['vhd']}),
	'TRS-80': SystemInfo(['trs80', 'trs80l2', 'trs80m3'], [], ['MAME (TRS-80)'], {MediaType.Executable: ['cmd'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: ['dmk'] + mame_floppy_formats}),
	'ZX Spectrum': SystemInfo(['spectrum', 'spec128'], ['spectrum_cart', 'spectrum_cass', 'specpls3_flop', 'pentagon_cass', 'spectrum_flop_opus', 'spectrum_mgt_flop', 'spectrum_microdrive', 'spectrum_wafadrive', 'timex_dock', 'timex_cass'], ['MAME (ZX Spectrum)'], {MediaType.Snapshot: ['z80', 'sna'], MediaType.Tape: ['wav', 'cas', 'tap', 'tzx'], MediaType.Executable: ['raw', 'scr'], MediaType.Floppy: ['dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi', 'opd', 'opu'], MediaType.Cartridge: ['bin', 'rom']}, dat_names=['Sinclair - ZX Spectrum', 'Sinclair - ZX Spectrum +3']), #There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

	#Other computers that aren't as exciting
	'Acorn Archimedes': SystemInfo(['aa310', 'aa4000', 'aa5000'], ['archimedes'], [], {MediaType.Floppy: mame_floppy_formats + ['adf']}), 
	'Apple III': SystemInfo(['apple3'], ['apple3'], ['MAME (Apple III)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz']}),
	'Apple Lisa': SystemInfo(['lisa', 'lisa2'], ['lisa'], [], {MediaType.Floppy: mame_floppy_formats + ['dc', 'dc42']}),
	'C128': SystemInfo(['c128', 'c128p'], ['c128_cart', 'c128_flop', 'c128_rom'], ['VICE (C128)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	),
	'CBM-II': SystemInfo(['b128hp', 'b500', 'p500'], ['cbm2_cart', 'cbm2_flop'], [], {MediaType.Floppy: ['d80', 'd88', 'd77'] + mame_floppy_formats, MediaType.Cartridge: ['20', '40', '60'], MediaType.Executable: ['p00', 'prg', 't64']}),
	'Commodore PET': SystemInfo(['pet2001', 'cbm8296', 'pet2001b', 'pet2001n', 'pet4016', 'pet4032b', 'pet8032'], ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], ['VICE (Commodore PET)'], {MediaType.Floppy: commodore_disk_formats, MediaType.Cartridge: ['bin', 'rom'], MediaType.Executable: ['prg', 'p00'], MediaType.Tape: ['wav', 'tap']}),
	'Dragon': SystemInfo(['dragon32'], ['dragon_cart', 'dragon_cass', 'dragon_flex', 'dragon_flop', 'dragon_os9'], [], {MediaType.Floppy: ['dmk', 'jvc', 'vdk', 'sdf', 'os9'] + mame_floppy_formats, MediaType.Cartridge: ['ccc', 'rom'], MediaType.Tape: ['wav', 'cas']}),
	'FM-7': SystemInfo(['fm7', 'fm8', 'fm11', 'fm16beta'], ['fm7_cass', 'fm7_disk', 'fm77av'], ['MAME (FM-7)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav', 't77']}),
	'IBM PCjr': SystemInfo(['ibmpcjr', 'ibmpcjx'], ['ibmpcjr_cart'], ['MAME (IBM PCjr)'], {MediaType.Cartridge: ['bin', 'jrc'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#Most software is going to go under DOS or PC Booter, but this would be the carts… hmm… does this make sense, actually
	'PC Booter': SystemInfo(['ibm5150'], ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)'], {MediaType.Floppy: mame_floppy_formats + ['img'], MediaType.Executable: ['exe', 'com', 'bat']}), #TODO: Reconsider this name; does it make more sense to be called "IBM PC"? Are PCjr carts not just PC booters that are carts instead of floppies (hot take)?
	'PC-6001': SystemInfo(['pc6001'], [], ['MAME (PC-6001)'], {MediaType.Tape: ['cas', 'p6'], MediaType.Cartridge: generic_cart_extensions}),
	'PC-88': SystemInfo(['pc8801', 'pc88va'], ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}, dat_names=['NEC - PC-8001 - PC-8801']),
	'PDP-1': SystemInfo(['pdp1'], [], [], {MediaType.Tape: ['tap', 'rim']}),
	'Plus/4': SystemInfo(['c264'], ['plus4_cart', 'plus4_cass', 'plus4_flop'], ['VICE (Plus/4)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	), 	#Also includes C16 and C116 (I admit I am not cool enough to know the difference)
	'SAM Coupe': SystemInfo(['samcoupe'], ['samcoupe_cass', 'samcoupe_flop'], ['SimCoupe', 'MAME (SAM Coupe)'], {MediaType.Floppy: ['mgt', 'sad', 'dsk', 'sdf'], MediaType.Executable: ['sbt']}),
	'Sharp X1': SystemInfo(['x1'], ['x1_cass', 'x1_flop'], ['X Millennium (libretro)', 'MAME (Sharp X1)'], {MediaType.Floppy: ['2d'] + mame_floppy_formats, MediaType.Tape: ['wav', 'tap']}),
	'TI-99': SystemInfo(['ti99_4', 'ti99_4a', 'ti99_8'], ['ti99_cart'], [], {MediaType.Cartridge: ['bin', 'rpk', 'c', 'g'], MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}, autodetect_tv_type=True),
	'VIC-20': SystemInfo(['vic1001'], ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)', 'VICE (VIC-20)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['wav', 'tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	),
	'ZX81': SystemInfo(['zx81', 'zx80'], ['zx80_cass', 'zx81_cass'], ['81 (libretro)'], {MediaType.Tape: ['wav', 'cas', 'p', '81', 'tzx', 't81']}, dat_names=['Sinclair - ZX 81']),
	
	#More obscure computers because otherwise the above section is long and hard to read
	'Acorn Atom': SystemInfo(['atom'], ['atom_cass', 'atom_flop', 'atom_rom'], [], {MediaType.Floppy: ['40t', 'dsk'], MediaType.Tape: ['wav', 'tap', 'csw', 'uef'], MediaType.Executable: ['atm'], MediaType.Cartridge: ['bin', 'rom']}),
	'Alice 32': SystemInfo(['alice32'], ['alice32', 'alice90'], [], {MediaType.Tape: ['wav', 'cas', 'c10', 'k7']}),
	'Amstrad PCW': SystemInfo(['pcw8256'], ['pcw'], ['MAME (Amstrad PCW)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['com']}),
	'Amstrad PCW16': SystemInfo(['pcw16'], ['pcw16'], [], {MediaType.Floppy: mame_floppy_formats}),
	'APF Imagination Machine': SystemInfo(['apfimag'], ['apfimag_cass', 'apfm1000'], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas', 'cpf', 'apt'], MediaType.Floppy: mame_floppy_formats}), #Considered separate from APF-M1000 (same predicament as Coleco Adam) (or is it? (maybe?))
	'Apple I': SystemInfo(['apple1'], ['apple1'], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['snp']}), #Loading tapes would require parsing software list usage to figure out where to put load addresses and things to make an autoboot script, because otherwise it's just way too messy to warrant being in a frontend. Snapshots supposedly exist, but I haven't seen any whoops
	'Apogey BK-01': SystemInfo(['apogee'], ['apogee'], [], {MediaType.Tape: ['wav', 'rka']}), #Should this be rolled up into Radio 86?
	'Atari Portfolio': SystemInfo(['pofo'], ['pofo'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	'Bandai RX-78': SystemInfo(['rx78'], ['rx78_cart', 'rx78_cass'], ['MAME (Bandai RX-78)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}), #Software list was just rx78 prior to MAME 0.228
	'Bullet': SystemInfo(['wmbullet'], ['wmbullet'], [], {MediaType.Floppy: mame_floppy_formats}),
	'C64DTV': SystemInfo(['c64dtv'], [], [], {MediaType.Floppy: commodore_disk_formats, MediaType.Executable: ['prg']}),
	'Cambridge Z88': SystemInfo(['z88'], ['z88_cart'], [], {MediaType.Cartridge: ['epr', 'bin']}),
	'Camputers Lynx': SystemInfo(['lynx48k'], ['camplynx_cass', 'camplynx_flop'], [], {MediaType.Floppy: mame_floppy_formats + ['ldf'], MediaType.Tape: ['wav', 'tap']}),
	#Convinced that whoever invented this system and the way it loads programs personally hates me, even though I wasn't born when it was made and so that's not really possible
	'Canon X07': SystemInfo(['x07'], ['x07_card', 'x07_cass'], [], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav', 'tap']}),
	'Casio PV-2000': SystemInfo(['pv2000'], ['pv2000'], ['MAME (Casio PV-2000)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Central Data 2650': SystemInfo(['cd2650'], [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'Coleco Adam': SystemInfo(['adam'], ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)'], {MediaType.Cartridge: ['col', 'bin'], MediaType.Tape: ['wav', 'ddp'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['lbr', 'com']}),
	'Colour Genie': SystemInfo(['cgenie'], ['cgenie_cass', 'cgenie_flop_rom'], [], {MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['rom']}),
	'Commodore 65': SystemInfo(['c65'], ['c65_flop'], [], {MediaType.Floppy: commodore_disk_formats}), #Never actually released, has software anyway; only good for software lists
	'Compis': SystemInfo(['compis'], ['compis'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'Cosmac VIP': SystemInfo(['vip'], ['vip'], [], {MediaType.Tape: ['wav']}), #Also a Chip-8 interpreter
	'Dream 6800': SystemInfo(['d6800'], [], [], {MediaType.Tape: ['wav']}), #Chip-8 interpreter
	'Electronika BK': SystemInfo(['bk0010'], ['bk0010'], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: mame_floppy_formats, MediaType.HardDisk: ['hdi'], MediaType.Executable: ['bin']}),
	'Elf II': SystemInfo(['elf2'], [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['bin']}),
	'Enterprise': SystemInfo(['ep64'], ['ep64_cart', 'ep64_cass', 'ep64_flop'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav']}),
	'ETI-660': SystemInfo(['eti660'], ['eti660_quik'], [], {MediaType.Tape: ['wav']}), #A Chip-8 interpreting machine
	'Exidy Sorcerer': SystemInfo(['sorcerer'], ['sorcerer_cart', 'sorcerer_cass', 'sorcerer_flop'], [], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav', 'tape'], MediaType.Snapshot: ['snp'], MediaType.Executable: ['bin']}),
	'Galaksija': SystemInfo(['galaxy', 'galaxyp'], ['galaxy'], [], {MediaType.Snapshot: ['gal'], MediaType.Tape: ['wav', 'gtp']}),
	'Goldstar FC-100': SystemInfo(['fc100'], [], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas']}), #Some kind of PC-6001 clone or something, apparently
	'Pencil II': SystemInfo(['pencil2'], ['pencil2'], [], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav']}),
	'Instructor 50': SystemInfo(['instruct'], [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'Interact': SystemInfo(['interact', 'hec2hrp'], ['interact'], [], {MediaType.Tape: ['wav', 'k7', 'cin', 'for']}),
	'Jupiter Ace': SystemInfo(['jupace'], ['jupace_snap', 'jupace_cass'], ['MAME (Jupiter Ace)'], {MediaType.Tape: ['wav', 'tap', 'tzx'], MediaType.Snapshot: ['ace']}),
	'KC-85': SystemInfo(['kc85_2'], ['kc_cart', 'kc_cass', 'kc_flop'], ['MAME (KC-85)'], {MediaType.Executable: ['kcc'], MediaType.Tape: ['wav', 'kcb', 'tap', '853', '854', '855', 'tp2', 'kcm', 'sss'], MediaType.Cartridge: ['bin']}), #kcc might also be a tape format?? ehhhh???
	'Luxor ABC80': SystemInfo(['abc80'], ['abc80_cass', 'abc80_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['bac']}), 'Mattel Aquarius': SystemInfo(['aquarius'], ['aquarius_cart', 'aquarius_cass'], ['MAME (Mattel Aquarius)'], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav', 'caq']}), #Software list was just "aquarius" prior to 0.226
	'Orao': SystemInfo(['orao'], ['orao'], [], {MediaType.Tape: ['wav', 'tap']}),
	'Memotech MTX': SystemInfo(['mtx512'], ['mtx_cart', 'mtx_cass', 'mtx_rom'], [], {MediaType.Snapshot: ['mtx'], MediaType.Executable: ['run'], MediaType.Tape: ['wav'], MediaType.Cartridge: ['bin', 'rom']}),
	'Microbee': SystemInfo(['mbee'], [], ['MAME (Microbee)'], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['mwb', 'com', 'bee']}), #Also a second .bin quickload?
	'Microtan 65': SystemInfo(['mt65'], ['mt65_snap'], ['MAME (Microtan 65)'], {MediaType.Tape: ['wav'], MediaType.Executable: ['hex'], MediaType.Snapshot: ['dmp', 'm65']}), #MAME driver was "microtan" prior to 0.212
	'MikroMikko 1': SystemInfo(['mm1m6'], ['mm1_flop'], [], {MediaType.Floppy: mame_floppy_formats}),
	'Mikrosha': SystemInfo(['mikrosha'], ['mikrosha_cart', 'mikrosha_cass'], [], {MediaType.Tape: ['wav', 'rkm'], MediaType.Cartridge: ['bin', 'rom']}), #Maybe should just be part of Radio 86?
	'Nascom': SystemInfo(['nascom1', 'nascom2'], ['nascom_flop', 'nascom_snap', 'nascom_socket'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['nas', 'chr']}),
	'Oric': SystemInfo(['oric1'], [], [], {MediaType.Tape: ['wav', 'tap']}),
	'Orion-128': SystemInfo(['orion128'], ['orion_cart', 'orion_cass', 'orion_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi'], MediaType.Cartridge: ['bin']}),
	'Panasonic JR-200': SystemInfo(['jr200'], [], []),
	'Pasopia 7': SystemInfo(['pasopia7'], [], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),
	'Pasopia 1600': SystemInfo(['paso1600'], [], [], {}),
	'Partner 01.01': SystemInfo(['partner'], ['partner_cass', 'partner_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi']}), #Another Radio 86 clone?
	'PipBug': SystemInfo(['pipbug'], [], [], {MediaType.Executable: ['pgm']}),
	'PMD 85': SystemInfo(['pmd851'], ['pmd85_cass'], [], {MediaType.Tape: ['wav', 'pmd', 'tap', 'ptp']}),
	'Radio 86-RK': SystemInfo(['radio86'], ['radio86_cart', 'radio86_cass'], [], {MediaType.Tape: ['wav', 'rk', 'rkr', 'gam', 'g16', 'pki']}),
	'Robotron Z1013': SystemInfo(['z1013'], [], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['z80']}),
	'Sharp MZ-700': SystemInfo(['mz700'], ['mz700'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sharp MZ-800': SystemInfo(['mz800', 'mz1500'], ['mz800'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sharp MZ-2000': SystemInfo(['mz2000', 'mz80b'], ['mz2000_cass', 'mz2000_flop', 'mz2200_cass'], ['MAME (Sharp MZ-2000)'], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt'], MediaType.Floppy: ['2d'] + mame_floppy_formats}),
	'Sinclair QL': SystemInfo(['ql', 'tonto'], ['ql_cart', 'ql_cass', 'ql_flop'], [], {MediaType.Tape: ['mdv'], MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats}),
	'Sony SMC-777': SystemInfo(['smc777'], ['smc777'], ['MAME (Sony SMC-777)'], {MediaType.Floppy: mame_floppy_formats + ['1dd'], MediaType.Executable: ['com', 'cpm']}),
	'Sord M5': SystemInfo(['m5'], ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)'], {MediaType.Cartridge: ['bin'], MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	'Squale': SystemInfo(['squale'], ['squale_cart'], ['MAME (Squale)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin']}),
	'SVI-3x8': SystemInfo(['svi318', 'svi328'], ['svi318_cart', 'svi318_cass', 'svi318_flop'], ['MAME (SVI-3x8)'], {MediaType.Tape: ['wav', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'Tandy MC-10': SystemInfo(['mc10'], ['mc10'], [], {MediaType.Tape: ['wav', 'cas', 'c10']}),
	'Tatung Einstein': SystemInfo(['einstein', 'einst256'], ['einstein'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav'], MediaType.Executable: ['com']}),
	'Thomson MO5': SystemInfo(['mo5', 'mo5nr'], ['mo5_cart', 'mo5_cass', 'mo5_flop', 'mo5_qd'], ['MAME (Thomson MO5)'], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}, dat_names=['Thomson - MOTO']),
	'Thomson MO6': SystemInfo(['mo6'], ['mo6_cass', 'mo6_flop'], [], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}, dat_names=['Thomson - MOTO']),
	'Thomson TO': SystemInfo(['to7', 'to770', 'to8', 'to9', 'to9p'], ['to7_cart', 'to7_cass', 'to7_qd', 'to8_cass', 'to8_qd', 'to770a_cart', 'to770_cart'], [], {MediaType.Tape: ['wav', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m7', 'bin', 'rom']}, dat_names=['Thomson - MOTO']),
	'Tiki 100': SystemInfo(['kontiki'], ['tiki100'], [], {MediaType.HardDisk: ['chd', 'hd', 'hdv', 'hdi'], MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'Tomy Tutor': SystemInfo(['tutor'], ['tutor'], ['MAME (Tomy Tutor)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Toshiba Pasopia': SystemInfo(['pasopia'], ['pasopia_cass'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),	#Ow my freaking ears… every tape seems to take a long time to get anywhere
	'Vector-06C': SystemInfo(['vector06'], ['vector06_cart', 'vector06_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin', 'emr']}),
	'VIC-10': SystemInfo(['vic10'], ['vic10'], ['MAME (VIC-10)'], {MediaType.Cartridge: ['crt', 'bin', '80', 'e0'], MediaType.Tape: ['wav', 'tap', 't64']}),
	'Videoton TVC': SystemInfo(['tvc64'], ['tvc_cart', 'tvc_cass', 'tvc_flop'], ['MAME (Videoton TVC)'], {MediaType.Cartridge: ['bin', 'rom', 'crt'], MediaType.Tape: ['wav', 'cas']}), #.cas is also quickload? I donut understand
	'VideoBrain': SystemInfo(['vidbrain'], ['vidbrain'], ['MAME (VideoBrain)'], {MediaType.Cartridge: ['bin']}),
	'VZ-200': SystemInfo(['vz200', 'laser200', 'laser110', 'laser210', 'laser310'], ['vz_cass', 'vz_snap'], ['MAME (VZ-200)'], {MediaType.Snapshot: ['vz'], MediaType.Tape: ['wav', 'cas']}), #There are many different systems in this family, but I'll go with this one, because the software list is named after it
	'Zorba': SystemInfo(['zorba'], ['zorba'], [], {MediaType.Floppy: mame_floppy_formats}),

	#Hmm, not quite computers or any particular hardware so much as OSes which probably don't belong here anyway
	'Android': SystemInfo([], [], [], {MediaType.Digital: ['apk']}),
	'PalmOS': SystemInfo([], [], ['Mu (libretro)'], {MediaType.Executable: ['prc', 'pqa']}),

	#Interpreted virtual machine thingy…
	'Chip-8': SystemInfo([], ['chip8_quik'], [], {MediaType.Executable: ['bin', 'c8', 'ch8']}), #Many interpreters available in MAME - Cosmac VIP, Dream 6800, ETI-660, etc; though I'm not sure if it makes sense to put them as the mame_driver for this, but when I get around to that I suppose they would be emulators for it

	#Stuff that isn't actually hardware but we can pretend it is one
	'ChaiLove': SystemInfo([], [], ['ChaiLove (libretro)'], {MediaType.Executable: ['chai'], MediaType.Digital: ['chailove']}, is_virtual=True, dat_names=['ChaiLove']),
	'Dinothawr': SystemInfo([], [], ['Dinothawr (libretro)'], {MediaType.Executable: ['game']}, is_virtual=True, dat_names=['Dinothawr']),
	'Doom': SystemInfo(
		[], [], ['PrBoom+'], {MediaType.Digital: ['wad']}, 
		{'save_dir': SystemConfigValue(ConfigValueType.FolderPath, None, 'Folder to put save files in')},
		is_virtual=True, dat_names=['DOOM']
	),
	'Flash': SystemInfo([], [], ['Ruffle'], {MediaType.Digital: ['swf']}, is_virtual=True),
	'J2ME': SystemInfo([], [], ['FreeJ2ME (libretro)'], {MediaType.Executable: ['jar']}, is_virtual=True),
	'LowRes NX': SystemInfo([], [], ['LowRes NX (libretro)'], {MediaType.Digital: ['nx']}, is_virtual=True, dat_names=['LowRes NX']),
	'Pico-8': SystemInfo([], [], ['Pico-8'], {MediaType.Cartridge: ['p8.png'], MediaType.Executable: ['p8']}, is_virtual=True),
}

#For Machine.is_system_driver to work correctly
ibmpc_drivers = ['ibm5150', 'ibm5170', 'pcipc', 'pcipctx', 'nforcepc']
mac_drivers = ['mac128k', 'macplus', 'macse', 'macsefd', 'macclasc', 'macii', 'mac2fdhd', 'macprtb', 'maciici', 'maciifx', 'maclc', 'maciisi', 'macpb100', 'macpb140', 'macclas2', 'maclc2', 'macpb160', 'macpd210', 'maccclas', 'maclc3', 'maciivx', 'maclc520', 'pmac6100', 'macqd700']

all_mame_drivers = [d for s in systems.values() for d in s.mame_drivers] + ibmpc_drivers + mac_drivers

#Things where I can't be fucked right now making a SystemInfo object:
#Altair 8800 (is 8800bt a different thing)
#TIC-80 (one of those non-existent systems) (Libretro dat: "TIC-80")
#TRS-80 Model 2 (trs80m2)
#TRS-80 MC-10 (mc10)
#Hitachi S1
#Virtual systems: TADS, Z-Machine, Adobe AIR
#Acorn System (acrnsys3, acrnsys5)
#Amstrad PC1512 (pc1512, pc1640)
#Indy (indy_4610, indigo2_4415)
#SSEM

#Confusing things:
#Which of TI calculators are software compatible with which (and hence which ones would be considered individual systems)?
	#TI-73, 81, 82, 83x, 84x, 85, 86 are Z80; 89, 92x are M68K
#Bandai Super Note Club (snotec, snotecu, snotecex): Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
#Amstrad PC20/Sinclair PC200: Is this just IBM PC compatible stuff? Have seen one demoscene prod which claims to be for it specifically
#Epoch (not Super) Cassette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
#DEC Rainbow: Uses DOS so maybe goes in pc_systems but maybe the CP/M part is its own thing

class PCSystem():
	def __init__(self, json_name, emulators, options=None):
		self.json_name = json_name
		self.emulators = emulators
		self.options = options if options else {}

pc_systems = {
	'Mac': PCSystem('mac', ['BasiliskII', 'SheepShaver']),
	'DOS': PCSystem('dos', ['DOSBox Staging', 'DOSBox-X'], {
		'use_directory_as_fallback_name': SystemConfigValue(ConfigValueType.Bool, False, 'Use base directory name for fallback name if you don\'t feel like providing a name in dos.json')
	}),
}
