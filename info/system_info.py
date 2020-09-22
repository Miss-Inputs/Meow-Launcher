import os

from common_paths import data_dir
from common_types import ConfigValueType, MediaType
from info.format_info import (atari_2600_cartridge_extensions, cdrom_formats,
                              commodore_cart_formats, commodore_disk_formats,
                              generic_cart_extensions, mame_floppy_formats)

class SystemConfigValue():
	#This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno
	def __init__(self, value_type, default_value, description):
		self.type = value_type
		self.default_value = default_value
		self.description = description

class SystemInfo():
	def __init__(self, mame_drivers, mame_software_lists, emulators, file_types=None, options=None, is_virtual=False):
		self.mame_drivers = mame_drivers #Parent drivers that represent this system
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators
		self.file_types = file_types if file_types else {}
		self.options = options if options else {}
		self.is_virtual = is_virtual #Maybe needs better name

	def is_valid_file_type(self, extension):
		return any([extension in extensions for _, extensions in self.file_types.items()])

	def get_media_type(self, extension):
		for media_type, extensions in self.file_types.items():
			if extension in extensions:
				return media_type
		return None

arabic_msx1_drivers = ['ax150', 'ax170', 'svi738ar']
japanese_msx1_drivers = ['fmx', 'mbh2', 'mbh25', 'mbh50', 'mlf110', 'mlf120', 'cf1200', 'cf2000', 'cf2700', 'cf3000', 'cf3300', 'fs1300', 'fs4000', 'mpc64', 'hb701fd', 'hc7', 'cx5f']
korean_msx1_drivers = ['cpc88', 'dpc200', 'gsfc80u', 'cpc51', 'gfc1080', 'gfc1080a', 'mx64']
other_msx1_drivers = ['svi728', 'svi738', 'canonv8', 'canonv20', 'mx10', 'pv7', 'pv16', 'dpc200e', 'dgnmsx', 'fdpc200', 'fpc500', 'fspc800', 'bruc100', 'gsfc200', 'jvchc7gb', 'mlf48', 'mlf80', 'mlfx1', 'phc2', 'phc28', 'cf2700g', 'perfect1', 'nms801', 'vg8010', 'vg802020', 'piopx7', 'spc800', 'mpc100', 'mpc200', 'phc28l', 'phc28s', 'mpc10', 'hb10p', 'hb101p', 'hb20p', 'hb201p', 'hb501p', 'hb55p', 'hb75p', 'hx10', 'hx20', 'cx5m128', 'yis303', 'yis503', 'yc64', 'expert13', 'expertdp', 'expertpl', 'hotbi13p'] #Anything that isn't one of those other three (which are apparently specifically different or needed in some cases)
working_msx1_drivers = other_msx1_drivers + arabic_msx1_drivers + japanese_msx1_drivers + korean_msx1_drivers
broken_msx1_drivers = ['hx21', 'hx22']
msx1_drivers = working_msx1_drivers + broken_msx1_drivers

arabic_msx2_drivers = ['ax350', 'ax370']
korean_msx2_drivers = ['cpc300', 'cpc300e', 'cpc330k', 'cpc400', 'cpc400s', 'cpc61']
japanese_msx2_drivers = ['kmc5000', 'mlg10', 'fs5500f2', 'fs4500', 'fs4700', 'fs5000', 'fs4600', 'fsa1a', 'fsa1mk2', 'fsa1f', 'fsa1fm', 'nms8250j', 'hbf500', 'hbf900a', 'hx33', 'yis604', 'phc23', 'phc55fd2', 'hbf1xd', 'hbf1xdm2']
other_msx2_drivers = ['canonv25', 'canonv30', 'fpc900', 'expert20', 'mlg1', 'mlg3', 'mlg30', 'nms8220a', 'vg8230', 'vg8235', 'vg8240', 'nms8245', 'nms8255', 'nms8280', 'mpc25fd', 'hx34i', 'fstm1', 'hbf5', 'hbf9p', 'hbf500p', 'hbf700p', 'hbg900ap', 'hbg900p', 'tpc310', 'tpp311', 'tps312', 'hx23i', 'cx7m128']
working_msx2_drivers = other_msx2_drivers + arabic_msx2_drivers + korean_msx2_drivers + japanese_msx2_drivers
broken_msx2_drivers = ['cpg120', 'y503iiir', 'y805256', 'mbh70', 'victhc95', 'hotbit20', 'mpc27', 'nms8260', 'mpc2300', 'mpc2500f', 'phc77', 'hbf1', 'hbf12']
msx2_drivers = working_msx2_drivers + broken_msx2_drivers

working_msx2plus_drivers = ['hbf1xv', 'fsa1fx', 'fsa1wxa', 'fsa1wsx', 'hbf1xdj', 'phc70fd2', 'phc35j', 'hbf9sp']
broken_msx2plus_drivers = ['expert3i', 'expert3t', 'expertac', 'expertdx']
msx2plus_drivers = working_msx2plus_drivers + broken_msx2plus_drivers

msxtr_drivers = ['fsa1gt', 'fsa1st'] #Neither of these are working

