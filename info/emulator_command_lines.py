import shlex
import os
import sys
import configparser
import subprocess

from config import main_config
from platform_metadata.nes import NESPeripheral
from .system_info import MediaType
from .region_info import TVSystem

debug = '--debug' in sys.argv

class EmulationNotSupportedException(Exception):
	pass

class NotARomException(Exception):
	#File type mismatch, etc
	pass

def _get_autoboot_script_by_name(name):
	this_package = os.path.dirname(__file__)
	root_package = os.path.dirname(this_package)
	return os.path.join(root_package, 'mame_autoboot', name + '.lua')

def make_mednafen_command_line(module):
	return 'mednafen -video.fs 1 -force_module %s $<path>' % module

def mame_command_line(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None):
	command_line = 'mame -skip_gameinfo'
	if has_keyboard:
		command_line += ' -ui_active'

	command_line += ' ' + driver

	if slot_options:
		for name, value in slot_options.items():
			if not value:
				value = '""'
			command_line += ' -' + name + ' ' + value

	if slot:
		command_line += ' -' + slot + ' $<path>'

	if autoboot_script:
		command_line += ' -autoboot_script ' + shlex.quote(_get_autoboot_script_by_name(autoboot_script))

	return command_line

def _is_highscore_cart_available():
	#Unfortunately it seems we cannot verify an individual software, which would probably take less time
	proc = subprocess.run(['mame', '-verifysoftlist', 'a7800'], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
	#Don't check return code - it'll return 2 if other software is bad, but we don't care about those
	for line in proc.stdout.splitlines():
		#Bleh
		if line == 'romset a7800:hiscore is good':
			return True
	return False

_have_hiscore_software = _is_highscore_cart_available()

def mame_atari_7800(game, _):
	if not game.metadata.specific_info.get('Headered', False):
		raise EmulationNotSupportedException('No header')

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a7800p'
	else:
		system = 'a7800'

	if _have_hiscore_software and game.metadata.specific_info.get('Uses-Hiscore-Cart', False):
		return mame_command_line(system, 'cart2', {'cart': 'hiscore'})

	return mame_command_line(system, 'cart')

def mame_vic_20(game, _):
	size = game.rom.get_size()
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		raise EmulationNotSupportedException('ROM too big: %d' % size)

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'vic20p'
	else:
		system = 'vic20'

	return mame_command_line(system, 'cart', {'iec8': '""'}, has_keyboard=True)

def mame_atari_8bit(game, _):
	if game.metadata.specific_info.get('Headered', False):
		cart_type = game.metadata.specific_info['Cart-Type']
		if cart_type in (13, 14, 23, 24, 25) or (cart_type >= 33 and cart_type <= 38):
			raise EmulationNotSupportedException('Actually a XEGS ROM which is not supported by MAME yet, cart type is %d' % cart_type)

		#You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become supported
		if cart_type in (5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61) or (cart_type >= 26 and cart_type <= 32) or (cart_type >= 54 and cart_type <= 56):
			raise EmulationNotSupportedException('Unsupported cart type: %d' % cart_type)

		if cart_type in (4, 6, 7, 16, 19, 20):
			raise EmulationNotSupportedException('Actually an Atari 5200 ROM, cart type = %d' % cart_type)
	else:
		size = game.rom.get_size()
		#Treat 8KB files as type 1, 16KB as type 2, everything else is unsupported for now
		if size > ((16 * 1024) + 16):
			raise EmulationNotSupportedException('May actually be a XL/XE/XEGS cartridge, no header and size = %d' % size)

	slot = 'cart1' if game.metadata.specific_info.get('Slot', 'Left') == 'Left' else 'cart2'

	if game.metadata.tv_type == TVSystem.PAL:
		#Atari 800 should be fine for everything, and I don't feel like the XL/XE series to see in which ways they don't work
		system = 'a800p'
	else:
		system = 'a800'

	return mame_command_line(system, slot, has_keyboard=True)

def _find_c64_system(game):
	if game.metadata.platform == 'C64GS':
		#For some reason, C64GS carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
		#Note that C64GS doesn't really work properly in MAME anyway, but the carts... not work... less than in the regular C64 driver
		return 'c64gs'

	#Don't think we really need c64c unless we really want the different SID chip

	if game.metadata.tv_type == TVSystem.PAL:
		return 'c64p'

	return 'c64'

def mame_c64(game, _):
	#While we're here building a command line, should mention that you have to manually put a joystick in the first
	#joystick port, because by default there's only a joystick in the second port.  Why the fuck is that the default?
	#Most games use the first port (although, just to be annoying, some do indeed use the second...  why????)
	#Anyway, might as well use this "Boostergrip" thingy, or really it's like using the C64GS joystick, because it just
	#gives us two extra buttons for any software that uses it (probably nothing), and the normal fire button works as
	#normal.  _Should_ be fine
	#(Super cool pro tip: Bind F1 to Start)

	#Explicitly listed as UNSUPPORTED in the cbm_crt.cpp source file
	unsupported_mappers = [1, 2, 6, 9, 20, 29, 30, 33, 34, 35, 36, 37, 38, 40, 42, 45, 46, 47, 50, 52, 54]
	#Not listed as unsupported, but from anecdotal experience doesn't seem to work. Should try these again one day
	unsupported_mappers += [18, 32]
	#18 = Sega (Zaxxon/Super Zaxxon), nothing in the source there that says it's unsupported, but it consistently segfaults every time I try to launch it, so I guess it doesn't actually work
	#32 = EasyFlash. Well, at least it doesn't segfault. Just doesn't boot, even if I play with the dip switch that says "Boot". Maybe I'm missing something here?
		#There's a Prince of Persia cart in c64_cart.xml that uses easyflash type and is listed as being perfectly supported, but maybe it's one of those things where it'll work from the software list but not as a normal ROM (it's broken up into multiple ROMs)
	#15 (System 3/C64GS) does seem to be a bit weird too, oh well
	#Maybe check the software list for compatibility
	cart_type = game.metadata.specific_info.get('Mapper-Number', None)
	cart_type_name = game.metadata.specific_info.get('Mapper', None)

	if cart_type in unsupported_mappers:
		raise EmulationNotSupportedException('%s cart not supported' % cart_type_name)

	system = _find_c64_system(game)
	return mame_command_line(system, 'cart', {'joy1': 'joybstr', 'joy2': 'joybstr', 'iec8': '""'}, True)

def verify_mgba_mapper(game):
	if game.metadata.specific_info.get('Override-Mapper', False):
		#If the mapper in the ROM header is different than what the mapper actually is, it won't work, since we can't override it from the command line or anything
		raise EmulationNotSupportedException('Overriding the mapper in header is not supported')

	mapper = game.metadata.specific_info.get('Mapper', None)
	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		raise EmulationNotSupportedException('Mapper is not detected at all')

	if mapper not in ['ROM only', 'MBC1', 'MBC1 Multicart', 'MBC2', 'MBC3', 'HuC1', 'MBC5', 'HuC3', 'MBC6', 'MBC7', 'MMM01', 'Pocket Camera', 'Bandai TAMA5']:
		raise EmulationNotSupportedException('Mapper ' + mapper + ' not supported')

def mgba(game, _):
	if game.metadata.platform in ('Game Boy', 'Game Boy Color'):
		verify_mgba_mapper(game)

	command_line = 'mgba-qt -f'
	if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
		command_line += ' -C useBios=0'
	return command_line + ' $<path>'

def medusa(game, _):
	if game.metadata.platform in ('Game Boy', 'Game Boy Color'):
		verify_mgba_mapper(game)

	if game.metadata.platform == 'DSi' or game.metadata.specific_info.get('Is-iQue', False):
		raise EmulationNotSupportedException('DSi-only and iQue games not supported')
	return 'medusa-emu-qt -f $<path>'

def gambatte(game, _):
	if game.metadata.specific_info.get('Override-Mapper', False):
		#If the mapper in the ROM header is different than what the mapper actually is, it won't work, since we can't override it from the command line or anything
		raise EmulationNotSupportedException('Overriding the mapper in header is not supported')

	mapper = game.metadata.specific_info.get('Mapper', None)
	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		raise EmulationNotSupportedException('Mapper is not detected at all')

	if mapper not in ['ROM only', 'MBC1', 'MBC1 Multicart', 'MBC2', 'MBC3', 'HuC1', 'MBC5']:
		raise EmulationNotSupportedException('Mapper ' + mapper + ' not supported')

	return 'gambatte_qt --full-screen $<path>'

def mame_game_boy(game, other_config):
	#TODO: Bound to be some mappers which won't be supported (Game Boy Camera would be one of them I guess)
	#Not much reason to use gameboy, other than a green tinted screen. I guess that's the only difference
	system = 'gbcolor' if other_config.get('use_gbc_for_dmg') else 'gbpocket'

	#Should be just as compatible as supergb but with better timing... I think
	super_gb_system = 'supergb2'

	is_colour = game.metadata.platform == 'Game Boy Color'
	is_sgb = game.metadata.specific_info.get('SGB-Enhanced', False)

	prefer_sgb = other_config.get('prefer_sgb_over_gbc', False)
	if is_colour and is_sgb:
		system = super_gb_system if prefer_sgb else 'gbcolor'
	elif is_colour:
		system = 'gbcolor'
	elif is_sgb:
		system = super_gb_system

	return mame_command_line(system, 'cart')

def mame_snes(game, other_config):
	#Snes9x's GTK+ port doesn't let us load carts with slots for other carts from the command line yet, so this will have
	#to do, but unfortunately it's a tad slower
	if game.rom.extension == 'st':
		bios_path = other_config.get('sufami_turbo_bios_path', None)
		if not bios_path:
			#TODO Only print this once!
			raise EmulationNotSupportedException('Sufami Turbo BIOS not set up, check emulators.ini')

		#We don't need to detect TV type because the Sufami Turbo (and also BS-X) was only released in Japan and so the Super Famicom can be used for everything
		return mame_command_line('snes', 'cart2', {'cart': shlex.quote(bios_path)}, False)

	if game.rom.extension == 'bs':
		bios_path = other_config.get('bsx_bios_path', None)
		if not bios_path:
			raise EmulationNotSupportedException('BS-X/Satellaview BIOS not set up, check emulators.ini')
		return mame_command_line('snes', 'cart2', {'cart': shlex.quote(bios_path)}, False)

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'snespal'
	else:
		#American SNES and Super Famicom are considered to be the same system, so that works out nicely
		system = 'snes'

	return mame_command_line(system, 'cart')

def mame_nes(game, _):
	if game.rom.extension == 'fds':
		#We don't need to detect TV type because the FDS was only released in Japan and so the Famicom can be used for everything
		return mame_command_line('fds', 'flop')

	uses_sb486 = game.metadata.specific_info.get('Peripheral', None) == NESPeripheral.SuborKeyboard

	#27 and 103 might be unsupported too?
	unsupported_ines_mappers = (29, 30, 55, 59, 60, 81, 84, 98,
	99, 100, 101, 102, 109, 110, 111, 122, 124, 125, 127, 128,
	129, 130, 131, 135, 151, 161, 169, 170, 174, 181, 219, 220,
	236, 237, 239, 247, 248, 251, 253)
	if game.metadata.specific_info.get('Header-Format', None) == 'iNES':
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: %d (%s)' % (mapper, game.metadata.specific_info.get('Mapper')))
		if mapper == 167:
			#This might not be true for all games with this mapper, I dunno, hopefully it's about right.
			#At any rate, Subor - English Word Blaster needs to be used with the keyboard thing it's designed for
			uses_sb486 = True

	#TODO: Use dendy if we can know the game uses it
	#TODO: Set up controller ports if game uses Zapper, etc
	if uses_sb486:
		system = 'sb486'
	elif game.metadata.tv_type == TVSystem.PAL:
		system = 'nespal'
	else:
		#There's both a "famicom" driver and also a "nes" driver which does include the Famicom (as well as NTSC NES), so that's weird
		#Gonna presume this works, though
		system = 'nes'

	return mame_command_line(system, 'cart', has_keyboard=uses_sb486)

def mame_atari_2600(game, _):
	size = game.rom.get_size()
	if size > (512 * 1024):
		raise EmulationNotSupportedException('ROM too big: %d' % size)
	#TODO: Switch based on input type
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a2600p'
	else:
		system = 'a2600'

	return mame_command_line(system, 'cart')

def mame_zx_spectrum(game, _):
	#TODO: Add casettes and ROMs; former will require autoboot_script, I don't know enough about the latter but it seems to use exp = intf2
	#Maybe quickload things? Do those do anything useful?
	options = {}
	if game.metadata.media_type == MediaType.Floppy:
		system = 'specpls3'
		slot = 'flop1'
		#If only one floppy is needed, you can add -upd765:1 "" to the commmand line and use just "flop" instead of "flop1".
		#Seemingly the "exp" port doesn't do anything, so we can't attach a Kempston interface. Otherwise, we could use this for snapshots and tape games too.
	elif game.metadata.media_type == MediaType.Snapshot:
		#No harm in using this for 48K games, it works fine, and saves us from having to detect which model a game is designed for. Seems to be completely backwards compatible, which is a relief.
		#We do need to plug in the Kempston interface ourselves, though; that's fine. Apparently how the ZX Interface 2 works is that it just maps joystick input to keyboard input, so we don't really need it, but I could be wrong and thinking of something else entirely.
		system = 'spec128'
		slot = 'dump'
		options['exp'] = 'kempjoy'
	else:
		#Should not happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')

	return mame_command_line(system, slot, options, True)

def dolphin(game, _):
	if game.metadata.specific_info.get('No-Disc-Magic', False):
		raise EmulationNotSupportedException('No disc magic')

	return 'dolphin-emu -b -e $<path>'

def citra(game, _):
	if game.rom.extension != '3dsx':
		if not game.metadata.specific_info.get('Decrypted', True):
			raise EmulationNotSupportedException('ROM is encrypted')
		if not game.metadata.specific_info.get('Is-CXI', True):
			raise EmulationNotSupportedException('Not CXI')
		if not game.metadata.specific_info.get('Has-SMDH', False):
			raise EmulationNotSupportedException('No icon (SMDH), probably an applet')
		if game.metadata.product_code[3:6] == '-U-':
			#Ignore update data, which either are pointless (because you install them in Citra and then when you run the main game ROM, it has all the updates applied) or do nothing
			#I feel like there's probably a better way of doing this whoops
			raise NotARomException('Update data, not actual game')
	return 'citra-qt $<path>'

def mednafen_nes(game, _):
	#Yeah okay, I need a cleaner way of doing this
	unsupported_ines_mappers = (14, 20, 27, 28, 29, 30, 31, 35, 36, 39, 43, 50,
		53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 81, 83, 84, 91, 98, 100,
		102, 103, 104, 106, 108, 109, 110, 111, 116, 136, 137, 138, 139, 141,
		142, 143, 181, 183, 186, 187, 188, 191, 192, 211, 212, 213, 214, 216,
		218, 219, 220, 221, 223, 224, 225, 226, 227, 229, 230, 231, 233, 235,
		236, 237, 238, 239, 243, 245)
	unsupported_ines_mappers += tuple(range(120, 133))
	unsupported_ines_mappers += tuple(range(145, 150))
	unsupported_ines_mappers += tuple(range(161, 180))
	unsupported_ines_mappers += tuple(range(194, 206))

	if game.metadata.specific_info.get('Header-Format', None) == 'iNES':
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: %d (%s)' % (mapper, game.metadata.specific_info.get('Mapper')))

	return make_mednafen_command_line('nes')

def reicast(game, _):
	if game.metadata.specific_info.get('Uses-Windows-CE', False):
		raise EmulationNotSupportedException('Uses Windows CE')
	return 'reicast -config x11:fullscreen=1 $<path>'

def mame_sg1000(game, _):
	#TODO: SC-3000 casettes (wav bit)
	slot_options = {}
	has_keyboard = False

	ext = game.rom.extension
	if game.metadata.media_type == MediaType.Floppy:
		system = 'sf7000'
		slot = 'flop'
		has_keyboard = True
		#There are standard Centronics and RS-232 ports/devices available with this, but would I really need them?
	elif ext == 'sc':
		#SC-3000H is supposedly identical except it has a mechanical keyboard. Not sure why sc3000h is a separate driver, but oh well
		system = 'sc3000'
		slot = 'cart'
		has_keyboard = True
	elif ext in ('bin', 'sg'):
		#Use original system here. Mark II seems to have no expansion and it should just run Othello Multivision stuff?
		system = 'sg1000'
		slot = 'cart'
		slot_options['sgexp'] = 'fm' #Can also put sk1100 in here. Can't detect yet what uses which though
	else:
		#Should not happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')


	return mame_command_line(system, slot, slot_options, has_keyboard)

def mame_sharp_x68000(game, _):
	if game.subroms:
		#FIXME: This won't work if the referenced m3u files have weird compression formats supported by 7z but not by MAME; but maybe that's your own fault
		floppy_slots = {}
		for i, individual_floppy in enumerate(game.subroms):
			floppy_slots['flop%d' % (i + 1)] = shlex.quote(individual_floppy.path)

		return mame_command_line('x68000', slot=None, slot_options=floppy_slots, has_keyboard=True)
	return mame_command_line('x68000', 'flop1', has_keyboard=True)

def mame_fm_towns_marty(game, _):
	slot_options = {
		#Don't need hard disks here
		'scsi:1': '',
		'scsi:2': '',
		'scsi:3': '',
		'scsi:4': '',
		'scsi:5': '',
	}

	if game.metadata.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.OpticalDisc:
		slot = 'cdrom'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_command_line('fmtmarty', slot, slot_options)

def mame_ibm_pcjr(game, _):
	slot_options = {'bios': 'quiksilver'}

	if game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart1'
	elif game.metadata.media_type == MediaType.Floppy:
		#Floppy is the only other kind of rom we accept at this time
		slot = 'flop'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_command_line('ibmpcjr', slot, slot_options, has_keyboard=True)

def mame_atari_jaguar(game, _):
	if game.metadata.media_type == MediaType.Cartidge:
		slot = 'cart1'
	elif game.metadata.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_command_line('jaguar', slot)

def mupen64plus(game, other_config):
	if game.metadata.specific_info.get('ROM-Format', None) == 'Unknown':
		raise EmulationNotSupportedException('Undetectable ROM format')

	command_line = 'mupen64plus --nosaveoptions --fullscreen'

	no_plugin = 1
	controller_pak = 2
	transfer_pak = 4
	rumble_pak = 5

	use_controller_pak = game.metadata.specific_info.get('Uses-Controller-Pak', False)
	use_transfer_pak = game.metadata.specific_info.get('Uses-Transfer-Pak', False)
	use_rumble_pak = game.metadata.specific_info.get('Force-Feedback', False)

	plugin = no_plugin

	if use_controller_pak and use_rumble_pak:
		plugin = controller_pak if other_config.get('prefer_controller_pak_over_rumble', 'no') == 'yes' else rumble_pak
	elif use_controller_pak:
		plugin = controller_pak
	elif use_rumble_pak:
		plugin = rumble_pak

	if plugin != no_plugin:
		#TODO: Only do this if using SDL plugin (i.e. not Raphnet raw plugin)
		command_line += ' --set %s' % shlex.quote('Input-SDL-Control1[plugin]=%d' % plugin)

	#TODO: If use_transfer_pak, put in a rom + save with --gb-rom-1 and --gb-ram-1 somehow... hmm... can't insert one at runtime with console UI sooo

	return command_line + ' $<path>'

def fs_uae(game, other_config):
	command_line = 'fs-uae --fullscreen'
	if game.metadata.platform == 'Amiga CD32':
		command_line += ' --amiga_model=CD32 --joystick_0_mode=%s --cdrom_drive_0=$<path>' % shlex.quote('cd32 gamepad')
	else:
		amiga_models = {
			'OCS': 'A500', #Also A1000 (A2000 also has OCS but doesn't appear to be an option?)
			'ECS': 'A600', #Also A500+ (A3000 should work, but doesn't seem to be possible)
			'AGA': 'A4000/040', #Also 1200 (which only has 68EC020 CPU instead of 68040)
		}
		#TODO: It would be better if this didn't force specific models, but could look at what ROMs the user has for FS-UAE and determines which models are available that support the given chipset, falling back to backwards compatibility for newer models or throwing EmulationNotSupportedException as necessary

		chipset = game.metadata.specific_info.get('Chipset')
		if not chipset:
			#AGA is the default default if there's no default, because we should probably have one
			chipset = other_config.get('default_chipset', 'AGA')

		if chipset in amiga_models:
			command_line += ' --amiga_model=%s' % amiga_models[chipset]

		#Hmm... there is also --cpu=68060 which some demoscene productions use so maybe I should look into that...
		command_line += ' --floppy_drive_0=$<path>'
	if game.metadata.tv_type == TVSystem.NTSC:
		command_line += ' --ntsc_mode=1'
	return command_line

def mame_intellivision(game, _):
	system = 'intv'

	uses_keyboard = False
	if game.metadata.specific_info.get('Uses-ECS', False):
		#This has a keyboard and Intellivoice module attached; -ecs.ctrl_port synth gives a music synthesizer instead of keyboard
		#Seemingly none of the prototype keyboard games use intvkbd, they just use this
		system = 'intvecs'
		uses_keyboard = True
	elif game.metadata.specific_info.get('Uses-Intellivoice', False):
		system = 'intvoice'

	return mame_command_line(system, 'cart', has_keyboard=uses_keyboard)

def basilisk_ii(app, other_config):
	if 'arch' in app.config:
		if app.config['arch'] == 'ppc':
			raise EmulationNotSupportedException('PPC not supported')

	#This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	#Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	autoboot_txt_path = os.path.join(other_config['shared_folder'], 'autoboot.txt')
	width = other_config.get('default_width', 1920)
	height = other_config.get('default_height', 1080)
	if 'max_resolution' in app.config:
		width, height = app.config['max_resolution']
	#Can't do anything about colour depth at the moment (displaycolordepth is functional on some SDL1 builds, but not SDL2)
	#Or controls... but I swear I will find a way!!!!

	#If you're not using an SDL2 build of BasiliskII, you probably want to change dga to window! Well you really want to get an SDL2 build of BasiliskII, honestly
	actual_emulator_command = 'BasiliskII --screen dga/{0}/{1}'.format(width, height)
	inner_command = 'echo {0} > {1} && {2} && rm {1}'.format(shlex.quote(app.path), shlex.quote(autoboot_txt_path), actual_emulator_command)
	return 'sh -c {0}'.format(shlex.quote(inner_command))

def _get_dosbox_config(app):
	if not os.path.isdir(main_config.dosbox_configs_path):
		return None

	for conf in os.listdir(main_config.dosbox_configs_path):
		path = os.path.join(main_config.dosbox_configs_path, conf)
		name, _ = os.path.splitext(conf)
		if app.name in (name, name.replace(' - ', ': ')):
			return path

	return None

def _make_dosbox_config(app, other_config):
	configwriter = configparser.ConfigParser()
	configwriter.optionxform = str

	configwriter['sdl'] = {}
	configwriter['sdl']['fullscreen'] = 'true'
	configwriter['sdl']['fullresolution'] = 'desktop'
	#TODO: Set mapper file, which will of course require another separate directory
	#TODO: Might have to set autoexec instead of just pointing to the file as a command line argument for some versions of DOSBox

	if 'required_hardware' in app.config:
		if 'for_xt' in app.config['required_hardware']:
			if app.config['required_hardware']['for_xt']:
				configwriter['cpu'] = {}
				configwriter['cpu']['cycles'] = other_config.get('slow_cpu_cycles', 400)

		if 'max_graphics' in app.config['required_hardware']:
			configwriter['dosbox'] = {}
			graphics = app.config['required_hardware']['max_graphics']
			configwriter['dosbox']['machine'] = 'svga_s3' if graphics == 'svga' else graphics

	#TODO: Perform other sanity checks on name
	name = app.name.replace(': ', ' - ') + '.ini'
	path = os.path.join(main_config.dosbox_configs_path, name)

	os.makedirs(main_config.dosbox_configs_path, exist_ok=True)
	with open(path, 'wt') as config_file:
		configwriter.write(config_file)

	return path

def dosbox(app, other_config):
	conf = _get_dosbox_config(app)
	if ('--regen-dos-config' in sys.argv) or not conf:
		conf = _make_dosbox_config(app, other_config)
	actual_command = "dosbox -exit -noautoexec -userconf -conf {1} {0}".format(shlex.quote(app.path), shlex.quote(conf))
	return actual_command
