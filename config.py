import socket
import os

DOOM_SAVE_DIR = '/media/Stuff/Roms/Doom/Saves'
SUFAMI_TURBO_BIOS_PATH = '/media/Stuff/Roms/SNES/BIOS/Sufami Turbo (Japan).sfc'
BSX_BIOS_PATH = '/media/Stuff/Roms/SNES/BIOS/BS-X BIOS/BS-X BIOS (English) [No DRM] [2016 v1.3].sfc'
CATLIST_PATH = '/media/Stuff/Roms/Arcade/Categories/catlist.ini'
LANGUAGES_PATH = '/media/Stuff/Roms/Arcade/Categories/languages.ini'
is_toaster = socket.gethostname() == 'Bridgette'
pce_emulator = 'mednafen-pce_fast' if is_toaster else 'mednafen-pce'
basilisk_ii_shared_folder = '/media/Things/Mac_OS_Stuff/Shared'

mac_disk_images = ['/media/Things/Mac_OS_Stuff/Games 68k.hfv']
mac_db_path = os.path.join(os.path.dirname(__file__), 'mac_db.json')

class SystemConfig():
	def __init__(self, name, rom_dir, chosen_emulator, other_config=None):
		self.name = name
		self.rom_dir = rom_dir
		self.chosen_emulator = chosen_emulator
		self.other_config = {} if other_config is None else other_config

system_configs = [
	SystemConfig('Game Boy', '/media/Stuff/Roms/Gameboy', 'gambatte'),
	SystemConfig('GBA', '/media/Stuff/Roms/GBA', 'mgba'), 
	SystemConfig('SNES', '/media/Stuff/Roms/SNES', 'snes9x'),
	SystemConfig('N64', '/media/Stuff/Roms/N64', 'mupen64plus'), 
	SystemConfig('Mega Drive', '/media/Stuff/Roms/Megadrive', 'kega-fusion'),
	SystemConfig('Game Gear', '/media/Stuff/Roms/Game Gear', 'kega-fusion'),
	SystemConfig('Master System', '/media/Stuff/Roms/Master System', 'kega-fusion'),
	SystemConfig('PSP', '/media/Stuff/Roms/PSP', 'ppsspp'),
	SystemConfig('Neo Geo Pocket', '/media/Stuff/Roms/Neo Geo Pocket', 'mednafen-ngp'),
	SystemConfig('Atari 2600', '/media/Stuff/Roms/Atari 2600', 'stella'), 
	SystemConfig('Pokemon Mini', '/media/Stuff/Roms/Pokemon Mini', 'pokemini-wrapper'),
	SystemConfig('NES', '/media/Stuff/Roms/NES', 'mednafen-nes'),
	SystemConfig('Mega CD', '/media/Stuff/Roms/Mega CD', 'kega-fusion'), 
	SystemConfig('SG-1000', '/media/Stuff/Roms/Sega SG-1000', 'kega-fusion'),
	SystemConfig('PC Engine', '/media/Stuff/Roms/PC Engine', pce_emulator), 
	SystemConfig('PC Engine CD', '/media/Stuff/Roms/PC Engine CD', pce_emulator), 
	SystemConfig('Virtual Boy', '/media/Stuff/Roms/Virtual Boy', 'mednafen-vb'),
	SystemConfig('Atari 7800', '/media/Stuff/Roms/Atari 7800', 'mame-atari-7800'), 
	SystemConfig('Neo Geo CD', '/media/Stuff/Roms/Neo Geo CD', 'mame-neo-geo-cd'),
	SystemConfig('Atari 5200', '/media/Stuff/Roms/Atari 5200', 'mame-atari-5200'), 

	SystemConfig('Watara Supervision', '/media/Stuff/Roms/Watara Supervision', 'mame-watara-supervision'), 
	SystemConfig('Casio PV-1000', '/media/Stuff/Roms/Casio PV-1000', 'mame-pv-1000'),
	SystemConfig('Arcadia 2001', '/media/Stuff/Roms/Arcadia 2001', 'mame-arcadia-2001'), 
	SystemConfig('Entex Adventure Vision', '/media/Stuff/Roms/Adventure Vision', 'mame-adventure-vision'), 
	SystemConfig('Vectrex', '/media/Stuff/Roms/Vectrex', 'mame-vectrex'), 
	SystemConfig('Mega Duck', '/media/Stuff/Roms/Mega Duck', 'mame-mega-duck'), 
	SystemConfig('Amstrad GX4000', '/media/Stuff/Roms/Amstrad GX4000', 'mame-amstrad-gx4000'), 
	SystemConfig('Gamate', '/media/Stuff/Roms/Gamate', 'mame-gamate', 'gamate'),
	SystemConfig('Epoch Game Pocket Computer', '/media/Stuff/Roms/Game Pocket Computer', 'mame-game-pocket-computer'),

	SystemConfig('Colecovision', '/media/Stuff/Roms/Colecovision', 'mame-colecovision'), 
	SystemConfig('Intellivison', '/media/Stuff/Roms/Intellivision', 'mame-intellivision-voice'), 
	SystemConfig('APF-MP1000', '/media/Stuff/Roms/APF-MP1000', 'mame-apfm1000'),
	SystemConfig('Astrocade', '/media/Stuff/Roms/Astrocade', 'mame-astrocade'), 
	SystemConfig('Channel F', '/media/Stuff/Roms/Channel F', 'mame-channelf'), 
	SystemConfig('Lynx', '/media/Stuff/Roms/Atari Lynx', 'mednafen-lynx'), 
	SystemConfig('WonderSwan', '/media/Stuff/Roms/WonderSwan', 'mednafen-wonderswan'), 
	SystemConfig('Doom', '/media/Stuff/Roms/Doom/', 'prboom-plus', {'save_dir': DOOM_SAVE_DIR}),
	
	SystemConfig('MSX', '/media/Stuff/Roms/MSX', 'mame-msx2'), 
	SystemConfig('MSX2', '/media/Stuff/Roms/MSX2', 'mame-msx2'), 
	SystemConfig('VIC-20', '/media/Stuff/Roms/Commodore VIC-20', 'mame-vic-20'),
	SystemConfig('Casio PV-2000', '/media/Stuff/Roms/Casio PV-2000', 'mame-pv-2000'), 
	SystemConfig('Sord M5', '/media/Stuff/Roms/Sord M5', 'mame-sord-m5'), 
	SystemConfig('Atari 8-bit', '/media/Stuff/Roms/Atari 8-bit', 'mame-atari-8bit'), 
]

