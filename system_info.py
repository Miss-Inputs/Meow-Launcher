class System():
	def __init__(self, name, mame_driver, mame_software_lists):
		self.name = name
		self.mame_driver = mame_driver
		self.mame_software_lists = mame_software_lists

systems = [
	System('Game Boy', 'gbcolor', ['gameboy', 'gbcolor']),
	System('GBA', 'gba', ['gba']), 
	System('SNES', 'snes', ['snes']),
	System('N64', 'n64', ['n64']), 
	System('Mega Drive', 'megadriv', ['megadriv']),
	System('Game Gear', 'gamegear', ['gamegear']),
	System('Master System', 'sms', ['sms']),
	System('PSP', None, []),
	System('Neo Geo Pocket', 'ngpc', ['ngp', 'ngpc']),
	System('Atari 2600', 'a2600', ['a2600', 'a2600_cass']), 
	System('Pokemon Mini', 'pokemini', ['pokemini']),
	System('NES', 'nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom']),
	System('Mega CD', 'megacd', ['megacd', 'megacdj', 'segacd']), 
	System('SG-1000', 'sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000']),
	System('PC Engine', 'pce', ['pce', 'sgx']), 
	System('PC Engine CD', 'pce', ['pcecd']), 
	System('Virtual Boy', 'vboy', ['vboy']),
	System('Atari 7800', 'a7800', ['a7800']), 
	System('Neo Geo CD', 'neocdz', ['neocd']),
	System('Atari 5200', 'a5200', ['a5200']), 

	System('Watara Supervision', 'svision', ['svision']), 
	System('Casio PV-1000', 'pv1000', ['pv1000']),
	System('Arcadia 2001', 'arcadia', ['arcadia']), 
	System('Entex Adventure Vision', 'advision', ['advision']), 
	System('Vectrex', 'vectrex', ['vectrex']), 
	System('Mega Duck', 'megaduck', ['megaduck']), 
	System('Amstrad GX4000', 'gx4000', ['gx4000']), 
	System('Gamate', 'gamate', ['gamate']),
	System('Epoch Game Pocket Computer', 'gamepock', ['gamepock']),

	#These ones may have control schemes that don't actually map too easily to a normal XInput controller or any other
	#controller that looks like the kind of controller that's standard these days (y'know what I mean, []), or other weirdness
	System('Colecovision', 'coleco', ['coleco']), 
	System('Intellivison', 'intv', ['intv', 'intvecs']), 
	System('APF-MP1000', 'apfm1000', ['apfm1000']),
	System('Astrocade', 'astrocde', ['astrocde']), 
	System('Channel F', 'channelf', ['channelf']), 
	System('Lynx', 'lynx', ['lynx']), 
	System('WonderSwan', 'wscolor', ['wswan', 'wscolor']), 
	
	#Computers!  These actually aren't that bad control-wise because most sensible games would use a simple one-button
	#joystick, and most of the time MAME lets you attach one.  But some of them don't!  And the ones that don't just use
	#any damn keys they want!  And some software might only work properly with particular models of a computer within an
	#allegedly compatible family!  Yaaaay!  But they have games, so let's put them in here
	#I avoid using anything which requires me to input arcane commands or hear arcane sounds here or wait for arcane
	#times, though I suppose I _could_ do that, it just doesn't feel like a nicely organized bunch of launcher scripts if
	#I do that
	System('MSX', 'svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop']), 
	System('MSX2', 'fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop']), 
	System('VIC-20', 'vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop']),
	System('Casio PV-2000', 'pv2000', ['pv2000']), 
	System('Sord M5', 'm5', ['m5_cart', 'm5_cass', 'm5_flop']), 
	System('Atari 8-bit', 'a800', ['a800', 'a800_flop', 'xegs']), 
	System('PlayStation', 'psj', ['psx']), 
	System('GameCube', 'gcjp', []),
	System('3DS', None, []), 
	System('DS', None, []),
	System('PS2', 'ps2', []), 
	System('32X', '32x', ['32x']), 
	System('CD-i', 'cdimono1', ['cdi']),
	System('Game.com', 'gamecom', ['gamecom']),
	
	#TODO: These two shouldn't be systems, and there should just be SNES and this has an autodetection thing to switch to MAME if Snes9x GTK would otherwise be used (because it can't do these from the command line just yet) when encountering .bs or .st files
	System('Sufami Turbo', 'snes', ['snes_strom']),
	System('Satellaview', 'snes', ['snes_bspack']),

	System('Wii', None, []), 
	System('Saturn', 'saturn', ['saturn', 'sat_cart', 'sat_vccart']), 

	System('Tomy Tutor', 'tutor', ['tutor']), 
	System('C64', 'c64', ['c64_cart', 'c64_cass', 'c64_flop']),
	System('VIC-10', 'vic10', ['vic10']), 
	System('Sharp X1', 'x1', ['x1_cass', 'x1_flop']), 
	System('Sharp X68000', 'x68000', ['x68k_flop']),
]
