import sys
import shlex

import common

debug = '--debug' in sys.argv

class Emulator():
	def __init__(self, command_line, supported_extensions, supported_compression):
		self.command_line = command_line
		self.supported_extensions = supported_extensions
		self.supported_compression = supported_compression

	def get_command_line(self, rom, other_config):
		if callable(self.command_line):
			return self.command_line(rom, other_config)
		
		return self.command_line

class MednafenModule(Emulator):
	def __init__(self, module, supported_extensions):
		Emulator.__init__(self, 'mednafen -video.fs 1 -force_module %s {0}' % module, supported_extensions, ['zip', 'gz'])

def make_mame_command_line(driver, slot=None, slot_options=None, has_keyboard=False):
	command_line = 'mame -skip_gameinfo'
	if has_keyboard:
		command_line += ' -ui_active'

	command_line += ' ' + driver

	if slot_options:
		for name, value in slot_options.items():
			command_line += ' -' + name + ' ' + value

	if slot:
		command_line += ' -' + slot + ' {0}'

	return command_line

class MameSystem(Emulator):
	def __init__(self, command_line, supported_extensions):
		Emulator.__init__(self, command_line, supported_extensions, ['7z', 'zip'])

MAME_CDROM_FORMATS = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
MAME_FLOPPY_FORMATS = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']
		
def detect_region_from_filename(name):
	#TODO Make this more robust, and maybe consolidate with roms.get_metadata_from_filename_tags
	tags = ''.join(common.find_filename_tags.findall(name)).lower()
	
	if 'world' in tags or ('ntsc' in tags and 'pal' in tags):
		return 'world'
	elif 'ntsc' in tags or 'usa' in tags or '(us)' in tags or 'japan' in tags:
		return 'ntsc'
	elif 'pal' in tags or 'europe' in tags or 'netherlands' in tags or 'spain' in tags or 'germany' in tags or 'australia' in tags: #Shit, I'm gonna have to put every single European/otherwise PAL country in there.  That's all that I need to put in here so far, though
		return 'pal'

	return None

def build_atari7800_command_line(rom, _):
	#TODO: New plan: Split 'mame-atari-7800' emulator info into 'mame-atari-7800-ntsc' and 'mame-atari-7800-pal', then rewrite get_metadata (or some function similar to it) that gets the region in a more unified way (to allow for getting the language more sensibly etc), then pick which emulator to use here
	#Hmm... how would you specify the usage of MAME in config.py though? Maybe if preferred emulator is 'mame-atari-7800', do auto-region-thingo, otherwise don't do that
	#Or perhaps there's no need to split emulators, but just put a 'region' attribute on Rom that this reads instead of doing the detection itself
	base_command_line = 'mame -skip_gameinfo %s -cart {0}'
	#TODO: Put read_file and get_real_size in roms.Rom()
	rom_data = common.read_file(rom.path, rom.compressed_entry)
	if rom_data[1:10] != b'ATARI7800':
		if debug:
			print(rom.path, 'has no header and is therefore unsupported')
		return None
	
	region_byte = rom_data[57]
		
	if region_byte == 1:
		return base_command_line % 'a7800p'
	elif region_byte == 0:
		return base_command_line % 'a7800'
	else:
		if debug:
			print('Something is wrong with', rom.path, ', has region byte of', region_byte)
		return None

def build_vic20_command_line(rom, _):
	size = common.get_real_size(rom.path, rom.compressed_entry)
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		if debug:
			print('Bugger!', rom.path, 'is too big for MAME at the moment, it is', size)
		return None
	
	base_command_line = 'mame %s -skip_gameinfo -ui_active -cart {0}'
	region = detect_region_from_filename(rom.display_name)
	if region == 'pal':
		return base_command_line % 'vic20p'
	
	return base_command_line % 'vic20'
		
