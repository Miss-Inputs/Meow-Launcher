import configparser
import os

import input_metadata
from common import find_filename_tags, pluralize, remove_capital_article
from common_types import MediaType, SaveType
from config import main_config
from mame_helpers import find_cpus, get_mame_ui_config
from metadata import CPU, EmulationStatus, ScreenInfo
from region_detect import (get_language_by_english_name,
                           get_regions_from_filename_tags,
						   get_languages_from_regions)

#Maybe I just want to put all this back into mame_machines... it's only used there

mame_statuses = {
	'good': EmulationStatus.Good,
	'imperfect': EmulationStatus.Imperfect,
	'preliminary': EmulationStatus.Broken,
}

def get_mame_categories_folders():
	ui_config = get_mame_ui_config()
	return ui_config.settings.get('categorypath')

def get_machine_category(basename, category_name):
	mame_categories_folders = get_mame_categories_folders()
	if not mame_categories_folders:
		return None
	for folder in mame_categories_folders:
		category_file_path = os.path.join(folder, category_name + '.ini')

		parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
		parser.optionxform = str
		#This won't fail if category_file_path doesn't exist, so I guess it's fine
		parser.read(category_file_path)

		for section in parser.sections():
			if basename in parser[section]:
				#Dunno if it's a thing for MAME category .ini files to have multiple sections containing the same machine
				return section
	return None

def get_category(basename):
	cat = get_machine_category(basename, 'catlist')
	if not cat:
		return 'Unknown', 'Unknown', 'Unknown', False

	if ': ' in cat:
		category, _, genres = cat.partition(': ')
		genre, _, subgenre = genres.partition(' / ')
		is_nsfw = False
		if subgenre.endswith('* Mature *'):
			is_nsfw = True
			subgenre = subgenre[:-10]

		return category, genre, subgenre, is_nsfw

	genre, _, subgenre = cat.partition(' / ')
	return None, genre, subgenre, False

def get_language(basename):
	lang = get_machine_category(basename, 'languages')
	if not lang:
		return None

	return get_language_by_english_name(lang)

