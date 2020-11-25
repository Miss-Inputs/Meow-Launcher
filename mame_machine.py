import re

from common import (find_filename_tags_at_end, normalize_name,
                    remove_capital_article, remove_filename_tags)
from common_types import EmulationStatus
from config.main_config import main_config
from data.subtitles import subtitles
from info.system_info import all_mame_drivers
from mame_helpers import (consistentify_manufacturer, get_mame_xml,
                          list_by_source_file)
from mame_metadata import (add_metadata_from_catlist, get_machine_folder,
                           mame_statuses)
from metadata import Metadata


class MediaSlot():
	def __init__(self, xml):
		self.type = xml.attrib.get('type')
		self.tag = xml.attrib.get('tag')
		self.fixed_image = xml.attrib.get('fixed_image')
		self.mandatory = xml.attrib.get('mandatory', '0') == '1'
		self.interface = xml.attrib.get('interface')
		
		#This is the actual thing you see in -listmedia and use to insert media
		self.instances = [(instance_xml.attrib.get('name'), instance_xml.get('briefname')) for instance_xml in xml.findall('instance')]
		self.extensions = {extension_xml.attrib.get('name') for extension_xml in xml.findall('extension')}

arcade_system_names = {
	#Normal stuff
	'20pacgal': 'Namco Anniversary',
	'alien': 'Capcom Medalusion',
	'aristmk4': 'Aristocrat MK4', #Gambling
	'aristmk5': 'Aristocrat MK5', #Gambling, Acorn Archimedes based purrhaps
	'aristmk6': 'Aristocrat MK6', #Gambling
	'arsystems': 'Arcadia System', #Amiga 500 based
	'atarig1': 'Atari G1',
	'atarig42': 'Atari G42',
	'atarigt': 'Atari GT',
	'atarigx2': 'Atari GX2',
	'atarisy1': 'Atari System 1',
	'atarisy2': 'Atari System 2',
	'atarisy4': 'Atari System IV',
	'atlantis': 'Midway Atlantis', #Linux based (on MIPS CPU)
	'balsente': 'Bally/Sente SAC-1',
	'calchase': 'AUSCOM System 1', #PC (Windows 98, Cyrix 686MX + Trident TGUI9680) based
	'cedar_magnet': 'Cedar Magnet System',
	'chihiro': 'Chihiro', #Based on Xbox
	'circus': 'Exidy Universal Game Board v1',
	'cobra': 'Konami Cobra System',
	'coolridr': 'Sega System H1',
	'cps1': 'CPS-1',
	'cps2': 'CPS-2',
	'cps3': 'CPS-3',
	'csplayh5': 'Nichibutsu High Rate DVD',
	'cubo': 'Cubo CD32', #Amiga CD32 + JAMMA
	'cv1k': 'Cave CV1000B', #Also CV1000D (only differentiated by cv1k_d constructor)
	'cvs': 'Century CVS System',
	'deco156': 'Deco 156',
	'decocass': 'Deco Casette',
	'deco_mlc': 'Data East MLC System',
	'dgpix': 'dgPIX VRender0',
	'djmain': 'Bemani DJ Main', #Konami GX with hard drive
	'eolith': 'Eolith Gradation 2D System',
	'exidy440': 'Exidy 440',
	'exidy': 'Exidy Universal Game Board v2',
	'expro02': 'Kaneko EXPRO-02',
	'f-32': 'F-E1-32',
	'firebeat': 'Bemani Firebeat',
	'funworld': 'Fun World Series 7000',
	'fuukifg2': 'Fuuki FG-2',
	'fuukifg3': 'Fuuki FG-3',
	'gaelco2': 'Gaelco CG-1V/GAE1',
	'gammagic': 'Bally V8000', #Pentium PC based
	'ghosteo': 'Eolith Ghost',
	'hikaru': 'Sega Hikaru',
	'hng64': 'Hyper Neo Geo 64',
	'hornet': 'Konami Hornet',
	'iteagle': 'Incredible Technologies Eagle',
	'jaguar': 'Atari CoJag', #This is the same source file used for the Jaguar console too
	'jpmimpct': 'JPM Impact',
	'jpmsys5': 'JPM System 5',
	'konamigq': 'Konami GQ', #Based on PS1
	'konamigs': 'Konami GSAN1', 
	'konamigv': 'Konami GV', #Based on PS1
	'konamigx': 'Konami GX',
	'konamim2': 'Konami M2', #Based on unreleased Panasonic M2
	'konendev': 'Konami Endeavour', #Gambling
	'ksys573': 'Konami System 573', #Based on PS1
	'limenko': 'Limenko Power System 2',
	'lindbergh': 'Sega Lindbergh', #(modern) PC based
	'm107': 'Irem M107',
	'm52': 'Irem M52',
	'm58': 'Irem M58',
	'm62': 'Irem M62',
	'm63': 'Irem M63',
	'm72': 'Irem M72', #Also M81, M82, M84, M85
	'm90': 'Irem M90', #Also M97 I guess
	'm92': 'Irem M92',
	'macs': 'Multi Amenity Casette System',
	'maxaflex': 'Exidy Max-a-Flex', #Basically an Atari 600XL with ordinary Atari 8-bit games but coins purchase time. Weird maxaflex but okay
	'mcatadv': 'FACE Linda',
	'mcr3': 'Midway MCR-3', #Also "MCR-Scroll", "MCR-Monobard"
	'mcr68': 'Midway MCR-68k',
	'mediagx': 'Atari Media GX', #Based on Cyrix multimedia PC
	'megaplay': 'Mega-Play', #Megadrive based (home games converted to arcade format, coins buy lives)
	'megasys1': 'Jaleco Mega System 1',
	'megatech': 'Mega-Tech', #Megadrive games with timer
	'midas': 'Andamiro Midas',
	'midqslvr': 'Midway Quicksilver', #PC based
	'midtunit': 'Midway T-Unit',
	'midvunit': 'Midway V-Unit',
	'midwunit': 'Midway Wolf Unit', #Also known as W-Unit
	'midxunit': 'Midway X-Unit',
	'midyunit': 'Midway Y-Unit',
	'midzeus': 'Midway Zeus',
	'model1': 'Sega Model 1',
	'model2': 'Sega Model 2',
	'model3': 'Sega Model 3',
	'mquake': 'Bally/Sente SAC-III', #Amiga 500 based
	'ms32': 'Jaleco Mega System 32',
	'namcofl': 'Namco System FL',
	'namcona1': 'Namco System NA-1', #Also NA-2
	'namconb1': 'Namco System NB-1', #Also NB-2
	'namcond1': 'Namco System ND-1',
	'namcos10': 'Namco System 10', #Based on PS1
	'namcos11': 'Namco System 11', #Based on PS1
	'namcos12': 'Namco System 12', #Based on PS1
	'namcos1': 'Namco System 1',
	'namcos22': 'Namco System 22',
	'namcos23': 'Namco System 23', #Also Gorgon / "System 22.5"
	'namcos2': 'Namco System 2',
	'namcos86': 'Namco System 86',
	'neoprint': 'Neo Print',
	'nexus3d': 'Nexus 3D',
	'nss': 'Nintendo Super System', #SNES games with timer
	'nwk-tr': 'Konami NWK-TR',
	'pgm2': 'PolyGame Master 2',
	'pgm3': 'PolyGame Master 3',
	'pgm': 'PolyGame Master',
	'photon2': 'Photon IK-3', #Leningrad-1 based (Russian ZX Spectrum clone)
	'photon': 'Photon System', #PK8000 based (Russian PC that was supposed to be MSX1 compatible)
	'playch10': 'PlayChoice-10', #NES games with timer
	'plygonet': 'Konami Polygonet',
	'policetr': 'ATILLA Video System',
	'psikyo4': 'Psikyo PS4',
	'pyson': 'Konami Python', #Also called Pyson, I guess... Japan-English transliteration error? PS2 based
	'rastersp': 'Bell-Fruit/ATD RasterSpeed',
	'redalert': 'Irem M27',
	'seattle': 'Midway Seattle',
	'segaatom': 'Sega Atom',
	'segac2': 'Sega System C2', #Similar to Megadrive
	'segae': 'Sega System E', #Similar to Master System
	'segag80r': 'Sega G-80 Raster',
	'segag80v': 'Sega G-80 Vector',
	'segam1': 'Sega M1', #Gambling
	'segas16a': 'Sega System 16A', #Similar to Megadrive
	'segas18': 'Sega System 18',
	'segas24': 'Sega System 24',
	'segas32': 'Sega System 32',
	'segasp': 'Sega System SP', #Dreamcast based, for medal games
	'segaufo': 'Sega UFO Board', #Mechanical
	'segaxbd': 'Sega X-Board',
	'segaybd': 'Sega Y-Board',
	'seibucats': 'E-Touch Mahjong Series',
	'seibuspi': 'Seibu SPI',
	'sfcbox': 'Super Famicom Box', #Arcadified SNES sorta
	'sg1000a': 'Sega SG-1000', #Same hardware as the home system
	'shootaway2': 'Namco M74', #Mechanical?
	'simpl156': 'Deco Simple 156',
	'ssv': 'SSV', #Sammy Seta Visco
	'stv': 'Sega ST-V', #Based on Saturn
	'suprnova': 'Kaneko Super Nova System',
	'taitoair': 'Taito Air System',
	'taito_b': 'Taito B System',
	'taito_f2': 'Taito F2 System', #Also F1
	'taito_f3': 'Taito F3 System',
	'taitogn': 'Taito G-NET',
	'taito_h': 'Taito H System',
	'taitojc': 'Taito JC',
	'taito_l': 'Taito L System',
	'taito_o': 'Taito O System',
	'taitopjc': 'Taito Power-JC',
	'taitosj': 'Taito SJ',
	'taitotx': 'Taito Type X', #Modern PC based
	'taitotz': 'Taito Type-Zero', #PPC based
	'taitowlf': 'Taito Wolf', #3Dfx (Pentium) based
	'taito_x': 'Taito X System',
	'taito_z': 'Taito Z System',
	'tiamc1': 'TIA-MC1',
	'toypop': 'Namco System 16 Universal',
	'triforce': 'Triforce', #GameCube based
	'twin16': 'Konami Twin 16',
	'twinkle': 'Konami Bemani Twinkle', #PS1 based (but not System 573 related)
	'uapce': 'United Amusements PC Engine', #PC Engine with JAMMA connector
	'ultrsprt': 'Konami Ultra Sports',
	'vegaeo': 'Eolith Vega System',
	'vegas': 'Midway Vegas',
	'vicdual': 'VIC Dual',
	'vigilant': 'Irem M75', #Also M77 (maybe?)
	'viper': 'Konami Viper', #3Dfx (PPC) based
	'vsnes': 'VS Unisystem',
	'zr107': 'Konami ZR107',
	'namcos21': 'Namco System 21',
	'namcos21_c67': 'Namco System 21',
	'namcos21_de': 'Namco System 21', #Drivers Eyes
	
	#Not really names of arcade systems
	'megadriv_acbl': 'Mega Drive Bootleg', #Mega Drive based ofc
	'snesb': 'SNES Bootleg',
	'snesb51': 'SNES Bootleg',
	'pcxt': 'IBM PC-XT', #Games running off a PC-XT (mostly bootlegs, but not necessarily)
	'astrocde': 'Astrocade', #The home console used the same hardware, I can't remember the names of all the different things
	'cdi': 'Philips CD-i', #Literally a CD-i player with a JAMMA adapter (used for some quiz games)
	'cps1bl_pic': 'CPS-1 Bootleg with PIC',
	'cps1bl_5205': 'CPS-1 Bootleg',
	'vectrex': 'Vectrex', #Also used for actual Vectrex console
	'sms_bootleg': 'Master System Bootleg',

	#Pinned ball
	'de_3': 'Data East/Sega Version 3',
	'de_3b': 'Data East/Sega Version 3B',
	'gp_1': 'Game Plan MPU-1',
	'gts1': 'Gottlieb System 1',
	'gts3': 'Gottlieb System 3',
	'gts3a': 'Gottlieb System 3', #With dot matrix display
	'gts80a': 'Gottlieb System 80A',
	'pinball2k': 'Pinball 2000',
	's11b': 'Williams System 11B',
	'whitestar': 'Sega/Stern Whitestar',
	'white_mod': 'Sega/Stern Whitestar', #Modified
	'wpc_flip2': 'Williams WPC Flipstar 2',
	
	#Arcade platforms that don't have a name or anything, but companies consistently use them
	'alg': 'American Laser Games Hardware', #Amiga 500 based (w/ laserdisc player)
	'artmagic': 'Art & Magic Hardware',
	'atarittl': 'Atari TTL Hardware',
	'cave': 'Cave 68K Hardware',
	'cavepc': 'Cave PC Hardware', #Athlon 64 X2 + Radeon 3200 based
	'cinemat': 'Cinematronics Vector Hardware',
	'cmmb': 'Cosmodog Hardware',
	'dec0': 'Data East 16-bit Hardware', #Have heard some of these games called "Data East MEC-M1" but I dunno where that name comes from
	'deco32': 'Data East 32-bit Hardware', #Or "Data East ARM6", if you prefer
	'dec8': 'Data East 8-bit Hardware',
	'ettrivia': 'Enerdyne Technologies Trivia Hardware',
	'eolith16': 'Eolith 16-bit Hardware',
	'esd16': 'ESD 16-bit Hardware',
	'gaelco3d': 'Gaelco 3D Hardware',
	'gaelco': 'Gaelco Hardware', #Specifically from 1991-1996 apparently?
	'gameplan': 'Game Plan Hardware',
	'gottlieb': 'Gottlieb Hardware',
	'gei': 'Greyhound Electronics Hardware',
	'homedata': 'Home Data Hardware',
	'igs011': 'IGS011 Blitter Based Hardware',
	'itech32': 'Incredible Technologies 32-bit Blitter Hardware',
	'itech8': 'Incredible Technologies 8-bit Blitter Hardware',
	'kaneko16': 'Kaneko 16-bit Hardware',
	'konmedal': 'Konami Z80 Medal Games Hardware',
	'konmedal68k': 'Konami 68K Medal Games Hardware',
	'leland': 'Leland Hardware',
	'meadows': 'Meadows S2650 Hardware',
	'metro': 'Metro Hardware',
	'micro3d': 'Microprose 3D Hardware',
	'mw8080bw': 'Midway 8080 Black & White Hardware',
	'seta2': 'Newer Seta Hardware',
	'toaplan2': 'Newer Toaplan Hardware',
	'n8080': 'Nintendo 8080 Hardware',
	'nmk16': 'NMK 16-bit Hardware',
	'playmark': 'Playmark Hardware',
	'psikyo': 'Psikyo Hardware',
	'psikyosh': 'Psikyo SH-2 Hardware', #Psikyo PS3, PS5
	'dreamwld': 'Semicom 68020 Hardware',
	'seta': 'Seta Hardware',
	'simple_st0016': 'Seta ST-0016 Based Hardware',
	'snk68': 'SNK 68K Hardware',
	'alpha68k': 'SNK Alpha 68K Hardware',
	'snk': 'SNK Hardware',
	'statriv2': 'Status Trivia Hardware',
	'subsino2': 'Subsino Newer Tilemaps Hardware',
	'toaplan1': 'Toaplan Hardware',
	'unico': 'Unico Hardware',
	'williams': 'Williams 6809 Hardware',
	'yunsun16': 'Yun Sung 16 Bit Hardware',

	#Arcade platforms that don't really have a name except a game that uses them; I try not to fill this up with every single remaining source file, just where it's notable for having other games on it or some other reason (because it's based on a home console/computer perhaps, or because it's 3D or modern and therefore interesting), or maybe I do because I feel like it sometimes, oh well
	'8080bw': '8080 Black & White Hardware',
	'ambush': 'Ambush Hardware',
	'arkanoid': 'Arkanoid Hardware',
	'armedf': 'Armed Formation Hardware',
	'atetris': 'Atari Tetris Hardware',
	'backfire': 'Backfire! Hardware',
	'battlera': 'Battle Rangers Hardware', #PC Engine based
	'btoads': 'Battletoads Hardware',
	'beathead': 'Beathead Hardware',
	'realbrk': 'Billiard Academy Real Break Hardware',
	'bishi': 'Bishi Bashi Champ Hardware',
	'btime': 'BurgerTime Hardware',
	'cischeat': 'Cisco Heat Hardware',
	'coolpool': 'Cool Pool Hardware',
	'cclimber': 'Crazy Climber Hardware',
	'deshoros': 'Destiny Hardware',
	'ddenlovr': 'Don Den Lover Hardware',
	'dkong': 'Donkey Kong Hardware',
	'dkmb': 'Donkey Kong / Mario Bros Multigame Hardware',
	'ertictac': 'Erotictac Hardware', #Acorn Archimedes based
	'exterm': 'Exterminator Hardware',
	'fcrash': 'Final Crash Hardware', #Bootleg of Final Fight; this is used for other bootlegs too
	'galaga': 'Galaga Hardware',
	'ggconnie': 'Go! Go! Connie Hardware', #Supergrafx based
	'gstream': 'G-Stream G2020 Hardware',
	'gticlub': 'GTI Club Hardware',
	'segahang': 'Hang-On Hardware',
	'harddriv': "Hard Drivin' Hardware",
	'hshavoc': 'High Seas Havoc Hardware', #Megadrive based
	'kinst': 'Killer Instinct Hardware',
	'lastfght': 'Last Fighting Hardware',
	'lethalj': 'Lethal Justice Hardware',
	'liberate': 'Liberation Hardware',
	'macrossp': 'Macross Plus Hardware',
	'metalmx': 'Metal Maniax Hardware',
	'segaorun': 'Out Run Hardware',
	'pacman': 'Pac-Man Hardware',
	'pong': 'Pong Hardware',
	'qix': 'Qix Hardware',
	'quakeat': 'Quake Arcade Tournament Hardware', #Unknown PC based
	'qdrmfgp': 'Quiz Do Re Mi Fa Grand Prix Hardware',
	'raiden2': 'Raiden 2 Hardware',
	'rallyx': 'Rally-X Hardware',
	'ssfindo': 'See See Find Out Hardware', #RISC PC based
	'slapshot': 'Slap Shot Hardware',
	'snowbros': 'Snow Bros Hardware',
	'invqix': 'Space Invaders / Qix Silver Anniversary Edition Hardware',
	'pcat_nit': 'Street Games Hardware', #PC-AT 386 based
	'mappy': 'Super Pac-Man Hardware', #While the source file is called mappy, this seems to be more commonly known as the Super Pac-Man board
	'tvcapcom': 'Tatsunoko vs. Capcom Hardware', #Wii based
	'tetrisp2': 'Tetris Plus 2 Hardware',
	'tnzs': 'The NewZealand Story Hardware',
	'tmnt': 'TMNT Hardware',
	'tourtabl': 'Tournament Table Hardware', #Atari 2600 based
	'tumbleb': 'Tumble Pop Bootleg Hardware',
	'turrett': 'Turret Tower Hardware',
	'tx1': 'TX-1 Hardware',
	'vamphalf': 'Vamp x1/2 Hardware', #I guess the source file is for Hyperstone based games but I dunno if I should call it that
	'wheelfir': 'Wheels & Fire Hardware',
	'zaxxon': 'Zaxxon Hardware',
	'galaxian': 'Galaxian Hardware',
	'scramble': 'Galaxian Hardware',
	'galaxold': 'Galaxian Hardware', #Comment says it will be merged into galaxian one day

	#Multiple things stuffed into one source file, so there'd have to be something else to identify it (that isn't BIOS used) or it doesn't matter
	'm10': 'Irem M10/M11/M15',
	'mcr': 'Midway MCR-1/MCR-2',
	'namcops2': 'Namco System 246/256', #Based on PS2
	'system1': 'Sega System 1/2',
	'vp101': 'Play Mechanix VP50/VP100/VP101',
	'system16': 'Sega System 16/18 Bootleg',
}

