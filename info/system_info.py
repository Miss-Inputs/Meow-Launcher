class System():
	def __init__(self, name, mame_driver, mame_software_lists, emulators):
		self.name = name
		self.mame_driver = mame_driver
		self.mame_software_lists = mame_software_lists
		self.emulators = emulators

def get_system_by_name(name):
	for system in systems:
		if system.name == name:
			return system

	return None

def get_mame_driver_by_system_name(name):
	for system in systems:
		if system.name == name:
			return system.mame_driver

	return None

systems = [
	#TODO: Convert to dict where name = key
	System('32X', '32x', ['32x'], ['Kega Fusion']), 
	System('3DS', None, [], ['Citra']), 
	System('Amstrad GX4000', 'gx4000', ['gx4000'], ['MAME (Amstrad GX4000)', 'MAME (Amstrad CPC+)']), 
	System('Arcadia 2001', 'arcadia', ['arcadia'], ['MAME (Arcadia 2001)']), 
	System('Atari 2600', 'a2600', ['a2600', 'a2600_cass'], ['Stella']), 
	System('Atari 5200', 'a5200', ['a5200'], ['MAME (Atari 5200)']), 
	System('Atari 7800', 'a7800', ['a7800'], ['MAME (Atari 7800)']), 
	System('Casio PV-1000', 'pv1000', ['pv1000'], ['MAME (PV-1000)']),
	System('CD-i', 'cdimono1', ['cdi'], ['MAME (CD-i)']),
	System('DS', None, [], ['Medusa']),
	System('Entex Adventure Vision', 'advision', ['advision'], ['MAME (Entex Adventure Vision)']), 
	System('Epoch Game Pocket Computer', 'gamepock', ['gamepock'], ['MAME (Game Pocket Computer)']),
	System('Gamate', 'gamate', ['gamate'], ['MAME (Gamate)']),
	System('Game Boy', 'gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'MAME (Game Boy Color)', 'MAME (Super Game Boy)']),
	System('Game.com', 'gamecom', ['gamecom'], ['MAME (Game.com)']),
	System('GameCube', 'gcjp', [], ['Dolphin']),
	System('Game Gear', 'gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)']),
	System('GBA', 'gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)']), 
	System('Master System', 'sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)']),
	System('Mega CD', 'megacd', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion']), 
	System('Mega Drive', 'megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)']),
	System('Mega Duck', 'megaduck', ['megaduck'], ['MAME (Mega Duck)']), 
	System('Neo Geo CD', 'neocdz', ['neocd'], ['MAME (Neo Geo CD)']),
	System('Neo Geo Pocket', 'ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)']),
	System('NES', 'nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass'], ['Mednafen (NES)']),
	System('PC Engine CD', 'pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']), 
	System('PC Engine', 'pce', ['pce', 'sgx'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']), 
	System('PlayStation', 'psj', ['psx'], ['Mednafen (PS1)']), 
	System('Pokemon Mini', 'pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)']),
	System('PS2', 'ps2', [], ['PCSX2']), 
	System('PSP', None, [], ['PPSSPP']),
	System('SG-1000', 'sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)']),
	System('SNES', 'snes', ['snes'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)']),
	System('Vectrex', 'vectrex', ['vectrex'], ['MAME (Vectrex)']), 
	System('Virtual Boy', 'vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)']),
	System('Watara Supervision', 'svision', ['svision'], ['MAME (Watara Supervision)']), 

	#These ones may have control schemes that don't actually map too easily to a normal XInput controller or any other
	#controller that looks like the kind of controller that's standard these days (y'know what I mean), or other weirdness
	System('APF-MP1000', 'apfm1000', ['apfm1000'], ['MAME (APF-MP1000)']),
	System('Astrocade', 'astrocde', ['astrocde'], ['MAME (Astrocade)']), 
	System('Channel F', 'channelf', ['channelf'], ['MAME (Channel F)']), 
	System('Colecovision', 'coleco', ['coleco'], ['MAME (ColecoVision)']), 
	System('Intellivison', 'intv', ['intv', 'intvecs'], ['MAME (Intellivision)', 'MAME (Intellivoice)', 'MAME (Intellivision ECS)', 'MAME (Intellivision Keyboard)']), 
	System('Lynx', 'lynx', ['lynx'], ['Mednafen (Lynx)']), 
	System('N64', 'n64', ['n64'], ['Mupen64Plus']), 
	System('Saturn', 'saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)']), 
	#Not the most easily mappable of controllers due to having both 6 face buttons and 2 shoulder buttons
	System('Wii', None, [], ['Dolphin']), 
	System('WonderSwan', 'wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)']), 


	#Computers!  These actually aren't that bad control-wise because most sensible games would use a simple one-button
	#joystick, and most of the time MAME lets you attach one.  But some of them don't!  And the ones that don't just use
	#any damn keys they want!  And some software might only work properly with particular models of a computer within an
	#allegedly compatible family!  Yaaaay!  But they have games, so let's put them in here
	#I avoid using anything which requires me to input arcane commands or hear arcane sounds here or wait for arcane
	#times, though I suppose I _could_ do that, it just doesn't feel like a nicely organized bunch of launcher scripts if
	#I do that
	System('Atari 8-bit', 'a800', ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)']), 
	System('C64', 'c64', ['c64_cart', 'c64_cass', 'c64_flop'], ['MAME (C64)']),
	System('Casio PV-2000', 'pv2000', ['pv2000'], ['MAME (PV-2000)']), 
	System('MSX2', 'fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop'], ['MAME (MSX2)']), 
	System('MSX', 'svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX1)', 'MAME (MSX2)']), 
	System('Sharp X1', 'x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)']), 
	System('Sharp X68000', 'x68000', ['x68k_flop'], ['MAME (Sharp X68000)']),
	System('Sord M5', 'm5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)']), 
	System('Tomy Tutor', 'tutor', ['tutor'], ['MAME (Tomy Tutor)']), 
	System('VIC-10', 'vic10', ['vic10'], ['MAME (VIC-10)']), 
	System('VIC-20', 'vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)']),

	#These shouldn't actually be systems, but anyway, I have a Github issue for that I think so leave me alone
	System('Satellaview', 'snes', ['snes_bspack'], ['MAME (Satellaview)']),
	System('Sufami Turbo', 'snes', ['snes_strom'], ['MAME (Sufami Turbo)']),
]

#TODO: Those should just be considered emulated systems, need to add these as well:
#Arcade: I guess it's not an array, it's just MAME
#Engines: Doom
#Computers: Mac, DOS (well, they're emulated too, but differently than the above systems)
#This allows us to organize supported emulators easily and such