arcade_systems = {
	#Right now, this is kiinda pointless and only really used by 1) disambiguate 2) the user's own interest, but one day when there are non-MAME emulators in here, it would make sense for this list to be as big as it is and to expand it into full ArcadeSystem objects with more detailed info on which does what and have things that aren't just source file names mapped to each system and whatnot
	'20pacgal': 'Namco Anniversary',
	'3do': '3DO', #Used for the 3DO console as well, but there are 3DO-based arcade games which are just called that; non-working
	'aleck64': 'Seta Aleck64', #Based on N64
	'alien': 'Capcom Medalusion', #Non-working
	'aristmk5': 'Aristocrat MK5', #Gambling, Acorn Archimedes based purrhaps
	'aristmk6': 'Aristocrat MK6', #Gambling, non-working
	'arsystems': 'Arcadia System', #Amiga 500 based
	'astrocde': 'Astrocade', #The home console used the same hardware, I can't remember the names of all the different things
	'atarig1': 'Atari G1',
	'atarig42': 'Atari G42',
	'atarigt': 'Atari GT',
	'atarigx2': 'Atari GX2',
	'atarisy1': 'Atari System 1',
	'atarisy2': 'Atari System 2',
	'atarisy4': 'Atari System IV',
	'atlantis': 'Midway Atlantis', #Linux based (on MIPS CPU); claims to be skeleton but seems to work a bit anyway
	'balsente': 'Bally/Sente SAC-1',
	'cdi': 'Philips CD-i', #Literally a CD-i player with a JAMMA adapter (used for some quiz games)
	'cedar_magnet': 'Cedar Magnet System',
	'chihiro': 'Chihiro', #Based on Xbox, seemingly non-working
	'circus': 'Exidy Universal Game Board v1',
	'cobra': 'Konami Cobra System',
	'coolridr': 'Sega System H1',
	'cps1': 'CPS-1',
	'cps2': 'CPS-2',
	'cps3': 'CPS-3',
	'crystal': 'Brezzasoft Crystal System',
	'csplayh5': 'Nichibutsu High Rate DVD',
	'cubo': 'Cubo CD32', #Amiga CD32 + JAMMA
	'cv1k': 'Cave CV1000B', #Also CV1000D
	'cvs': 'Century CVS System',
	'dec0': 'Data East MEC-M1', #Or is it just "Data East 16-bit Hardware"?
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
	'firebeat': 'Bemani Firebeat', #Non-working
	'funworld': 'Fun World Series 7000',
	'fuukifg2': 'Fuuki FG-2',
	'fuukifg3': 'Fuuki FG-3',
	'gaelco2': 'Gaelco CG-1V/GAE1',
	'gammagic': 'Bally V8000', #Pentium PC based, skeleton
	'gts1': 'Gottlieb System 1', #Pinball, I think?
	'hikaru': 'Sega Hikaru', #Based on souped up Naomi and in turn Dreamcast, non-working
	'hng64': 'Hyper Neo Geo 64', #Barely working
	'hornet': 'Konami Hornet',
	'igs011': 'IGS011 Blitter Based Hardware',
	'jaguar': 'Atari CoJag', #This is the same source file used for the Jaguar console too
	'konamigq': 'Konami GQ', #Based on PS1
	'konamigv': 'Konami GV', #Based on PS1
	'konamigx': 'Konami GX',
	'konamim2': 'Konami M2', #Based on unreleased Panasonic M2
	'ksys573': 'Konami System 573', #Based on PS1
	'lindbergh': 'Sega Lindbergh', #(modern) PC based, very non-working
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
	'megadriv_acbl': 'Mega Drive Bootleg', #Mega Drive based ofc
	'megasys1': 'Jaleco Mega System 1',
	'midqslvr': 'Midway Quicksilver', #PC based, non-working
	'midtunit': 'Midway T-Unit',
	'midvunit': 'Midway V-Unit',
	'midwunit': 'Midway Wolf Unit', #Also known as W-Unit
	'midxunit': 'Midway X-Unit',
	'midyunit': 'Midway Y-Unit',
	'midzeus': 'Midway Zeus',
	'model1': 'Sega Model 1',
	'model2': 'Sega Model 2', #Barely working
	'model3': 'Sega Model 3', #Non-working
	'mquake': 'Bally/Sente SAC-III', #Amiga 500 based
	'ms32': 'Jaleco Mega System 32',
	'namcofl': 'Namco System FL',
	'namcona1': 'Namco System NA-1', #Also NA-2
	'namconb1': 'Namco System NB-1', #Also NB-2
	'namcond1': 'Namco System ND-1',
	'namcos10': 'Namco System 10', #Based on PS1; seems this one isn't working as much as the other PS1 derivatives?
	'namcos11': 'Namco System 11', #Based on PS1
	'namcos12': 'Namco System 12', #Based on PS1
	'namcos1': 'Namco System 1',
	'namcos21_c67': 'Namco System 21', #With C67 DSP
	'namcos21': 'Namco System 21',
	'namcos22': 'Namco System 22',
	'namcos23': 'Namco System 23', #Also Gorgon / "System 22.5"; not really working yet
	'namcos2': 'Namco System 2',
	'namcos86': 'Namco System 86',
	'naomi': 'Naomi', #Based on Dreamcast. romof="awbios" == Atomiswave; not entirely working
	'neogeo': 'Neo-Geo',
	'neoprint': 'Neo Print',
	'nwk-tr': 'Konami NWK-TR',
	'pcxt': 'IBM PC-XT', #Games running off a PC-XT (mostly bootlegs, but not necessarily)
	'pgm2': 'PolyGame Master 2',
	'pgm3': 'PolyGame Master 3', #Non-working
	'pgm': 'PolyGame Master',
	'photon2': 'Photon IK-3', #Leningrad-1 based (Russian ZX Spectrum clone)
	'photon': 'Photon System', #PK8000 based (Russian PC that was supposed to be MSX1 compatible)
	'plygonet': 'Konami Polygonet',
	'policetr': 'ATILLA Video System',
	'psikyo4': 'Psikyo PS4',
	'pyson': 'Konami Python', #Also called Pyson, I guess... Japan-English transliteration error? PS2 based
	'redalert': 'Irem M27',
	'seattle': 'Midway Seattle',
	'segac2': 'Sega System C2', #Similar to Megadrive
	'segae': 'Sega System E', #Similar to Master System
	'segag80r': 'Sega G-80 Raster',
	'segag80v': 'Sega G-80 Vector',
	'segam1': 'Sega M1', #Gambling
	'segas16a': 'Sega System 16A', #Similar to Megadrive
	'segas16b': 'Sega System 16B',
	'segas18': 'Sega System 18',
	'segas24': 'Sega System 24',
	'segas32': 'Sega System 32',
	'segasp': 'Sega System SP', #Dreamcast based, for medal games; non-working
	'segaufo': 'Sega UFO Board', #Mechanical
	'segaxbd': 'Sega X-Board',
	'segaybd': 'Sega Y-Board',
	'seibuspi': 'Seibu SPI',
	'sfcbox': 'Super Famicom Box', #Arcadified SNES sorta
	'sg1000a': 'Sega SG-1000', #Same hardware as the home system
	'sigmab98': 'Sigma B-98',
	'simpl156': 'Deco Simple 156',
	'snesb': 'SNES Bootleg', #SNES based, natch
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
	'taitotx': 'Taito Type X', #Modern PC based, very non-working
	'taitotz': 'Taito Type-Zero', #PPC based
	'taitowlf': 'Taito Wolf', #3Dfx (Pentium) based, not working
	'taito_x': 'Taito X System',
	'taito_z': 'Taito Z System',
	'tiamc1': 'TIA-MC1',
	'toypop': 'Namco System 16 Universal',
	'triforce': 'Triforce', #GameCube based
	'twin16': 'Konami Twin 16',
	'twinkle': 'Konami Bemani Twinkle', #PS1 based (but not System 573 related)
	'ultrsprt': 'Konami Ultra Sports',
	'vectrex': 'Vectrex', #Also used for actual Vectrex console
	'vegas': 'Midway Vegas',
	'vicdual': 'VIC Dual',
	'vigilant': 'Irem M75', #Also M77
	'viper': 'Konami Viper', #3Dfx (PPC) based
	'vsnes': 'VS Unisystem',
	'zr107': 'Konami ZR107',

	#Arcade platforms that don't have a name or anything, but companies consistently use them
	'alg': 'American Laser Games Hardware', #Amiga 500 based (w/ laserdisc player)
	'alpha68k': 'SNK Alpha 68K Hardware',
	'artmagic': 'Art & Magic Hardware',
	'cave': 'Cave 68K Hardware',
	'cavepc': 'Cave PC Hardware', #Athlon 64 X2 + Radeon 3200 based
	'cinemat': 'Cinematronics Vector Hardware',
	'cmmb': 'Cosmodog Hardware',
	'dec8': 'Data East 8-bit Hardware',
	'deco32': 'Data East 32-bit Hardware', #Or "Data East ARM6", if you prefer
	'dreamwld': 'Semicom 68020 Hardware',
	'eolith16': 'Eolith 16-bit Hardware',
	'esd16': 'ESD 16-bit Hardware',
	'ettrivia': 'Enerdyne Technologies Trivia Hardware',
	'gaelco3d': 'Gaelco 3D Hardware',
	'gaelco': 'Gaelco Hardware', #Specifically from 1991-1996 apparently?
	'gameplan': 'Game Plan Hardware',
	'gei': 'Greyhound Electronics Hardware',
	'gottlieb': 'Gottlieb Hardware',
	'homedata': 'Home Data Hardware',
	'itech32': 'Incredible Technologies 32-bit Blitter Hardware',
	'itech8': 'Incredible Technologies 8-bit Blitter Hardware',
	'kaneko16': 'Kaneko 16-bit Hardware',
	'leland': 'Leland Hardware',
	'meadows': 'Meadows S2650 Hardware',
	'metro': 'Metro Hardware',
	'micro3d': 'Microprose 3D Hardware',
	'mw8080bw': 'Midway 8080 Black & White Hardware',
	'n8080': 'Nintendo 8080 Hardware',
	'nmk16': 'NMK 16-bit Hardware',
	'playmark': 'Playmark Hardware',
	'psikyo': 'Psikyo Hardware',
	'psikyosh': 'Psikyo SH-2 Hardware',
	'seta2': 'Newer Seta Hardware',
	'seta': 'Seta Hardware',
	'simple_st0016': 'Seta ST-0016 Based Hardware',
	'snk': 'SNK Hardware',
	'snk68': 'SNK 68K Hardware',
	'statriv2': 'Status Trivia Hardware',
	'subsino2': 'Subsino Newer Tilemaps Hardware',
	'toaplan1': 'Toaplan Hardware',
	'toaplan2': 'Newer Toaplan Hardware',
	'unico': 'Unico Hardware',
	'williams': 'Williams 6809 Hardware',

	#Arcade platforms that don't really have a name except a game that uses them; I try not to fill this up with every single remaining source file, just where it's notable for having other games on it or some other reason (because it's based on a home console/computer perhaps, or because it's 3D or modern and therefore interesting)
	'ambush': 'Ambush Hardware',
	'armedf': 'Armed Formation Hardware',
	'arkanoid': 'Arkanoid Hardware',
	'backfire': 'Backfire! Hardware',
	'battlera': 'Battle Rangers Hardware', #PC Engine based
	'bishi': 'Bishi Bashi Champ Hardware',
	'btime': 'BurgerTime Hardware',
	'btoads': 'Battletoads Hardware',
	'cclimber': 'Crazy Climber Hardware',
	'cischeat': 'Cisco Heat Hardware',
	'coolpool': 'Cool Pool Hardware',
	'ddenlovr': 'Don Don Lover Hardware',
	'deshoros': 'Destiny Hardware',
	'dkong': 'Donkey Kong Hardware',
	'ertictac': 'Erotictac Hardware', #Acorn Archimedes based
	'fcrash': 'Final Crash Hardware', #Bootleg of Final Fight; this is used for other bootlegs too
	'galaga': 'Galaga Hardware',
	'galaxian': 'Galaxian Hardware', #Was used for a lot of games and bootlegs, actually; seems that Moon Cresta hardware has the same source file
	'galaxold': 'Galaxian Hardware', #There's a comment in that source file saying it'll be merged into galaxian eventually; seems that this one has all the bootlegs etc
	'ggconnie': 'Go! Go! Connie Hardware', #Supergrafx based
	'gticlub': 'GTI Club Hardware',
	'harddriv': "Hard Drivin' Hardware",
	'hshavoc': 'High Seas Havoc Hardware', #Megadrive based
	'invqix': 'Space Invaders / Qix Silver Anniversary Edition Hardware',
	'kinst': 'Killer Instinct Hardware',
	'lethalj': 'Lethal Justice Hardware',
	'liberate': 'Liberation Hardware',
	'metalmx': 'Metal Maniax Hardware',
	'pacman': 'Pac-Man Hardware',
	'pcat_nit': 'Street Games Hardware', #PC-AT 386 based
	'pong': 'Pong Hardware',
	'qdrmfgp': 'Quiz Do Re Mi Fa Grand Prix Hardware',
	'qix': 'Qix Hardware',
	'quakeat': 'Quake Arcade Tournament Hardware', #Unknown PC based
	'raiden2': 'Raiden 2 Hardware',
	'rallyx': 'Rally-X Hardware',
	'scramble': 'Scramble Hardware', #Apparently also to be merged into galaxian
	'segahang': 'Hang-On Hardware',
	'segaorun': 'Out Run Hardware',
	'slapshot': 'Slap Shot Hardware',
	'snowbros': 'Snow Bros Hardware',
	'ssfindo': 'See See Find Out Hardware', #RISC PC based
	'tnzs': 'The NewZealand Story Hardware',
	'tourtabl': 'Tournament Table Hardware', #Atari 2600 based
	'tumbleb': 'Tumble Pop Bootleg Hardware',
	'turrett': 'Turret Tower Hardware',
	'tvcapcom': 'Tatsunoko vs. Capcom Hardware', #Wii based
	'tx1': 'TX-1 Hardware',
	'vamphalf': 'Vamp x1/2 Hardware', #I guess the source file is for Hyperstone based games but I dunno if I should call it that
	'zaxxon': 'Zaxxon Hardware',

	#Multiple things stuffed into one source file, so there'd have to be something else to identify it or it doesn't matter
	'm10': 'Irem M10/M11/M15',
	'mcr': 'Midway MCR-1/MCR-2',
	'namcops2': 'Namco System 246/256', #Based on PS2
	'nemesis': 'Nemesis Hardware', #If BIOS = bubsys, Konami Bubble System
	'system1': 'Sega System 1/2',
	'vp101': 'Play Mechanix VP50/VP100/VP101',
	'zn': 'Sony ZN1/ZN2', #PS1 based; BIOS identifies what exactly it is (licensed to a few other companies too with some variations)
}