arcade_system_bios_names = {
	('3do', '3dobios'): '3DO', #Used for the 3DO console as well, but there are 3DO-based arcade games with the system seemingly just called that; non-working
	('aleck64', 'aleck64'): 'Seta Aleck64', #N64 based
	('crystal', 'crysbios'): 'Brezzasoft Crystal System',
	('galgames', 'galgbios'): 'Galaxy Games',
	('naomi', 'naomi'): 'Naomi', #Dreamcast based
	('naomi', 'hod2bios'): 'Naomi',
	('naomi', 'f355dlx'): 'Naomi',
	('naomi', 'f355bios'): 'Naomi',
	('naomi', 'airlbios'): 'Naomi',
	('naomi', 'awbios'): 'Atomiswave',
	('naomi', 'naomi2'): 'Naomi 2',
	('naomi', 'naomigd'): 'Naomi GD-ROM',
	('nemesis', None): 'Nemesis Hardware',
	('nemesis', 'bubsys'): 'Konami Bubble System',
	('neogeo', 'neogeo'): 'Neo-Geo',
	('segas16b', None): 'Sega System 16B',
	('segas16b', 'isgsm'): 'ISG Selection Master Type 2006',
	('sigmab98', None): 'Sigma B-98',
	('sigmab98', 'sammymdl'): 'Sammy Medal Game System',
	('zn', 'coh1000a'): 'Acclaim PSX', #PS1 based
	('zn', 'coh1000c'): 'Capcom ZN1', #PS1 based
	('zn', 'coh1000t'): 'Taito FX1', #PS1 based, there are actually Taito FX-1A and Taito FX-1B
	('zn', 'coh1000w'): 'Atari PSX', #PS1 based, non-working
	('zn', 'coh1001l'): 'Atlus PSX', #PS1 based
	('zn', 'coh1002e'): 'PS Arcade 95', #PS1 based, used by Eighting/Raizing?
	('zn', 'coh1002m'): 'Tecmo TPS', #PS1 based
	('zn', 'coh1002v'): 'Video System PSX', #PS1 based
	('zn', 'coh3002c'): 'Capcom ZN2', #PS1 based
	('mpu4vid', 'v4bios'): 'MPU4 Video',

	('allied', 'allied'): 'Allied System',

	('3do', 'alg3do'): 'American Laser Games 3DO Hardware',

}