if not is_toaster:
	system_configs.extend([
		SystemConfig('PlayStation', '/media/Stuff/Roms/Playstation', 'mednafen-ps1'), 
		SystemConfig('GameCube', '/media/Stuff/Roms/Gamecube', 'dolphin'),
		SystemConfig('3DS', '/media/Stuff/Roms/3DS', 'citra'), 
		SystemConfig('DS', '/media/Stuff/Roms/DS', 'medusa'),
		SystemConfig('PS2', '/media/Stuff/Roms/PS2', 'pcsx2'), 
		SystemConfig('32X', '/media/Stuff/Roms/32X', 'kega-fusion'), 
		#Kega Fusion almost runs 32X well on toaster, but not enough games run at full speed for me to bother...
		SystemConfig('CD-i', '/media/Stuff/Roms/CD-i', 'mame-cdi'),
		SystemConfig('Game.com', '/media/Stuff/Roms/Game.com', 'mame-game-com'),
		SystemConfig('Sufami Turbo', '/media/Stuff/Roms/SNES/Sufami Turbo', 'mame-sufami-turbo', {'bios_path': SUFAMI_TURBO_BIOS_PATH}),
		SystemConfig('Satellaview', '/media/Stuff/Roms/SNES/Satellaview', 'mame-satellaview', {'bios_path': BSX_BIOS_PATH}),

		SystemConfig('Wii', '/media/Stuff/Roms/Wii', 'dolphin'), 
		#Gonna have to map these motion controls somehow
		SystemConfig('Saturn', '/media/Stuff/Roms/Saturn', 'mednafen-saturn'), 
		#Not the most easily mappable of controllers due to having both 6 face buttons and 2 shoulder buttons

		SystemConfig('Tomy Tutor', '/media/Stuff/Roms/Tomy Tutor', 'mame-tomy-tutor'), 
		SystemConfig('C64', '/media/Stuff/Roms/Commodore 64', 'mame-c64'),
		SystemConfig('VIC-10', '/media/Stuff/Roms/Commodore VIC-10', 'mame-vic-10'), 
		SystemConfig('Sharp X1', '/media/Stuff/Roms/Sharp X1', 'mame-sharp-x1'), 
		SystemConfig('Sharp X68000', '/media/Stuff/Roms/Sharp X68000', 'mame-sharp-x68k'),
	])

with open(os.path.join(os.path.dirname(__file__), 'ignored_directories.txt'), 'rt') as ignored_txt:
	ignored_directories = ignored_txt.read().splitlines()

