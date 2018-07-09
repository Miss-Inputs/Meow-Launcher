import socket
import shlex
import os

DOOM_SAVE_DIR = '/media/Stuff/Roms/Doom/Saves'
SUFAMI_BIOS_PATH = '/media/Stuff/Roms/SNES/BIOS/Sufami Turbo (Japan).sfc'
BSX_BIOS_PATH = '/media/Stuff/Roms/SNES/BIOS/BS-X BIOS/BS-X BIOS (English) [No DRM] [2016 v1.3].sfc'
CATLIST_PATH = '/media/Stuff/Roms/Arcade/Categories/catlist.ini'
LANGUAGES_PATH = '/media/Stuff/Roms/Arcade/Categories/languages.ini'
is_toaster = socket.gethostname() == 'Bridgette'
pce_module = 'pce_fast' if is_toaster else 'pce'

emulator_configs = [{'name': 'Game Boy', 'command_line': 'gambatte_qt --full-screen {0}', 'rom_dir': '/media/Stuff/Roms/Gameboy', 'supported_extensions': ['gb', 'gbc'], 'supported_compression': ['zip']},
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations
	{'name': 'GBA', 'command_line': 'mgba-qt -f {0}', 'rom_dir': '/media/Stuff/Roms/GBA', 'supported_extensions': ['gba', 'srl', 'bin', 'mb'], 'supported_compression': ['zip', '7z']}, 
	#Use -C useBios=0 for homebrew with bad checksum/logo that won't boot on real hardware.  Some intensive games (e.g.
	#Doom) will not run at full speed on toaster, but generally it's fine
	{'name': 'SNES', 'command_line': 'snes9x-gtk {0}', 'rom_dir': '/media/Stuff/Roms/SNES', 'supported_extensions': ['sfc', 'smc', 'swc'], 'supported_compression': ['zip', 'gz']},
	#Slows down for a lot of intensive games e.g.  SuperFX.  Can't set fullscreen mode from the command line so you have
	#to set up that yourself; GTK port can't do Sufami Turbo due to lacking multi-cart support that Windows has, MAME can
	#emulate this but it's too slow on toasters so we do that later; GTK port can do Satellaview but not directly from the
	#command line
	{'name': 'N64', 'command_line': 'env MESA_GL_VERSION_OVERRIDE=3.3COMPAT mupen64plus --nosaveoptions --fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/N64', 'supported_extensions': ['z64', 'v64', 'n64'], 'supported_compression': []}, 
	#Often pretty slow but okay for turn-based games; environment variable is needed for GLideN64 which sometimes is
	#preferred over Rice and sometimes not (the latter wins at speed and not much else).  Do I still need that environment
	#variable?  I think I might
	{'name': 'Mega Drive', 'command_line': 'kega-fusion -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/Megadrive', 'supported_extensions': ['bin', 'gen', 'md', 'smd', 'sgd'], 'supported_compression': ['zip']},
	{'name': 'Game Gear', 'command_line': 'kega-fusion -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/Game Gear', 'supported_extensions': ['gg'], 'supported_compression': ['zip']},
	{'name': 'Master System', 'command_line': 'kega-fusion -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/Master System', 'supported_extensions': ['sms'], 'supported_compression': ['zip']},
	{'name': 'PSP', 'command_line': 'ppsspp-qt {0}', 'rom_dir': '/media/Stuff/Roms/PSP', 'supported_extensions': ['iso', 'pbp', 'cso'], 'supported_compression': []},
	{'name': 'Neo Geo Pocket', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/Neo Geo Pocket', 'supported_extensions': ['ngp', 'npc', 'ngc'], 'supported_compression': ['zip', 'gz']},
	{'name': 'Atari 2600', 'command_line': 'stella -fullscreen 1 {0}', 'rom_dir': '/media/Stuff/Roms/Atari 2600', 'supported_extensions': ['a26', 'bin', 'rom'], 'supported_compression': ['gz', 'zip']}, 
	{'name': 'Pokemon Mini', 'command_line': 'PokeMini.sh -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/Pokemon Mini', 'supported_extensions': ['min'], 'supported_compression': ['zip']},
	{'name': 'NES', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/NES', 'supported_extensions': ['nes', 'fds', 'unf'], 'supported_compression': ['zip', 'gz']},
	{'name': 'Mega CD', 'command_line': 'kega-fusion -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/Mega CD', 'supported_extensions': ['iso', 'cue'], 'supported_compression': ['zip']}, 
	#May support more CD formats?  But you don't really see anything other than that
	{'name': 'SG-1000', 'command_line': 'kega-fusion -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/Sega SG-1000', 'supported_extensions': ['sg'], 'supported_compression': ['zip']},
	{'name': 'PC Engine', 'command_line': 'mednafen -force_module %s -video.fs 1 {0}' % pce_module, 'rom_dir': '/media/Stuff/Roms/PC Engine', 'supported_extensions': ['pce', 'sgx'], 'supported_compression': ['zip', 'gz']}, 
	#Mednafen assumes that there is only 1 gamepad and it's the 6 button kind, so button mapping is kind of weird when I
	#was perfectly fine just using 2 buttons
	{'name': 'PC Engine CD', 'command_line': 'mednafen -force_module %s -video.fs 1 {0}' % pce_module, 'rom_dir': '/media/Stuff/Roms/PC Engine CD', 'supported_extensions': ['iso', 'cue', 'ccd', 'toc', 'm3u'], 'supported_compression': []}, 
	{'name': 'Virtual Boy', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/Virtual Boy', 'supported_extensions': ['bin', 'vb'], 'supported_compression': ['zip', 'gz']},

		
	#Some other systems that are a bit more obscure perhaps, don't really understand them, but MAME works more or less
	#just fine
	{'name': 'Atari 5200', 'command_line': 'mame a5200 -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Atari 5200', 'supported_extensions': ['bin', 'rom', 'car', 'a52'], 'supported_compression': ['zip', '7z']}, 
	#Analog stuff like Gorf doesn't really work that well, but it doesn't in real life either; could use -sio casette
	#-cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory
	{'name': 'Watara Supervision', 'command_line': 'mame svision -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Watara Supervision', 'supported_extensions': ['bin', 'ws', 'sv'], 'supported_compression': ['zip', '7z']}, 
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes
	#the colours look even worse (they're all inverted and shit)
	{'name': 'Casio PV-1000', 'command_line': 'mame pv1000 -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Casio PV-1000', 'supported_extensions': ['bin'], 'supported_compression': ['zip', '7z']},
	{'name': 'Arcadia 2001', 'command_line': 'mame arcadia -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Arcadia 2001', 'supported_extensions': ['bin'], 'supported_compression': ['zip', '7z']}, 
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all?  Some games seem to be
	#weird with the input so that sucks
	{'name': 'Entex Adventure Vision', 'command_line': 'mame advision -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Adventure Vision', 'supported_extensions': ['bin'], 'supported_compression': ['zip', '7z']}, #Doesn't work with the "Code Red" demo
	{'name': 'Vectrex', 'command_line': 'mame vectrex -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Vectrex', 'supported_extensions': ['bin', 'gam', 'vec'], 'supported_compression': ['zip', '7z']}, 
	#I wonder if there's a way to set the overlay programmatically...  doesn't look like there's a command line option to
	#do that.  Also the buttons are kinda wack I must admit, as they're actually a horizontal row of 4
	{'name': 'Mega Duck', 'command_line': 'mame megaduck -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Mega Duck', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']},
	{'name': 'Atari 7800', 'rom_dir': '/media/Stuff/Roms/Atari 7800', 'supported_extensions': ['bin', 'a78'], 'supported_compression': ['7z', 'zip']}, 
	#You may notice there is no command_line here, we'll deal with that later (as we're using MAME, so we need to make
	#sure we're using NTSC or PAL as necessary)
	{'name': 'Amstrad GX4000', 'command_line': 'mame gx4000 -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Amstrad GX4000', 'supported_extensions': ['bin', 'cpr'], 'supported_compression': ['7z', 'zip']}, 
	#"But why not just use Amstrad CPC+?" you ask, well, there's no games that are on CPC+ cartridges that aren't on
	#GX4000, and I don't feel like fondling around with disks and tapes
	{'name': 'Gamate', 'command_line': 'mame gamate -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Gamate', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']},
	{'name': 'Epoch Game Pocket Computer', 'command_line': 'mame gamepock -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Game Pocket Computer', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']},
	{'name': 'Neo Geo CD', 'command_line': 'mame neocdz -bios official -skip_gameinfo -cdrom {0}', 'rom_dir': '/media/Stuff/Roms/Neo Geo CD', 'supported_extensions': ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi'], 'supported_compression': ['7z', 'zip']},
	#This is interesting, because this runs alright on toasters, but Neo Geo-based arcade games do not (both being
	#emulated in MAME); meaning I am probably doing something wrong.  Don't think it has region lock so I should never
	#need to use neocdzj?

	#These ones may have control schemes that don't actually map too easily to a normal XInput controller or any other
	#controller that looks like the kind of controller that's standard these days (y'know what I mean), or other weirdness
	{'name': 'Colecovision', 'command_line': 'mame coleco -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Colecovision', 'supported_extensions': ['bin', 'col', 'rom'], 'supported_compression': ['7z', 'zip']}, 
	#Controls are actually fine in-game, just requires a keypad to select levels/start games and that's not consistent at
	#all so good luck with that.  All carts are either USA or combination USA/Europe, so why play in 50Hz when we don't
	#have to
	{'name': 'Intellivison', 'command_line': 'mame intvoice -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Intellivision', 'supported_extensions': ['bin', 'int', 'rom', 'itv'], 'supported_compression': ['7z', 'zip']}, 
	#Well this sure is a shit console.  There's no consistency to how any game uses any buttons or keypad keys (is it the
	#dial?  Is it keys 2 4 6 8?, so good luck with that; also 2 player mode isn't practical because some games use the
	#left controller and some use the right, so you have to set both controllers to the same inputs; and Pole Position has
	#glitchy graphics.  Why did Mattel make consoles fuck you Mattel I hope you burn; anyway, might as well use the voice
	#module here since it shouldn't break any existing games (but the ECS module does, or so I heard)
	{'name': 'APF-MP1000', 'command_line': 'mame apfm1000 -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/APF-MP1000', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']},
	{'name': 'Astrocade', 'command_line': 'mame astrocde -exp rl64_ram -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Astrocade', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']}, 
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the
	#actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that
	#RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway whoops
	{'name': 'Channel F', 'command_line': 'mame channelf -skip_gameinfo -cart {0}', 'rom_dir': '/media/Stuff/Roms/Channel F', 'supported_extensions': ['bin', 'chf'], 'supported_compression': ['7z', 'zip']}, 
	#How the fuck do these controls work?  Am I just too much of a millenial?
	{'name': 'Lynx', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/Atari Lynx', 'supported_extensions': ['lnx', 'lyx', 'o'], 'supported_compression': ['zip', 'gz']}, 
	#Sorta has like...  2 sets of A and B buttons, and 3 buttons on one side and 2 on the other?  It's supposed to be
	#ambidextrous or something which is cool in real life but not so great here, I might need to look more into it and
	#then maybe move it into the normal-but-less-cool platforms
	{'name': 'WonderSwan', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/WonderSwan', 'supported_extensions': ['ws', 'wsc'], 'supported_compression': ['zip', 'gz']}, 
	#Oof this is just super mega weird because you can turn the thing sideways and it still does a thing.  I'll need some
	#point of reference to figure out how to set this up for a normal-ish gamepad...
	{'name': 'Doom', 'command_line': 'prboom-plus -save %s -iwad {0}' % shlex.quote(DOOM_SAVE_DIR), 'rom_dir': '/media/Stuff/Roms/Doom', 'supported_extensions': ['wad'], 'supported_compression': []},
	#Joystick support not so great, otherwise it plays perfectly well with keyboard + mouse; except the other issue where
	#it doesn't really like running in fullscreen when more than one monitor is around.  Can I maybe utilize some kind of
	#wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard
	
	#Computers!  These actually aren't that bad control-wise because most sensible games would use a simple one-button
	#joystick, and most of the time MAME lets you attach one.  But some of them don't!  And the ones that don't just use
	#any damn keys they want!  And some software might only work properly with particular models of a computer within an
	#allegedly compatible family!  Yaaaay!  But they have games, so let's put them in here
	#I avoid using anything which requires me to input arcane commands or hear arcane sounds here or wait for arcane
	#times, though I suppose I _could_ do that, it just doesn't feel like a nicely organized bunch of launcher scripts if
	#I do that
	{'name': 'MSX', 'command_line': 'mame fsa1wsx -skip_gameinfo -ui_active -cart1 {0}', 'rom_dir': '/media/Stuff/Roms/MSX', 'supported_extensions': ['bin', 'rom'], 'supported_compression': ['7z', 'zip']}, 
	#Yay!  I got a computer working!  I don't fully understand disks (they present me with a menu with Japanese text I
	#can't read), so carts will have to do, luckily there are quite a number of cartridge-based games
	{'name': 'MSX2', 'command_line': 'mame fsa1wsx -skip_gameinfo -ui_active -cart1 {0}', 'rom_dir': '/media/Stuff/Roms/MSX2', 'supported_extensions': ['bin', 'rom'], 'supported_compression': ['7z', 'zip']}, 
	#Still don't understand disks.  This includes MSX2+ but Turbo-R doesn't work in MAME, and I'm just presuming this
	#Panasonic thing is the best MSX2+ system to emulate because I looked it up and it sounds cool
	{'name': 'VIC-20', 'rom_dir': '/media/Stuff/Roms/Commodore VIC-20', 'supported_extensions': ['20', '40', '60', '70', 'a0', 'b0', 'crt'], 'supported_compression': ['7z', 'zip']},
	#Need to figure out which region to use and we can only really do that by filename, also it doesn't like 16KB carts;
	#disks and tapes are a pain in the ass IRL so MAME emulates the ass-pain of course; and I dunno about .prg files,
	#those are just weird (but it'd be great if I could get those working though); with this and C64 there are some games
	#where you'll have to manually change to the paddle which kinda sucks but I guess it can't be helped and also turn on
	#"Paddle Reverse" in "Analog Controls" for some reason
	{'name': 'Casio PV-2000', 'command_line': 'mame pv2000 -skip_gameinfo -ui_active -cart {0}', 'rom_dir': '/media/Stuff/Roms/Casio PV-2000', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']}, 
	#Not the PV-1000!  Although it might as well be the same thing except it's technically a computer.  MAME says it
	#doesn't work but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a
	#gamepad to map to emulated cursor keys) which maybe is why they say it's preliminary
	{'name': 'Sord M5', 'command_line': 'mame m5 -skip_gameinfo -ramsize 64K -ui_active -cart {0}', 'rom_dir': '/media/Stuff/Roms/Sord M5', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']}, 
	#Apparently has joysticks with no fire button?  Usually space seems to be fire but sometimes 1 is, which is usually
	#for starting games.  I hate everything.
	{'name': 'Atari 8-bit', 'rom_dir': '/media/Stuff/Roms/Atari 8-bit', 'supported_extensions': ['bin', 'rom', 'car'], 'supported_compression': ['7z', 'zip']}, 
	#Might get a bit of slowdown on toaster if you open the MAME menu, but usually you'd want to do that when paused
	#anyway, and the games themselves run fine
]

if not is_toaster:
	emulator_configs.extend([{'name': 'PlayStation', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/Playstation', 'supported_extensions': ['iso', 'cue', 'exe', 'toc', 'ccd', 'm3u'], 'supported_compression': ['gz', 'zip']}, 
		#Seems like some PAL games don't run at the resolution Mednafen thinks they should, so they need per-game configs
		#that override the scanline start/end settings
		{'name': 'GameCube', 'command_line': 'dolphin-emu -b -e {0}', 'rom_dir': '/media/Stuff/Roms/Gamecube', 'supported_extensions': ['iso', 'gcz', 'elf', 'dol'], 'supported_compression': []},
		{'name': '3DS', 'command_line': 'citra-qt {0}', 'rom_dir': '/media/Stuff/Roms/3DS', 'supported_extensions': ['3ds', 'cxi', '3dsx'], 'supported_compression': []}, 
		#Will not run full screen from the command line and you always have to set it manually whether you like it or not (I
		#do not)
		{'name': 'DS', 'command_line': 'medusa-emu-qt -f {0}', 'rom_dir': '/media/Stuff/Roms/DS', 'supported_extensions': ['nds'], 'supported_compression': ['7z', 'zip']},
		{'name': 'PS2', 'command_line': 'pcsx2 --nogui --fullscreen --fullboot {0}', 'rom_dir': '/media/Stuff/Roms/PS2', 'supported_extensions': ['iso', 'cso', 'bin'], 'supported_compression': ['gz']}, 
		#Has a few problems.  Takes some time to load the interface so at first it might look like it's not working; take out
		#--fullboot if it forbids any homebrew stuff (but it should be fine, and Katamari Damacy needs it).  ELF still
		#doesn't work, though it'd need a different command line anyway
		{'name': '32X', 'command_line': 'kega-fusion -fullscreen {0}', 'rom_dir': '/media/Stuff/Roms/32X', 'supported_extensions': ['32x', 'bin'], 'supported_compression': ['zip']}, 
		#Aaaalllmost runs fine on toaster, but a lot of games don't so I decided to move it here...

		{'name': 'Sufami Turbo', 'command_line': 'mame snes -skip_gameinfo -cart %s -cart2 {0}' % shlex.quote(SUFAMI_BIOS_PATH), 'rom_dir': '/media/Stuff/Roms/SNES/Sufami Turbo', 'supported_extensions': ['st'], 'supported_compression': ['zip', '7z']},
		#Snes9x's GTK+ port doesn't let us load carts with slots for other carts from the command line yet, so this will have
		#to do, but unfortunately it's a tad slower
		{'name': 'Satellaview', 'command_line': 'mame snes -skip_gameinfo -cart %s -cart2 {0}' % shlex.quote(BSX_BIOS_PATH), 'rom_dir': '/media/Stuff/Roms/SNES/Satellaview', 'supported_extensions': ['bs'], 'supported_compression': ['zip', '7z']}, 
		#Still have to go to the house and talk to the floating television, yes I took my meds
		{'name': 'CD-i', 'command_line': 'mame cdimono1 -skip_gameinfo -cdrom {0}', 'rom_dir': '/media/Stuff/Roms/CD-i', 'supported_extensions': ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi'], 'supported_compression': ['7z', 'zip']},
		{'name': 'Game.com', 'command_line': 'mame gamecom -skip_gameinfo -cart1 {0}', 'rom_dir': '/media/Stuff/Roms/Game.com', 'supported_extensions': ['bin', 'tgc'], 'supported_compression': ['7z', 'zip']},
		
		{'name': 'Wii', 'command_line': 'dolphin-emu -b -e {0}', 'rom_dir': '/media/Stuff/Roms/Wii', 'supported_extensions': ['iso', 'gcz', 'wad', 'elf', 'dol'], 'supported_compression': []}, 
		#Gonna have to map these motion controls somehow
		{'name': 'Saturn', 'command_line': 'mednafen -video.fs 1 {0}', 'rom_dir': '/media/Stuff/Roms/Saturn', 'supported_extensions': ['iso', 'cue', 'toc', 'ccd', 'm3u'], 'supported_compression': []}, 
		#Not the most easily mappable of controllers due to having both 6 face buttons and 2 shoulder buttons

		{'name': 'Tomy Tutor', 'command_line': 'mame tutor -skip_gameinfo -ui_active -cart {0}', 'rom_dir': '/media/Stuff/Roms/Tomy Tutor', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']}, 
		#Well, at least there's no region crap, though there is pyuuta if you want to read Japanese instead.  The controls in
		#the menus are a bit wack but I think I've set them up so it should work relatively smoothly, also there's not really
		#a way to skip the "Graphics/BASIC/Cartridge" screen so you'll always have to select that
		{'name': 'C64', 'rom_dir': '/media/Stuff/Roms/Commodore 64', 'supported_extensions': ['80', 'a0', 'e0', 'crt'], 'supported_compression': ['7z', 'zip']},
		#Same kerfluffle with regions and different media formats here.  Could use c64c/c64cp for the newer model with the
		#new SID chip, but that might break compatibility I dunno; could also use sx64 for some portable version, there's a
		#whole bunch of models; c64gs doesn't really have much advantages (just like in real life) except for those few
		#cartridges that were made for it specifically.
		{'name': 'VIC-10', 'command_line': 'mame vic10 -joy1 joy -skip_gameinfo -ui_active -cart {0}', 'rom_dir': '/media/Stuff/Roms/Commodore VIC-10', 'supported_extensions': ['crt', '80', 'e0'], 'supported_compression': ['7z', 'zip']}, 
		#More similar to the C64 than the VIC-20, need to plug a joystick into both ports because once again games can use
		#either port and thanks I hate it.  At least there's only one TV type
		{'name': 'Sharp X1', 'command_line': 'mame x1turbo40 -skip_gameinfo -ui_active -flop1 {0}', 'rom_dir': '/media/Stuff/Roms/Sharp X1', 'supported_extensions': ['2d', 'd77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk'], 'supported_compression': ['7z', 'zip']}, 
		#Hey!!  We finally have floppies working!!  Because they boot automatically!  Assumes that they will all work fine
		#though without any other disks, and this will need to be updated if we see any cartridges (MAME says it has a cart
		#slot)...
		{'name': 'Sharp X68000', 'command_line': 'mame x68000 -skip_gameinfo -ui_active -flop1 {0}', 'rom_dir': '/media/Stuff/Roms/Sharp X68000', 'supported_extensions': ['xdf', 'dim', 'hdm', '2hd', 'd77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk'], 'supported_compression': ['7z', 'zip']},])

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
name_replacement = [('240p Test Suite GX', '240p Suite'), 
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
	('Q-Bert', 'Q*bert'), #To be fair, this is just a technical restriction on filenames that isn't relevant when using a MAME display name
	('Robotron - 2084', 'Robotron 2084'), 
	('Sangokushi 3', 'Sangokushi III'), 
	('Super Boy 3', 'Super Boy III'), 
	("Street Fighter II'", 'Street Fighter II'), 
	('Twin Bee', 'TwinBee'),]

#Add "The " in front of these things (but not if there's already "The " in front of them of course)
add_the = ['Lion King', 
	'Goonies',]

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
	('Parodius - Shinwa kara Owarai e', 'Parodius'), #Technically wrong, Parodius is the first game on MSX and Parodius DA!  is the sequel but it's called just Parodius in
                                                  #Europe which is annoying and I've already gotten rid of the DA!  as
                                                                                                   #above and
                                                                                                                                                    #everything
                                                                                                                                                                                                     #is
                                                                                                                                                                                                     #confusing
	('Pitfall II - Lost Caverns', 'Pitfall II'),
	('Pitfall II - The Lost Caverns', 'Pitfall II'),
	("Pitfall! - Pitfall Harry's Jungle Adventure", "Pitfall!"),
	('Puzzle Bobble 2 / Bust-A-Move Again', 'Puzzle Bobble 2'),
	('Puzzle Bobble / Bust-A-Move', 'Puzzle Bobble'), #Fuck you America
	('Q*bert for Game Boy', 'Q*bert'), #This wouldn't be confusing if there wasn't another Q*Bert for Game Boy Color
	('Shadow Squadron ~ Stellar Assault', 'Stellar Assault'),
	('SimAnt - The Electronic Ant Colony', 'SimAnt'), 
	('SimCity 2000 - The Ultimate City Simulator', 'SimCity 2000'), 
	("Sonic 3D Blast ~ Sonic 3D Flickies' Island", 'Sonic 3D Blast'),
	('Space Invaders / Space Invaders M', 'Space Invaders'),
	('Street Fighter II: The World Warrior', 'Street Fighter II'), 
	('Super Street Fighter II: The New Challengers', 'Super Street Fighter II'), 
	('Who Wants to Be a Millionaire - 2nd Edition', 'Who Wants to Be a Millionaire'), #This is not even a 2nd edition of anything, it's just the GBC version
]

