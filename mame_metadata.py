import configparser
import sys
import os

import input_metadata
from common_types import MediaType, SaveType
from metadata import EmulationStatus, CPU, ScreenInfo
from region_detect import get_language_by_english_name, get_regions_from_filename_tags
from common import find_filename_tags, pluralize
from mame_helpers import find_main_cpus, get_mame_ui_config

debug = '--debug' in sys.argv

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

	category, _, genre = cat.partition(' / ')
	return category, genre, None, False

def get_language(basename):
	lang = get_machine_category(basename, 'languages')
	if not lang:
		return None

	return get_language_by_english_name(lang)

arcade_systems = {
	'3do': '3DO', #Used for the 3DO console as well, but there are 3DO-based arcade games which are just called that; non-working
	'aleck64': 'Aleck64', #Based on N64
	'alien': 'Capcom Medalusion', #Non-working
	'aristmk5': 'Aristocrat MK5', #Gambling, Acorn Archimedes based purrhaps
	'aristmk6': 'Aristocrat MK6', #Gambling, non-working
	'arsystems': 'Arcadia System', #Amiga 500 based
	'astrocde': 'Astrocade', #The home console used the same hardware, I can't remember the names of all the different things
	'atarig42': 'Atari G42',
	'atarigt': 'Atari GT',
	'atarigx2': 'Atari GX2',
	'atarisy1': 'Atari System 1',
	'atarisy2': 'Atari System 2',
	'atlantis': 'Midway Atlantis', #Linux based (on MIPS CPU); claims to be skeleton but seems to work a bit anyway
	'balsente': 'Bally/Sente SAC-1',
	'cdi': 'Philips CD-i', #Literally a CD-i player with a JAMMA adapter (used for some quiz games)
	'cedar_magnet': 'Magnet System',
	'chihiro': 'Chihiro', #Based on Xbox, seemingly non-working
	'cobra': 'Konami Cobra System',
	'coolridr': 'Sega System H1',
	'cps1': 'CPS-1',
	'cps2': 'CPS-2',
	'cps3': 'CPS-3',
	'crystal': 'Brezzasoft Crystal System',
	'cubo': 'Cubo CD32', #Amiga CD32 + JAMMA
	'cvs': 'Century CVS System',
	'decocass': 'Deco Casette',
	'dgpix': 'dgPIX VRender0',
	'djmain': 'DJ Main',
	'eolith': 'Eolith Gradation 2D System',
	'exidy440': 'Exidy 440',
	'expro02': 'Kaneko EXPRO-02',
	'firebeat': 'Konami Bemani Firebeat', #Non-working
	'fuukifg2': 'Fuuki FG-2',
	'fuukifg3': 'Fuuki FG-3',
	'gaelco2': 'Gaelco CG-1V/GAE1',
	'hikaru': 'Hikaru', #Based on souped up Naomi and in turn Dreamcast, non-working
	'hng64': 'Hyper Neo Geo 64', #Barely working
	'hornet': 'Konami Hornet',
	'jaguar': 'CoJag', #This is the same source file used for the Jaguar console too
	'konamigq': 'Konami GQ', #Based on PS1
	'konamigv': 'Konami GV', #Based on PS1
	'konamigx': 'Konami GX',
	'konamim2': 'Konami M2', #Based on unreleased Panasonic M2
	'ksys573': 'Konami System 573', #Based on PS1
	'gammagic': 'Bally V8000', #Pentium PC based, skeleton
	'lindbergh': 'Sega Lindbergh', #(modern) PC based, very non-working
	'm52': 'Irem M52',
	'm58': 'Irem M58',
	'm62': 'Irem M62',
	'm72': 'Irem M72',
	'm90': 'Irem M90', #Also M97 I guess
	'm92': 'Irem M92',
	'macs': 'Multi Amenity Casette System',
	'mcr': 'Midway MCR',
	'mcr3': 'Midway MCR-3',
	'mcr68': 'Midway MCR-68k',
	'meadows': 'Meadows S2650',
	'mediagx': 'Atari Media GX', #Based on Cyrix multimedia PC
	'megadriv_acbl': 'Mega Drive Bootleg', #Mega Drive based ofc
	'megasys1': 'Jaleco Mega System 1',
	'midqslvr': 'Midway Quicksilver', #Non-working
	'midtunit': 'Midway T-Unit',
	'midvunit': 'Midway V-Unit',
	'midwunit': 'Midway W-Unit',
	'midxunit': 'Midway X-Unit',
	'midyunit': 'Midway Y-Unit',
	'midzeus': 'Midway Zeus',
	'model1': 'Sega Model 1',
	'model2': 'Sega Model 2', #Barely working
	'model3': 'Sega Model 3', #Non-working
	'ms32': 'Jaleco Mega System 32',
	'namconb1': 'Namco System NB-1',
	'namcond1': 'Namco System ND-1',
	'namcops2': 'Namco PS2', #Based on PS2
	'namcos1': 'Namco System 1',
	'namcos10': 'Namco System 10', #Based on PS1
	'namcos11': 'Namco System 11', #Based on PS1
	'namcos12': 'Namco System 12',
	'namcos2': 'Namco System 2',
	'namcos21': 'Namco System 21',
	'namcos21_c67': 'Namco System 21', #With C67 DSP
	'namcos22': 'Namco System 22',
	'namcos23': 'Namco System 23',
	'naomi': 'Naomi', #Based on Dreamcast. romof="awbios" == Atomiswave; not entirely working
	'neogeo': 'Neo-Geo',
	'nwk-tr': 'Konami NWK-TR',
	'pcxt': 'IBM PC-XT', #Games running off a PC-XT
	'pgm': 'PolyGame Master',
	'pgm2': 'PolyGame Master 2',
	'pgm3': 'PolyGame Master 3', #Non-working
	'photon': 'Photon System', #PK8000 based (Russian PC that was supposed to be MSX1 compatible)
	'photon2': 'Photon IK-3', #Leningrad-1 based (Russian ZX Spectrum clone)
	'policetr': 'ATILLA Video System',
	'psikyo4': 'Psikyo PS4',
	'pyson': 'Konami Pyson',
	'seattle': 'Midway Seattle',
	'segac2': 'System C2', #Similar to Megadrive
	'segae': 'System E', #Similar to Master System
	'segag80r': 'Sega G-80 Raster',
	'segag80v': 'Sega G-80 Vector',
	'segas16a': 'System 16A', #Similar to Megadrive
	'segas16b': 'System 16B',
	'segas18': 'System 18',
	'segas24': 'System 24',
	'segas32': 'System 32',
	'segasp': 'Sega System SP', #Dreamcast based, for medal games; non-working
	'segaxbd': 'Sega X-Board',
	'segaybd': 'Sega Y-Board',
	'seibuspi': 'Seibu SPI',
	'sfcbox': 'Super Famicom Box', #Arcadified SNES sorta
	'sg1000a': 'Sega SG-1000',
	'snesb': 'SNES Bootleg', #SNES based, natch
	'sigmab98': 'Sigma B-98',
	'simpl156': 'Deco 156',
	'ssv': 'SSV', #Sammy Seta Visco
	'stv': 'ST-V', #Based on Saturn
	'suprnova': 'Kaneko Super Nova System',
	'taito_b': 'Taito B System',
	'taito_f2': 'Taito F2',
	'taito_f3': 'Taito F3',
	'taitogn': 'Taito G-NET',
	'taito_h': 'Taito H System',
	'taitojc': 'Taito JC',
	'taito_l': 'Taito L-System',
	'taitosj': 'Taito SJ',
	'taito_o': 'Taito O System',
	'taitopjc': 'Taito Power-JC',
	'taitotx': 'Taito Type X', #Modern PC based, very non-working
	'taitotz': 'Taito Type-Zero', #PPC based
	'taitowlf': 'Taito Wolf', #3Dfx (Pentium) based
	'taito_x': 'Taito X-System',
	'taito_z': 'Taito Z System',
	'tiamc1': 'TIA-MC1',
	'triforce': 'Triforce', #GameCube based
	'ultrsprt': 'Konami Ultra Sports',
	'vegas': 'Midway Vegas',
	'vicdual': 'VIC Dual',
	'viper': 'Konami Viper', #3Dfx (PPC) based
	'vsnes': 'VS Unisystem',
	'williams': 'Williams 6809',
	'zr107': 'Konami ZR701',

	#Arcade platforms that don't have a name or anything, but companies consistently use them
	'cave': 'Cave Hardware',
	'alg': 'American Laser Games Hardware', #Amiga 500 based (w/ laserdisc player)
	'artmagic': 'Art & Magic Hardware',
	'cinemat': 'Cinematronics Vector Hardware',
	'dec0': 'Data East 16-bit Hardware',
	'dec8': 'Data East 8-bit Hardware',
	'dreamwld': 'Semicom 68020 Hardware',
	'ettrivia': 'Enerdyne Technologies Trivia',
	'exidy': 'Exidy Hardware',
	'gameplan': 'Game Plan Hardware',
	'gei': 'Greyhound Electronics Hardware',
	'gottlieb': 'Gottlieb Hardware',
	'homedata': 'Home Data Hardware',
	'itech8': 'Incredible Technologies 8-bit Blitter Hardware',
	'itech32': 'Incredible Technologies 32-bit Blitter Hardware',
	'kaneko16': 'Kaneko 16-bit Hardware',
	'leland': 'Leland Hardware',
	'micro3d': 'Microprose 3D Hardware',
	'mw8080bw': 'Midway 8080 Black & White Hardware',
	'playmark': 'Playmark Hardware',
	'seta': 'Seta Hardware',
	'subsino2': 'Subsino Newer Tilemaps Hardware',
	'unico': 'Unico Hardware',

	#Arcade platforms that don't really have a name except a game that uses them; I try not to fill this up with every single remaining source file, just where it's notable for having other games on it or some other reason
	'ambush': 'Ambush Hardware',
	'armedf': 'Armed Formation Hardware',
	'battlera': 'Battle Rangers', #PC Engine based
	'btime': 'BurgerTime Hardware',
	'cclimber': 'Crazy Climber Hardware',
	'dkong': 'Donkey Kong Hardware',
	'ertictac': 'Erotictac Hardware', #Acorn Archimedes based
	'fcrash': 'Final Crash Hardware', #Bootleg of Final Fight; this is used for other bootlegs too
	'galaga': 'Galaga Hardware',
	'galaxian': 'Galaxian Hardware', #Was used for a lot of games and bootlegs, actually; seems that Moon Cresta hardware has the same source file
	'galaxold': 'Galaxian Hardware', #There's a comment in that source file saying it'll be merged into galaxian eventually; seems that this one has all the bootlegs etc
	'ggconnie': 'Go! Go! Connie Hardware', #Supergrafx based
	'gticlub': 'Konami GTI Club Hardware',
	'lethalj': 'Lethal Justice Hardware',
	'liberate': 'Liberation Hardware',
	'nemesis': 'Nemesis Hardware',
	'pacman': 'Pac-Man Hardware',
	'pcat_nit': 'Street Games Hardware', #PC-AT 386 based
	'pong': 'Pong Hardware',
	'qix': 'Qix Hardware',
	'quakeat': 'Quake Arcade Tournament Hardware', #Unknown PC based
	'rallyx': 'Rally-X Hardware',
	'scramble': 'Scramble Hardware', #Apparently also to be merged into galaxian
	'snowbros': 'Snow Bros Hardware',
	'ssfindo': 'See See Find Out Hardware', #RISC PC based
	'tnzs': 'The NewZealand Story Hardware',
	'tvcapcom': 'Tatsunoko vs. Capcom Hardware', #Wii based
	'tumbleb': 'Tumble Pop Bootleg Hardware',
	'turrett': 'Turret Tower Hardware',
	'vamphalf': 'Vamp x1/2 Hardware', #I guess the source file is for Hyperstone based games but I dunno if I should call it that
	'zaxxon': 'Zaxxon Hardware',

	#Identified by BIOS and not source file:
	#coh100c: Sony ZN1 (PS1 based)
	#coh100t: Taito FX1 (PS1 based)

	#system1 = Sega System 1 or Sega System 2
	#m10 = Irem M10/M11/M15
}