#These just kinda don't work entirely (namcos10, namcos11 might be fine?) or in the case of aleck64 and seattle, are
#too cool to run on normal PCs affordable by normal people
#model2: Daytona, Sonic the Fighters; model3: Daytona 2; aleck64: Vivid Dolls; namcos10: ??; namcos11: Tekken;
#namcos23: Time Crisis 2; chihiro: Outrun 2; naomi: Virtua Tennis, Puyo Puyo Fever, Azumanga Daioh Puzzle Bobble;
#hikaru: ?; 3do: One prototype game called "Orbatak" that I've never heard of ; konamim2: ?; ksys573: DDR; hng64: ?;
#seattle: CarnEvil (very close to full speed!); viper: Pop'n' Music 9, Jurassic Park 3; 39in1: weird MAME bootlegs;
#taitowlf: Psychic Force 2012; alien: Donkey Kong Banana Kingdom, Pingu's Ice Block
too_slow_drivers = ['model2', 'model3', 'aleck64', 'namcos10', 'namcos11', 'namcos12', 'namcos23', 'chihiro', 'naomi', 'hikaru', '3do', 'konamim2', 'ksys573', 'hng64', 'seattle', 'viper', '39in1', 'taitowlf', 'alien']
if is_toaster:
	#These won't go to well on anything in the toaster tier of performance due to being 3D or whatever, but otherwise they
	#should work well enough
	#stv: Puyo Puyo Sun; jaguar: Area 51; namcos22: Time Crisis, Ridge Racer; namcos12: Tekken 3, Point Blank 2; konamigv:
	#Simpsons Bowling; vegas: Gauntlet Legends
	too_slow_drivers.extend(['stv', 'jaguar', 'namcos22', 'namcos12', 'konamigv', 'vegas'])
	#These ones would probably work with just a bit more oomph...  if I get an upgrade of any kind I should try them again
	#m62 is an otherwise normal 8-bit system but the slowdown has to do with analogue sound, so it may need samples
	#fuukifg3: Asura Blade; segac2: Puyo Puyo; segas18: Michael Jackson's Moonwalker; segas32: Outrunners, SegaSonic;
	#namconb1: Point Blank; konamigx: Sexy Parodius (it thinks it doesn't work); megatech & megaplay: Arcadified Megadrive
	#games; segaorun: Outrun; taito_f3: Puzzle Bobble 2; m62: Lode Runner; neogeo: Metal Slug X; pong: Pong, Breakout;
	#atarisy2: like Paperboy or something I think; midtunit: Mortal Kombat 2; midwunit: Mortal Kombat 3 midyunit: NARC,
	#Smash TV, Mortal Kombat 1
	too_slow_drivers.extend(['fuukifg3', 'segac2', 'segas18', 'segas32', 'namconb1', 'konamigx', 'megatech', 'megaplay', 'segaorun', 'taito_f3', 'm62', 'neogeo', 'pong', 'atarisy2', 'midtunit', 'midwunit', 'midyunit', '1945kiii'])
	
skip_fruit_machines = ['mpu3', 'mpu4', 'mpu5', 'bfm_', 'pluto5', 'maygay', 'jpmimpctsw', 'peplus', 'ecoinf', 'arist', 'acesp']
	
#Normally, we'd skip over anything that has software because that indicates it's a system you plug games into and not
#usable by itself.  But these are things that are really just standalone things, but they have an expansion for
#whatever reason and are actually fine
#cfa3000 is kinda fine but it counts as a BBC Micro so it counts as not fine, due to detecting this stuff by
#parent/clone family
okay_to_have_software = ['vii', 'snspell', 'tntell']

output_folder = os.path.join('/tmp', 'crappy_game_launcher')
organized_output_folder = os.path.expanduser("~/Apps")

#For when I do a hecking disagreement about how names should be formatted, and if subtitles should be in the title or
#not.  This probably annoys purists, but I think it makes things less confusing at the end of the day
#When has anyone mentioned a game called "Space Invaders M", anyway?
#TODO: Review the practicality of just changing normalize_name to remove all spaces and punctuation.  Would that cause
#any false positives at all?  Though there would still be use for this part here
name_replacement = [
	('240p Test Suite GX', '240p Suite'), 
	('Arkanoid - Revenge of DOH', 'Arkanoid II - Revenge of Doh'), #What the hell?
	('Bad Lands', 'BadLands'),
	('Battle Zone', 'Battlezone'), 
	('Block Out', 'Blockout'), 
	('Bomber Man', 'Bomberman'),
	('Bubsy in - Claws Encounters of the Furred Kind', 'Bubsy in Claws Encounters of the Furred Kind'),	
	('Burger Time', 'BurgerTime'), 
	('Chuck Norris - Super Kicks', 'Chuck Norris Superkicks'), 
	('Cosmo Gang the Video', 'Cosmo Gang - The Video'), 
	('Donkey Kong Junior', 'Donkey Kong Jr.'), 
	('Final Fantasy 4', 'Final Fantasy IV'),
	('James Pond 2 - Codename RoboCod', 'James Pond II - Codename RoboCod'),
	('James Pond II - Codename - Robocod', 'James Pond II - Codename RoboCod'),
	("John Romero's Daikatana", 'Daikatana'),
	('Mario Brothers', 'Mario Bros.'), 
	('Mega Man III', 'Mega Man 3'),
	("Miner 2049'er", 'Miner 2049er'),
	('OutRun', 'Out Run'), 
	('Pacman', 'Pac-Man'), 
	('Pac Man', 'Pac-Man'), 
	('Parodius DA!', 'Parodius'),
	('Pitfall 2', 'Pitfall II'),
	('Puyo Puyo Tsuu', 'Puyo Puyo 2'), 
	('Q-Bert', 'Q*bert'), 
	#To be fair, this is just a technical restriction on filenames that isn't relevant when using a MAME display name
	('Robotron - 2084', 'Robotron 2084'), 
	('Sangokushi 3', 'Sangokushi III'), 
	('Sim Ant', 'SimAnt'),
	('Sim City', 'SimCity'),
	('Sim Earth', 'SimEarth'),
	('Super Boy 3', 'Super Boy III'), 
	("Street Fighter II'", 'Street Fighter II'), 
	('Twin Bee', 'TwinBee'),
	('Ultima 3', 'Ultima III'),
	('Where in the World is Carmen Sandiego?', 'Where in the World is Carmen Sandiego'), 
	#Hmm... yeah, maybe I really should just remove ? in disambiguate.normalize_name...
	('Wolfenstein 3-D', 'Wolfenstein 3D'),
]