#Some games have memory card slots, but they don't actually support saving, it's just t hat the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['diggerma', 'neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']

def add_save_type(machine):
	if machine.metadata.platform == 'Arcade':
		has_memory_card = False
		for media_slot in machine.media_slots:
			if not media_slot.instances: #Does this ever happen?
				continue
			if media_slot.type == 'memcard':
				has_memory_card = True

		has_memory_card = has_memory_card and (machine.family not in not_actually_save_supported)

		machine.metadata.save_type = SaveType.MemoryCard if has_memory_card else SaveType.Nothing
	elif machine.metadata.platform in ('Mega-Tech', 'Mega-Play', 'Nintendo Super System', 'PlayChoice-10'):
		machine.metadata.save_type = SaveType.Nothing
	else:
		has_nvram = machine.uses_device('nvram')
		has_i2cmem = machine.uses_device('i2cmem')

		#Assume that if there's non-volatile memory that it's used for storing some kind of save data, and not like... stuff
		#This may be wrong!!!!!!!!!!! but it seems to hold true for plug & play TV games and electronic handheld games so that'd be the main idea
		machine.metadata.save_type = SaveType.Internal if has_nvram or has_i2cmem else SaveType.Nothing

def add_status(machine):
	driver = machine.driver_element
	#See comments for overall_status property for what that actually means
	machine.metadata.specific_info['MAME-Overall-Emulation-Status'] = machine.overall_status
	machine.metadata.specific_info['MAME-Emulation-Status'] = machine.emulation_status
	machine.metadata.specific_info['Cocktail-Status'] = mame_statuses.get(driver.attrib.get('cocktail'), EmulationStatus.Unknown)
	machine.metadata.specific_info['Supports-Savestate'] = driver.attrib.get('savestate') == 'supported'

	unemulated_features = []
	for feature_type, feature_status in machine.feature_statuses.items():
		if feature_status == 'unemulated':
			unemulated_features.append(feature_type)
		else:
			#Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
			#Note: MAME 0.208 has added capture, media, tape, punch, drum, rom, comms; although I guess I don't need to write any more code here
			machine.metadata.specific_info['MAME-%s-Status' % feature_type.capitalize()] = mame_statuses.get(feature_status, EmulationStatus.Unknown)

	if unemulated_features:
		machine.metadata.specific_info['MAME-Unemulated-Features'] = unemulated_features