def add_machine_platform(machine):
	category = machine.metadata.categories[0]

	source_file_platforms = {
		'megatech': 'Mega-Tech',
		'megaplay': 'Mega-Play',
		'playch10': 'PlayChoice-10',
		'nss': 'Nintendo Super System',
	}

	#Public coin-op machines that could be still considered 'Arcade' as the platform, but meh
	if machine.source_file in source_file_platforms:
		return source_file_platforms[machine.source_file], MediaType.Standalone

	#Home systems that have the whole CPU etc inside the cartridge, and hence work as separate systems in MAME instead of being in roms.py
	elif machine.source_file == 'cps1' and '(CPS Changer, ' in machine.name:
		machine.name = machine.name.replace('CPS Changer, ', '')
		return 'CPS Changer', MediaType.Cartridge
	elif machine.name.endswith('(XaviXPORT)'):
		return 'XaviXPORT', MediaType.Cartridge
	elif machine.name.startswith(('Game & Watch: ', 'Select-A-Game: ', 'R-Zone: ')):
		platform, _, machine.name = machine.name.partition(': ')
		return platform, MediaType.Cartridge if platform in ('Select-A-Game', 'R-Zone') else MediaType.Standalone

	#Other weird and wacky devices
	#Note: "Handheld / Electronic Game" could also be a tabletop system which takes AC input and you would not be able to hold in your hands at all (see also: cpacman), but since catlist.ini doesn't take that into account, I don't really have a way of doing so either
	elif (category == 'Game Console') or (category == 'Handheld' and machine.metadata.genre == "Plug n' Play TV Game"):
		machine.metadata.platform = 'Plug & Play'
		#Since we're skipping over stuff with software lists, anything that's still classified as a game console is a plug & play system. Also if you plug it into your TV it's not really a handheld so I'm not sure what the logic is there, and I'm not actually sure why that's used for some instead of Game Console / Home Videogame and what's the difference
		return 'Plug & Play', MediaType.Standalone
	elif machine.metadata.genre in ('Electromechanical', 'Slot Machine') and machine.metadata.subgenre == 'Reels':
		#"Slot Machine", "Fruit Machine", "Gambling", "AWP", whatevs; this ends up being the mechanical kind specifically and maybe doesn't actually need to be a separate platform anyway
		return 'Slot Machine', MediaType.Standalone
	elif machine.metadata.genre == 'Electromechanical' and machine.metadata.subgenre == 'Pinball':
		#There are a few things under Arcade: Electromechanical / Utilities that are also pinball stuff, although perhaps not all of them. It only becomes apparent due to them using the "genpin" sample set
		return 'Pinball', MediaType.Standalone
	elif category == 'Handheld' and machine.metadata.genre in ('Electronic Game', 'Home Videogame Console'):
		#Home Videogame Console seems to be used for stuff that would be normally excluded due to having software lists and hence being a platform for other software (e.g. GBA), or stuff that ends up there because it has no software list yet (e.g. Gizmondo, Sony PocketStation), but also some stuff like kcontra (Contra handheld) that should definitely be called a handheld, or various "plug & play" (except without the plug) stuff like BittBoy 300 in 1 or VG Pocket
		#Anyway that's why I put that there
		#Other genres of handheld: Pocket Device - Pad - PDA; Child Computer (e.g. Speak & Spell) but those seem more suited to Non-Arcade particularly the former
		return category, MediaType.Standalone
	elif category == 'Unknown':
		#Because catlist.ini might be not updated just yet or the user might not have it; MediaType.Standalone is an assumption but oh well
		return category, MediaType.Standalone
	elif category == 'Arcade':
		#Things that might not be arcade: Genre == Utilities (screen tests, etc); genre == Music && subgenre == Jukebox; genre == Misc && subgenre == Print Club (more of a photo booth I guess)
		return category, MediaType.Standalone

	#This leaves categories like Board Game, Computer, Telephone, Utilities (EEPROM programmers), Music, Misc., Multigame
	#Misc has a lot of different things in it and I guess catlist just uses it as a catch-all for random things which don't really fit anywhere else and there's not enough to give them their own category, probably
	#Some things inside Misc that might be of interest to people because they're actual games: Electronic Board Game (Electronic Battleship), Electronic Game (Electronic Soccer, Reversi Sensory Challenger), and then there's V-Dog (prototype) which ends up as "Unknown"; perhaps I could split these off into their own platform
	#MultiGame tends to have genre of "Compilation" and has things like CoolBoy RS-8 168 in 1 which really should be under Handheld/Plug & Play but oh well
	return 'Non-Arcade', MediaType.Standalone