def build_a800_command_line(rom, _):
	is_left = True
	rom_data = common.read_file(rom.path, rom.compressed_entry)
	if rom_data[:4] == b'CART':
		cart_type = int.from_bytes(rom_data[4:8], 'big')
		#See also: https://github.com/dmlloyd/atari800/blob/master/DOC/cart.txt,
		#https://github.com/mamedev/mame/blob/master/src/devices/bus/a800/a800_slot.cpp
		if cart_type in (13, 14, 23, 24, 25) or (cart_type >= 33 and cart_type <= 38):
			if debug:
				print(rom.path, 'is actually a XEGS ROM which is not supported by MAME yet, cart type is', cart_type)
			return None
			
		#You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become
		#supported (even if I have to use some other emulator or something to do it)
		if cart_type in (5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61) or (cart_type >= 26 and cart_type <= 32) or (cart_type >= 54 and cart_type <= 56):
			if debug:
				print(rom.path, "won't work as cart type is", cart_type)
			return None

		if cart_type in (4, 6, 7, 16, 19, 20):
			if debug:
				print(rom.path, "is an Atari 5200 ROM ya goose!! It won't work as an Atari 800 ROM as the type is", cart_type)
			return None
			
		if cart_type == 21: #59 goes in the right slot as well, but that's not supported
			if debug:
				print(rom.path, 'goes in right slot')
			is_left = False
	else:
		size = common.get_real_size(rom.path, rom.compressed_entry)
		#Treat 8KB files as type 1, 16KB as type 2, everything else is unsupported for now
		if size > ((16 * 1024) + 16):
			if debug:
				print(rom.path, 'may actually be a XL/XE/XEGS cartridge, please check it as it has no header and a size of', size)
			return None
	
	if is_left:
		base_command_line = 'mame %s -skip_gameinfo -ui_active -cart1 {0}'
	else:
		base_command_line = 'mame %s -skip_gameinfo -ui_active -cart2 {0}'

	region = detect_region_from_filename(rom.display_name) 
	#Why do these CCS64 and CART and whatever else thingies never frickin' store the TV type?
	if region == 'pal':
		#Atari 800 should be fine for everything, and I don't feel like the XL/XE series to see in which ways they don't work
		return base_command_line % 'a800p'

	return base_command_line % 'a800'
	
def build_c64_command_line(rom, _):
	#While we're here building a command line, should mention that you have to manually put a joystick in the first
	#joystick port, because by default there's only a joystick in the second port.  Why the fuck is that the default?
	#Most games use the first port (although, just to be annoying, some do indeed use the second...  why????)
	#Anyway, might as well use this "Boostergrip" thingy, or really it's like using the C64GS joystick, because it just
	#gives us two extra buttons for any software that uses it (probably nothing), and the normal fire button works as
	#normal.  _Should_ be fine
	#(Super cool pro tip: Bind F1 to Start)
	base_command_line = 'mame %s -joy1 joybstr -joy2 joybstr -skip_gameinfo -ui_active -cart {0}'
	
	rom_data = common.read_file(rom.path, rom.compressed_entry)
	if rom_data[:16] == b'C64 CARTRIDGE   ':
		#Just gonna make sure we're actually dealing with the CCS64 header format thingy first (see:
		#http://unusedino.de/ec64/technical/formats/crt.html)
		#It's okay if it doesn't, though; just means we won't be able to be clever here
		cart_type = int.from_bytes(rom_data[22:24], 'big')
		
		if cart_type == 15: #Commodore C64GS System 3 cart
			#For some reason, these carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
			return base_command_line % 'c64gs'
	
	region = detect_region_from_filename(rom.display_name)
	#Don't think we really need c64c unless we really want the different SID chip
	if region == 'pal':
		return base_command_line % 'c64p'

	return base_command_line % 'c64'

def make_snes_addon_cart_command_line(rom, other_config):
	if 'bios_path' not in other_config:
		if debug:
			#TODO Only print this once!
			print("You can't do", rom.path, "because you haven't set up the BIOS for it yet, check config.py")
		return None
	return make_mame_command_line('snes', 'cart2', {'cart': shlex.quote(other_config['bios_path'])}, False)

def make_prboom_plus_command_line(rom, other_config):
	#'command_line': 'prboom-plus -save %s -iwad {0}' % shlex.quote(DOOM_SAVE_DIR), 'supported_extensions': ['wad'], 'supported_compression': []
	if 'save_dir' in other_config:
		return 'prboom-plus -save %s -iwad {0}' % shlex.quote(other_config['save_dir'])
	else:
		#Fine don't save then, nerd
		return 'prboom-plus -iwad {0}'

