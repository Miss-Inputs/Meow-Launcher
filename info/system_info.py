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
	def __init__(self, mame_driver, mame_software_lists, emulators, file_types=None, options=None, is_virtual=False):
		self.mame_driver = mame_driver
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

systems = {
	#Put all the "most normal people would be interested in" consoles up here, which is completely subjective and not even the same as my own personal view of notable, not to mention completely meaningless because it's a dict and the order shouldn't matter, and even if it did, ROMs are scanned in the order they're listed in systems.ini anyway. I guess it makes this a bit easier to read than having a huge wall of text though
	'3DS': SystemInfo(None, [], ['Citra'], {MediaType.Cartridge: ['3ds'], MediaType.Digital: ['cxi'], MediaType.Executable: ['3dsx']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB 3dstdb.xml file (https://www.gametdb.com/3dstdb.zip)'),
	}),
	'Atari 2600': SystemInfo('a2600', ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)'], {MediaType.Cartridge: ['a26'] + atari_2600_cartridge_extensions + generic_cart_extensions}),
	'ColecoVision': SystemInfo('coleco', ['coleco'], ['MAME (ColecoVision)'], {MediaType.Cartridge: ['col'] + generic_cart_extensions}),
	'Dreamcast': SystemInfo('dc', ['dc'], ['Reicast', 'Flycast', 'MAME (Dreamcast)'], {MediaType.OpticalDisc: cdrom_formats}),
	'DS': SystemInfo('nds', [], ['Medusa'], {MediaType.Cartridge: ['nds', 'dsi', 'ids']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB dstdb.xml file (https://www.gametdb.com/dstdb.zip)')
	}),
	'Game Boy': SystemInfo('gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa', 'GBE+', 'bsnes'], {MediaType.Cartridge: ['gb', 'gbc', 'gbx', 'sgb']},
		{'super_game_boy_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to Super Game Boy BIOS to use'),
		'set_gbc_as_different_platform': SystemConfigValue(ConfigValueType.Bool, False, 'Set the platform of GBC games to Game Boy Color instead of leaving them as Game Boy'),
	}),
	'GameCube': SystemInfo('gcjp', [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'ciso', 'rvz'], MediaType.Executable: ['dol', 'elf']}),
	'Game Gear': SystemInfo('gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'GBA': SystemInfo('gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa', 'GBE+'], {MediaType.Cartridge: ['gba', 'bin', 'srl'], MediaType.Executable: ['elf', 'mb']}),
	'Intellivision': SystemInfo('intv', ['intv', 'intvecs'], ['MAME (Intellivision)'], {MediaType.Cartridge: ['bin', 'int', 'rom', 'itv']}),
	'Master System': SystemInfo('sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)', 'MAME (Master System)'], {MediaType.Cartridge: ['sms', 'gg', 'bin']}),
	'Mega Drive': SystemInfo('megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)', 'MAME (Mega Drive)'], {MediaType.Cartridge: ['bin', 'gen', 'md', 'smd', 'sgd']}),
	'N64': SystemInfo('n64', ['n64'], ['Mupen64Plus', 'MAME (N64)'], {MediaType.Cartridge: ['z64', 'v64', 'n64', 'bin']}, 
		{'prefer_controller_pak_over_rumble': SystemConfigValue(ConfigValueType.Bool, True, 'If a game can use both the Controller Pak and the Rumble Pak, use the Controller Pak')
	}),
	'Neo Geo AES': SystemInfo('aes', ['neogoeo'], [], {MediaType.Cartridge: ['bin']}), #For software list usage
	'Neo Geo Pocket': SystemInfo('ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'], {MediaType.Cartridge: ['ngp', 'npc', 'ngc', 'bin']}),
	'NES': SystemInfo('nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)', 'cxNES'], {MediaType.Cartridge: ['nes', 'unf', 'unif'], MediaType.Floppy: ['fds', 'qd']}, {
		'set_fds_as_different_platform': SystemConfigValue(ConfigValueType.Bool, False, 'Set the platform of FDS games to FDS instead of leaving them as NES'),
	}),
	'PC Engine': SystemInfo('pce', ['pce', 'sgx', 'tg16'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)', 'MAME (PC Engine)'], {MediaType.Cartridge: ['pce', 'sgx', 'bin']}),
	'PlayStation': SystemInfo('psj', ['psx'], ['Mednafen (PlayStation)', 'DuckStation', 'PCSX2'], {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: ['exe', 'psx']}, {
	}),
	'PS2': SystemInfo('ps2', [], ['PCSX2'], {MediaType.OpticalDisc: cdrom_formats + ['cso', 'bin'], MediaType.Executable: ['elf']}),
	'PS3': SystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Digital: ['pkg'], MediaType.Executable: ['self', 'elf', 'bin']}),
	'PSP': SystemInfo(None, [], ['PPSSPP'], {MediaType.OpticalDisc: cdrom_formats + ['cso'], MediaType.Executable: ['pbp']}),
	'Saturn': SystemInfo('saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)', 'MAME (Saturn)'], {MediaType.OpticalDisc: cdrom_formats}),
	'SNES': SystemInfo('snes', ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)', 'bsnes'], {MediaType.Cartridge: ['sfc', 'swc', 'smc', 'bs', 'st', 'bin']}, 
		{'sufami_turbo_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to Sufami Turbo BIOS, required to run Sufami Turbo carts'),
		'bsx_bios_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to BS-X BIOS, required to run Satellaview games'),
	}),
	'Switch': SystemInfo(None, [], ['Yuzu'], {MediaType.Cartridge: ['xci'], MediaType.Digital: ['nsp', 'nca'], MediaType.Executable: ['nro', 'nso', 'elf']}),
	'Virtual Boy': SystemInfo('vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'], {MediaType.Cartridge: ['vb', 'vboy', 'bin']}),
	'Vita': SystemInfo(None, [], [], {MediaType.Digital: ['vpk']}),
	'Xbox': SystemInfo('xbox', [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xbe']}),
	'Xbox 360': SystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso'], MediaType.Executable: ['xex']}),
	'Wii': SystemInfo(None, [], ['Dolphin'], {MediaType.OpticalDisc: ['iso', 'gcm', 'tgc', 'gcz', 'wbfs', 'ciso', 'wia', 'rvz'], MediaType.Executable: ['dol', 'elf'], MediaType.Digital: ['wad']}, {
		'tdb_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB wiitdb.xml file (https://www.gametdb.com/wiitdb.zip), note that GameCube will use this too!'),
		'common_key': SystemConfigValue(ConfigValueType.String, '', 'Wii common key used for decrypting Wii discs which some projects are brave enough to hardcode but I am not'),
	}),
	'Wii U': SystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso', 'wud'], MediaType.Executable: ['rpx', 'elf']}),
	'WonderSwan': SystemInfo('wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['ws', 'wsc', 'bin']}),
	#Rotates around so that sometimes the dpad becomes buttons and vice versa and there's like two dpads??? but if you use Mednafen's rotation auto-adjust thing it kinda works
	
	#Less notable stuff goes here
	'3DO': SystemInfo('3do', [], ['MAME (3DO)'], {MediaType.OpticalDisc: cdrom_formats}),
	'3DO M2': SystemInfo(None, ['3do_m2'], [], {MediaType.OpticalDisc: cdrom_formats}), #Was never actually released, but prototypes exist
	'Amiga CD32': SystemInfo('cd32', ['cd32'], ['FS-UAE', 'MAME (Amiga CD32)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Amstrad GX4000': SystemInfo('gx4000', ['gx4000'], ['MAME (Amstrad GX4000)'], {MediaType.Cartridge: ['cpr'] + generic_cart_extensions}),
	'APF-MP1000': SystemInfo('apfm1000', ['apfm1000'], ['MAME (APF-MP1000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Arcadia 2001': SystemInfo('arcadia', ['arcadia'], ['MAME (Arcadia 2001)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Astrocade': SystemInfo('astrocde', ['astrocde'], ['MAME (Astrocade)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Atari 5200': SystemInfo('a5200', ['a5200'], ['MAME (Atari 5200)'], {MediaType.Cartridge: ['a52', 'car'] + generic_cart_extensions, MediaType.Tape: ['wav']}),
	'Atari 7800': SystemInfo('a7800', ['a7800'], ['A7800', 'MAME (Atari 7800)'], {MediaType.Cartridge: ['a78'] + generic_cart_extensions}),
	'Bandai Playdia': SystemInfo(None, [], [], {MediaType.OpticalDisc: cdrom_formats}),
	'Bandai Super Vision 8000': SystemInfo('sv8000', ['sv8000'], ['MAME (Bandai Super Vision 8000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'C2 Color': SystemInfo('c2color', ['c2color_cart'], ['MAME (C2 Color)'], {MediaType.Cartridge: ['bin']}),
	'Casio PV-1000': SystemInfo('pv1000', ['pv1000'], ['MAME (Casio PV-1000)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Channel F': SystemInfo('channelf', ['channelf'], ['MAME (Channel F)'], {MediaType.Cartridge: ['chf', 'bin']}),
	'Coleco Telstar Arcade': SystemInfo(None, [], [], {}),
	'CreatiVision': SystemInfo('crvision', ['crvision'], ['MAME (CreatiVision)'], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav']}),
	'Dreamcast VMU': SystemInfo('svmu', ['svmu'], [], {MediaType.Executable: ['bin'], MediaType.Digital: ['vms']}),
	'Entex Adventure Vision': SystemInfo('advision', ['advision'], ['MAME (Entex Adventure Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Epoch Game Pocket Computer': SystemInfo('gamepock', ['gamepock'], ['MAME (Epoch Game Pocket Computer)'], {MediaType.Cartridge: ['bin']}),
	'G7400': SystemInfo('g7400', ['g7400'], ['MAME (G7400)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Gamate': SystemInfo('gamate', ['gamate'], ['MAME (Gamate)'], {MediaType.Cartridge: ['bin']}),
	'Game.com': SystemInfo('gamecom', ['gamecom'], ['MAME (Game.com)'], {MediaType.Cartridge: ['tgc', 'bin']}),
	'GameKing': SystemInfo('gameking', ['gameking'], ['MAME (GameKing)'], {MediaType.Cartridge: ['bin', 'gk']}),
	'GameKing 3': SystemInfo('gamekin3', ['gameking3'], ['MAME (GameKing 3)'], {MediaType.Cartridge: ['bin', 'gk3']}),
	'Gakken TV Boy': SystemInfo(None, [], [], {}),
	'GoGo TV Video Vision': SystemInfo('tvgogo', ['tvgogo'], ['MAME (GoGo TV Video Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'GP2X': SystemInfo('gp2x', [], [], {}), #TODO: File formats and things
	'GP32': SystemInfo('gp32', ['gp32'], ['MAME (GP32)'], {MediaType.Cartridge: ['smc'], MediaType.Executable: ['gxb', 'sxf', 'bin', 'gxf', 'fxe']}),
	'Hartung Game Master': SystemInfo('gmaster', ['gmaster'], ['MAME (Hartung Game Master)'], {MediaType.Cartridge: ['bin']}),
	'Jaguar': SystemInfo('jaguar', ['jaguar'], ['MAME (Jaguar)'], {MediaType.Cartridge: ['j64', 'bin', 'rom'], MediaType.Executable: ['abs', 'cof', 'jag', 'prg']}),
	'Lynx': SystemInfo('lynx', ['lynx'], ['Mednafen (Lynx)', 'MAME (Lynx)'], {MediaType.Cartridge: ['lnx', 'lyx'], MediaType.Executable: ['o']}),
	'Magnavox Odyssey²': SystemInfo('odyssey2', ['odyssey2'], ['MAME (Magnavox Odyssey²)', 'MAME (G7400)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Mattel HyperScan': SystemInfo('hyprscan', ['hyperscan'], ['MAME (Mattel HyperScan)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Mega Duck': SystemInfo('megaduck', ['megaduck'], ['MAME (Mega Duck)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Microvision': SystemInfo('microvsn', ['microvision'], ['MAME (Microvision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Monon Color': SystemInfo('mononcol', ['monon_color'], ['MAME (Monon Color)'], {MediaType.Cartridge: ['bin']}),
	'Neo Geo CD': SystemInfo('neocdz', ['neocd'], ['MAME (Neo Geo CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Nuon': SystemInfo(None, ['nuon'], [], {MediaType.OpticalDisc: ['iso']}),
	'PC-FX': SystemInfo('pcfx', ['pcfx'], ['Mednafen (PC-FX)'], {MediaType.OpticalDisc: cdrom_formats}),
	'PocketStation': SystemInfo('pockstat', [], [], {MediaType.Digital: ['gme']}),
	'Pokemon Mini': SystemInfo('pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)'], {MediaType.Cartridge: ['min', 'bin']}),
	'RCA Studio 2': SystemInfo('studio2', ['studio2'], [], {MediaType.Cartridge: ['st2', 'bin', 'rom']}), #This console sucks and I hate it, anyway; I'd need to make multiple autoboot scripts that press F3 and then combinations of buttons depending on software list > usage somehow? God fuck I hate this console so much. PAL games (and some homebrew stuff) need mpt02'Select-a-Game': SystemInfo('sag', ['entex_sag'], ['MAME (Select-a-Game)'], {MediaType.Cartridge: ['bin']}),
	'SG-1000': SystemInfo('sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)'], {MediaType.Cartridge: ['sg', 'bin', 'sc'], MediaType.Tape: ['wav', 'bit'], MediaType.Floppy: mame_floppy_formats + ['sf', 'sf7']}),
	"Super A'Can": SystemInfo('supracan', ['supracan'], ["MAME (Super A'Can)"], {MediaType.Cartridge: ['bin']}),
	'Super Cassette Vision': SystemInfo('scv', ['scv'], ['MAME (Super Cassette Vision)'], {MediaType.Cartridge: ['bin']}),
	'VC 4000': SystemInfo('vc4000', ['vc4000', 'database'], ['MAME (VC 4000)'], {MediaType.Cartridge: generic_cart_extensions}), #Which one is the "main" system, really, bit of a clusterfuck
	'Vectrex': SystemInfo('vectrex', ['vectrex'], ['MAME (Vectrex)'], {MediaType.Cartridge: ['vec', 'gam', 'bin']}),
	'Watara Supervision': SystemInfo('svision', ['svision'], ['MAME (Watara Supervision)'], {MediaType.Cartridge: ['ws', 'sv', 'bin']}),
	'ZAPit Game Wave': SystemInfo(None, [], [], {MediaType.OpticalDisc: ['iso']}),
	'Zeebo': SystemInfo(None, [], [], {}), #Folders with "mif" and "mod"?

	#Homebrew projects or whatever
	'Arduboy': SystemInfo(None, [], [], {MediaType.Digital: ['arduboy'], MediaType.Executable: ['hex']}),
	'Uzebox': SystemInfo('uzebox', ['uzebox'], ['MAME (Uzebox)'], {MediaType.Executable: ['bin', 'uze']}),

	#Educational sort-of-game consoles
	'Advanced Pico Beena': SystemInfo('beena', ['sega_beena_cart'], ['MAME (Advanced Pico Beena)'], {MediaType.Cartridge: ['bin']}),
	'ClickStart': SystemInfo('clikstrt', ['clickstart_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Copera': SystemInfo('copera', ['copera'], ['MAME (Copera)'], {MediaType.Cartridge: ['bin', 'md']}), #Pico-related, but not quite the same (software will show warning message on Pico)
	'Didj': SystemInfo('didj', ['leapfrog_didj_cart'], ['MAME (Didj)'], {MediaType.Cartridge: generic_cart_extensions}),
	'LeapPad': SystemInfo('leappad', ['leapfrog_leappad_cart'], ['MAME (LeapPad)'], {MediaType.Cartridge: ['bin']}),
	'Leapster': SystemInfo('leapster', ['leapster'], ['MAME (Leapster)'], {MediaType.Cartridge: ['bin']}),
	'Little Touch LeapPad': SystemInfo('ltleappad', ['leapfrog_ltleappad_cart'], [], {MediaType.Cartridge: ['bin']}),
	'MobiGo': SystemInfo('mobigo', ['mobigo_cart'], ['MAME (MobiGo)'], {MediaType.Cartridge: ['bin']}),
	'My First LeapPad': SystemInfo('mfleappad', ['leapfrog_mfleappad_cart'], ['MAME (My First LeapPad)'], {MediaType.Cartridge: ['bin']}),
	'Sawatte Pico': SystemInfo('sawatte', ['sawatte'], [], {}),
	'Sega Pico': SystemInfo('pico', ['pico'], ['Kega Fusion', 'MAME (Sega Pico)'], {MediaType.Cartridge: ['bin', 'md']}),
	'SmarTV Adventures': SystemInfo('smartvad', ['smarttv_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Story Reader': SystemInfo('pi_stry', ['pi_storyreader_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Story Reader 2': SystemInfo('pi_stry2', ['pi_storyreader_v2_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Telestory': SystemInfo('telestry', ['telestory_cart'], [], {MediaType.Cartridge: ['bin']}),
	'Tomy Prin-C': SystemInfo('princ', ['princ'], ['MAME (Tomy Prin-C)'], {MediaType.Cartridge: ['bin']}),
	'V.Reader': SystemInfo('vreader', ['vtech_storio_cart'], ['MAME (V.Reader)'], {MediaType.Cartridge: ['bin']}), 
	#Skeleton driver, apparently also known as Storio, or something like that
	'V.Smile Pro': SystemInfo('vsmilpro', ['vsmile_cd'], ['MAME (V.Smile Pro)'], {MediaType.OpticalDisc: cdrom_formats}),
	'V.Smile': SystemInfo('vsmile', ['vsmile_cart'], ['MAME (V.Smile)'], {MediaType.Cartridge: generic_cart_extensions}),
	'V.Smile Baby': SystemInfo('vsmileb', ['vsmileb_cart'], ['MAME (V.Smile Baby)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	'V.Smile Motion': SystemInfo('vsmilem', ['vsmilem_cart'], ['MAME (V.Smile Motion)'], {MediaType.Cartridge: ['bin', 'u1', 'u3']}),
	'V.Tech Socrates': SystemInfo('socrates', ['socrates'], ['MAME (V.Tech Socrates)'], {MediaType.Cartridge: ['bin']}),
	
	#Consoles that barely count as consoles because aren't for gaming or whatever (or games push the definition), but for the purposes of creating a launcher, might as well be consoles
	'Action Max': SystemInfo(None, [], [], {}),
	'Arcadia Skeet Shoot': SystemInfo(None, [], [], {}), #VHS? At this point me putting this in here seems very much pointless
	'BBC Bridge Companion': SystemInfo('bbcbc', ['bbcbc'], ['MAME (BBC Bridge Companion)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Benesse Pocket Challenge V2': SystemInfo(None, ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)'], {MediaType.Cartridge: ['pc2', 'bin']}), #Sort of WonderSwan with different controls
	'Buzztime Home Trivia System':  SystemInfo('buzztime', ['buzztime_cart'], ['MAME (Buzztime Home Trivia System)'], {MediaType.Cartridge: ['bin']}),
	'Casio Loopy': SystemInfo('casloopy', ['casloopy'], ['MAME (Casio Loopy)'], {MediaType.Cartridge: ['bin']}),
	'Design Master Denshi Mangajuku': SystemInfo('bdesignm', ['bdesignm_design_cart', 'bdesignm_game_cart'], [], {MediaType.Cartridge: ['bin']}), #This will be interesting because you're supposed to use combinations of different design carts and game carts at the same time
	'Gachinko Contest! Slot Machine TV': SystemInfo('gcslottv', ['gcslottv'], ['MAME (Gachinko Contest! Slot Machine TV)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Koei PasoGo': SystemInfo('pasogo', ['pasogo'], ['MAME (Koei PasoGo)'], {MediaType.Cartridge: ['bin']}),
	'Konami Picno': SystemInfo('picno', ['picno'], ['MAME (Konami Picno)'], {MediaType.Cartridge: ['bin']}),
	'Mattel Juice Box': SystemInfo('juicebox', ['juicebox'], ['MAME (Mattel Juice Box)'], {MediaType.Cartridge: ['smc']}),
	'Nichibutsu My Vision': SystemInfo('myvision', ['myvision'], ['MAME (Nichibutsu My Vision)'], {MediaType.Cartridge: generic_cart_extensions}),
	'Pocket Challenge W': SystemInfo('pockchal', ['pockchalw'], ['MAME (Pocket Challenge W)'], {MediaType.Cartridge: ['bin', 'pcw']}),
	'Terebikko': SystemInfo(None, [], [], {}), #VHS
	'Video Challenger': SystemInfo('vidchal', [], [], {}), #From hh_cop400.cpp comments: Needs screen, gun cursor, VHS player device, and software list for tapes; at the moment displays a score counter and has one button input (supposed to be the gun) which makes a "pew" sound
	'View-Master Interactive Vision': SystemInfo(None, [], [], {}), #VHS

	#Multimedia consoles that also don't like to be classified as game consoles
	'CD-i': SystemInfo('cdimono1', ['cdi'], ['MAME (CD-i)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Commodore CDTV': SystemInfo('cdtv', ['cdtv'], ['FS-UAE', 'MAME (Commodore CDTV)'], {MediaType.OpticalDisc: cdrom_formats}),	
	'Memorex VIS': SystemInfo('vis', [], ['MAME (Memorex VIS)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Pippin': SystemInfo('pippin', ['pippin', 'pippin_flop'], ['MAME (Pippin)'], {MediaType.OpticalDisc: cdrom_formats}),

	#Addons for other systems that we're going to treat as separate things because it seems to make more sense that way, until it doesn't
	'32X': SystemInfo('32x', ['32x'], ['Kega Fusion', 'MAME (32X)'], {MediaType.Cartridge: ['32x', 'bin']}),
	'64DD': SystemInfo('n64dd', ['n64dd'], [], {MediaType.Floppy: ['ndd', 'ddd']}),
	'e-Reader': SystemInfo('gba', ['gba_ereader'], [], {MediaType.Barcode: ['bin', 'raw', 'bmp']}),
	'Jaguar CD': SystemInfo('jaguarcd', [], ['MAME (Jaguar CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Mega CD': SystemInfo('megacdj', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion', 'MAME (Mega CD)'], {MediaType.OpticalDisc: cdrom_formats}),
	'PC Engine CD': SystemInfo('pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'], {MediaType.OpticalDisc: cdrom_formats}),
	'Play-Yan': SystemInfo('gba', [], [], {MediaType.Digital: ['asf']}),

	#PDA type things that I don't really wanna put under computers
	'Cybiko': SystemInfo('cybikov1', [], [], {MediaType.Digital: ['app']}),
	'Cybiko Xtreme': SystemInfo('cybikoxt', [], [], {MediaType.Digital: ['app']}),
	'Gizmondo': SystemInfo('gizmondo', [], [], {}), #Uses folders seemingly, so that may be weird with the file types
	'N-Gage': SystemInfo(None, [], [], {MediaType.Digital: ['app']}),
	'Tapwave Zodiac': SystemInfo(None, [], [], {}), #File type is like, kinda .prc but kinda not (the device runs spicy PalmOS, would it be considered part of that if any of that was emulated?)
	
	#Computers that most people are here for (wew I'm being subjective again)
	'Acorn Electron': SystemInfo('electron', ['electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl']}), #TODO Same Shift+Break shenanigans as BBC Micro
	'Amiga': SystemInfo('a500', ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'], ['FS-UAE'], {MediaType.Floppy: ['adf', 'ipf', 'dms']},
		{'default_chipset': SystemConfigValue(ConfigValueType.String, 'AGA', 'Default chipset to use if a game doesn\'t specify what chipset it should use (AGA, OCS, ECS)')
	}),
	'Apple II': SystemInfo('apple2', ['apple2', 'apple2_cass', 'apple2_flop_orig', 'apple2_flop_clcracked', 'apple2_flop_misc'], ['MAME (Apple II)', 'Mednafen (Apple II)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz', 'shk', 'bxy'], MediaType.Tape: ['wav']}),
	'Apple IIgs': SystemInfo('apple2gs', ['apple2gs'], ['MAME (Apple IIgs)'], {MediaType.Floppy: mame_floppy_formats + ['2mg', '2img', 'dc', 'shk', 'bxy']}),
	'Atari 8-bit': SystemInfo('a800', ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)'], {MediaType.Floppy: ['atr', 'dsk', 'xfd', 'dcm'], MediaType.Executable: ['xex', 'bas', 'com'], MediaType.Cartridge: ['bin', 'rom', 'car'], MediaType.Tape: ['wav']}, 
		{'basic_path': SystemConfigValue(ConfigValueType.FilePath, None, 'Path to BASIC ROM for floppy software which requires that, or use "basicc" to use software')
	}),
	'Atari ST': SystemInfo('st', ['st_flop', 'st_cart'], [], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats + ['st', 'stx', 'msa']}),
	'BBC Micro': SystemInfo('bbcb', ['bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig', 'bbc_flop_65c102', 'bbc_flop_6502', 'bbc_flop_32016', 'bbc_flop_68000', 'bbc_flop_80186', 'bbc_flop_arm', 'bbc_flop_torch', 'bbc_flop_z80'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'dsk', 'ima', 'ufi', '360'], MediaType.Cartridge: ['rom', 'bin']}), #TODO The key combination to boot a floppy is Shift+Break which is rather awkward to press, so I want an autoboot script
	'C64': SystemInfo('c64', ['c64_cart', 'c64_cass', 'c64_flop', 'c64_flop_clcracked', 'c64_flop_orig', 'c64_flop_misc'], ['MAME (C64)', 'VICE (C64)', 'VICE (C64 Fast)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}),
	'FM Towns': SystemInfo('fmtmarty', ['fmtowns_cd', 'fmtowns_flop'], ['MAME (FM Towns Marty)'], {MediaType.Floppy: mame_floppy_formats + ['bin'], MediaType.OpticalDisc: cdrom_formats}),
	#Not bothering adding the FM Towns Not-Marty MAME driver as it just makes some things not work (if they're non-bootable disks) #TODO: Add it coward
	'MSX': SystemInfo('svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX)', 'MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions}),
	'MSX2': SystemInfo('fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop', 'msx2p_flop'], ['MAME (MSX2)'], {MediaType.Floppy: mame_floppy_formats + ['dmk'], MediaType.Tape: ['wav', 'tap', 'cas'], MediaType.Cartridge: generic_cart_extensions}),
	'MSX Turbo-R': SystemInfo('fsa1st', ['msxr_flop'], [], {MediaType.Floppy: mame_floppy_formats}),
	'PC-98': SystemInfo('pc9801rs', ['pc98', 'pc98_cd'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}), #TODO This does somewhat work, but I probably want to filter out stuff that requires HDD install (only some stuff autoboots from floppy)
	'Sharp X68000': SystemInfo('x68000', ['x68k_flop'], ['MAME (Sharp X68000)'], {MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim'], MediaType.HardDisk: ['hdf']}),
	'Tandy CoCo': SystemInfo('coco3', ['coco_cart', 'coco_flop'], ['MAME (Tandy CoCo)'], {MediaType.Cartridge: ['ccc', 'rom', 'bin'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats + ['dmk', 'jvc'], MediaType.HardDisk: ['vhd']}),
	'TRS-80': SystemInfo('trs80l2', [], ['MAME (TRS-80)'], {MediaType.Executable: ['cmd'], MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: ['dmk'] + mame_floppy_formats}),
	'ZX Spectrum': SystemInfo('spectrum', ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)'], {MediaType.Snapshot: ['z80', 'sna'], MediaType.Tape: ['wav', 'cas', 'tap', 'tzx'], MediaType.Executable: ['raw', 'scr'], MediaType.Floppy: ['dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi', 'opd', 'opu'], MediaType.Cartridge: ['bin', 'rom']}),
	#Joystick interface is non-standard so not all games support it and might decide to use the keyboard instead, but eh. It works I guess.
	#There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

	#Other computers
	'Acorn Archimedes': SystemInfo('aa310', ['archimedes'], [], {MediaType.Floppy: mame_floppy_formats + ['adf']}), #TODO: Put MAME driver in there anyway, even if I need to click the thing
	'Alice 32': SystemInfo('alice32', ['alice32', 'alice90'], [], {MediaType.Tape: ['wav', 'cas', 'c10', 'k7']}),
	'Amstrad PCW': SystemInfo('pcw10', ['pcw'], ['MAME (Amstrad PCW)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['com']}),
	'Apogey BK-01': SystemInfo('apogee', ['apogee'], [], {MediaType.Tape: ['wav', 'rka']}),
	'Apple I': SystemInfo('apple1', ['apple1'], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['snp']}), #Loading tapes would require parsing software list usage to figure out where to put load addresses and things to make an autoboot script, because otherwise it's just way too messy to warrant being in a frontend. Snapshots supposedly exist, but I haven't seen any whoops
	'Apple III': SystemInfo('apple3', ['apple3'], ['MAME (Apple III)'], {MediaType.Floppy: ['do', 'dsk', 'po', 'nib', 'woz']}),
	'Apple Lisa': SystemInfo('lisa', ['lisa'], [], {MediaType.Floppy: mame_floppy_formats + ['dc', 'dc42']}),
	'Atari Portfolio': SystemInfo('pofo', ['pofo'], [], {MediaType.Cartridge: ['bin', 'rom']}),
	'Bandai RX-78': SystemInfo('rx78', ['rx78'], ['MAME (Bandai RX-78)'], {MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav']}),
	'C64DTV': SystemInfo('c64dtv', [], [], {MediaType.Floppy: commodore_disk_formats, MediaType.Executable: ['prg']}),
	'C128': SystemInfo('c128', ['c128_cart', 'c128_flop', 'c128_rom'], ['VICE (C128)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'Camputers Lynx': SystemInfo('lynx128k', ['camplynx_cass', 'camplynx_flop'], [], {MediaType.Floppy: mame_floppy_formats + ['ldf'], MediaType.Tape: ['wav', 'tap']}),
	#Convinced that whoever invented this system and the way it loads programs personally hates me, even though I wasn't born when it was made and so that's not really possible
	'Casio PV-2000': SystemInfo('pv2000', ['pv2000'], ['MAME (Casio PV-2000)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Coleco Adam': SystemInfo('adam', ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)'], {MediaType.Cartridge: ['col', 'bin'], MediaType.Tape: ['wav', 'ddp'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['lbr', 'com']}),
	'Commodore 65': SystemInfo('c65', ['c65_flop'], [], {MediaType.Floppy: commodore_disk_formats}), #Never actually released, has software anyway; only good for software lists
	'Commodore PET': SystemInfo('pet2001', ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], ['VICE (Commodore PET)'], {MediaType.Floppy: commodore_disk_formats, MediaType.Cartridge: ['bin', 'rom'], MediaType.Executable: ['prg', 'p00'], MediaType.Tape: ['wav', 'tap']}),
	#Unsure which one the "main" driver is, or if some of them count as separate systems...
	#TODO: This can work with MAME by using -quik and autoboot, and... there's cartridges? Huh?
	'Electronika BK': SystemInfo('bk0011m', ['bk0010'], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: mame_floppy_formats, MediaType.HardDisk: ['hdi'], MediaType.Executable: ['bin']}),
	'FM-7': SystemInfo('fm7', ['fm7_cass', 'fm7_disk', 'fm77av'], ['MAME (FM-7)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav', 't77']}),
	'Galaksija': SystemInfo('galaxyp', ['galaxy'], [], {MediaType.Snapshot: ['gal'], MediaType.Tape: ['wav', 'gtp']}), #This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why. Anyway, we'd go with those and make an autoboot script (maybe just -autoboot_command '\n' would work with suitable delay). galaxy is regular system, galaxyp is an upgraded one which appears to be completely backwards compatible
	'IBM PCjr': SystemInfo('ibmpcjr', ['ibmpcjr_cart'], ['MAME (IBM PCjr)'], {MediaType.Cartridge: ['bin', 'jrc'], MediaType.Floppy: mame_floppy_formats, MediaType.Executable: ['exe', 'com', 'bat']}),
	#Most software is going to go under DOS or PC Booter, but this would be the carts… hmm… does this make sense, actually
	'Interact': SystemInfo('interact', ['interact'], [], {MediaType.Tape: ['wav', 'k7', 'cin', 'for']}),
	'KC-85': SystemInfo('kc85_5', ['kc_cart', 'kc_cass', 'kc_flop'], ['MAME (KC-85)'], {MediaType.Executable: ['kcc'], MediaType.Tape: ['wav', 'kcb', 'tap', '853', '854', '855', 'tp2', 'kcm', 'sss'], MediaType.Cartridge: ['bin']}), #kcc might also be a tape format?? ehhhh???
	'Luxor ABC80': SystemInfo('abc80', ['abc80_cass', 'abc80_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['bac']}), #Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	'Mattel Aquarius': SystemInfo('aquarius', ['aquarius'], ['MAME (Mattel Aquarius)'], {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav', 'caq']}),
	'Microbee': SystemInfo('mbee', [], [], {MediaType.Tape: ['wav', 'tap'], MediaType.Floppy: [mame_floppy_formats], MediaType.Executable: ['mwb', 'com', 'bee']}), #Also a second .bin quickload?
	'Microtan 65': SystemInfo('mt65', ['mt65_snap'], ['MAME (Microtan 65)'], {MediaType.Tape: ['wav'], MediaType.Executable: ['hex'], MediaType.Snapshot: ['dmp', 'm65']}), #MAME driver was "microtan" prior to 0.212
	'Mikrosha': SystemInfo('mikrosha', ['mikrosha_cart', 'mikrosha_cass'], [], {MediaType.Tape: ['wav', 'rkm'], MediaType.Cartridge: ['bin', 'rom']}),
	'Oric': SystemInfo('orica', [], [], {MediaType.Tape: ['wav', 'tap']}),
	'Orion-128': SystemInfo('orion128', ['orion_cart', 'orion_cass', 'orion_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi'], MediaType.Cartridge: ['bin']}),
	'Panasonic JR-200': SystemInfo('jr200', [], []),
	'Partner 01.01': SystemInfo('partner', ['partner_cass', 'partner_flop'], [], {MediaType.Tape: ['wav', 'rkp'], MediaType.Floppy: mame_floppy_formats + ['odi']}),
	'PC Booter': SystemInfo('ibm5150', ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)'], {MediaType.Floppy: mame_floppy_formats + ['img'], MediaType.Executable: ['exe', 'com', 'bat']}), #TODO: Reconsider this name; does it make more sense to be called "IBM PC"? Are PCjr carts not just PC booters that are carts instead of floppies (hot take)?
	'PC-6001': SystemInfo('pc6001', [], ['MAME (PC-6001)'], {MediaType.Tape: ['cas', 'p6'], MediaType.Cartridge: generic_cart_extensions}),
	'PC-88': SystemInfo('pc8801', ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'PDP-1': SystemInfo('pdp1', [], [], {MediaType.Tape: ['tap', 'rim']}), #TODO autoboot script; MAME needs us to press control panel key + read in, and then it does the thing and all is well
	'Plus/4': SystemInfo('c16', ['plus4_cart', 'plus4_cass', 'plus4_flop'], ['VICE (Plus/4)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	), 	#Also includes C16 and C116 (I admit I am not cool enough to know the difference)
	'PMD 85': SystemInfo('pmd853', ['pmd85_cass'], [], {MediaType.Tape: ['wav', 'pmd', 'tap', 'ptp']}), #This has quite a few variants and apparently works, pmd85.cpp has todos/notes. Notably, floppy interface and speaker apparently not there yet. Anyway, boo tapes
	'Radio 86-RK': SystemInfo('radio86', ['radio86_cart', 'radio86_cass'], [], {MediaType.Tape: ['wav', 'rk', 'rkr', 'gam', 'g16', 'pki']}),
	'Robotron Z1013': SystemInfo('z1013', [], [], {MediaType.Tape: ['wav'], MediaType.Snapshot: ['z80']}),
	'SAM Coupe': SystemInfo('samcoupe', ['samcoupe_cass', 'samcoupe_flop'], ['SimCoupe', 'MAME (SAM Coupe)'], {MediaType.Floppy: ['mgt', 'sad', 'dsk', 'sdf'], MediaType.Executable: ['sbt']}),
	'Sharp MZ-700': SystemInfo('mz700', ['mz700'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sharp MZ-800': SystemInfo('mz800', ['mz800'], [], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt']}),
	'Sharp MZ-2000': SystemInfo('mz2000', ['mz2000_cass', 'mz2000_flop'], ['MAME (Sharp MZ-2000)'], {MediaType.Tape: ['wav', 'm12', 'mzf', 'mzt'], MediaType.Floppy: ['2d'] + mame_floppy_formats}),
	'Sharp X1': SystemInfo('x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)'], {MediaType.Floppy: ['2d'] + mame_floppy_formats, MediaType.Tape: ['wav', 'tap']}),
	'Sinclair QL': SystemInfo('ql', ['ql_cart', 'ql_cass', 'ql_flop'], [], {MediaType.Tape: ['mdv'], MediaType.Cartridge: ['bin', 'rom'], MediaType.Floppy: mame_floppy_formats}),
	'Sony SMC-777': SystemInfo('smc777', ['smc777'], ['MAME (Sony SMC-777)'], {MediaType.Floppy: mame_floppy_formats + ['1dd'], MediaType.Executable: ['com', 'cpm']}),
	'Sord M5': SystemInfo('m5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)'], {MediaType.Cartridge: ['bin'], MediaType.Floppy: mame_floppy_formats + ['xdf', 'hdm', '2hd', 'dim']}),
	'Squale': SystemInfo('squale', ['squale_cart'], ['MAME (Squale)'], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin']}),
	'SVI-3x8': SystemInfo('svi328', ['svi318_cart', 'svi318_cass', 'svi318_flop'], ['MAME (SVI-3x8)'], {MediaType.Tape: ['wav', 'cas'], MediaType.Cartridge: ['bin', 'rom']}),
	'Thomson MO5': SystemInfo('mo5', ['mo5_cart', 'mo5_cass', 'mo5_flop', 'mo5_qd'], ['MAME (Thomson MO5)'], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}),
	'Tomy Tutor': SystemInfo('tutor', ['tutor'], ['MAME (Tomy Tutor)'], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav']}),
	'Toshiba Pasopia': SystemInfo('pasopia', ['pasopia_cass'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),	#Ow my freaking ears… every tape seems to take a long time to get anywhere
	'VIC-10': SystemInfo('vic10', ['vic10'], ['MAME (VIC-10)'], {MediaType.Cartridge: ['crt', 'bin', '80', 'e0'], MediaType.Tape: ['wav', 'tap', 't64']}),
	'VIC-20': SystemInfo('vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)', 'VICE (VIC-20)'],
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: ['wav', 'tap', 't64'], MediaType.Executable: ['prg', 'p00'], MediaType.Floppy: commodore_disk_formats}
	),
	'Videoton TVC': SystemInfo('tvc64', ['tvc_cart', 'tvc_cass', 'tvc_flop'], ['MAME (Videoton TVC)'], {MediaType.Cartridge: ['bin', 'rom', 'crt'], MediaType.Tape: ['wav', 'cas']}), #.cas is also quickload? I donut understand
	'VideoBrain': SystemInfo('vidbrain', ['vidbrain'], ['MAME (VideoBrain)'], {MediaType.Cartridge: ['bin']}),
	'VZ-200': SystemInfo('vz200', ['vz_cass', 'vz_snap'], ['MAME (VZ-200)'], {MediaType.Snapshot: ['vz'], MediaType.Tape: ['wav', 'cas']}),
	#There are many different systems in this family, but I'll go with this one, because the software list is named after it
	'ZX81': SystemInfo('zx81', ['zx80_cass', 'zx81_cass'], [], {MediaType.Tape: ['wav', 'cas', 'p', '81', 'tzx']}),
	#Gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing baaggghghh which is why I haven't bothered trying more of this
	
	#Hmm, not quite computers or any particular hardware so much as OSes which probably don't belong here anyway
	'Android': SystemInfo(None, [], [], {MediaType.Digital: ['apk']}),

	#Stuff that isn't actually hardware but we can pretend it is one
	'Doom': SystemInfo(None, [], ['PrBoom+'], {MediaType.Digital: ['wad']}, {
		'save_dir': SystemConfigValue(ConfigValueType.FolderPath, None, 'Folder to put save files in')
	}, is_virtual=True),
}

#TODO: None of this stuff should be down here:
systems.update({	
	#TODO: Requires an autoboot script for these to work smoothly, or otherwise effort that I haven't done yet:
	'Cambridge Z88': SystemInfo('z88', ['z88_cart'], [], {MediaType.Cartridge: ['epr', 'bin']}),
	#Marked as not working due to missing expansion interface and serial port and other things, not sure how important that would be... anyway, I'd need to do an autoboot thing to press the key to start the thing, because otherwise it's annoying to navigate every time, and then... hmm, I guess I dunno what actually is a function of things not working yet
	'Thomson MO6': SystemInfo('mo6', ['mo6_cass', 'mo6_flop'], [], {MediaType.Tape: ['wav', 'k5', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m5', 'bin', 'rom']}),
	#MO6 is an upgraded model, Prodest PC 128 is an Italian MO6
	#Floppies work (and cassettes and carts have same problem as MO5), but this time we need to press the F1 key and I don't waaaanna do that myself
	'Thomson TO': SystemInfo('to8', ['to7_cart', 'to7_cass', 'to7_qd', 'to8_cass', 'to8_qd', 'to770a_cart', 'to770_cart'], [], {MediaType.Tape: ['wav', 'k7'], MediaType.Floppy: ['fd', 'sap', 'qd'] +  mame_floppy_formats, MediaType.Cartridge: ['m7', 'bin', 'rom']}),
	#Fuck I hate this. Carts need to press 1 on TO7 or press the button with the lightpen on TO8/9 and also they suck, floppies need BASIC cart inserted on TO7 (and then the same method to boot that cart) or press B on TO8/9, tapes are a shitload of fuck right now (same broken as MO5/MO6), not all of this seems to be cross compatible so might need to separate systems or work out what's going on there
	'TI-99': SystemInfo('ti99_4a', ['ti99_cart'], [], {MediaType.Cartridge: ['bin', 'rpk', 'c', 'g'], MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats}),
	#Carts need to press the any key and then 2 to actually load them. Floppies are the most asinine irritating thing ever fuck it
	#Actually if we can detect that a floppy has Extended BASIC autoboot that could work with an autoboot script in the same way that cartridges work
	
	#TODO: Things that I haven't been able to check work or not, or just haven't entirely:
	'Acorn Atom': SystemInfo('atom', ['atom_cass', 'atom_flop', 'atom_rom'], [], {MediaType.Floppy: ['40t', 'dsk'], MediaType.Tape: ['wav', 'tap', 'csw', 'uef'], MediaType.Executable: ['atm'], MediaType.Cartridge: ['bin', 'rom']}),
	'Amstrad CPC': SystemInfo('cpc464', ['cpc_cass', 'cpc_flop'], [], {MediaType.Snapshot: ['sna'], MediaType.Tape: ['wav', 'cdt'], MediaType.Floppy: mame_floppy_formats}),
	#The not-plus one (probably will need to switch to cpc664/cpc6128 for flopppy stuff)
	#CPC+: Use cpc6128p, this uses the gx4000 software list (as well as original cpc_cass and cpc_flop) so I should probably consider these to be the same platform
	'Amstrad PCW16': SystemInfo('pcw16', ['pcw16'], [], {MediaType.Floppy: mame_floppy_formats}),
	#Marked as MACHINE_NOT_WORKING and MAME pcw.cpp mentions needing an OS rescue disk, probably doesn't work conveniently or at all
	'APF Imagination Machine': SystemInfo('apfimag', ['apfimag_cass', 'apfm1000'], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas', 'cpf', 'apt'], MediaType.Floppy: mame_floppy_formats}),
	#Considered separate from APF-M1000 (same predicament as Coleco Adam)
	'BBC Master': SystemInfo('bbcm', ['bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'], [], {MediaType.Tape: ['wav', 'csw', 'uef'], MediaType.Floppy: ['ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'ima', 'ufi', '360'] + mame_floppy_formats, MediaType.Cartridge: ['rom', 'bin']}),
	'Exidy Sorcerer': SystemInfo('sorcerer', ['sorcerer_cart', 'sorcerer_cass', 'sorcerer_flop'],
		{MediaType.Cartridge: ['bin', 'rom'], MediaType.Tape: ['wav', 'tape'], MediaType.Snapshot: ['snp']}),
	#Would need automated tape loading to do anything interesting (carts and floppies are just BASIC/OS stuff, also what even is the file type for floppies?) hnmn
	'Goldstar FC-100': SystemInfo('fc100', [], [], {MediaType.Cartridge: ['bin'], MediaType.Tape: ['wav', 'cas']}), #No software list, some kind of PC-6001 clone or something, apparently
	'Memotech MTX': SystemInfo('mtx512', ['mtx_cart', 'mtx_cass', 'mtx_rom'], [], {MediaType.Snapshot: ['mtx'], MediaType.Executable: ['run'], MediaType.Tape: ['wav'], MediaType.Cartridge: ['bin', 'rom']}),
	'Vector-06C': SystemInfo('vector06', ['vector06_cart', 'vector06_flop'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['bin', 'emr']}),
	#MAME driver is marked as working but clones are not; needs to hold F2 then press F11 then F12 to boot from cartridge so that may be wacky; and I can't get that working, not sure if floppies/tapes do work
	'Tandy MC-10': SystemInfo('mc10', ['mc10'], [], {MediaType.Tape: ['wav', 'cas', 'c10']}),
	#Hmm... tapes...
	'Central Data 2650': SystemInfo('cd2650', [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'Instructor 50': SystemInfo('instruct', [], [], {MediaType.Tape: ['wav'], MediaType.Executable: ['pgm']}),
	'PipBug': SystemInfo('pipbug', [], [], {MediaType.Executable: ['pgm']}),
	'Nascom': SystemInfo('nascom2c', ['nascom_flop', 'nascom_snap', 'nascom_socket'], [], {MediaType.Tape: ['wav'], MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: ['nas', 'chr']}),
	#romimage1,2 = bin, rom as well (this is probably just related to nascom_socket and doesn't sound like the kind of thing we worry about around here)
	'Colour Genie': SystemInfo('cgenie', ['cgenie_cass', 'cgenie_flop_rom'], [], {MediaType.Tape: ['wav', 'cas'], MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: ['rom']}),
	'CBM-II': SystemInfo('cbm610', ['cbm2_cart', 'cbm2_flop'], [], {MediaType.Floppy: ['d80', 'd88', 'd77'] + mame_floppy_formats, MediaType.Cartridge: ['20', '40', '60'], MediaType.Executable: ['p00', 'prg', 't64']}),
	'Compis': SystemInfo('compis', ['compis'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: ['wav']}),
	'Enterprise': SystemInfo('ep128', ['ep64_cart', 'ep64_cass', 'ep64_flop'], [], {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: ['wav']}),
	#ugh don't like this one. Floppies need weirdness with both the actual thing itself and isdos from the software list and aaggh fuck off
	'Dragon 64': SystemInfo('dragon64', ['dragon_cart', 'dragon_cass', 'dragon_flex', 'dragon_flop', 'dragon_os9'], [], {MediaType.Floppy: ['dmk', 'jvc', 'vdk', 'sdf', 'os9'] + mame_floppy_formats, MediaType.Cartridge: ['ccc', 'rom'], MediaType.Tape: ['wav', 'cas']}),

	#Things where I can't be fucked right now making a SystemInfo object:
	#Altair 8800 (is 8800bt a different thing)
	#TIC-80 (one of those non-existent systems)
	#Sharp MZ-2200 (could be part of MZ-2000? If it's compatible with MZ-2000 software, just use it as the main system for both)
	#TRS-80 Model 3
	#TRS-80 MC-10
	#Hitachi S1
	#Virtual systems: Flash, J2ME, TADS, Z-Machine (not that I have found cool emulators for any of that)
	
	#Confusing things:
	#Which of TI calculators are software compatible with which (and hence which ones would be considered individual systems)?
		#TI-73, 81, 82, 83x, 84x, 85, 86 are Z80; 89, 92x are M68K
	#Bandai Super Note Club: Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
	#Jupiter Ace (ZX Spectrum clone but has different compatibility?)
	#PalmOS: Not sure if there would be something which can just run .prc files or whatsitcalled
	#Amstrad PC20/Sinclair PC200: Is this just IBM PC compatible stuff? Have seen one demoscene prod which claims to be for it specifically
	#Epoch (not Super) Cassette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
	#Pioneer LaserActive probably just counts as Mega CD and PC Engine CD except with Laserdisc instead of CD, but I'll worry about that when emulation for it becomes a thing
})

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