#Some games have memory card slots, but they don't actually support saving, it's just t hat the arcade system board thing they use always has that memory card slot there. So let's not delude ourselves into thinking that games which don't save let you save, because that might result in emotional turmoil.
#Fatal Fury 2, Fatal Fury Special, Fatal Fury 3, and The Last Blade apparently only save in Japanese or something? That might be something to be aware of
#Also shocktro has a set 2 (shocktroa), and shocktr2 has a bootleg (lans2004), so I should look into if those clones don't save either. They probably don't, though, and it's probably best to expect that something doesn't save and just playing it like any other arcade game, rather than thinking it does and then finding out the hard way that it doesn't. I mean, you could always use savestates, I guess. If those are supported. Might not be. That's another story.
not_actually_save_supported = ['diggerma', 'neobombe', 'pbobbl2n', 'popbounc', 'shocktro', 'shocktr2', 'irrmaze']

def add_save_type(machine):
	if machine.metadata.platform == 'Arcade':
		has_memory_card = False
		for device in machine.xml.findall('device'):
			instance = device.find('instance')
			if instance is None:
				continue
			if instance.attrib['name'] == 'memcard':
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
	machine.metadata.specific_info['MAME-Emulation-Status'] = machine.overall_status
	#I guess I gotta think of better names for this stuff
	machine.metadata.specific_info['MAME-Actual-Emulation-Status'] = mame_statuses.get(driver.attrib['emulation'], EmulationStatus.Unknown)
	machine.metadata.specific_info['Cocktail-Status'] = mame_statuses.get(driver.attrib.get('cocktail'), EmulationStatus.Unknown)
	machine.metadata.specific_info['Supports-Savestate'] = driver.attrib.get('savestate') == 'supported'

	unemulated_features = []
	for feature in machine.xml.findall('feature'):
		feature_type = feature.attrib['type']
		if 'status' in feature.attrib:
			feature_status = feature.attrib['status']
		elif 'overall' in feature.attrib:
			#wat?
			feature_status = feature.attrib['overall']
		else:
			continue

		if feature_status == 'unemulated':
			unemulated_features.append(feature_type)
		else:
			#Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
			#Note: MAME 0.208 will add capture, media, tape, punch, drum, rom, comms; although I guess I don't need to write any more code here
			machine.metadata.specific_info['MAME-%s-Status' % feature_type.capitalize()] = mame_statuses.get(feature_status, EmulationStatus.Unknown)

	if unemulated_features:
		machine.metadata.specific_info['MAME-Unemulated-Features'] = unemulated_features