#Stealing this from mame_machines.py while I'm still using it there
#These all indicate something that _is_ a plug & play system if they exist
plug_and_play_software_lists = ('vii', 'jakks_gamekey', 'ekara')
def is_plug_and_play(machine):
	#"Game Console / Home Videogame Console" in catlist.ini doesn't differentiate between plug & play systems that are meant to be used by themselves, and normal consoles which are meant to be used by other software. So, we'll do that ourselves
	if machine.software_lists:
		for software_list in machine.software_lists:
			if software_list.startswith(plug_and_play_software_lists):
				return True
		return False

	#Hmm...
	return True

def add_metadata_from_catlist(machine):
	category, genre, subgenre, nsfw = get_category(machine.basename)
	
	#Fix some errata present in the default catlist.ini, maybe one day I should tell them about it, but I'm shy or maybe they're meant to be like that
	if subgenre == 'Laser Disk Simulator':
		#Both of these spellings appear twice...
		subgenre = 'Laserdisc Simulator'
	#ddrstraw is Rhythm / Dance but it's more accurately a plug & play game, although that is the genre, so it's not wrong
	#kuzmich is just Platform / Run Jump, it's an arcade machine though
	
	machine.metadata.media_type = MediaType.Standalone

	if category == 'Unknown':
		#Not in catlist or user doesn't have catlist
		machine.metadata.platform = 'Unknown'
		machine.metadata.categories = ['Unknown']
		return

	if category:
		#'Arcade: ' or whatever else at the beginning
		machine.metadata.platform = category
		machine.metadata.genre = genre
		machine.metadata.subgenre = subgenre
		machine.metadata.nsfw = nsfw
	else:
		#Non-arcade thing
		machine.metadata.platform = 'Non-Arcade'
		machine.metadata.genre = genre
		machine.metadata.subgenre = subgenre

	filename_tags = find_filename_tags.findall(machine.name)
	for tag in filename_tags:
		if 'prototype' in tag.lower():
			machine.metadata.categories = ['Betas'] if machine.has_parent else ['Unreleased']
			break
		if 'bootleg' in tag.lower():
			machine.metadata.categories = ['Hacks'] if machine.has_parent else ['Bootleg']
			break
		if 'hack' in tag.lower():
			machine.metadata.categories = ['Hacks']
	if machine.is_mechanical:
		machine.metadata.categories = ['Electromechanical']
	if machine.is_hack:
		machine.metadata.categories = ['Hacks']
	if machine.uses_device('coin_hopper'):
		#Redemption games sometimes also have one, but then they will have their category set later by their subgenre being Redemption
		machine.metadata.categories = ['Gambling']

	#Now we separate things into additional platforms where relevant

	source_file_platforms = {
		'megatech': 'Mega-Tech',
		'megaplay': 'Mega-Play',
		'playch10': 'PlayChoice-10',
		'nss': 'Nintendo Super System',
	}	

	#Public coin-op machines with specific things, could make the argument that it should be left as Arcade as the platform and this as the category
	if machine.source_file in source_file_platforms:
		machine.metadata.platform = source_file_platforms[machine.source_file]
	#Home systems that have the whole CPU etc inside the cartridge, and hence work as separate systems in MAME instead of being in roms.py
	if machine.source_file == 'cps1' and '(CPS Changer, ' in machine.name:
		machine.name = machine.name.replace('CPS Changer, ', '')
		machine.metadata.platform = 'CPS Changer'
		machine.metadata.media_type = MediaType.Cartridge
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return 
	if machine.name.endswith('(XaviXPORT)'):
		machine.metadata.platform = 'XaviXPORT'
		machine.metadata.media_type = MediaType.Cartridge
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return
	if machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		platform, _, machine.name = machine.name.partition(': ')
		machine.metadata.platform = platform
		machine.metadata.media_type = MediaType.Cartridge if platform in ('Select-A-Game', 'R-Zone') else MediaType.Standalone
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
		return

	if (genre == 'Computer') or (genre == 'Calculator') or (genre == 'Handheld' and subgenre == 'Pocket Device - Pad - PDA') or (genre == 'Handheld' and subgenre == 'Child Computer') or (genre == 'Misc.' and subgenre == 'Electronic Game') or (genre == 'Board Game'):
		#Board Game is more like chess machines than actual board games
		#Hmm, need a better name for this I think
		machine.metadata.platform = 'Standalone System'
	if genre == 'Game Console' and subgenre == 'Home Videogame':
		machine.metadata.platform = 'Plug & Play' if is_plug_and_play(machine) else 'Standalone System'
	if genre == 'Misc.' and subgenre == 'Electronic Board Game':
		#Hmm does Misc. / Electronic Game (stuff like Electronic Soccer, Reversi Sensory Challenger) count as this, or as something else entirely
		machine.metadata.platform = 'Board Game'
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
	if not category and ((genre == 'Handheld' and subgenre == "Plug n' Play TV Game") or (genre == 'Rhythm' and subgenre == 'Dance') or (genre == 'MultiGame' and subgenre == 'Compilation') or (genre == 'Game Console' and subgenre == 'Fitness Game')):
		#MultiGame / Compilation is also used for some handheld systems (and also there is Arcade: MultiGame / Compilation)
		machine.metadata.platform = 'Plug & Play'
		if not machine.metadata.categories:
			machine.metadata.categories = ['Games']
	if genre == 'Electromechanical' and subgenre == 'Pinball':
		#There are a few things under Arcade: Electromechanical / Utilities that are also pinball stuff, although perhaps not all of them. It only becomes apparent due to them using the "genpin" sample set
		machine.metadata.platform = 'Pinball'
	if genre == 'Handheld' and subgenre == 'Electronic Game':
		#Note: "Handheld / Electronic Game" could also be a tabletop system which takes AC input and you would not be able to hold in your hands at all (see also: cpacman), but since catlist.ini doesn't take that into account, I don't really have a way of doing so either
		machine.metadata.platform = 'Handheld'
	if genre == 'Handheld' and subgenre == 'Home Videogame Console':
		#Home Videogame Console seems to be used for stuff that would be normally excluded due to having software lists and hence being a platform for other software (e.g. GBA), or stuff that ends up there because it has no software list yet (e.g. Gizmondo, Sony PocketStation), but also some stuff like kcontra (Contra handheld) that should definitely be called a handheld, or various "plug & play" (except without the plug) stuff like BittBoy 300 in 1 or VG Pocket
		#Anyway that's why I put that there
		#Other genres of handheld: Pocket Device - Pad - PDA; Child Computer (e.g. Speak & Spell) but those seem more suited to Standalone System particularly the former
		machine.metadata.platform = 'Handheld' if is_plug_and_play(machine) else 'Standalone System'
	if genre in ('Electromechanical', 'Utilities', 'Medal Game'):
		machine.metadata.categories = [genre]
	elif genre == 'Misc.' and subgenre in ('Laserdisc Simulator', 'Print Club', 'Unknown', 'Redemption'):
		machine.metadata.categories = [subgenre]
	elif genre == 'Music' and subgenre == 'Jukebox':
		machine.metadata.categories = [subgenre]
	elif (genre == 'Misc.' and subgenre == 'Coin Pusher') or (genre == 'Coin Pusher' and subgenre == 'Misc.'):
		machine.metadata.categories = ['Coin Pusher']
	elif category == 'Arcade' and ((genre == 'Casino') or (genre == 'Slot Machine') or (genre == 'Electromechanical' and subgenre == 'Reels') or (genre == 'Multiplay' and subgenre == 'Cards')):
		machine.metadata.categories = ['Gambling']
	elif category == 'Arcade' and machine.coin_slots == 0:
		#Or something among those lines, but if it has no coins then it doesn't meet the definition of "coin operated machine"
		machine.metadata.categories = ['Non-Arcade']

	if not machine.metadata.categories:
		if category:
			machine.metadata.categories = ['Arcade']
		else:
			machine.metadata.categories = ['Non-Arcade']
	#Misc has a lot of different things in it and I guess catlist just uses it as a catch-all for random things which don't really fit anywhere else and there's not enough to give them their own category, probably
	#Anyway, the name 'Non-Arcade' sucks because it's just used as a "this isn't anything in particular" thing