licensed_arcade_game_regex = re.compile(r'^(.+?) \((.+?) license\)$')
licensed_from_regex = re.compile(r'^(.+?) \(licensed from (.+?)\)$')
hack_regex = re.compile(r'^hack \((.+)\)$')
bootleg_with_publisher_regex = re.compile(r'^bootleg \((.+)\)$')
class Machine():
	def __init__(self, xml, init_metadata=False):
		self.xml = xml
		#This can't be a property because we might need to override it later, so stop trying to do that
		self.name = self.xml.findtext('description')

		cloneof = self.xml.attrib.get('cloneof')
		if cloneof:
			self.has_parent = True
			self.parent_basename = cloneof
		else:
			self.has_parent = False
			self.parent_basename = None
		self._parent = None #We will add this later when it is needed

		self.metadata = Metadata()
		self._has_inited_metadata = False
		add_metadata_from_catlist(self)
		self.arcade_system = arcade_system_names.get(self.source_file)
		if not self.arcade_system:
			self.arcade_system = arcade_system_bios_names.get((self.source_file, self.bios_basename))
		self.add_alternate_names()

		if init_metadata:
			self._add_metadata_fields()
	
	def add_alternate_names(self):
		if self.arcade_system in ('Space Invaders / Qix Silver Anniversary Edition Hardware', 'ISG Selection Master Type 2006', 'Cosmodog Hardware', 'Donkey Kong / Mario Bros Multigame Hardware') or self.basename == 'jak_hmhsm':
			#These don't use the / as a delimiter for alternate names, they're like two things in one or whatever
			return

		tags_at_end = find_filename_tags_at_end(self.name)
		name = remove_filename_tags(self.name)
		if ' / ' not in name:
			#We don't want to touch Blah (Fgsfds / Zzzz) (or bother trying to do something for a name that never had any / in it to begin with)
			return

		splitty_bois = name.split(' / ')
		primary_name = splitty_bois[0]
		alt_names = splitty_bois[1:]

		primary_name_tags = find_filename_tags_at_end(primary_name)
		if tags_at_end:
			if not primary_name_tags:
				#This stuff in brackets was probably a part of the whole thing, not the last alternate name
				primary_name += ' ' + ' '.join(tags_at_end)
				alt_names[-1] = remove_filename_tags(alt_names[-1])
			else:
				#The name is something like "aaa (bbb) / ccc (ddd)" so the (ddd) here actually belongs to the ccc, not the whole thing
				alt_names[-1] += ' ' + ' '.join(tags_at_end)

		for alt_name in alt_names:
			self.metadata.add_alternate_name(alt_name)
		
		self.name = primary_name

	def __str__(self):
		return self.name

	def _add_metadata_fields(self):
		self._has_inited_metadata = True
		self.metadata.specific_info['Source-File'] = self.source_file
		self.metadata.specific_info['Family-Basename'] = self.family
		self.metadata.specific_info['Family'] = self.family_name
		self.metadata.specific_info['Has-Parent'] = self.has_parent

		self.metadata.year = self.xml.findtext('year')

		self.metadata.specific_info['Number-of-Players'] = self.number_of_players
		self.metadata.specific_info['Is-Mechanical'] = self.is_mechanical
		self.metadata.specific_info['Dispenses-Tickets'] = self.uses_device('ticket_dispenser')
		self.metadata.specific_info['Coin-Slots'] = self.coin_slots
		self.metadata.specific_info['Requires-CHD'] = self.requires_chds
		self.metadata.specific_info['Romless'] = self.romless
		self.metadata.specific_info['Slot-Names'] = [slot.instances[0][0] for slot in self.media_slots if slot.instances]
		self.metadata.specific_info['Software-Lists'] = self.software_lists
		self.metadata.series = self.series
		bios = self.bios
		if bios:
			self.metadata.specific_info['BIOS-Used'] = bios.basename
			self.metadata.specific_info['BIOS-Used-Full-Name'] = bios.name
		if self.samples_used:
			self.metadata.specific_info['Samples-Used'] = self.samples_used
		arcade_system = self.arcade_system
		if arcade_system:
			self.metadata.specific_info['Arcade-System'] = arcade_system

		licensed_from = self.licensed_from
		if self.licensed_from:
			self.metadata.specific_info['Licensed-From'] = licensed_from

		hacked_by = self.hacked_by
		if self.hacked_by:
			self.metadata.specific_info['Hacked-By'] = hacked_by

		self.metadata.developer, self.metadata.publisher = self.developer_and_publisher

	@property
	def basename(self):
		return self.xml.attrib['name']

	@property
	def parent(self):
		if not self.has_parent:
			return None
			
		if not self._parent:
			self._parent = Machine(get_mame_xml(self.parent_basename), True)
		return self._parent

	@property
	def family(self):
		return self.parent_basename if self.has_parent else self.basename

	@property
	def family_name(self):
		return self.parent.name if self.has_parent else self.name
	
	@property
	def source_file(self):
		return self.xml.attrib['sourcefile'].rsplit('.', 1)[0]

	@property
	def is_mechanical(self):
		return self.xml.attrib.get('ismechanical', 'no') == 'yes'

	@property
	def input_element(self):
		return self.xml.find('input')

	@property
	def coin_slots(self):
		return self.input_element.attrib.get('coins', 0) if self.input_element is not None else 0

	@property
	def number_of_players(self):
		if self.input_element is None:
			#This would happen if we ended up loading a device or whatever, so let's not crash the whole dang program. Also, since you can't play a device, they have 0 players. But they won't have launchers anyway, this is just to stop the NoneType explosion.
			return 0
		return int(self.input_element.attrib.get('players', 0))

	@property
	def driver_element(self):
		return self.xml.find('driver')

	@property
	def overall_status(self):
		#Hmm, so how this works according to https://github.com/mamedev/mame/blob/master/src/frontend/mame/info.cpp: if any particular feature is preliminary, this is preliminary, if any feature is imperfect this is imperfect, unless protection = imperfect then this is preliminary
		#It even says it's for the convenience of frontend developers, but since I'm an ungrateful piece of shit and I always feel the need to take matters into my own hands, I'm gonna get the other parts of the emulation too
		if self.driver_element is None:
			return EmulationStatus.Unknown
		return mame_statuses.get(self.driver_element.attrib.get('status'), EmulationStatus.Unknown)

	@property
	def emulation_status(self):
		if self.driver_element is None:
			return EmulationStatus.Unknown
		return mame_statuses.get(self.driver_element.attrib.get('emulation'), EmulationStatus.Unknown)

	@property
	def feature_statuses(self):
		features = {}
		for feature in self.xml.findall('feature'):
			feature_type = feature.attrib['type']
			if 'status' in feature.attrib:
				feature_status = feature.attrib['status']
			elif 'overall' in feature.attrib:
				#wat?
				feature_status = feature.attrib['overall']
			else:
				continue
			
			features[feature_type] = feature_status
			#Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
			#Note: MAME 0.208 has added capture, media, tape, punch, drum, rom, comms; although because I have been somewhat clever in writing this code, I don't need to hardcode any of that anyway
		return features

	@property
	def is_skeleton_driver(self):
		#Actually, we're making an educated guess here, as MACHINE_IS_SKELETON doesn't appear directly in the XML...
		#What I actually want to happen is to tell us if a machine will just display a blank screen and nothing else (because nobody wants those in a launcher). Right now that's not really possible without the false positives of games which don't have screens as such but they do display things via layouts (e.g. wackygtr) so the best we can do is say everything that doesn't have any kind of controls, which tends to be the case for a lot of these.
		#MACHINE_IS_SKELETON is actually defined as MACHINE_NO_SOUND and MACHINE_NOT_WORKING, so we'll look for that too
		return self.number_of_players == 0 and self.emulation_status in (EmulationStatus.Broken, EmulationStatus.Unknown) and self.feature_statuses.get('sound') == 'unemulated'

	def uses_device(self, name):
		for device_ref in self.xml.findall('device_ref'):
			if device_ref.attrib['name'] == name:
				return True

		return False

	@property
	def requires_chds(self):
		#Hmm... should this include where all <disk> has status == "nodump"? e.g. Dragon's Lair has no CHD dump, would it be useful to say that it requires CHDs because it's supposed to have one but doesn't, or not, because you have a good romset without one
		#I guess I should have a look at how the MAME inbuilt UI does this
		#Who really uses this kind of thing, anyway?
		return self.xml.find('disk') is not None

	@property
	def romless(self):
		if self.requires_chds:
			return False
		if self.xml.find('rom') is None:
			return True

		for rom in self.xml.findall('rom'):
			if rom.attrib.get('status', 'good') != 'nodump':
				return False
		return True

	@property
	def bios_basename(self):
		romof = self.xml.attrib.get('romof')
		if self.has_parent and romof == self.family:
			return self.parent.bios_basename
		if romof:
			return romof
		return None

	@property
	def bios(self):
		bios_basename = self.bios_basename
		if bios_basename:
			return Machine(get_mame_xml(bios_basename), True)
		return None
		
	@property
	def samples_used(self):
		return self.xml.attrib.get('sampleof')

	@property
	def media_slots(self):
		return [MediaSlot(device_xml) for device_xml in self.xml.findall('device')]

	@property
	def has_mandatory_slots(self):
		return any(slot.mandatory for slot in self.media_slots)

	@property
	def software_lists(self):
		return [software_list.attrib.get('name') for software_list in self.xml.findall('softwarelist')]

	@property
	def manufacturer(self):
		return self.xml.findtext('manufacturer')

	@property
	def is_hack(self):
		return bool(self.hacked_by)

	@property
	def licensed_from(self):
		manufacturer = self.manufacturer
		if not manufacturer:
			return None
		licensed_from_match = licensed_from_regex.fullmatch(manufacturer)
		if licensed_from_match:
			return licensed_from_match[2]
		return None

	@property
	def hacked_by(self):
		manufacturer = self.manufacturer
		if not manufacturer:
			return None
		hack_match = hack_regex.fullmatch(manufacturer)
		if hack_match:
			return hack_match[1]
		return None

	@property
	def developer_and_publisher(self):
		if not self.manufacturer:
			#Not sure if this ever happens, but still
			return None, None

		license_match = licensed_arcade_game_regex.fullmatch(self.manufacturer)
		if license_match:
			developer = consistentify_manufacturer(license_match[1])
			if developer:
				developer = developer.replace(' / ', ', ')
			publisher = consistentify_manufacturer(license_match[2])
			return developer, publisher
	
		manufacturer = self.manufacturer
		licensed_from_match = licensed_from_regex.fullmatch(manufacturer)
		if licensed_from_match:
			manufacturer = licensed_from_match[1]
		
		bootleg_match = bootleg_with_publisher_regex.fullmatch(manufacturer)
		if manufacturer in ('bootleg', 'hack') or self.is_hack:
			if self.has_parent:
				developer = self.parent.metadata.developer
				publisher = self.parent.metadata.publisher
			else:
				developer = None #It'd be the original not-bootleg/hack game's developer but we can't get that programmatically without a parent etc
				publisher = None
		elif bootleg_match:
			developer = None
			if self.has_parent:
				developer = self.parent.metadata.developer
				publisher = self.parent.metadata.publisher
			
			publisher = consistentify_manufacturer(bootleg_match[1])
		else:
			if ' / ' in manufacturer:
				#Let's try and clean up things a bit when this happens
				manufacturers = [consistentify_manufacturer(m) for m in manufacturer.split(' / ')]
				if main_config.sort_multiple_dev_names:
					manufacturers.sort()

				developer = publisher = ', '.join(manufacturers)
				if len(manufacturers) == 2:
					#Try and figure out who's publisher / who's developer, if possible
					arcade_system = self.arcade_system
					if manufacturers[0] == 'bootleg':
						developer = publisher = manufacturers[1]
					elif manufacturers[1] == 'bootleg':
						developer = publisher = manufacturers[0]
					elif 'JAKKS Pacific' in manufacturers:
						#Needs to be a better way of what I'm saying, surely. I'm tired, so I can't boolean logic properly. It's just like… if the manufacturer is X / Y or Y / X, then the developer is X, and the publisher is Y
						#Anyway, we at least know that JAKKS Pacific is always the publisher in this scenario, so that cleans up the plug & play games a bit
						developer = manufacturers[0] if manufacturers[1] == 'JAKKS Pacific' else manufacturers[1]
						publisher = manufacturers[1] if manufacturers[1] == 'JAKKS Pacific' else manufacturers[0]
					elif 'Sega' in manufacturers and arcade_system and ('Sega' in arcade_system or 'Naomi' in arcade_system):
						#It would also be safe to assume Sega is not going to get someone else to be the publisher on their own hardware, I think; so in this case (manufacturer: Blah / Sega) we can probably say Blah is the developer and Sega is the publisher
						#I really really hope I'm not wrong about this assumption, but I want to make it
						developer = manufacturers[0] if manufacturers[1] == 'Sega' else manufacturers[1]
						publisher = manufacturers[1] if manufacturers[1] == 'Sega' else manufacturers[0]
					elif 'Capcom' in manufacturers and arcade_system and ('Capcom' in arcade_system):
						#Gonna make the same assumption here...
						developer = manufacturers[0] if manufacturers[1] == 'Capcom' else manufacturers[1]
						publisher = manufacturers[1] if manufacturers[1] == 'Capcom' else manufacturers[0]
					elif 'Namco' in manufacturers and arcade_system and ('Namco' in arcade_system):
						#And here, too
						developer = manufacturers[0] if manufacturers[1] == 'Namco' else manufacturers[1]
						publisher = manufacturers[1] if manufacturers[1] == 'Namco' else manufacturers[0]
					elif 'Sammy' in manufacturers and arcade_system and arcade_system == 'Atomiswave':
						developer = manufacturers[0] if manufacturers[1] == 'Sammy' else manufacturers[1]
						publisher = manufacturers[1] if manufacturers[1] == 'Sammy' else manufacturers[0]
					elif manufacturer == 'Rare / Electronic Arts':
						#Well at least we know what's going on in this case
						developer = 'Rare'
						publisher = 'Electronic Arts'

			else:
				developer = publisher = consistentify_manufacturer(manufacturer)
		return developer, publisher

	@property
	def series(self):
		serieses = get_machine_folder(self.basename, 'series')
		if serieses:
			#It is actually possible to have more than one series (e.g. invqix is both part of Space Invaders and Qix)
			#I didn't think this far ahead so just get the first one for now
			series = serieses[0]
			not_real_series = ('Hot', 'Aristocrat MK Hardware')

			if series.endswith(' * Pinball'):
				series = series[:-len(' * Pinball')]
			elif series.endswith(' * Slot'):
				series = series[:-len(' * Slot')]
			if series.startswith('The '):
				series = series[len('The '):]
			
			if series not in not_real_series:
				return remove_capital_article(series)
		return None
		
	@property
	def is_system_driver(self):
		return self.family in all_mame_drivers

	