emulators = {
	'gambatte': Emulator('gambatte_qt --full-screen {0}', ['gb', 'gbc'], ['zip']),
	#--gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations
	'mgba': Emulator('mgba-qt -f {0}', ['gb', 'gbc', 'gba', 'srl', 'bin', 'mb'], ['7z', 'zip']),
	#Use -C useBios=0 for homebrew with bad checksum/logo that won't boot on real hardware.  Some intensive games (e.g.
	#Doom) will not run at full speed on toaster, but generally it's fine
	'snes9x': Emulator('snes9x-gtk {0}', ['sfc', 'smc', 'swc'], ['zip', 'gz']),
	#Slows down on toaster for a lot of intensive games e.g.  SuperFX.  Can't set fullscreen mode from the command line so you have
	#to set up that yourself; GTK port can't do Sufami Turbo due to lacking multi-cart support that Windows has, MAME can
	#emulate this but it's too slow on toasters so we do that later; GTK port can do Satellaview but not directly from the
	#command line
	'mupen64plus': Emulator('env MESA_GL_VERSION_OVERRIDE=3.3COMPAT mupen64plus --nosaveoptions --fullscreen {0}', ['z64', 'v64', 'n64'], []),
	#Often pretty slow on toaster but okay for turn-based games; environment variable is needed for GLideN64 which sometimes is
	#preferred over Rice and sometimes not (the latter wins at speed and not much else).  Do I still need that environment
	#variable?  I think I might
	'kega-fusion': Emulator('kega-fusion -fullscreen {0}', ['bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', '32x'], ['zip']),
	#May support other CD formats for Mega CD other than iso, cue?
	'ppsspp': Emulator('ppsspp-qt {0}', ['iso', 'pbp', 'cso'], []),
	'mednafen-ngp': MednafenModule('ngp', ['ngp', 'npc', 'ngc']),
	'mednafen-pce': MednafenModule('pce', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	#Mednafen assumes that there is only 1 gamepad and it's the 6 button kind, so button mapping is kind of weird when I
	#was perfectly fine just using 2 buttons
	'mednafen-pce_fast': MednafenModule('pce_fast', ['pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u']),
	'mednafen-nes': MednafenModule('nes', ['nes', 'fds', 'unf']),
	'mednafen-vb': MednafenModule('vb', ['bin', 'vb']),
	'stella': Emulator('stella -fullscreen 1 {0}', ['a26', 'bin', 'rom'], ['gz', 'zip']),
	'pokemini': Emulator('PokeMini -fullscreen {0}', ['min'], ['zip']),
	'pokemini-wrapper': Emulator('PokeMini.sh -fullscreen {0}', ['min'], ['zip']),
	'mednafen-lynx': MednafenModule('lynx', ['lnx', 'lyx', 'o']),
	#Sorta has like...  2 sets of A and B buttons, and 3 buttons on one side and 2 on the other?  It's supposed to be
	#ambidextrous or something which is cool in real life but not so great here, I might need to look more into it and
	#then maybe move it into the normal-but-less-cool platforms
	'mednafen-wonderswan': MednafenModule('wswan', ['ws', 'wsc', 'bin']),
	#Oof this is just super mega weird because you can turn the thing sideways and it still does a thing.  I'll need some
	#point of reference to figure out how to set this up for a normal-ish gamepad...
	#, 'command_line': 'mednafen -video.fs 1 {0}', 'supported_extensions': , 'supported_compression': ['gz', 'zip']
	'mednafen-ps1': MednafenModule('psx', ['iso', 'cue', 'exe', 'toc', 'ccd', 'm3u']),
	#Seems like some PAL games don't run at the resolution Mednafen thinks they should, so they need per-game configs
	#that override the scanline start/end settings
	'dolphin': Emulator('dolphin-emu -b -e {0}', ['iso', 'gcz', 'elf', 'dol', 'wad'], []),
	#, 'command_line': 'citra-qt {0}', 'supported_extensions': , 'supported_compression': []
	'citra': Emulator('citra-qt {0}', ['3ds', 'cxi', '3dsx'], []),
	#Will not run full screen from the command line and you always have to set it manually whether you like it or not (I
	#do not)
	'medusa': Emulator('medusa-emu-qt -f {0}', ['nds'], ['7z', 'zip']),
	'pcsx2': Emulator('pcsx2 --nogui --fullscreen --fullboot {0}', ['iso', 'cso', 'bin'], ['gz']),
	#Has a few problems.  Takes some time to load the interface so at first it might look like it's not working; take out --fullboot if it forbids any homebrew stuff (but it should be fine, and Katamari Damacy needs it).  ELF still doesn't work, though it'd need a different command line anyway
	'mednafen-saturn': MednafenModule('ss', ['cue', 'toc', 'ccd', 'm3u']),
	#Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not
	'mednafen-game-boy': MednafenModule('gb', ['gb', 'gbc']),
	#Would not recommend due to this being based on VisualBoyAdvance, it's just here for completeness
	'mednafen-gba': MednafenModule('gba', ['gba']),
	#Would not recommend due to this being based on VisualBoyAdvance, it's just here for completeness
	'mednafen-game-gear': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes"
	'mednafen-master-system': MednafenModule('gg', ['gg']),
	#Apparently "a low-priority system in terms of proactive maintenance and bugfixes"
	'mednafen-megadrive': MednafenModule('md', ['md', 'bin', 'gen', 'smd', 'sgd']),
	#Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
	'mednafen-snes': MednafenModule('snes', ['sfc', 'smc', 'swc']),
	#Based on bsnes v0.059, probably not so great on toasters. Not sure how well it works necessarily, probably doesn't do Sufami Turbo or Satellaview
	'mednafen-snes_faust': MednafenModule('snes_faust', ['sfc', 'smc', 'swc']),
	#Experimental and doesn't support expansion chips
	'prboom-plus': Emulator(make_prboom_plus_command_line, ['wad'], []),
	#Joystick support not so great, otherwise it plays perfectly well with keyboard + mouse; except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay

	'mame-atari-5200': MameSystem(make_mame_command_line('a5200', 'cart'), ['bin', 'rom', 'car', 'a52']),
	#Analog stuff like Gorf doesn't really work that well, but it doesn't in real life either; could use -sio casette
	#-cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory
	'mame-watara-supervision': MameSystem(make_mame_command_line('svision', 'cart'), ['bin', 'ws', 'sv']),
	#I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes
	#the colours look even worse (they're all inverted and shit)
	'mame-pv-1000': MameSystem(make_mame_command_line('pv1000', 'cart'), ['bin']),
	'mame-arcadia-2001': MameSystem(make_mame_command_line('arcadia', 'cart'), ['bin']),
	#Can also use bndarc for Bandai version but that doesn't seem to make any difference at all?  Some games seem to be
	#weird with the input so that sucks
	'mame-adventure-vision': MameSystem(make_mame_command_line('advision', 'cart'), ['bin']),
	#Doesn't work with the "Code Red" demo last time I tried
	'mame-vectrex': MameSystem(make_mame_command_line('vectrex', 'cart'), ['bin', 'gam', 'vec']),
	#I wonder if there's a way to set the overlay programmatically...  doesn't look like there's a command line option to
	#do that.  Also the buttons are kinda wack I must admit, as they're actually a horizontal row of 4
	#, 'command_line': 'mame megaduck -skip_gameinfo -cart {0}', 'supported_extensions': ['bin'], 'supported_compression': ['7z', 'zip']
	'mame-mega-duck': MameSystem(make_mame_command_line('megaduck', 'cart'), ['bin']),
	'mame-amstrad-gx4000': MameSystem(make_mame_command_line('gx4000', 'cart'), ['bin', 'cpr']),
	#"But why not just use Amstrad CPC+?" you ask, well, there's no games that are on CPC+ cartridges that aren't on
	#GX4000, and I don't feel like fondling around with disks and tapes
	'mame-amstrad-cpc+': MameSystem(make_mame_command_line('cpc6128p', 'cart'), ['bin', 'cpr']),
	#Just in case I change my mind on that. cpc464p is a different CPC+ model but I'm not sure that would be useful?
	'mame-gamate': MameSystem(make_mame_command_line('gamate', 'cart'), ['bin']),
	'mame-game-pocket-computer': MameSystem(make_mame_command_line('gamepock', 'cart'), ['bin']),
	'mame-neo-geo-cd': MameSystem(make_mame_command_line('neocdz', 'cdrom'), MAME_CDROM_FORMATS),
	#This is interesting, because this runs alright on toasters, but Neo Geo-based arcade games do not (both being
	#emulated in MAME); meaning I am probably doing something wrong.  Don't think it has region lock so I should never
	#need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	'mame-colecovision': MameSystem(make_mame_command_line('coleco', 'cart'), ['bin', 'col', 'rom']),
	#Controls are actually fine in-game, just requires a keypad to select levels/start games and that's not consistent at
	#all so good luck with that (but mapping 1 to Start seems to work well).  All carts are either USA or combination USA/Europe and are required by Coleco to run on both regions, so why play in 50Hz when we don't have to
	'mame-intellivision': MameSystem(make_mame_command_line('intv', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Well this sure is a shit console.  There's no consistency to how any game uses any buttons or keypad keys (is it the
	#dial?  Is it keys 2 4 6 8?, so good luck with that; also 2 player mode isn't practical because some games use the
	#left controller and some use the right, so you have to set both controllers to the same inputs; and Pole Position has
	#glitchy graphics.  Why did Mattel make consoles fuck you Mattel I hope you burn
	'mame-intellivision-voice': MameSystem(make_mame_command_line('intvoice', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#Anyway, might as well use the voice module here since it shouldn't break any existing games 
	'mame-intellivision-ecs': MameSystem(make_mame_command_line('intvecs', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#The ECS module does, in fact, break some existing games (I've heard so anyway, don't know which ones), but it is here for usage anyway
	'mame-intellivision-keyboard': MameSystem(make_mame_command_line('intvkbd', 'cart'), ['bin', 'int', 'rom', 'itv']),
	#This was unreleased, but there are dumps of the keyboard-using games out there
	'mame-apfm1000': MameSystem(make_mame_command_line('apfm1000', 'cart'), ['bin']),
	'mame-astrocade': MameSystem(make_mame_command_line('astrocde', 'cart', {'exp': 'rl64_ram'}), ['bin']),
	#There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the
	#actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that
	#RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	'mame-channelf': MameSystem(make_mame_command_line('channelf', 'cart'), ['bin', 'chf']),
	#How the fuck do these controls work?  Am I just too much of a millenial?
	'mame-msx1': MameSystem(make_mame_command_line('svi738', 'cart', has_keyboard=True), ['bin', 'rom']),
	#Note that MSX2 is backwards compatible anyway, so there's not much reason to use this, unless you do have some reason. This model in particular is used because it should be completely in English and if anything goes wrong I'd be able to understand it. I still don't know how disks work (they don't autoboot), or if there's even a consistent command to use to boot them.
	'mame-msx2': MameSystem(make_mame_command_line('fsa1wsx', 'cart', has_keyboard=True), ['bin', 'rom']),
	#This includes MSX2+ because do you really want me to make those two separate things? Turbo-R doesn't work in MAME though, so that'd have to be its own thing. This model is used just because I looked it up and it seems like the best one, the MSX2/MSX2+ systems in MAME are all in Japanese (the systems were only really released in Japan, after all) so you can't avoid that part. Still don't understand disks.
	'mame-pv-2000': MameSystem(make_mame_command_line('pv2000', 'cart', has_keyboard=True), ['bin']),
	#Not the same as the PV-1000!  Although it might as well be, except it's a computer, and they aren't compatible with each other.  MAME says it
	#doesn't work but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a
	#gamepad to map to emulated cursor keys) which maybe is why they say it's preliminary
	'mame-sord-m5': MameSystem(make_mame_command_line('m5', 'cart', {'ramsize': '64K'}, True), ['bin']),
	#Apparently has joysticks with no fire button?  Usually space seems to be fire but sometimes 1 is, which is usually
	#for starting games.  I hate everything.
	'mame-cdi': MameSystem(make_mame_command_line('cdimono1', 'cdrom'), MAME_CDROM_FORMATS),
	#This is the only CD-i model that works, and it says it's not working, but it seems fine
	'mame-game-com': MameSystem(make_mame_command_line('gamecom', 'cart1'), ['bin', 'tgc']),
	#I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything
	'mame-tomy-tutor': MameSystem(make_mame_command_line('tutor', 'cart', has_keyboard=True), ['bin']),
	#Well, at least there's no region crap, though there is pyuuta if you want to read Japanese instead.  The controls in
	#the menus are a bit wack but I think I've set them up so it should work relatively smoothly, also there's not really
	#a way to skip the "Graphics/BASIC/Cartridge" screen that I know of so you'll always have to select that
	'mame-vic-10': MameSystem(make_mame_command_line('vic10', 'cart', {'joy1': 'joy', 'joy2': 'joy'}, has_keyboard=True), ['crt', '80', 'e0']),
	#More similar to the C64 than the VIC-20, need to plug a joystick into both ports because once again games can use
	#either port and thanks I hate it.  At least there's only one TV type
	'mame-sharp-x1': MameSystem(make_mame_command_line('x1turbo40', 'flop1', has_keyboard=True), MAME_FLOPPY_FORMATS + ['2d']),
	#Hey!!  We finally have floppies working!!  Because they boot automatically!  Assumes that they will all work fine
	#though without any other disks, and this will need to be updated if we see any cartridges (MAME says it has a cart
	#slot)...
	'mame-sharp-x68k': MameSystem(make_mame_command_line('x68000', 'flop1', has_keyboard=True), MAME_FLOPPY_FORMATS + ['xdf', 'hdm', '2hd', 'dim']),	
	'mame-atari-8bit': MameSystem(build_a800_command_line, ['bin', 'rom', 'car']),
	#Might get a bit of slowdown on toaster if you open the MAME menu, but usually you'd want to do that when paused
	#anyway, and the games themselves run fine	
	'mame-vic-20': MameSystem(build_vic20_command_line, ['20', '40', '60', '70', 'a0', 'b0', 'crt']),
	#Need to figure out which region to use and we can only really do that by filename, also it doesn't like 16KB carts;
	#disks and tapes are a pain in the ass IRL so MAME emulates the ass-pain of course; and I dunno about .prg files,
	#those are just weird (but it'd be great if I could get those working though); with this and C64 there are some games
	#where you'll have to manually change to the paddle which kinda sucks but I guess it can't be helped and also turn on
	#"Paddle Reverse" in "Analog Controls" for some reason
	'mame-c64': MameSystem(build_c64_command_line, ['80', 'a0', 'e0', 'crt']),
	#Same kerfluffle with regions and different media formats here.  Could use c64c/c64cp for the newer model with the
	#new SID chip, but that might break compatibility I dunno; could also use sx64 for some portable version, there's a
	#whole bunch of models; c64gs doesn't really have much advantages (just like in real life) except for those few
	#cartridges that were made for it specifically.
	'mame-atari-7800': MameSystem(build_atari7800_command_line, ['bin', 'a78']),
	'mame-game-boy': MameSystem(make_mame_command_line('gbpocket', 'cart'), ['bin', 'gb', 'gbc']),
	'mame-super-game-boy': MameSystem(make_mame_command_line('supergb2', 'cart'), ['bin', 'gb', 'gbc']),
	'mame-game-boy-color': MameSystem(make_mame_command_line('gbcolor', 'cart'), ['bin', 'gb', 'gbc']),
	'mame-gba': MameSystem(make_mame_command_line('gba', 'cart'), ['bin', 'gba']),
	'mame-game-gear': MameSystem(make_mame_command_line('gamegear', 'cart'), ['bin', 'gg']),
	'mame-ngp': MameSystem(make_mame_command_line('ngpc', 'cart'), ['bin', 'ngp', 'npc', 'ngc']),
	'mame-pokemon-mini': MameSystem(make_mame_command_line('pokemini', 'cart'), ['bin', 'min']),
	#Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life
	'mame-sg1000': MameSystem(make_mame_command_line('sg1000', 'cart'), ['bin', 'sg']),
	'mame-virtual-boy': MameSystem(make_mame_command_line('vboy', 'cart'), ['bin', 'vb']),
	#Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there; no ROMs required though so that's neat
	'mame-wonderswan': MameSystem(make_mame_command_line('wscolor', 'cart'), ['ws', 'wsc', 'bin']),
	'mame-sufami-turbo': MameSystem(make_snes_addon_cart_command_line, ['st']),
	#Snes9x's GTK+ port doesn't let us load carts with slots for other carts from the command line yet, so this will have
		#to do, but unfortunately it's a tad slower
	'mame-satellaview': MameSystem(make_snes_addon_cart_command_line, ['bs']),
	#Also you still have to go through all the menus and stuff for BS-X/Satellaview/whatsitcalled

	#Other systems that MAME can do but I'm too lazy to do them yet because they'd need a command line generator function:
	#Lynx: Need to select -quick for .o files and -cart otherwise
	#SC-3000: Need to select -cart for carts and -cass for cassettes (.wav .bit); I'm not sure Kega Fusion can do .sc or cassettes yet
	#SF-7000: Need to select -flop for disk images (sf7 + normal MAME disk formats) and -cass for cassettes (.wav .bit); very sure Kega Fusion can't do this
	#NES, SMS, Megadrive, SNES, Atari 2600: Need to detect region 
	#	(Notable that Megadrive and SNES support lock-on carts, i.e. Sonic & Knuckles, Sufami Turbo respectively)
	#N64: Does not do PAL at all. The game might even tell you off if it's a PAL release
	#PC Engine: Need to select between pce and tg16 depending on region, -cdrom and -cart slots, and sgx accordingly

}