def add_metadata(machine):
	add_metadata_from_catlist(machine)

	machine.metadata.cpu_info.set_inited()
	cpus = find_cpus(machine.xml)
	if cpus:
		for cpu_xml in cpus:
			cpu = CPU()
			cpu.load_from_xml(cpu_xml)
			machine.metadata.cpu_info.add_cpu(cpu)

	machine.metadata.screen_info = ScreenInfo()
	displays = machine.xml.findall('display')
	machine.metadata.screen_info.load_from_xml_list(displays)

	add_input_info(machine)
	if machine.source_file in arcade_systems:
		machine.metadata.specific_info['Arcade-System'] = arcade_systems[machine.source_file]
	add_save_type(machine)

	machine.metadata.regions = get_regions_from_filename_tags(find_filename_tags.findall(machine.name), loose=True)

	language = get_language(machine.basename)
	if language:
		machine.metadata.languages = [language]

	if machine.metadata.regions and not machine.metadata.languages:
		languages = get_languages_from_regions(machine.metadata.regions)
		if languages:
			machine.metadata.languages = languages

	series = get_machine_category(machine.basename, 'series')
	if series:
		not_real_series = ('Hot', 'Aristocrat MK Hardware')

		if series.endswith(' * Pinball'):
			series = series[:-len(' * Pinball')]
		elif series.endswith(' * Slot'):
			series = series[:-len(' * Slot')]
		if series.startswith('The '):
			series = series[len('The '):]
		
		if series not in not_real_series:
			machine.metadata.series = remove_capital_article(series)

	#Might not be so hardcoded one day...
	machine.metadata.emulator_name = 'MAME'

	add_status(machine)