def get_machine(driver):
	return Machine(get_mame_xml(driver))

def get_machines_from_source_file(source_file):
	for machine_name, source_file_with_ext in list_by_source_file():
		if source_file_with_ext.rsplit('.', 1)[0] == source_file:
			yield Machine(get_mame_xml(machine_name))

def machine_name_matches(machine_name, game_name, match_vs_system=False):
	#TODO Should also use name_consistency stuff once I refactor that (Turbo OutRun > Turbo Out Run)
	
	machine_name = remove_filename_tags(machine_name)
	game_name = remove_filename_tags(game_name)

	#Until I do mess around with name_consistency.ini though, here's some common substitutions
	machine_name = machine_name.replace('Bros.', 'Brothers')
	game_name = game_name.replace('Bros.', 'Brothers')
	machine_name = machine_name.replace('Jr.', 'Junior')
	game_name = game_name.replace('Jr.', 'Junior')

	if match_vs_system:
		if not machine_name.upper().startswith('VS. '):
			return False
		machine_name = machine_name[4:]

	if normalize_name(machine_name, False) == normalize_name(game_name, False):
		return True

	if machine_name in subtitles:
		if normalize_name(machine_name + ': ' + subtitles[machine_name], False) == normalize_name(game_name, False):
			return True
	elif game_name in subtitles:
		if normalize_name(game_name + ': ' + subtitles[game_name], False) == normalize_name(machine_name, False):
			return True
	return False

def does_machine_match_name(name, machine, match_vs_system=False):
	for machine_name in list(machine.metadata.names.values()) + [machine.name]:
		if machine_name_matches(machine_name, name, match_vs_system):
			return True
	return False

def does_machine_match_game(game_rom_name, game_metadata, machine, match_vs_system=False):
	for game_name in list(game_metadata.names.values()) + [game_rom_name]:
		#Perhaps some keys in game names don't need to be looked at here
		if does_machine_match_name(game_name, machine, match_vs_system):
			return True
	return False
