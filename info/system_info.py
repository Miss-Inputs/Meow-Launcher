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
	System('Atari 2600', 'a2600', ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)']), 
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
	System('NES', 'nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)']),
	System('PC Engine CD', 'pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']), 
	System('PC Engine', 'pce', ['pce', 'sgx'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']), 
	System('PC-FX', 'pcfx', ['pcfx'], ['Mednafen (PC-FX)']),
	System('PlayStation', 'psj', ['psx'], ['Mednafen (PS1)']), 
	System('Pokemon Mini', 'pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)']),
	System('PS2', 'ps2', [], ['PCSX2']), 
	System('PSP', None, [], ['PPSSPP']),
	System('SG-1000', 'sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)']),
	System('SNES', 'snes', ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)']),
	System('Vectrex', 'vectrex', ['vectrex'], ['MAME (Vectrex)']), 
	System('Virtual Boy', 'vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)']),
	System('Watara Supervision', 'svision', ['svision'], ['MAME (Watara Supervision)']), 

	#These ones may have control schemes that don't actually map too easily to a normal XInput controller or any other
	#controller that looks like the kind of controller that's standard these days (y'know what I mean), or other weirdness
	System('Benesse Pocket Challenge V2', None, ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)']),
	#Controls are mapped even worse than regular WonderSwan games, even with rotation auto-adjust you still end up using a stick/dpad as buttons and it gets weird, also the module must be forced or else it won't be recognized. But it works though
	System('Channel F', 'channelf', ['channelf'], ['MAME (Channel F)']), 
	#It has some sort of knob that you twist up and down or something? What the fuck
	System('Lynx', 'lynx', ['lynx'], ['Mednafen (Lynx)']), 
	#uhhh it's like ambidextrous or something? Remind me to look into this again later
	System('Wii', None, [], ['Dolphin']), 
	#Heckin motion controls, what are you gonna do... how do you replicate 3D movement without having 3D movement, really. Of course you could argue 3DS has the same problem but motion controls are used a lot less there. I think I heard something about Dolphin implementing per-game controller profiles or somethinig like that though, so once that all works nicely I might move Wii out of this category
	System('WonderSwan', 'wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)']), 
	#Rotates around so that sometimes the dpad becomes buttons and vice versa and there's like two dpads??? but if you use Mednafen's rotation auto-adjust thing it kinda works

	#Hecking keypads, but I guess they're fine if you're using a keyboard with a keypad
	System('APF-MP1000', 'apfm1000', ['apfm1000'], ['MAME (APF-MP1000)']),
	System('Astrocade', 'astrocde', ['astrocde'], ['MAME (Astrocade)']), 
	System('Colecovision', 'coleco', ['coleco'], ['MAME (ColecoVision)']), 
	System('Intellivison', 'intv', ['intv', 'intvecs'], ['MAME (Intellivision)', 'MAME (Intellivoice)', 'MAME (Intellivision ECS)', 'MAME (Intellivision Keyboard)']), 
	System('VC 4000', 'vc4000', ['vc4000'], ['MAME (VC 4000)']),
	
	#More than 6 buttons, would be okay if you have an older gamepad that had 6 face buttons before the industry decided 4 face buttons was the way to go (N64 or Saturn controllers with USB adapters work well, even for each other's control schemes; or one of those late 90s gamepads like the kind I have lying around)
	System('N64', 'n64', ['n64'], ['Mupen64Plus']), 
	System('Saturn', 'saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)']), 

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
	System('Coleco Adam', 'adam', ['adam_cart', 'adam_cass', 'adam_flop'], ['MAME (Coleco Adam)']),
	System('MSX2', 'fsa1wsx', ['msx2_cart', 'msx2_cass', 'msx2_flop'], ['MAME (MSX2)']), 
	System('MSX', 'svi738', ['msx1_cart', 'msx1_cass', 'msx1_flop'], ['MAME (MSX1)', 'MAME (MSX2)']), 
	System('Sharp X1', 'x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)']), 
	System('Sharp X68000', 'x68000', ['x68k_flop'], ['MAME (Sharp X68000)']),
	System('Sord M5', 'm5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)']), 
	System('Tomy Tutor', 'tutor', ['tutor'], ['MAME (Tomy Tutor)']), 
	System('VIC-10', 'vic10', ['vic10'], ['MAME (VIC-10)']), 
	System('VIC-20', 'vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)']),
	System('ZX Spectrum', 'spectrum', ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)']),
	#Joystick interface is non-standard so not all games support it and might decide to use the keyboard instead, but eh. It works I guess.

	#No emulators that are cool enough on Linux. Yet. Maybe? That I know of. They're here for completeness.
	#They are also here to remind me to check up on them every now and again to make sure they indeed don't work or if I was just being stupid all along
	System('3DO', '3do', [], []),
	#4DO doesn't like Wine and has no native Linux version (just libretro and meh), Phoenix Emu has no command line support
	System('Bandai Playdia', None, [], []),
	System('Casio Loopy', 'casloopy', ['casloopy'], []),
	System('FM Towns Marty', 'fmtmarty', ['fmtowns_cd', 'fmtowns_flop'], []),
	#MAME driver has corrupted graphics in a lot of things. These games do work with FM Towns Not-Marty but then I'm using a computer instead of a console, so I'd have to verify that everything would still work the way I expect, and I think it doesn't...
	System('GameKing', 'gameking', ['gameking'], []),
	System('GameKing 3', 'gamekin3', ['gameking3'], []),
	System('GP32', 'gp32', ['gp32'], []),
	#Runs too slow to verify if anything else works, but all documentation points to not
	System('Hartung Game Master', 'gmaster', ['gmaster'], []),
	#No sound (but seems to work fine otherwise? maybe)
	System('IBM PCjr', 'ibmpcjr', ['ibmpcjr_cart'], []),
	#For the carts, because otherwise we'd just call the software DOS or PC Booter. Has the same problem as PC booter disks in that the joystick tends to play up.
	System('Jaguar', 'jaguar', ['jaguar'], []),
	#Virtual Jaguar doesn't like gamepads seemingly, and Phoenix Emu has no command line support
	System('Konami Picno', 'picno', ['picno'], []),
	System('Leapster', 'leapster', ['gameking'], []),
	System('Microvision', 'microvsn', ['microvision'], []),
	System('N-Gage', None, [], []),
	System('PC Booter', 'ibm5150', [], []),
	#This one is a bit tricky... both MAME and PCem have issues emulating a joystick. Do the games actually just suck like that? I don't know. The majority of these games assume a 4.77MHz CPU, of course. The software list is ibm5150 but that has some DOS games too, just to be confusing.
	System('Pippin', 'pippin', ['pippin', 'pippin_flop'], []),
	#Games don't just boot in a PPC Mac, unfortunately
	System('RCA Studio 2', 'studio2', ['studio2'], []),
	System("Super A'Can", 'supracan', ['supracan'], []),
	System('V.Smile', 'vsmile', ['vsmile_cart', 'vsmile_cd', 'vsmileb_cart', 'vsmilem_cart'], []),
	System('Xbox 360', None, [], []),
	#Xenia requires Windows 8 + Vulkan, somehow I don't think it'd ever run under Wine either
	System('ZAPit GameWave', None, [], []),

	#My computer isn't cool enough to emulate these systems, so I can't verify how they work or how well they work just yet
	System('Uzebox', 'uzebox', ['uzebox'], []),
	#MAME looks like it works, but at like 50% speed
	System('Wii U', None, [], []),
	#Decaf requires OpenGL 4.5 (even for software rendering it seems)

	#Things that have usability issues
	System('Apple IIgs', 'apple2gs', ['apple2gs'], []),
	#Some games require a hard disk with an OS install and they won't tell you this because of course not, and if you want to autoboot the floppies with a hard drive still in there you have to set it to always boot from slot 5 and it's really annoying and I hate it
	System('Cybiko', 'cybikov1', [], []),
	#Quickload slot doesn't seem to actually quickload anything, and seems to require setup each time. V2 and Extreme have same problems
	System('CreatiVision', 'crvision', ['crvision'], []),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it
	System('Mattel Aquarius', 'aquarius', [], []),
	#Controllers aren't emulated yet
	System('PocketStation', 'pockstat', [], []),
	#Makes you set time and date each time
	System('Dreamcast VMU', 'svmu', ['svmu'], []),
	#Makes you set time and date each time; also supposed to have sound apparently but I don't hear any
	System('Super Casette Vision', 'scv', ['scv'], []),
	#Only supports some games (e.g. with RAM enhancements) via software list, there's no way to override the cart type or anything like that. 
	System('SVI-3x8', 'svi328', ['svi318_cart', 'svi318_cass', 'svi318_flop'], []),
	#Works well, just needs to autoboot tapes, and that might be tricky because you have BLOAD and CLOAD
	System('ZX81', 'zx81', ['zx80_cass', 'zx81_cass'], []),
	#Not even gonna try testing any more software without autobooting it, though I'm not sure it does work from the one I did. Anyway, gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing, and even then it's like.... meh....

	#Might just be me doing something wrong, but seemingly doesn't work so I'll just put them here until I figure out if they definitely don't work, or they actually do
	System('Radio 86-RK', 'radio86', ['radio86_cart', 'radio86_cass'], []),
	System('Mikrosha', 'mikrosha', ['mikrosha_cart', 'mikrosha_cass'], []),
	System('Apogey BK-01', 'apogee', ['apogee'], []),
	System('Partner 01.01', 'partner', ['partner_cass', 'partner_flop'], []),
	System('Orion 128', 'orion128', ['orion_cart', 'orion_cass', 'orion_flop'], []),
	System('PC-6001', 'pc6001', [], []),
	System('FM-7', 'fm7', ['fm7_cass', 'fm7_disk', 'fm77av'], []),

	#Gonna try these again but they weren't working last time I checked
	System('Dreamcast', 'dc', ['dc'], []),
	#MAME requires a much better computer than what I have now to emulate at full speed; there are also Reicast and a few others; lxdream wouldn't compile
	System('Magnavox Odyssey²', 'odyssey2', ['odyssey2'], []),
	#O2EM doesn't really work; MAME should though, there's nothing that suggests emulation is inaccurate or some software is unsupported
	System('PC-88', 'pc8801', ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], []),
	#On the wiki I said "too many various issues with various games" which isn't really a good enough description of why it does or doesn't work
]

#TODO: Those should just be considered emulated systems, need to add these as well:
#Arcade: I guess it's not an array, it's just MAME
#Engines: Doom, later ScummVM and Quake... these may need to be thought about differently
#Computers: Mac, DOS (well, they're emulated too, but differently than the above systems)
#Other: J2ME, Flash
#This allows us to organize supported emulators easily and such