def add_input_info(machine):
	machine.metadata.input_info.set_inited()
	if machine.input_element is None:
		#Seems like this doesn't actually happen
		if main_config.debug:
			print('Oi m8', machine.basename, '/', machine.name, 'has no input')
		return

	control_elements = machine.input_element.findall('control')
	if not control_elements:
		#Sometimes you get some games with 1 or more players, but no control type defined.  This usually happens with
		#pinball games and weird stuff like a clock, but also some genuine games like Crazy Fight that are more or less
		#playable just fine, so we'll leave them in
		if machine.number_of_players > 0:
			machine.metadata.input_info.add_option(input_metadata.Custom('Unknown input device'))
		return

	controller = input_metadata.CombinedController()

	has_normal_input = False
	has_added_vii_motion_controls = False
	normal_input = input_metadata.NormalController()

	for control in control_elements:
		buttons = int(control.attrib.get('buttons', 0))

		if control.attrib.get('player', '1') != '1':
			#I care not for these "other people" and "social interaction" concepts
			#Anyway, this would only matter for stuff where player 2 has a different control scheme like Lucky & Wild, and... not sure what I'm gonna do about that, because we wanna avoid doubling up on input types where number of players > 1, and then that seems to be correct anyway
			continue

		#Still kinda feel like this is messy but ehhh
		#Input metadata will probably never be perfect, MAME -listxml outputs things for a different purpose really, it just be like that sometimes
		#I wonder if I'd be better off making some kind of controls.ini file myself
		input_type = control.attrib['type']
		if input_type == 'only_buttons':
			has_normal_input = True
			normal_input.face_buttons += buttons
		elif input_type == 'joy':
			has_normal_input = True
			normal_input.face_buttons += buttons
			normal_input.dpads += 1
		elif input_type == 'doublejoy':
			has_normal_input = True
			normal_input.face_buttons += buttons
			normal_input.dpads += 2
		elif input_type == 'triplejoy':
			has_normal_input = True
			normal_input.face_buttons += buttons
			normal_input.dpads += 3
		elif input_type == 'paddle':
			if machine.metadata.genre == 'Driving':
				#Yeah this looks weird and hardcody and dodgy but am I wrong
				if buttons > 0:
					has_normal_input = True
					normal_input.face_buttons += buttons
				controller.components.append(input_metadata.SteeringWheel())
			elif machine.basename == 'vii':
				#Uses 3 "paddle" inputs to represent 3-axis motion and I guess I'll have to deal with that
				if not has_added_vii_motion_controls:
					controller.components.append(input_metadata.MotionControls())
					has_added_vii_motion_controls = True
			else:
				paddle = input_metadata.Paddle()
				paddle.buttons = buttons
				controller.components.append(paddle)
		elif input_type == 'stick':
			has_normal_input = True
			normal_input.analog_sticks += 1
			normal_input.face_buttons += buttons
		elif input_type == 'pedal':
			if buttons > 0:
				has_normal_input = True
				normal_input.face_buttons += buttons
			pedal = input_metadata.Pedal()
			controller.components.append(pedal)
		elif input_type == 'lightgun':
			#TODO: See if we can be clever and detect if this is actually a touchscreen, like platform = handheld or something
			light_gun = input_metadata.LightGun()
			light_gun.buttons = buttons
			controller.components.append(light_gun)
		elif input_type == 'positional':
			#What _is_ a positional exactly
			positional = input_metadata.Positional()
			controller.components.append(positional)
		elif input_type == 'dial':
			dial = input_metadata.Dial()
			dial.buttons = buttons
			controller.components.append(dial)
		elif input_type == 'trackball':
			trackball = input_metadata.Trackball()
			trackball.buttons = buttons
			controller.components.append(trackball)
		elif input_type == 'mouse':
			mouse = input_metadata.Mouse()
			mouse.buttons = buttons
			controller.components.append(mouse)
		elif input_type == 'keypad':
			keypad = input_metadata.Keypad()
			keypad.keys = buttons
			controller.components.append(keypad)
		elif input_type == 'keyboard':
			keyboard = input_metadata.Keyboard()
			keyboard.keys = buttons
			controller.components.append(keyboard)
		elif input_type == 'mahjong':
			mahjong = input_metadata.Mahjong()
			mahjong.buttons = buttons
			controller.components.append(mahjong)
		elif input_type == 'hanafuda':
			hanafuda = input_metadata.Hanafuda()
			hanafuda.buttons = buttons
			controller.components.append(hanafuda)
		elif input_type == 'gambling':
			gambling = input_metadata.Gambling()
			gambling.buttons = buttons
			controller.components.append(gambling)
		else:
			if buttons:
				description = 'Custom input device with {0}'.format(pluralize(buttons, 'button'))
			else:
				description = 'Custom input device'
			controller.components.append(input_metadata.Custom(description))

	if has_normal_input:
		controller.components.append(normal_input)

	machine.metadata.input_info.input_options = [controller]
