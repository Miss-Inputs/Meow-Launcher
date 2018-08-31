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

	for k, v in games_with_engines.items():
		if k == name:
			return v

	return None

def get_mame_driver_by_system_name(name):
	for system in systems:
		if system.name == name:
			return system.mame_driver

	return None

def get_mame_software_list_names_by_system_name(name):
	for system in systems:
		if system.name == name:
			return system.mame_software_lists

	return None

systems = [
	#TODO: Convert to dict where name = key (but would that work out? hmm)

	System('3DS', None, [], ['Citra']),
	System('Amstrad GX4000', 'gx4000', ['gx4000'], ['MAME (Amstrad GX4000)', 'MAME (Amstrad CPC+)']),
	System('APF-MP1000', 'apfm1000', ['apfm1000'], ['MAME (APF-MP1000)']),
	System('Arcadia 2001', 'arcadia', ['arcadia'], ['MAME (Arcadia 2001)']),
	System('Astrocade', 'astrocde', ['astrocde'], ['MAME (Astrocade)']),
	System('Atari 2600', 'a2600', ['a2600', 'a2600_cass'], ['Stella', 'MAME (Atari 2600)']),
	System('Atari 5200', 'a5200', ['a5200'], ['MAME (Atari 5200)']),
	System('Atari 7800', 'a7800', ['a7800'], ['MAME (Atari 7800)']),
	System('Benesse Pocket Challenge V2', None, ['pockchalv2'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)']),
	#Controls are mapped even worse than regular WonderSwan games, even with rotation auto-adjust you still end up using a stick/dpad as buttons and it gets weird, also the module must be forced or else it won't be recognized. But it works though
	System('Casio PV-1000', 'pv1000', ['pv1000'], ['MAME (PV-1000)']),
	System('CD-i', 'cdimono1', ['cdi'], ['MAME (CD-i)']),
	System('Channel F', 'channelf', ['channelf'], ['MAME (Channel F)']),
	#It has some sort of knob that you twist up and down or something? What the fuck
	System('Colecovision', 'coleco', ['coleco'], ['MAME (ColecoVision)']),
	System('Dreamcast', 'dc', ['dc'], ['Reicast']),
	System('DS', 'nds', [], ['Medusa']),
	System('Entex Adventure Vision', 'advision', ['advision'], ['MAME (Entex Adventure Vision)']),
	System('Epoch Game Pocket Computer', 'gamepock', ['gamepock'], ['MAME (Game Pocket Computer)']),
	System('Gamate', 'gamate', ['gamate'], ['MAME (Gamate)']),
	System('Game Boy', 'gbpocket', ['gameboy', 'gbcolor'], ['Gambatte', 'mGBA', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'MAME (Game Boy Color)', 'MAME (Super Game Boy)', 'Medusa']),
	System('Game.com', 'gamecom', ['gamecom'], ['MAME (Game.com)']),
	System('GameCube', 'gcjp', [], ['Dolphin']),
	System('Game Gear', 'gamegear', ['gamegear'], ['Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)']),
	System('GBA', 'gba', ['gba'], ['mGBA', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa']),
	System('Hartung Game Master', 'gmaster', ['gmaster'], ['MAME (Hartung Game Master)']),
	System('Intellivision', 'intv', ['intv', 'intvecs'], ['MAME (Intellivision)', 'MAME (Intellivoice)', 'MAME (Intellivision ECS)', 'MAME (Intellivision Keyboard)']),
	System('IBM PCjr', 'ibmpcjr', ['ibmpcjr_cart'], ['MAME (IBM PCjr)']),
	#For the carts, because otherwise we'd just call the software DOS or PC Booter.
	System('Lynx', 'lynx', ['lynx'], ['Mednafen (Lynx)']),
	#uhhh it's like ambidextrous or something? Remind me to look into this again later
	System('Master System', 'sms', ['sms'], ['Kega Fusion', 'Mednafen (Master System)']),
	System('Mattel Juice Box', 'juicebox', ['juicebox'], ['MAME (Juice Box)']),
	#Now for those who actually do know what this is, you may be thinking: But doesn't that just play videos? Isn't this really pointless? And the answer is yes, yes it is. I love pointless.
	System('Mega Drive', 'megadriv', ['megadriv'], ['Kega Fusion', 'Mednafen (Mega Drive)']),
	System('Mega Duck', 'megaduck', ['megaduck'], ['MAME (Mega Duck)']),
	System('N64', 'n64', ['n64'], ['Mupen64Plus']),
	System('Neo Geo CD', 'neocdz', ['neocd'], ['MAME (Neo Geo CD)']),
	System('Neo Geo Pocket', 'ngpc', ['ngp', 'ngpc'], ['Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)']),
	System('NES', 'nes', ['nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'], ['Mednafen (NES)', 'MAME (NES)']),
	System('PC Engine', 'pce', ['pce', 'sgx', 'tg16'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']),
	System('PC-FX', 'pcfx', ['pcfx'], ['Mednafen (PC-FX)']),
	System('PlayStation', 'psj', ['psx'], ['Mednafen (PS1)']),
	System('Pokemon Mini', 'pokemini', ['pokemini'], ['PokeMini', 'PokeMini (wrapper)', 'MAME (Pokemon Mini)']),
	System('PS2', 'ps2', [], ['PCSX2']),
	System('PSP', None, [], ['PPSSPP']),
	System('SG-1000', 'sg1000', ['sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'], ['Kega Fusion', 'MAME (SG-1000)']),
	System('Saturn', 'saturn', ['saturn', 'sat_cart', 'sat_vccart'], ['Mednafen (Saturn)']),
	System('SNES', 'snes', ['snes', 'snes_bspack', 'snes_strom'], ['Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)']),
	System('Uzebox', 'uzebox', ['uzebox'], ['MAME (Uzebox)']),
	System('VC 4000', 'vc4000', ['vc4000'], ['MAME (VC 4000)']),
	System('Vectrex', 'vectrex', ['vectrex'], ['MAME (Vectrex)']),
	System('Virtual Boy', 'vboy', ['vboy'], ['Mednafen (Virtual Boy)', 'MAME (Virtual Boy)']),
	System('Watara Supervision', 'svision', ['svision'], ['MAME (Watara Supervision)']),
	System('Wii', None, [], ['Dolphin']),
	#Heckin motion controls, what are you gonna do... how do you replicate 3D movement without having 3D movement, really. Of course you could argue 3DS has the same problem but motion controls are used a lot less there. I think I heard something about Dolphin implementing per-game controller profiles or somethinig like that though, so once that all works nicely I might move Wii out of this category
	System('WonderSwan', 'wscolor', ['wswan', 'wscolor'], ['Mednafen (WonderSwan)', 'MAME (WonderSwan)']),
	#Rotates around so that sometimes the dpad becomes buttons and vice versa and there's like two dpads??? but if you use Mednafen's rotation auto-adjust thing it kinda works

	#Systems that are treated as though they were whole separate things, but they're addons for other systems with their own distinct set of software
	System('32X', '32x', ['32x'], ['Kega Fusion']),
	System('Mega CD', 'megacd', ['megacd', 'megacdj', 'segacd'], ['Kega Fusion']),
	System('PC Engine CD', 'pce', ['pcecd'], ['Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)']),

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
	System('PC-88', 'pc8801', ['pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'], ['MAME (PC-88)']),
	System('Sharp X1', 'x1', ['x1_cass', 'x1_flop'], ['MAME (Sharp X1)']),
	System('Sharp X68000', 'x68000', ['x68k_flop'], ['MAME (Sharp X68000)']),
	System('Sord M5', 'm5', ['m5_cart', 'm5_cass', 'm5_flop'], ['MAME (Sord M5)']),
	System('Tomy Tutor', 'tutor', ['tutor'], ['MAME (Tomy Tutor)']),
	System('VIC-10', 'vic10', ['vic10'], ['MAME (VIC-10)']),
	System('VIC-20', 'vic20', ['vic1001_cart', 'vic1001_cass', 'vic1001_flop'], ['MAME (VIC-20)']),
	System('VZ-200', 'vz200', ['vz_cass'], ['MAME (VZ-200)']),
	#There are many different systems in this family, but I'll go with this one, because the software list is named after it
	System('ZX Spectrum', 'spectrum', ['spectrum_cart', 'spectrum_cass', 'specpls3_flop'], ['MAME (ZX Spectrum)']),
	#Joystick interface is non-standard so not all games support it and might decide to use the keyboard instead, but eh. It works I guess.

	#Unsupported (yet) systems beyond this point

	#Theoretically supported, but not supported enough to be considered playable, but you could configure them if you wanted (see emulator_info)
	System('FM Towns Marty', 'fmtmarty', ['fmtowns_cd', 'fmtowns_flop'], ['MAME (FM Towns Marty)']),
	System('Jaguar', 'jaguar', ['jaguar'], ['MAME (Atari Jaguar)']),
	System('Magnavox Odyssey²', 'odyssey2', ['odyssey2'], []),
	#O2EM doesn't really work; MAME isn't completely broken but a lot of games have broken graphics so like... ehh
	System('G7400', 'g7400', ['g7400'], []),
	#just has the same problems as Odyssey 2...
	System('PC Booter', 'ibm5150', ['ibm5150'], ['MAME (IBM PCjr)', 'MAME (IBM PC)']),
	#This one is a bit tricky... both MAME and PCem have issues emulating a joystick. Do the games actually just suck like that? _All of them_? I don't know. The majority of these games assume a 4.77MHz CPU, of course. The software list is ibm5150 but that has some DOS games too, just to be confusing (but usage == 'PC booter' where it is a PC booter).
	System("Super A'Can", 'supracan', ['supracan'], []),
	#Some things work in MAME, except with no sound, so... nah

	#No emulators that are cool enough on Linux. Yet. Maybe? That I know of. They're here for completeness. Or no emulators at all.
	#They are also here to remind me to check up on them every now and again to make sure they indeed don't work or if I was just being stupid all along
	System('3DO', '3do', [], []),
	#4DO doesn't like Wine and has no native Linux version (just libretro and meh), Phoenix Emu has no command line support; so both are unusable for our purposes. MAME driver just kinda hangs at the 3DO logo at the moment
	System('3DO M2', '3do_m2', ['3do_m2'], []),
	#Was never actually released, but prototypes exist
	System('Bandai Playdia', None, [], []),
	System('Casio Loopy', 'casloopy', ['casloopy'], []),
	System('GameKing', 'gameking', ['gameking'], []),
	System('GameKing 3', 'gamekin3', ['gameking3'], []),
	System('GP32', 'gp32', ['gp32'], []),
	#Runs too slow to verify if anything else works, but all documentation points to not
	System('Jaguar CD', 'jaguarcd', [], []),
	#Unlike the lack of CD, this does not work at all on anything, doesn't even have a software list yet
	System('Koei PasoGo', 'pasogo', ['pasogo'], []),
	#No sound in MAME yet, and apparently the rest doesn't work either (I'll take their word for it)
	System('Konami Picno', 'picno', ['picno'], []),
	System('Leapster', 'leapster', ['leapster'], []),
	System('Mattel HyperScan', 'hs', ['hyperscan'], []),
	System('Microvision', 'microvsn', ['microvision'], []),
	#Cartridges boot, but seem to do nothing...
	System('N-Gage', None, [], []),
	System('Pippin', 'pippin', ['pippin', 'pippin_flop'], []),
	#Games don't just boot in a PPC Mac, unfortunately. No PPC Mac emulator has branched off into specific Pippin emulation yet
	System('Sawatte Pico', 'sawatte', ['sawatte'], []),
	#Similar to the Sega Pico but with different software (may or may not also use Megadrive ROM header?), but is completely unemulated
	System('V.Smile', 'vsmile', ['vsmile_cart', 'vsmile_cd', 'vsmileb_cart', 'vsmilem_cart'], []),
	System('Xbox 360', None, [], []),
	#Xenia requires Windows 8 + Vulkan, somehow I don't think it'd ever run under Wine either
	System('ZAPit GameWave', None, [], []),

	#My computer isn't cool enough to emulate these systems, so I can't verify how they work or how well they work just yet
	System('Wii U', None, [], []),
	#Decaf requires OpenGL 4.5 (even for software rendering it seems)

	#Things that have usability issues
	System('64DD', 'n64dd', ['n64dd'], []),
	#Mupen64Plus would work, but right now it has issues with usability that it says right in the readme (so it's not just me picking on them, they say it themselves). Basically you have to have a cart inserted which has the same properties as the 64DD software you want to emulate, and that wouldn't work for our launchering purposes. MAME doesn't seem to work with .ndd format dumps
	System('Apple IIgs', 'apple2gs', ['apple2gs'], []),
	#Some games require a hard disk with an OS install and they won't tell you this because of course not, and if you want to autoboot the floppies with a hard drive still in there you have to set it to always boot from slot 5 and it's really annoying and I hate it
	System('BBC Bridge Companion', 'bbcbc', ['bbcbc'], []),
	#Takes a single .bin file for the -cart slot, but known software dumps are in split ROM format. Unsure how to get around that
	System('Cybiko', 'cybikov1', [], []),
	#Quickload slot doesn't seem to actually quickload anything, and seems to require setup each time. V2 and Extreme have same problems
	System('CreatiVision', 'crvision', ['crvision'], []),
	#The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it
	System('e-Reader', None, ['gba_ereader'], []),
	#VBA-M works (nothing else emulates e-Reader that I know of), but you have to swipe the card manually, which doesn't really work for a nice launcher thing... and there's not really a way around that at this point in time.
	System('Luxor ABC80', 'abc80', ['abc80_cass', 'abc80_flop'], []),
	#Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	System('Mattel Aquarius', 'aquarius', [], []),
	#Controllers aren't emulated yet (and they're necessary for a lot of things)
	System('Nichibutsu My Vision', 'myvision', ['myvision'], []),
	#Same predicament as BBC Bridge Companion above
	System('RCA Studio 2', 'studio2', ['studio2'], []),
	#Due to the console's terrible design, asinine keypad sequences are needed to boot games any further than weird static or a black screen. They're so asinine that even if I look at the info usage in the software list, and do the thing, it still doesn't work. So if it's that complicated that I can't work it out manually, how can I do it programmatically? So yeah, shit
	System('Sega Pico', 'pico', ['pico'], []),
	#Emulation works in Kega Fusion and MAME, but they don't display the actual book, which would be needed for most of the software to make any sense. Kega Fusion doesn't even have controls to turn the pages, which is needed for stuff
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
	System('Orion-128', 'orion128', ['orion_cart', 'orion_cass', 'orion_flop'], []),
	System('PC-6001', 'pc6001', [], []),
	System('FM-7', 'fm7', ['fm7_cass', 'fm7_disk', 'fm77av'], []),

	#TODO: Me being lazy, need to check if these actually work or not:
	System('Acorn Atom', 'atom', ['atom_cass', 'atom_flop', 'atom_rom'], []),
	System('Amiga', 'a1200', ['amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench', 'cd32', 'cdtv'], []),
	#MAME is known to not work here
	System('Apple I', 'apple1', ['apple1'], []),
	System('Apple II', 'apple2', ['apple2', 'apple2_cass'], []),
	System('Apple Lisa', 'lisa', ['lisa'], []),
	System('Apple III', '', ['apple3'], []),
	System('Atari Portfolio', 'pofo', ['pofo'], []),
	#Nothing is dumped, so I think it's safe to say nothing will work, but still. Apparently it's supposed to be a PC clone, but doesn't support any PC software lists...
	System('Atari ST', 'st', ['st_flop', 'st_cart'], []),
	#MAME is known to not work here, and Hatari is known to have usability issues... is there anything else?
	System('Bandai Super Vision 8000', 'sv8000', ['sv8000'], []),
	System('Cambridge Z88', 'z88', ['z88_cart'], []),
	System('Commodore 16', 'c16', ['plus4_cart', 'plus4_cass', 'plus4_flop'], []),
	#Plus/4 and C116 are in the same software family, so those could be used too
	System('Commodore 65', 'c65', ['c65_flop'], []),
	#This was actually never released, but there's software for it anyway
	System('Commodore 128', 'c128', ['c128_cart', 'c128_flop', 'c128_rom'], []),
	System('Neo Geo AES', 'aes', ['neogoeo'], []),
	#Hmm... even emulated re-releases (like the stuff on Steam) is the MVS version. Also how it works is a bit tricky, since as a system you load single .bin files through the cart slot, but everything out there is stored as multiple ROMs, even in the software list... so I dunno if this would be usable
	System('Pocket Challenge W', 'pockchal', ['pockchalw'], []),
	#Everything in that software list says unsupported, so that's not a good sign
	System('Sam Coupe', 'samcoupe', ['samcoupe_cass', 'samcoupe_flop'], []),
	System('Squale', 'squale', ['squale_cart'], []),
	#What's interesting is that the XML for the driver says it's compatible with a software list simply called "squale", but that's not in the default hash directory
	System('Tandy CoCo', 'coco3', ['coco_cart', 'coco_flop'], []),
	#Did I want coco/coco2 instead? Hmm. Those seem to work but coco3 seems to not autoboot. It looks like carts >128K require coco3, or if the software list says so
	System('Xbox', 'xbox', [], []),
	#MAME definitely isn't ready yet.. do XQEMU or Cxbx-Reloaded work for our purposes yet?

	#TODO: Me being lazy, I know if these work or not:
	System('Commodore PET', 'pet4032', ['pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'], []),
	#Unsure which one the "main" driver is, or if some of them count as separate systems. This will require autoboot scripts to do stuff anyway
	#TODO: This can work with -quik and autoboot though
	System('Galaksija', 'galaxyp', ['galaxy'], []),
	#This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why.

	#Other todos, often just me not knowing which something actually is or being too lazy to organize it even into the "too lazy to look into right now" list:
	#Amstrad CPC-not-plus? Not sure how it all works
	#Is Acorn Electron the same as BBC Micro for emulation purposes?
	#Should Amiga CD32 and Commodore CDTV just count as Amiga?
	#APF Imagination Machine just APF-MP1000 or different?
	#Are Oric-1 and Oric Atmos software compatible or different things?
	#Which of Sharp MZ series are software compatible with which? (Software lists: MZ-700, MZ-800, MZ-2000)
	#Which of TI calculators are software compatible with which?
	#Thomson MO: Is MO5 or MO6 the main system? (latter has exclusive software lists, but is compatible with MO5)
	#Thomson MO: Is TO5 or TO8 the main system? (latter has exclusive software lists, but is compatible with TO7)
	#Which TRS-80 model is which?
	#Bandai Super Note Club: Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
	#Memotech MTX: 500 or 512?
	#Dragon 64 part of CoCo or nah?
	#Which PC-98 system is which?
	#Videoton TVC: Which is main system? TV64?
	#Acorn Archimedes stuff (could this end up being amongst dos_mac_common?)
	#Oric stuff (Oric-1 or Oric Atmos)
	#C64DTV
	#Jupiter Ace (ZX Spectrum clone but has different compatibility?)
	#TI-99: Main kerfluffle seems to be .rpk file format needed for -cart loading, but everything else is in .c and .g and who knows what else; -ioport peb -ioport:peb:slot2 32kmem -ioport:peb:slot3 speech might be needed?

	#Epoch (not Super) Casette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
	#Coleco Quiz Wiz Challenge might require its own thing: The software cartridges contain no ROMs, just different pinouts, you need the software list to select which one
]

class GameWithEngine():
	def __init__(self, name, engines, uses_folders):
		self.name = name
		self.engines = engines
		self.uses_folders = uses_folders
games_with_engines = {
	'Doom': GameWithEngine('Doom', ['PrBoom+'], False),
	'Quake': GameWithEngine('Quake', ['Darkplaces'], True),
}
#TODO: There should be a Z-Machine interpreter that runs nicely with modern sensibilities, I should look into that
#Duke Nukem 3D and Wolfenstein 3D definitely have various source ports too, just need to find one that works. Should try Theme Hospital (CorsixTH) and Morrowind (OpenMW) too. Enigma might be able to take original Oxyd data files, thus counting as an engine for that?

#TODO: Add these as well (or should I? Maybe I should just leave it to emulator_info):
#Arcade: I guess it's not an array, it's just MAME
#Computers: Mac, DOS (well, they're emulated too, but differently than the above systems)
#Virtual environment-but-not-quite-type-things: J2ME, Flash
#This allows us to organize supported emulators easily and such