systems = {
	#Put all the "most normal people would be interested in" consoles up here, which is completely subjective and not even the same as my own personal view of notable, not to mention completely meaningless because it's a dict and the order shouldn't matter, and even if it did, ROMs are scanned in the order they're listed in systems.ini anyway. I guess it makes this a bit easier to read than having a huge wall of text though
	'3DS': SystemInfo([], [], ['Citra'], {MediaType.Cartridge: ['3ds'], MediaType.Digital: ['cxi'], MediaType.Executable: ['3dsx']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB 3dstdb.xml file (https://www.gametdb.com/3dstdb.zip)'),
	}),
	'Atari 2600': SystemInfo(['a2600'], ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)'], {MediaType.Cartridge: ['a26'] + atari_2600_cartridge_extensions + generic_cart_extensions}),
	'ColecoVision': SystemInfo(['coleco', 'bit90', 'czz50'], ['coleco'], ['MAME (ColecoVision)'], {MediaType.Cartridge: ['col'] + generic_cart_extensions}),
	'Dreamcast': SystemInfo(['dcjp', 'dcdev'], ['dc'], ['Reicast', 'Flycast', 'MAME (Dreamcast)'], {MediaType.OpticalDisc: cdrom_formats}),
	'DS': SystemInfo(['nds'], [], ['Medusa'], {MediaType.Cartridge: ['nds', 'dsi', 'ids']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB dstdb.xml file (https://www.gametdb.com/dstdb.zip)')
	}),
	'Game Boy': SystemInfo(['gameboy', 'gbcolor'], ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa', 'GBE+', 'bsnes'], {MediaType.Cartridge: ['gb', 'gbc', 'gbx', 'sgb']},
		{'super_game_boy_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to Super Game Boy BIOS to use'),
		'set_gbc_as_different_platform': SystemConfigValue(ConfigValueType.Bool, False, 'Set the platform of GBC games to Game Boy Color instead of leaving them as Game Boy'),
	}),
	'GameCube': SystemInfo(['gcjp'], [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'ciso', 'rvz'], MediaType.Executable: ['dol', 'elf']}),
	'Game Gear': SystemInfo(['gamegear'], ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'GBA': SystemInfo(['gba'], ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gba', 'bin', 'srl'], MediaType.Executable: ['elf', 'mb']}),
	'Intellivision': SystemInfo(['intv'], ['intv', 'intvecs'], ['MAME (Intellivision)'], {MediaType.Cartridge: ['bin', 'int', 'rom', 'itv']}),
	'Master System': SystemInfo(['sms'], ['sms'], ['Kega Fusion', 'Mednafen (Master System)', 'MAME (Master System)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'Mega Drive': SystemInfo(['genesis', 'gen_nomd'], ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)', 'MAME (Mega Drive)'], {MediaType.Cartridge: ['bin', 'gen', 'md', 'smd', 'sgd']}),
	'N64': SystemInfo(['n64'], ['n64'], ['Mupen64Plus', 'MAME (N64)'], {MediaType.Cartridge: ['z64', 'v64', 'n64', 'bin']}, 
		{'prefer_controller_pak_over_rumble': SystemConfigValue(ConfigValueType.Bool, True, 'If a game can use both the Controller Pak and the Rumble Pak, use the Controller Pak')
	}),
	'Neo Geo AES': SystemInfo(['aes'], ['neogoeo'], [], {MediaType.Cartridge: ['bin']}), #For software list usage
	'Neo Geo Pocket': SystemInfo(['ngp'], ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'], {MediaType.Cartridge: ['ngp', 'npc', 'ngc', 'bin']}),
	'NES': SystemInfo(['nes', 'famicom', 'iq501', 'sb486'], ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)', 'cxNES'], {MediaType.Cartridge: ['nes', 'unf', 'unif'], MediaType.Floppy: ['fds', 'qd']}, {
		'set_fds_as_different_platform': SystemConfigValue(ConfigValueType.Bool, False, 'Set the platform of FDS games to FDS instead of leaving them as NES'),
	}),
	'PC Engine': SystemInfo(['pce'], ['pce', 'sgx', 'tg16'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)', 'MAME (PC Engine)'], {MediaType.Cartridge: ['pce', 'sgx', 'bin']}),
	'PlayStation': SystemInfo(['psj'], ['psx'], ['Mednafen (PlayStation)', 'DuckStation', 'PCSX2'], {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: ['exe', 'psx']}, {
	}),
	'PS2': SystemInfo(['ps2'], [], ['PCSX2'], {MediaType.OpticalDisc: cdrom_formats + ['cso', 'bin'], MediaType.Executable: ['elf']}),
	'PS3': SystemInfo([], [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Digital: ['pkg'], MediaType.Executable: ['self', 'elf', 'bin']}),
	'PSP': SystemInfo([], [], ['PPSSPP'], {MediaType.OpticalDisc: cdrom_formats + ['cso'], MediaType.Executable: ['pbp']}),
	'Saturn': SystemInfo(['saturn'], ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)', 'MAME (Saturn)'], {MediaType.OpticalDisc: cdrom_formats}),
	'SNES': SystemInfo(['snes'], ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)', 'bsnes'], {MediaType.Cartridge: ['sfc', 'swc', 'smc', 'bs', 'st', 'bin']}, 
		{'sufami_turbo_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to Sufami Turbo BIOS, required to run Sufami Turbo carts'),
		'bsx_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to BS-X BIOS, required to run Satellaview games'),
	}),
	'Switch': SystemInfo([], [], ['Yuzu'], {MediaType.Cartridge: ['xci'], MediaType.Digital: ['nsp', 'nca'], MediaType.Executable: ['nro', 'nso', 'elf']}),
	'Virtual Boy': SystemInfo(['vboy'], ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'], {MediaType.Cartridge: ['vb', 'vboy', 'bin']}),
	'Vita': SystemInfo([], [], [], {MediaType.Digital: ['vpk']}),
	'Xbox': SystemInfo(['xbox'], [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xbe']}),
	'Xbox 360': SystemInfo([], [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xex']}),
	'Wii': SystemInfo([], [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'wbfs', 'ciso', 'wia', 'rvz'], MediaType.Executable: ['dol', 'elf'], MediaType.Digital: ['wad']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB wiitdb.xml file (https://www.gametdb.com/wiitdb.zip), note that GameCube will use this too!'),
		'common_key': SystemConfigValue(ConfigValueType.String, '', 'Wii common key used for decrypting Wii discs which some projects are brave enough to hardcode but I am not'),
	}),
	'Wii U': SystemInfo([], [], [], {MediaType.OpticalDisc: ['iso', 'wud'], MediaType.Executable: ['rpx', 'elf']}),
	'WonderSwan': SystemInfo(['wswan'], ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['ws', 'wsc', 'bin']}),
	
	#Less notable stuff goes here
	'3DO': SystemInfo(['3do'], [], ['MAME (3DO)'], {MediaType.OpticalDisc: cdrom_formats}),
	'3DO M2': SystemInfo([], ['3do_m2'], [], {MediaType.OpticalDisc: cdrom_formats}), #Was never actually released, but prototypes exist
	'Amiga CD32': SystemInfo(['cd32'], ['cd32'], ['FS-UAE', 'MAME (Amiga CD32)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Amstrad GX4000': SystemInfo(['gx4000'], ['gx4000'], ['MAME (Amstrad GX4000)'], {MediaType.Cartridge: ['cpr'] + generic_cart_extensions}),
	'APF-MP1000': SystemInfo(['apfm1000'], ['apfm1000'], ['MAME (APF-MP1000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Arcadia 2001': SystemInfo(['arcadia', 'intmpt03', 'orbituvi', 'ormatu', 'plldium'], ['arcadia'], ['MAME (Arcadia 2001)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Astrocade': SystemInfo(['astrocde'], ['astrocde'], ['MAME (Astrocade)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Atari 5200': SystemInfo(['a5200'], ['a5200'], ['MAME (Atari 5200)'], {MediaType.Cartridge: ['a52', 'car'] + generic_cart_extensions, MediaType.Tape: ['wav']}),
	'Atari 7800': SystemInfo(['a7800'], ['a7800'], ['A7800', 'MAME (Atari 7800)'], {MediaType.Cartridge: ['a78'] + generic_cart_extensions}),
	'Bandai Playdia': SystemInfo([], [], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Bandai Super Vision 8000': SystemInfo(['sv8000'], ['sv8000'], ['MAME (Bandai Super Vision 8000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'C2 Color': SystemInfo(['c2color'], ['c2color_cart'], ['MAME (C2 Color)'], {MediaType.Cartridge: ['bin']}),
	'Casio PV-1000': SystemInfo(['pv1000'], ['pv1000'], ['MAME (Casio PV-1000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Champion 2711': SystemInfo(['unichamp'], ['unichamp'], [], {MediaType.Cartridge: generic_cart_extensions}),
	'Channel F': SystemInfo(['channelf', 'channlf2'], ['channelf'], ['MAME (Channel F)'], {MediaType.Cartridge: ['chf', 'bin']}),
	'Coleco Telstar Arcade': SystemInfo([], [], [], {}),
	'CreatiVision': SystemInfo(['crvision', 'lasr2001', 'manager'], ['crvision', 'laser2001_cart'], ['MAME (CreatiVision)'], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav']}),
	'Dreamcast VMU': SystemInfo(['svmu'], ['svmu'], [], {MediaType.Executable: ['bin'], MediaType.Digital: ['vms']}),
	'Entex Adventure Vision': SystemInfo(['advision'], ['advision'], ['MAME (Entex Adventure Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Epoch Game Pocket Computer': SystemInfo(['gamepock'], ['gamepock'], ['MAME (Epoch Game Pocket Computer)'], {MediaType.Cartridge: ['bin']}),
	'G7400': SystemInfo(['g7400'], ['g7400'], ['MAME (G7400)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Gamate': SystemInfo(['gamate'], ['gamate'], ['MAME (Gamate)'], {MediaType.Cartridge: ['bin']}),
	'Game.com': SystemInfo(['gamecom'], ['gamecom'], ['MAME (Game.com)'], {MediaType.Cartridge: ['tgc', 'bin']}),
	'GameKing': SystemInfo(['gameking'], ['gameking'], ['MAME (GameKing)'], {MediaType.Cartridge: ['bin', 'gk']}),
	'GameKing 3': SystemInfo(['gamekin3'], ['gameking3'], ['MAME (GameKing 3)'], {MediaType.Cartridge: ['bin', 'gk3']}),
	'Gakken TV Boy': SystemInfo([], [], [], {}),
	'GoGo TV Video Vision': SystemInfo(['tvgogo'], ['tvgogo'], ['MAME (GoGo TV Video Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'GP2X': SystemInfo(['gp2x'], [], [], {}), #TODO: File formats and things
	'GP32': SystemInfo(['gp32'], ['gp32'], ['MAME (GP32)'], {MediaType.Cartridge: ['smc'], MediaType.Executable: ['gxb', 'sxf', 'bin', 'gxf', 'fxe']}),
	'Hartung Game Master': SystemInfo(['gmaster'], ['gmaster'], ['MAME (Hartung Game Master)'], {MediaType.Cartridge: ['bin']}),
	'Jaguar': SystemInfo(['jaguar'], ['jaguar'], ['MAME (Jaguar)'], {MediaType.Cartridge: ['j64', 'bin', 'rom'], MediaType.Executable: ['abs', 'cof', 'jag', 'prg']}),
	'Lynx': SystemInfo(['lynx'], ['lynx'], ['Mednafen (Lynx)', 'MAME (Lynx)'], {MediaType.Cartridge: ['lnx', 'lyx'], MediaType.Executable: ['o']}),
	'Magnavox Odyssey²': SystemInfo(['odyssey2'], ['odyssey2'], ['MAME (Magnavox Odyssey²)', 'MAME (G7400)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Mattel HyperScan': SystemInfo(['hyprscan'], ['hyperscan'], ['MAME (Mattel HyperScan)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Mega Duck': SystemInfo(['megaduck', 'mduckspa'], ['megaduck'], ['MAME (Mega Duck)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Microvision': SystemInfo(['microvsn'], ['microvision'], ['MAME (Microvision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Monon Color': SystemInfo(['mononcol'], ['monon_color'], ['MAME (Monon Color)'], {MediaType.Cartridge: ['bin']}),
	'Neo Geo CD': SystemInfo(['neocdz'], ['neocd'], ['MAME (Neo Geo CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Nuon': SystemInfo([], ['nuon'], [], {MediaType.OpticalDisc: ['iso']}),
	'PC-FX': SystemInfo(['pcfx'], ['pcfx'], ['Mednafen (PC-FX)'], {MediaType.OpticalDisc: cdrom_formats}),
	'PocketStation': SystemInfo(['pockstat'], [], [], {MediaType.Digital: ['gme']}),
	'Pokemon Mini': SystemInfo(['pokemini'], ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)'], {MediaType.Cartridge: ['min', 'bin']}),
	'RCA Studio 2': SystemInfo(['studio2'], ['studio2'], [], {MediaType.Cartridge: ['st2', 'bin', 'rom']}),
	'Select-a-Game': SystemInfo(['sag'], ['entex_sag'], ['MAME (Select-a-Game)'], {MediaType.Cartridge: ['bin']}),
	'SG-1000': SystemInfo(['sg1000', 'sc3000'], ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)'], {MediaType.Cartridge: ['sg', 'bin', 'sc'], MediaType.Tape: ['wav', 'bit'], MediaType.Floppy: mame_floppy_formats + ['sf', 'sf7']}),
	"Super A'Can": SystemInfo(['supracan'], ['supracan'], ["MAME (Super A'Can)"], {MediaType.Cartridge: ['bin']}),
	'Super Cassette Vision': SystemInfo(['scv'], ['scv'], ['MAME (Super Cassette Vision)'], {MediaType.Cartridge: ['bin']}),
	'VC 4000': SystemInfo(['vc4000', '1292apvs', 'database', 'elektor', 'h21', 'krvnjvtv', 'mpt05', 'rwtrntcs'], ['vc4000', 'database'], ['MAME (VC 4000)'], {MediaType.Cartridge: generic_cart_extensions}), #Which one is the "main" system, really, bit of a clusterfuck (well the software list is named vc4000 I guess)
	'Vectrex': SystemInfo(['vectrex'], ['vectrex'], ['MAME (Vectrex)'], {MediaType.Cartridge: ['vec', 'gam', 'bin']}),
	'Watara Supervision': SystemInfo(['svision'], ['svision'], ['MAME (Watara Supervision)'], {MediaType.Cartridge: ['ws', 'sv', 'bin']}),
	'ZAPit Game Wave': SystemInfo([], [], [], {MediaType.OpticalDisc: ['iso']}),
	'Zeebo': SystemInfo([], [], [], {}), #Folders with "mif" and "mod"?

	#Homebrew projects or whatever
	'Arduboy': SystemInfo([], [], [], {MediaType.Digital: ['arduboy'], MediaType.Executable: ['hex']}),
	'Uzebox': SystemInfo(['uzebox'], ['uzebox'], ['MAME (Uzebox)'], {MediaType.Executable: ['bin', 'uze']}),

	#Educational sort-of-game consoles
	'Advanced Pico Beena': SystemInfo(['beena'], ['sega_beena_cart'], ['MAME (Advanced Pico Beena)'], {MediaType.Cartridge: ['bin']}),
	'ClickStart': SystemInfo(['clikstrt'], ['clickstart_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Copera': SystemInfo(['copera'], ['copera'], ['MAME (Copera)'], {MediaType.Cartridge: ['bin', 'md']}), #Pico-related, but not quite the same (software will show warning message on Pico)
	'Didj': SystemInfo(['didj'], ['leapfrog_didj_cart'], ['MAME (Didj)'], {MediaType.Cartridge: generic_cart_extensions}),
	'LeapPad': SystemInfo(['leappad'], ['leapfrog_leappad_cart'], ['MAME (LeapPad)'], {MediaType.Cartridge: ['bin']}),
	'Leapster': SystemInfo(['leapster'], ['leapster'], ['MAME (Leapster)'], {MediaType.Cartridge: ['bin']}),
	'Little Touch LeapPad': SystemInfo(['ltleappad'], ['leapfrog_ltleappad_cart'], [], {MediaType.Cartridge: ['bin']}),
	'MobiGo': SystemInfo(['mobigo', 'mobigo2'], ['mobigo_cart'], ['MAME (MobiGo)'], {MediaType.Cartridge: ['bin']}),
	'My First LeapPad': SystemInfo(['mfleappad'], ['leapfrog_mfleappad_cart'], ['MAME (My First LeapPad)'], {MediaType.Cartridge: ['bin']}),
	'Sawatte Pico': SystemInfo(['sawatte'], ['sawatte'], [], {}),
	'Sega Pico': SystemInfo(['pico'], ['pico'], ['Kega Fusion', 'MAME (Sega Pico)'], {MediaType.Cartridge: ['bin', 'md']}),
	'SmarTV Adventures': SystemInfo(['smartvad'], ['smarttv_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Story Reader': SystemInfo(['pi_stry'], ['pi_storyreader_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Story Reader 2': SystemInfo(['pi_stry2'], ['pi_storyreader_v2_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Telestory': SystemInfo(['telestry'], ['telestory_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Tomy Prin-C': SystemInfo(['princ'], ['princ'], ['MAME (Tomy Prin-C)'], {MediaType.Cartridge: ['bin']}),
	'V.Reader': SystemInfo(['vreader'], ['vtech_storio_cart'], ['MAME (V.Reader)'], {MediaType.Cartridge: ['bin']}), 
	#Skeleton driver, apparently also known as Storio, or something like that
	'V.Smile Pro': SystemInfo(['vsmilpro'], ['vsmile_cd'], ['MAME (V.Smile Pro)'], {MediaType.OpticalDisc: cdrom_formats}),
	'V.Smile': SystemInfo(['vsmile'], ['vsmile_cart'], ['MAME (V.Smile)'], {MediaType.Cartridge: generic_cart_extensions}),
	'V.Smile Baby': SystemInfo(['vsmileb'], ['vsmileb_cart'], ['MAME (V.Smile Baby)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	'V.Smile Motion': SystemInfo(['vsmilem'], ['vsmilem_cart'], ['MAME (V.Smile Motion)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	'V.Tech Socrates': SystemInfo(['socrates'], ['socrates'], ['MAME (V.Tech Socrates)'], {MediaType.Cartridge: ['bin']}),
	
	#Consoles that barely count as consoles because aren't for gaming or whatever (or games push the definition), but for the purposes of creating a launcher, might as well be consoles
	'Action Max': SystemInfo([], [], [], {}),
	'Arcadia Skeet Shoot': SystemInfo([], [], [], {}), #VHS? At this point me putting this in here seems very much pointless (why did I do it? Am I just being a wanker? I guess my past self must have had some reason, surely)
	'BBC Bridge Companion': SystemInfo(['bbcbc'], ['bbcbc'], ['MAME (BBC Bridge Companion)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Benesse Pocket Challenge V2': SystemInfo([], ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['pc2', 'bin']}), #Sort of WonderSwan with different controls
	'Buzztime Home Trivia System':  SystemInfo(['buzztime'], ['buzztime_cart'], ['MAME (Buzztime Home Trivia System)'], {MediaType.Cartridge: ['bin']}),
	'Casio Loopy': SystemInfo(['casloopy'], ['casloopy'], ['MAME (Casio Loopy)'], {MediaType.Cartridge: ['bin']}),
	'Design Master Denshi Mangajuku': SystemInfo(['bdesignm'], ['bdesignm_design_cart', 'bdesignm_game_cart'], [], {MediaType.Cartridge: ['bin']}), #This will be interesting because you're supposed to use combinations of different design carts and game carts at the same time
	'Gachinko Contest! Slot Machine TV': SystemInfo(['gcslottv'], ['gcslottv'], ['MAME (Gachinko Contest! Slot Machine TV)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Koei PasoGo': SystemInfo(['pasogo'], ['pasogo'], ['MAME (Koei PasoGo)'], {MediaType.Cartridge: ['bin']}),
	'Konami Picno': SystemInfo(['picno', 'picno2'], ['picno'], ['MAME (Konami Picno)'], {MediaType.Cartridge: ['bin']}),
	'Mattel Juice Box': SystemInfo(['juicebox'], ['juicebox'], ['MAME (Mattel Juice Box)'], {MediaType.Cartridge: ['smc']}),
	'Nichibutsu My Vision': SystemInfo(['myvision'], ['myvision'], ['MAME (Nichibutsu My Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Pocket Challenge W': SystemInfo(['pockchal'], ['pockchalw'], ['MAME (Pocket Challenge W)'], {MediaType.Cartridge: ['bin', 'pcw']}),
	'Terebikko': SystemInfo([], [], [], {}), #VHS
	'Video Challenger': SystemInfo(['vidchal'], [], [], {}), #From hh_cop400.cpp comments: Needs screen, gun cursor, VHS player device, and software list for tapes; at the moment displays a score counter and has one button input (supposed to be the gun) which makes a "pew" sound
	'View-Master Interactive Vision': SystemInfo([], [], [], {}), #VHS

	#Multimedia consoles that also don't like to be classified as game consoles
	'CD-i': SystemInfo(['cdimono1', 'cdimono2', 'cdi490a', 'cdi910'], ['cdi'], ['MAME (CD-i)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Commodore CDTV': SystemInfo(['cdtv'], ['cdtv'], ['FS-UAE', 'MAME (Commodore CDTV)'], {MediaType.OpticalDisc: cdrom_formats}),	
	'Memorex VIS': SystemInfo(['vis'], [], ['MAME (Memorex VIS)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Pippin': SystemInfo(['pippin'], ['pippin', 'pippin_flop'], ['MAME (Pippin)'], {MediaType.OpticalDisc: cdrom_formats}),

	#Addons for other systems that we're going to treat as separate things because it seems to make more sense that way, until it doesn't
	'32X': SystemInfo(['32x'], ['32x'], ['Kega Fusion', 'MAME (32X)'], {MediaType.Cartridge: ['32x', 'bin']}),
	'64DD': SystemInfo(['n64dd'], ['n64dd'], [], {MediaType.Floppy: ['ndd', 'ddd']}),
	'e-Reader': SystemInfo(['gba'], ['gba_ereader'], [], {MediaType.Barcode: ['bin', 'raw', 'bmp']}),
	'Jaguar CD': SystemInfo(['jaguarcd'], [], ['MAME (Jaguar CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Mega CD': SystemInfo(['segacd', '32x_scd', 'cdx', 'segacd2', 'xeye', 'laseract'], ['megacd', 'megacdj', 'segacd'], ['Kega Fusion', 'MAME (Mega CD)'], {MediaType.OpticalDisc: cdrom_formats}), #LaserActive counts as this for now
	'PC Engine CD': SystemInfo(['pce'], ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Play-Yan': SystemInfo(['gba'], [], [], {MediaType.Digital: ['asf']}),

	#PDA type things that I don't really wanna put under computers
	'Cybiko': SystemInfo(['cybikov1'], [], [], {MediaType.Digital: ['app']}),
	#'Cybiko Xtreme': SystemInfo('cybikoxt', [], [], {MediaType.Digital: ['app']}), #Does this really qualify as a different thing?
	'Gizmondo': SystemInfo(['gizmondo'], [], [], {}), #Uses folders seemingly, so that may be weird with the file types
	'N-Gage': SystemInfo([], [], [], {MediaType.Digital: ['app']}),
	'Tapwave Zodiac': SystemInfo([], [], [], {}), #File type is like, kinda .prc but kinda not (the device runs spicy PalmOS, would it be considered part of that if any of that was emulated?)
	
	#Computers that most people are here for (wew I'm being subjective again)
	'Acorn Electron': SystemInfo(['electron'], ['electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl']}),
	'Amiga': SystemInfo(['a1000', 'a1200', 'a2000', 'a3000', 'a4000', 'a4000t', 'a500', 'a500p', 'a600'], ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'], ['FS-UAE'], {MediaType.Floppy: ['adf', 'ipf', 'dms']},
		{'default_chipset': SystemConfigValue(ConfigValueType.String, 'AGA', 'Default chipset to use if a game doesn\'t specify what chipset it should use (AGA, OCS, ECS)')
	}),
	'Amstrad CPC': SystemInfo(['cpc464'], ['cpc_cass', 'cpc_flop'], [], {MediaType.Snapshot: ['sna'], MediaType.Tape: ['wav', 'cdt'], MediaType.Floppy: mame_floppy_formats}),
	'Apple II': SystemInfo(['apple2', 'apple2c', 'apple2e', 'cece', 'cecg', 'ceci', 'cecm', 'cec2000'], ['apple2', 'apple2_cass', 'apple2_flop_orig', 'apple2_flop_clcracked', 'apple2_flop_misc'], ['MAME (Apple II)', 'Mednafen (Apple II)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz', 'shk', 'bxy'], MediaType.Tape: ['wav']}),
	'Apple IIgs': SystemInfo(['apple2gs'], ['apple2gs'], ['MAME (Apple IIgs)'], {MediaType.Floppy: mame_floppy_formats + ['2mg', '2img', 'dc', 'shk', 'bxy']}),
	'Atari 8-bit': SystemInfo(['a800', 'a400', 'a800xl', 'xegs'], ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)'], {MediaType.Floppy: ['atr', 'dsk', 'xfd', 'dcm'], MediaType.Executable: ['xex', 'bas', 'com'], MediaType.Cartridge: ['bin', 'rom', 'car'], MediaType.Tape: ['wav']}, 
		{'basic_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to BASIC ROM for floppy software which requires that, or use "basicc" to use software')
	}),
	'Atari ST': SystemInfo(['st', 'ste', 'tt030', 'falcon30'], ['st_flop', 'st_cart'], [], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats + ['st', 'stx', 'msa']}),
	'BBC Master': SystemInfo(['bbcm', 'bbcmc'], ['bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'ima', 'ufi', '360'] + mame_floppy_formats, MediaType.Cartridge: ['rom', 'bin']}),
	'BBC Micro': SystemInfo(['bbcb', 'bbcbp'], ['bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig', 'bbc_flop_65c102', 'bbc_flop_6502', 'bbc_flop_32016', 'bbc_flop_68000', 'bbc_flop_80186', 'bbc_flop_arm', 'bbc_flop_torch', 'bbc_flop_z80'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'dsk', 'ima', 'ufi', '360'], MediaType.Cartridge: ['rom', 'bin']}),
	'C64': SystemInfo(['c64'], ['c64_cart', 'c64_cass', 'c64_flop', 'c64_flop_clcracked', 'c64_flop_orig', 'c64_flop_misc'], ['MAME (C64)', 'VICE (C64)', 'VICE (C64 Fast)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}),
	'FM Towns': SystemInfo(['fmtowns', 'fmtmarty'], ['fmtowns_cd', 'fmtowns_flop'], ['MAME (FM Towns Marty)'], {MediaType.Floppy: mame_floppy_formats + ['bin'], MediaType.OpticalDisc: cdrom_formats}),
	'MSX': SystemInfo(msx1_drivers, ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions}),
	'MSX2': SystemInfo(msx2_drivers, ['msx2_cart', 'msx2_cass', 'msx2_flop'], ['MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions}),
	'MSX2+': SystemInfo(msx2plus_drivers, ['msx2p_flop'], ['MAME (MSX2+)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions}),
	'MSX Turbo-R': SystemInfo(msxtr_drivers, ['msxr_flop'], [], {MediaType.Floppy: mame_floppy_formats}),
	'PC-98': SystemInfo(['pc9801f', 'pc9801rs', 'pc9801ux', 'pc9821'], ['pc98', 'pc98_cd'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}),
	'Sharp X68000': SystemInfo(['x68000'], ['x68k_flop'], ['MAME (Sharp X68000)'], {MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim'], MediaType.HardDisk: ['hdf']}),
	'Tandy CoCo': SystemInfo(['coco'], ['coco_cart', 'coco_flop'], ['MAME (Tandy CoCo)'], {MediaType.Cartridge: ['ccc', 'rom', 'bin'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats + ['dmk', 'jvc'], MediaType.HardDisk: ['vhd']}),
	'TRS-80': SystemInfo(['trs80', 'trs80l2', 'trs80m3'], [], ['MAME (TRS-80)'], {MediaType.Executable: ['cmd'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: ['dmk'] + mame_floppy_formats}),
	'ZX Spectrum': SystemInfo(['spectrum', 'spec128'], ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)'], {MediaType.Snapshot: ['z80', 'sna'], MediaType.Tape: ['wav', 'cas', 'tap', 'tzx'], MediaType.Executable: ['raw', 'scr'], MediaType.Floppy: ['dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi', 'opd', 'opu'], MediaType.Cartridge: ['bin', 'rom']}), #There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

	#Other computers
	'Acorn Archimedes': SystemInfo(['aa310', 'aa4000', 'aa5000'], ['archimedes'], [], {MediaType.Floppy: mame_floppy_formats + ['adf']}), 
	'Acorn Atom': SystemInfo(['atom'], ['atom_cass', 'atom_flop', 'atom_rom'], [], {MediaType.Floppy: ['40t', 'dsk'], MediaType.Tape: ['wav', 'tap', 'csw', 'uef'], MediaType.Executable: ['atm'], MediaType.Cartridge: ['bin', 'rom']}),
	'Alice 32': SystemInfo(['alice32'], ['alice32', 'alice90'], [], {MediaType.Tape: ['wav', 'cas', 'c10', 'k7']}),
	'Amstrad PCW': SystemInfo(['pcw8256'], ['pcw'], ['MAME (Amstrad PCW)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['com']}),
	'Amstrad PCW16': SystemInfo(['pcw16'], ['pcw16'], [], {MediaType.Floppy: mame_floppy_formats}),
	'APF Imagination Machine': SystemInfo(['apfimag'], ['apfimag_cass', 'apfm1000'], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas', 'cpf', 'apt'], MediaType.Floppy: mame_floppy_formats}), #Considered separate from APF-M1000 (same predicament as Coleco Adam) (or is it? (maybe?))
	'Apogey BK-01': SystemInfo(['apogee'], ['apogee'], [], {MediaType.Tape: ['wav', 'rka']}), #Should this be rolled up into Radio 86?
	'Apple I': SystemInfo(['apple1'], ['apple1'], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['snp']}), #Loading tapes would require parsing software list usage to figure out where to put load addresses and things to make an autoboot script, because otherwise it's just way too messy to warrant being in a frontend. Snapshots supposedly exist, but I haven't seen any whoops
	'Apple III': SystemInfo(['apple3'], ['apple3'], ['MAME (Apple III)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz']}),
	'Apple Lisa': SystemInfo(['lisa', 'lisa2'], ['lisa'], [], {MediaType.Floppy: mame_floppy_formats + ['dc', 'dc42']}),
	'Atari Portfolio': SystemInfo(['pofo'], ['pofo'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	'Bandai RX-78': SystemInfo(['rx78'], ['rx78'], ['MAME (Bandai RX-78)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}),
	'C64DTV': SystemInfo(['c64dtv'], [], [], {MediaType.Floppy: commodore_disk_formats, MediaType.Executable: ['prg']}),
	'C128': SystemInfo(['c128', 'c128p'], ['c128_cart', 'c128_flop', 'c128_rom'], ['VICE (C128)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'Cambridge Z88': SystemInfo(['z88'], ['z88_cart'], [], {MediaType.Cartridge: ['epr', 'bin']}),
	'Camputers Lynx': SystemInfo(['lynx48k'], ['camplynx_cass', 'camplynx_flop'], [], {MediaType.Floppy: mame_floppy_formats + ['ldf'], MediaType.Tape: ['wav', 'tap']}),
	#Convinced that whoever invented this system and the way it loads programs personally hates me, even though I wasn't born when it was made and so that's not really possible
	'Casio PV-2000': SystemInfo(['pv2000'], ['pv2000'], ['MAME (Casio PV-2000)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'CBM-II': SystemInfo(['b128hp', 'b500', 'p500'], ['cbm2_cart', 'cbm2_flop'], [], {MediaType.Floppy: ['d80', 'd88', 'd77'] + mame_floppy_formats, MediaType.Cartridge: ['20', '40', '60'], MediaType.Executable: ['p00', 'prg', 't64']}),
	'Central Data 2650': SystemInfo(['cd2650'], [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'Coleco Adam': SystemInfo(['adam'], ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)'], {MediaType.Cartridge: ['col', 'bin'], MediaType.Tape: ['wav', 'ddp'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['lbr', 'com']}),
	'Colour Genie': SystemInfo(['cgenie'], ['cgenie_cass', 'cgenie_flop_rom'], [], {MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['rom']}),
	'Commodore 65': SystemInfo(['c65'], ['c65_flop'], [], {MediaType.Floppy: commodore_disk_formats}), #Never actually released, has software anyway; only good for software lists
	'Commodore PET': SystemInfo(['pet2001', 'cbm8296', 'pet2001b', 'pet2001n', 'pet4016', 'pet4032b', 'pet8032'], ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], ['VICE (Commodore PET)'], {MediaType.Floppy: commodore_disk_formats, MediaType.Cartridge: ['bin', 'rom'], MediaType.Executable: ['prg', 'p00'], MediaType.Tape: ['wav', 'tap']}),
	'Compis': SystemInfo(['compis'], ['compis'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'Dragon': SystemInfo(['dragon32'], ['dragon_cart', 'dragon_cass', 'dragon_flex', 'dragon_flop', 'dragon_os9'], [], {MediaType.Floppy: ['dmk', 'jvc', 'vdk', 'sdf', 'os9'] + mame_floppy_formats, MediaType.Cartridge: ['ccc', 'rom'], MediaType.Tape: ['wav', 'cas']}),
	'Electronika BK': SystemInfo(['bk0010'], ['bk0010'], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: mame_floppy_formats, MediaType.HardDisk: ['hdi'], MediaType.Executable: ['bin']}),
	'Enterprise': SystemInfo(['ep64'], ['ep64_cart', 'ep64_cass', 'ep64_flop'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav']}),
	'Exidy Sorcerer': SystemInfo(['sorcerer'], ['sorcerer_cart', 'sorcerer_cass', 'sorcerer_flop'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav', 'tape'], MediaType.Snapshot: ['snp']}),
	'FM-7': SystemInfo(['fm7', 'fm8', 'fm11', 'fm16beta'], ['fm7_cass', 'fm7_disk', 'fm77av'], ['MAME (FM-7)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav', 't77']}),
	'Galaksija': SystemInfo(['galaxy', 'galaxyp'], ['galaxy'], [], {MediaType.Snapshot: ['gal'], MediaType.Tape: ['wav', 'gtp']}),
	'Goldstar FC-100': SystemInfo(['fc100'], [], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas']}), #Some kind of PC-6001 clone or something, apparently
	'IBM PCjr': SystemInfo(['ibmpcjr', 'ibmpcjx'], ['ibmpcjr_cart'], ['MAME (IBM PCjr)'], {MediaType.Cartridge: ['bin', 'jrc'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#Most software is going to go under DOS or PC Booter, but this would be the carts… hmm… does this make sense, actually
	'Instructor 50': SystemInfo(['instruct'], [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'Interact': SystemInfo(['interact', 'hec2hrp'], ['interact'], [], {MediaType.Tape: ['wav', 'k7', 'cin', 'for']}),
	'Jupiter Ace': SystemInfo(['jupace'], ['jupace_snap', 'jupace_cass'], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Snapshot: ['ace']}),
	'KC-85': SystemInfo(['kc85_2'], ['kc_cart', 'kc_cass', 'kc_flop'], ['MAME (KC-85)'], {MediaType.Executable: ['kcc'], MediaType.Tape: ['wav', 'kcb', 'tap', '853', '854', '855', 'tp2', 'kcm', 'sss'], MediaType.Cartridge: ['bin']}), #kcc might also be a tape format?? ehhhh???
	'Luxor ABC80': SystemInfo(['abc80'], ['abc80_cass', 'abc80_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['bac']}), 'Mattel Aquarius': SystemInfo(['aquarius'], ['aquarius'], ['MAME (Mattel Aquarius)'], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav', 'caq']}),
	'Memotech MTX': SystemInfo(['mtx512'], ['mtx_cart', 'mtx_cass', 'mtx_rom'], [], {MediaType.Snapshot: ['mtx'], MediaType.Executable: ['run'], MediaType.Tape: ['wav'], MediaType.Cartridge: ['bin', 'rom']}),
	'Microbee': SystemInfo(['mbee'], [], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: [mame_floppy_formats], MediaType.Executable: ['mwb', 'com', 'bee']}), #Also a second .bin quickload?
	'Microtan 65': SystemInfo(['mt65'], ['mt65_snap'], ['MAME (Microtan 65)'], {MediaType.Tape: ['wav'], MediaType.Executable: ['hex'], MediaType.Snapshot: ['dmp', 'm65']}), #MAME driver was "microtan" prior to 0.212
	'Mikrosha': SystemInfo(['mikrosha'], ['mikrosha_cart', 'mikrosha_cass'], [], {MediaType.Tape: ['wav', 'rkm'], MediaType.Cartridge: ['bin', 'rom']}), #Maybe should just be part of Radio 86?
	'Nascom': SystemInfo(['nascom1', 'nascom2'], ['nascom_flop', 'nascom_snap', 'nascom_socket'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['nas', 'chr']}),
	'Oric': SystemInfo(['oric1'], [], [], {MediaType.Tape: ['wav', 'tap']}),
	'Orion-128': SystemInfo(['orion128'], ['orion_cart', 'orion_cass', 'orion_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi'], MediaType.Cartridge: ['bin']}),
	'Panasonic JR-200': SystemInfo(['jr200'], [], []),
	'Pasopia 7': SystemInfo(['pasopia7'], [], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),
	'Pasopia 1600': SystemInfo(['paso1600'], [], [], {}),
	'Partner 01.01': SystemInfo(['partner'], ['partner_cass', 'partner_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi']}), #Another Radio 86 clone?
	'PC Booter': SystemInfo(['ibm5150'], ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)'], {MediaType.Floppy: mame_floppy_formats + ['img'], MediaType.Executable: ['exe', 'com', 'bat']}), #TODO: Reconsider this name; does it make more sense to be called "IBM PC"? Are PCjr carts not just PC booters that are carts instead of floppies (hot take)?
	'PC-6001': SystemInfo(['pc6001'], [], ['MAME (PC-6001)'], {MediaType.Tape: ['cas', 'p6'], MediaType.Cartridge: generic_cart_extensions}),
	'PC-88': SystemInfo(['pc8801', 'pc88va'], ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'PDP-1': SystemInfo(['pdp1'], [], [], {MediaType.Tape: ['tap', 'rim']}),
	'Plus/4': SystemInfo(['c264'], ['plus4_cart', 'plus4_cass', 'plus4_flop'], ['VICE (Plus/4)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	), 	#Also includes C16 and C116 (I admit I am not cool enough to know the difference)
	'PipBug': SystemInfo(['pipbug'], [], [], {MediaType.Executable: ['pgm']}),
	'PMD 85': SystemInfo(['pmd851'], ['pmd85_cass'], [], {MediaType.Tape: ['wav', 'pmd', 'tap', 'ptp']}),
	'Radio 86-RK': SystemInfo(['radio86'], ['radio86_cart', 'radio86_cass'], [], {MediaType.Tape: ['wav', 'rk', 'rkr', 'gam', 'g16', 'pki']}),
	'Robotron Z1013': SystemInfo(['z1013'], [], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['z80']}),
	'SAM Coupe': SystemInfo(['samcoupe'], ['samcoupe_cass', 'samcoupe_flop'], ['SimCoupe', 'MAME (SAM Coupe)'], {MediaType.Floppy: ['mgt', 'sad', 'dsk', 'sdf'], MediaType.Executable: ['sbt']}),
	'Sharp MZ-700': SystemInfo(['mz700'], ['mz700'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sharp MZ-800': SystemInfo(['mz800', 'mz1500'], ['mz800'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sharp MZ-2000': SystemInfo(['mz2000', 'mz80b'], ['mz2000_cass', 'mz2000_flop', 'mz2200_cass'], ['MAME (Sharp MZ-2000)'], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt'], MediaType.Floppy: ['2d'] + mame_floppy_formats}),
	'Sharp X1': SystemInfo(['x1'], ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)'], {MediaType.Floppy: ['2d'] + mame_floppy_formats, MediaType.Tape: ['wav', 'tap']}),
	'Sinclair QL': SystemInfo(['ql', 'tonto'], ['ql_cart', 'ql_cass', 'ql_flop'], [], {MediaType.Tape: ['mdv'], MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats}),
	'Sony SMC-777': SystemInfo(['smc777'], ['smc777'], ['MAME (Sony SMC-777)'], {MediaType.Floppy: mame_floppy_formats + ['1dd'], MediaType.Executable: ['com', 'cpm']}),
	'Sord M5': SystemInfo(['m5'], ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)'], {MediaType.Cartridge: ['bin'], MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	'Squale': SystemInfo(['squale'], ['squale_cart'], ['MAME (Squale)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin']}),
	'SVI-3x8': SystemInfo(['svi318', 'svi328'], ['svi318_cart', 'svi318_cass', 'svi318_flop'], ['MAME (SVI-3x8)'], {MediaType.Tape: ['wav', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'Tandy MC-10': SystemInfo(['mc10'], ['mc10'], [], {MediaType.Tape: ['wav', 'cas', 'c10']}),
	'Thomson MO5': SystemInfo(['mo5', 'mo5nr'], ['mo5_cart', 'mo5_cass', 'mo5_flop', 'mo5_qd'], ['MAME (Thomson MO5)'], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}),
	'Thomson MO6': SystemInfo(['mo6'], ['mo6_cass', 'mo6_flop'], [], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}),
	'Thomson TO': SystemInfo(['to7', 'to770', 'to8', 'to9', 'to9p'], ['to7_cart', 'to7_cass', 'to7_qd', 'to8_cass', 'to8_qd', 'to770a_cart', 'to770_cart'], [], {MediaType.Tape: ['wav', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m7', 'bin', 'rom']}),
	'TI-99': SystemInfo(['ti99_4', 'ti99_4a', 'ti99_8'], ['ti99_cart'], [], {MediaType.Cartridge: ['bin', 'rpk', 'c', 'g'], MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),
	'Tomy Tutor': SystemInfo(['tutor'], ['tutor'], ['MAME (Tomy Tutor)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Toshiba Pasopia': SystemInfo(['pasopia'], ['pasopia_cass'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),	#Ow my freaking ears… every tape seems to take a long time to get anywhere
	'Vector-06C': SystemInfo(['vector06'], ['vector06_cart', 'vector06_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin', 'emr']}),
	'VIC-10': SystemInfo(['vic10'], ['vic10'], ['MAME (VIC-10)'], {MediaType.Cartridge: ['crt', 'bin', '80', 'e0'], MediaType.Tape: ['wav', 'tap', 't64']}),
	'VIC-20': SystemInfo(['vic1001'], ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)', 'VICE (VIC-20)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['wav', 'tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'Videoton TVC': SystemInfo(['tvc64'], ['tvc_cart', 'tvc_cass', 'tvc_flop'], ['MAME (Videoton TVC)'], {MediaType.Cartridge: ['bin', 'rom', 'crt'], MediaType.Tape: ['wav', 'cas']}), #.cas is also quickload? I donut understand
	'VideoBrain': SystemInfo(['vidbrain'], ['vidbrain'], ['MAME (VideoBrain)'], {MediaType.Cartridge: ['bin']}),
	'VZ-200': SystemInfo(['vz200', 'laser200', 'laser110', 'laser210', 'laser310'], ['vz_cass', 'vz_snap'], ['MAME (VZ-200)'], {MediaType.Snapshot: ['vz'], MediaType.Tape: ['wav', 'cas']}), #There are many different systems in this family, but I'll go with this one, because the software list is named after it
	'ZX81': SystemInfo(['zx81', 'zx80'], ['zx80_cass', 'zx81_cass'], [], {MediaType.Tape: ['wav', 'cas', 'p', '81', 'tzx']}),
	
	#Hmm, not quite computers or any particular hardware so much as OSes which probably don't belong here anyway
	'Android': SystemInfo([], [], [], {MediaType.Digital: ['apk']}),

	#Stuff that isn't actually hardware but we can pretend it is one
	'Doom': SystemInfo([], [], ['PrBoom+'], {MediaType.Digital: ['wad']}, {
		'save_dir': SystemConfigValue(ConfigValueType.FolderPath, None, 'Folder to put save files in')
	}, is_virtual=True),
}

#For Machine.is_system_driver to work correctly
ibmpc_drivers = ['ibm5150', 'ibm5170']
mac_drivers = ['mac128k', 'macplus', 'macse', 'macsefd', 'macclasc', 'macii', 'mac2fdhd', 'macprtb', 'maciici', 'maciifx', 'maclc', 'maciisi', 'macpb100', 'macpb140', 'macclas2', 'maclc2', 'macpb160', 'macpd210', 'maccclas', 'maclc3', 'maciivx', 'maclc520', 'pmac6100']

all_mame_drivers = [d for s in systems.values() for d in s.mame_drivers] + ibmpc_drivers + mac_drivers

#Things where I can't be fucked right now making a SystemInfo object:
#Altair 8800 (is 8800bt a different thing)
#TIC-80 (one of those non-existent systems)
#TRS-80 Model 2
#TRS-80 MC-10
#Hitachi S1
#Virtual systems: Flash, J2ME, TADS, Z-Machine (not that I have found cool emulators for any of that)
#Acorn System (acrnsys3, acrnsys5)
#Tatung Einstein (einstein, einst256)
#ETI-660
#Amstrad PC1512 (pc1512, pc1640)
#Hanimex Pencil II (pencil2)
#Indy (indy_4610, indigo2_4415)
#Tiki 100
#Cosmac VIP
#Wave Mate Bullet (wmbullet)
#Telcon Zorba
#Canon X07
#Elf II

#Confusing things:
#Which of TI calculators are software compatible with which (and hence which ones would be considered individual systems)?
	#TI-73, 81, 82, 83x, 84x, 85, 86 are Z80; 89, 92x are M68K
#Bandai Super Note Club (snotec, snotecu, snotecex): Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
#PalmOS: Not sure if there would be something which can just run .prc files or whatsitcalled
#Amstrad PC20/Sinclair PC200: Is this just IBM PC compatible stuff? Have seen one demoscene prod which claims to be for it specifically
#Epoch (not Super) Cassette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
#DEC Rainbow: Uses DOS so maybe goes in pc_systems but maybe the CP/M part is normal

class PCSystem():
	def __init__(self, options):
		self.options = options if options else {}

pc_systems = {
	'Mac': PCSystem({
		'shared_folder': SystemConfigValue(ConfigValueType.FolderPath, None, 'Path to shared folder on host that guest can see. This is mandatory for all this Mac stuff to work'),
		'default_width': SystemConfigValue(ConfigValueType.String, 1920, 'Emulated screen width to run at if a game doesn\'t need a specific screen resolution'), 'default_height': SystemConfigValue(ConfigValueType.String, 1080, 'Emulated screen height to run at if a game doesn\'t need a specific screen resolution')
	}),
	'DOS': PCSystem({
		'dosbox_configs_path': SystemConfigValue(ConfigValueType.FolderPath, os.path.join(data_dir, 'dosbox_configs'), 'Folder to store DOSBox per-application configuration files'),
	})
}