#Add "The " in front of these things (but not if there's already "The " in front of them of course)
add_the = [
	'Lion King', 
	'Goonies',
]

#Only check for this at the start of a thing
subtitle_removal = [('After Burner Complete ~ After Burner', 'After Burner Complete'),
	('Art of Fighting / Ryuuko no Ken', 'Art of Fighting'), 
	('Batman Forever The Arcade Game', 'Batman Forever'),
	('Breakout ~ Breakaway IV', 'Breakout'),
	("Chaotix ~ Knuckles' Chaotix", "Knuckles' Chaotix"),
	('Chaotix Featuring Knuckles the Echidna', "Knuckles' Chaotix"),
	('Circus / Acrobat TV', 'Circus'),
	('Circus Atari', 'Circus'),
	('Cyber Brawl ~ Cosmic Carnage', 'Cosmic Carnage'),
	('Galaga - Demons of Death', 'Galaga'),
	('G-Sonic ~ Sonic Blast', 'Sonic Blast'),
	("Ironman Ivan Stewart's Super Off-Road", "Super Off-Road"), 
	("Ivan 'Ironman' Stewart's Super Off Road", "Super Off-Road"),
	('MegaMania - A Space Nightmare', 'MegaMania'),
	('Metal Slug 2 - Super Vehicle-001/II', 'Metal Slug 2'),
	('Metal Slug X - Super Vehicle-001', 'Metal Slug X'),
	('Miner 2049er - Starring Bounty Bob', 'Miner 2049er'),
	('Miner 2049er Starring Bounty Bob', 'Miner 2049er'),
	("Montezuma's Revenge featuring Panama Joe", "Montezuma's Revenge"),
	("Montezuma's Revenge - Featuring Panama Joe", "Montezuma's Revenge"),
	('Parodius - Shinwa kara Owarai e', 'Parodius'), 
	#Technically wrong, Parodius is the first game on MSX and Parodius DA!  is the sequel but it's called Parodius in Europe which is annoying and I've already gotten rid of the DA! as above and everything confusing
	('Pitfall II - Lost Caverns', 'Pitfall II'),
	('Pitfall II - The Lost Caverns', 'Pitfall II'),
	("Pitfall! - Pitfall Harry's Jungle Adventure", "Pitfall!"),
	('Puzzle Bobble 2 / Bust-A-Move Again', 'Puzzle Bobble 2'),
	('Puzzle Bobble / Bust-A-Move', 'Puzzle Bobble'), #Fuck you America
	('Q*bert for Game Boy', 'Q*bert'), #This wouldn't be confusing if there wasn't another Q*Bert for Game Boy Color
	('Shadow Squadron ~ Stellar Assault', 'Stellar Assault'),
	('SimAnt - The Electronic Ant Colony', 'SimAnt'), 
	('SimCity 2000 - The Ultimate City Simulator', 'SimCity 2000'), 
	('SimEarth - The Living Planet', 'SimEarth'), 
	("Sonic 3D Blast ~ Sonic 3D Flickies' Island", 'Sonic 3D Blast'),
	('Space Invaders / Space Invaders M', 'Space Invaders'),
	('Street Fighter II: The World Warrior', 'Street Fighter II'), 
	('Super Street Fighter II: The New Challengers', 'Super Street Fighter II'), 
	('Who Wants to Be a Millionaire - 2nd Edition', 'Who Wants to Be a Millionaire'), #This is not even a 2nd edition of anything, it's just the GBC version
	('Ys III - Wanderers from Ys', 'Ys III'),
]