def add_metadata(machine):
	category, genre, subgenre, nsfw = get_category(machine.basename)
	machine.metadata.categories = [category] if category else ['Unknown']
	machine.metadata.genre = genre
	machine.metadata.subgenre = subgenre
	machine.metadata.nsfw = nsfw

	machine.metadata.cpu_info.set_inited()
	cpus = find_main_cpus(machine.xml)
	if cpus:
		for cpu_xml in cpus:
			cpu = CPU()
			cpu.load_from_xml(cpu_xml)
			machine.metadata.cpu_info.add_cpu(cpu)

	machine.metadata.screen_info = ScreenInfo()
	displays = machine.xml.findall('display')
	machine.metadata.screen_info.load_from_xml_list(displays)

	add_input_info(machine)
	machine.metadata.platform, machine.metadata.media_type = add_machine_platform(machine)
	if machine.source_file in arcade_systems:
		machine.metadata.specific_info['Arcade-System'] = arcade_systems[machine.source_file]
	add_save_type(machine)

	language = get_language(machine.basename)
	if language:
		machine.metadata.languages = [language]

	series = get_machine_category(machine.basename, 'series')
	if series:
		machine.metadata.specific_info['Franchise'] = series.replace(' * Pinball', '').replace(' * Slot', '')

	machine.metadata.regions = get_regions_from_filename_tags(find_filename_tags.findall(machine.name), loose=True)

	#Might not be so hardcoded one day...
	machine.metadata.emulator_name = 'MAME'

	add_status(machine)

def add_input_info(machine):
	machine.metadata.input_info.set_inited()
	if machine.input_element is None:
		#Seems like this doesn't actually happen
		if debug:
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
