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
	System('Game Boy', 'gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'MAME (Game Boy Color)', 'MAME (Super Game Boy)']),
	System('GBA', 'gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)']), 
	System('SNES', 'snes', ['snes'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)']),
	System('N64', 'n64', ['n64'], ['Mupen64Plus']), 
	System('Mega Drive', 'megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)']),
	System('Game Gear', 'gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)']),
	System('Master System', 'sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)']),
	System('PSP', None, [], ['PPSSPP']),
	System('Neo Geo Pocket', 'ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)']),
	System('Atari 2600', 'a2600', ['a2600', 'a2600_cass'], ['Stella']), 
	System('Pokemon Mini', 'pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)']),
	System('NES', 'nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass'], ['Mednafen (NES)']),
	System('Mega CD', 'megacd', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion']), 
	System('SG-1000', 'sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)']),
	System('PC Engine', 'pce', ['pce', 'sgx'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']), 
	System('PC Engine CD', 'pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']), 
	System('Virtual Boy', 'vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)']),
	System('Atari 7800', 'a7800', ['a7800'], ['MAME (Atari 7800)']), 
	System('Neo Geo CD', 'neocdz', ['neocd'], ['MAME (Neo Geo CD)']),
	System('Atari 5200', 'a5200', ['a5200'], ['MAME (Atari 5200)']), 

	System('Watara Supervision', 'svision', ['svision'], ['MAME (Watara Supervision)']), 
	System('Casio PV-1000', 'pv1000', ['pv1000'], ['MAME (PV-1000)']),
	System('Arcadia 2001', 'arcadia', ['arcadia'], ['MAME (Arcadia 2001)']), 
	System('Entex Adventure Vision', 'advision', ['advision'], ['MAME (Entex Adventure Vision)']), 
	System('Vectrex', 'vectrex', ['vectrex'], ['MAME (Vectrex)']), 
	System('Mega Duck', 'megaduck', ['megaduck'], ['MAME (Mega Duck)']), 
	System('Amstrad GX4000', 'gx4000', ['gx4000'], ['MAME (Amstrad GX4000)', 'MAME (Amstrad CPC+)']), 
	System('Gamate', 'gamate', ['gamate'], ['MAME (Gamate)']),
	System('Epoch Game Pocket Computer', 'gamepock', ['gamepock'], ['MAME (Game Pocket Computer']),

	#These ones may have control schemes that don't actually map too easily to a normal XInput controller or any other
	#controller that looks like the kind of controller that's standard these days (y'know what I mean, []), or other weirdness
	System('Colecovision', 'coleco', ['coleco'], ['MAME (ColecoVision)']), 
	System('Intellivison', 'intv', ['intv', 'intvecs'], ['MAME (Intellivision)', 'MAME (Intellivoice)', 'MAME (Intellivision ECS)', 'MAME (Intellivision Keyboard)']), 
	System('APF-MP1000', 'apfm1000', ['apfm1000'], ['MAME (APF-MP1000)']),
	System('Astrocade', 'astrocde', ['astrocde'], ['MAME (Astrocade)']), 
	System('Channel F', 'channelf', ['channelf'], ['MAME (Channel F)']), 
	System('Lynx', 'lynx', ['lynx'], ['Mednafen (Lynx)']), 
	System('WonderSwan', 'wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)']), 
	
	#Computers!  These actually aren't that bad control-wise because most sensible games would use a simple one-button
	#joystick, and most of the time MAME lets you attach one.  But some of them don't!  And the ones that don't just use
	#any damn keys they want!  And some software might only work properly with particular models of a computer within an
	#allegedly compatible family!  Yaaaay!  But they have games, so let's put them in here
	#I avoid using anything which requires me to input arcane commands or hear arcane sounds here or wait for arcane
	#times, though I suppose I _could_ do that, it just doesn't feel like a nicely organized bunch of launcher scripts if
	#I do that
	System('MSX', 'svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX1)', 'MAME (MSX2)']), 
	System('MSX2', 'fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop'], ['MAME (MSX2)']), 
	System('VIC-20', 'vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)']),
	System('Casio PV-2000', 'pv2000', ['pv2000'], ['MAME (PV-2000)']), 
	System('Sord M5', 'm5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)']), 
	System('Atari 8-bit', 'a800', ['a800', 'a800_flop', 'xegs'], ['MAME (Atari 8-bit)']), 
	System('PlayStation', 'psj', ['psx'], ['Mednafen (PS1)']), 
	System('GameCube', 'gcjp', [], ['Dolphin']),
	System('3DS', None, [], ['Citra']), 
	System('DS', None, [], ['Medusa']),
	System('PS2', 'ps2', [], ['PCSX2']), 
	System('32X', '32x', ['32x'], ['Kega Fusion']), 
	System('CD-i', 'cdimono1', ['cdi'], ['MAME (CD-i)']),
	System('Game.com', 'gamecom', ['gamecom'], ['MAME (Game.com)']),
	
	System('Sufami Turbo', 'snes', ['snes_strom'], ['MAME (Sufami Turbo)']),
	System('Satellaview', 'snes', ['snes_bspack'], ['MAME (Satellaview)']),

	System('Wii', None, [], ['Dolphin']), 
	System('Saturn', 'saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)']), 

	System('Tomy Tutor', 'tutor', ['tutor'], ['MAME (Tomy Tutor)']), 
	System('C64', 'c64', ['c64_cart', 'c64_cass', 'c64_flop'], ['MAME (C64)']),
	System('VIC-10', 'vic10', ['vic10'], ['MAME (VIC-10)']), 
	System('Sharp X1', 'x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)']), 
	System('Sharp X68000', 'x68000', ['x68k_flop'], ['MAME (Sharp X68000)']),
]
