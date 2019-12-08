import configparser
import os
import sys

import io_utils
from common_types import (EmulationNotSupportedException, MediaType,
                          NotARomException)
from launchers import LaunchParams, MultiCommandLaunchParams
from mame_helpers import have_mame
from platform_metadata.apple_ii import AppleIIHardware
from platform_metadata.atari_2600 import Atari2600Controller
from platform_metadata.master_system import SMSPeripheral
from platform_metadata.megadrive import MegadriveRegionCodes
from platform_metadata.nes import NESPeripheral
from platform_metadata.saturn import SaturnRegionCodes
from platform_metadata.snes import ExpansionChip
from platform_metadata.zx_spectrum import ZXJoystick, ZXMachine
from software_list_info import get_software_list_by_name

from .region_info import TVSystem


#Utils
def _get_autoboot_script_by_name(name):
	this_package = os.path.dirname(__file__)
	root_package = os.path.dirname(this_package)
	return os.path.join(root_package, 'mame_autoboot', name + '.lua')

def _verify_supported_mappers(game, supported_mappers, detected_mappers):
	mapper = game.metadata.specific_info.get('Mapper', None)

	if not mapper:
		#If there was a problem detecting the mapper, or it's something invalid, it probably won't run
		raise EmulationNotSupportedException('Mapper is not detected at all')

	if game.metadata.specific_info.get('Override-Mapper', False) and mapper not in detected_mappers:
		#If the mapper in the ROM header is different than what the mapper actually is, it won't work, since we can't override it from the command line or anything
		#But it'll be okay if the mapper is something that gets autodetected outside of the header anyway
		raise EmulationNotSupportedException('Overriding the mapper in header is not supported')

	if mapper not in supported_mappers and mapper not in detected_mappers:
		raise EmulationNotSupportedException('Mapper ' + mapper + ' not supported')

def verify_mgba_mapper(game):
	supported_mappers = ['ROM only', 'MBC1', 'MBC2', 'MBC3', 'HuC1', 'MBC5', 'HuC3', 'MBC6', 'MBC7', 'Pocket Camera', 'Bandai TAMA5']
	detected_mappers = ['MBC1 Multicart', 'MMM01', 'Wisdom Tree']

	_verify_supported_mappers(game, supported_mappers, detected_mappers)

def _is_software_available(software_list_name, software_name):
	if not have_mame():
		return False

	software_list = get_software_list_by_name(software_list_name)
	if not software_list:
		return False
	available_software = software_list.get_available_software()
	for software in available_software:
		if software.name == software_name:
			return True
	return False

def _is_highscore_cart_available():
	return _is_software_available('a7800', 'hiscore')
	#FIXME: This is potentially wrong for A7800, where the software directory could be different than MAME... I've just decided to assume it's set up that way

#Common generators for multi-system stuff
def mednafen_base(module):
	return LaunchParams('mednafen', ['-video.fs', '1', '-force_module', module, '$<path>'])

def mame_base(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None, software=None):
	args = ['-skip_gameinfo']
	if has_keyboard:
		args.append('-ui_active')

	args.append(driver)
	if software:
		args.append(software)

	if slot_options:
		for name, value in slot_options.items():
			if not value:
				value = ''
			args.append('-' + name)
			args.append(value)

	if slot:
		args.append('-' + slot)
		args.append('$<path>')

	if autoboot_script:
		args.append('-autoboot-script')
		args.append(_get_autoboot_script_by_name(autoboot_script))

	return args

def mame_system(driver, slot=None, slot_options=None, has_keyboard=False, autoboot_script=None):
	args = mame_base(driver, slot, slot_options, has_keyboard, autoboot_script)
	return LaunchParams('mame', args)

#MAME drivers
def mame_32x(game, _):
	region_codes = game.metadata.specific_info.get('Region-Code')
	if region_codes:
		if MegadriveRegionCodes.USA in region_codes or MegadriveRegionCodes.World in region_codes or MegadriveRegionCodes.BrazilUSA in region_codes or MegadriveRegionCodes.JapanUSA in region_codes or MegadriveRegionCodes.USAEurope in region_codes:
			system = '32x'
		elif MegadriveRegionCodes.Japan in region_codes or MegadriveRegionCodes.Japan1 in region_codes:
			system = '32xj'
		elif MegadriveRegionCodes.Europe in region_codes or MegadriveRegionCodes.EuropeA in region_codes or MegadriveRegionCodes.Europe8 in region_codes:
			system = '32xe'
		else:
			system = '32x'
	else:
		system = '32x'
		if game.metadata.tv_type == TVSystem.PAL:
			system = '32xe'
	return mame_system(system, 'cart')

def mame_amiga_cd32(game, _):
	system = 'cd32'
	if game.metadata.tv_type == TVSystem.NTSC:
		#PAL is more likely if it is unknown
		system = 'cd32n'
	return mame_system(system, 'cdrom')

def mame_apple_ii(game, _):
	slot_options = {}
	if game.metadata.specific_info.get('Uses-Mouse', False):
		slot_options['sl4'] = 'mouse'
	system = 'apple2e' #Probably a safe default
	compatible_machines = game.metadata.specific_info.get('Machine')
	if compatible_machines:
		if AppleIIHardware.AppleIIE in compatible_machines:
			system = 'apple2e'
		elif AppleIIHardware.AppleIIC in compatible_machines:
			system = 'apple2c'
		elif AppleIIHardware.AppleIICPlus in compatible_machines:
			system = 'apple2cp'
		elif AppleIIHardware.AppleIIEEnhanced in compatible_machines:
			system = 'apple2ee' #Should this go first if it's supported? Not sure what it does
		elif AppleIIHardware.AppleIIC in compatible_machines:
			system = 'apple2c'
		elif AppleIIHardware.AppleIIPlus in compatible_machines:
			system = 'apple2p'
		else:
			#Not using Apple III / Apple III+ here, or Apple IIgs; or base model Apple II since that doesn't autoboot and bugger that
			raise EmulationNotSupportedException('We don\'t use' + str(compatible_machines))

	return mame_system(system, 'flop1', slot_options, True)

def mame_atari_2600(game, _):
	size = game.rom.get_size()
	#https://github.com/mamedev/mame/blob/master/src/devices/bus/vcs/vcs_slot.cpp#L188
	if size not in (0x800, 0x1000, 0x2000, 0x28ff, 0x2900, 0x3000, 0x4000, 0x8000, 0x10000, 0x80000):
		raise EmulationNotSupportedException('ROM size not supported: {0}'.format(size))

	if game.metadata.specific_info.get('Uses-Supercharger', False):
		#MAME does support Supercharger tapes with scharger software list and -cass, but it requires playing the tape, so we pretend it doesn't in accordance with me not liking to press the play tape button; and this is making me think I want some kind of manual_tape_load_okay option that enables this and other MAME drivers but anyway that's another story
		raise EmulationNotSupportedException('Requires Supercharger')

	left = game.metadata.specific_info.get('Left-Peripheral')
	right = game.metadata.specific_info.get('Right-Peripheral')

	options = {}
	if left == Atari2600Controller.Joystick:
		options['joyport1'] = 'joy'
	elif left == Atari2600Controller.Paddle:
		options['joyport1'] = 'pad'
	elif left == Atari2600Controller.KeyboardController:
		options['joyport1'] = 'keypad'
	elif left == Atari2600Controller.Boostergrip:
		options['joyport1'] = 'joybstr'
	elif left == Atari2600Controller.DrivingController:
		options['joyport1'] = 'wheel'

	if right == Atari2600Controller.Joystick:
		options['joyport2'] = 'joy'
	elif right == Atari2600Controller.Paddle:
		options['joyport2'] = 'pad'
	elif right == Atari2600Controller.KeyboardController:
		options['joyport2'] = 'keypad'
	elif right == Atari2600Controller.Boostergrip:
		options['joyport2'] = 'joybstr'
	elif right == Atari2600Controller.DrivingController:
		options['joyport2'] = 'wheel'

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a2600p'
	else:
		system = 'a2600'

	return mame_system(system, 'cart', slot_options=options)

def mame_atari_jaguar(game, _):
	if game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart'
	elif game.metadata.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_system('jaguar', slot)

_have_hiscore_software = None
def mame_atari_7800(game, _):
	if not game.metadata.specific_info.get('Headered', False):
		#This would only be supported via software list
		raise EmulationNotSupportedException('No header')

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'a7800p'
	else:
		system = 'a7800'

	global _have_hiscore_software
	if _have_hiscore_software is None:
		_have_hiscore_software = _is_highscore_cart_available()

	if _have_hiscore_software and game.metadata.specific_info.get('Uses-Hiscore-Cart', False):
		return mame_system(system, 'cart2', {'cart1': 'hiscore'})

	return mame_system(system, 'cart')

def mame_atari_8bit(game, specific_config):
	slot_options = {}
	if game.metadata.media_type == MediaType.Cartridge:
		if game.metadata.specific_info.get('Headered', False):
			cart_type = game.metadata.specific_info['Cart-Type']
			if cart_type in (13, 14, 23, 24, 25) or (33 <= cart_type <= 38):
				raise EmulationNotSupportedException('XEGS cart: %d' % cart_type)

			#You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become supported
			if cart_type in (5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61) or (26 <= cart_type <= 32) or (54 <= cart_type <= 56):
				raise EmulationNotSupportedException('Unsupported cart type: %d' % cart_type)

			if cart_type in (4, 6, 7, 16, 19, 20):
				raise EmulationNotSupportedException('Atari 5200 cart (will probably work if put in the right place): %d' % cart_type)
		else:
			size = game.rom.get_size()
			#8KB files are treated as type 1, 16KB as type 2, everything else is unsupported for now
			if size > ((16 * 1024) + 16):
				raise EmulationNotSupportedException('No header and size = %d, cannot be recognized as a valid cart yet (treated as XL/XE)' % size)

		slot = 'cart1' if game.metadata.specific_info.get('Slot', 'Left') == 'Left' else 'cart2'
	else:
		slot = 'flop1'
		if game.metadata.specific_info.get('Requires-BASIC', False):
			basic_path = specific_config.get('basic_path')
			if not basic_path:
				raise EmulationNotSupportedException('This software needs BASIC ROM to function')
			#TODO: Allow using software list (although I guess user could just put 'basicc' as the path?)
			slot_options['cart1'] = basic_path

	machine = game.metadata.specific_info.get('Machine')
	if machine == 'XL':
		system = 'a800xlp' if game.metadata.tv_type == TVSystem.PAL else 'a800xl'
	elif machine == 'XE':
		system = 'a65xe' #No PAL XE machine in MAME?
	else:
		system = 'a800pal' if game.metadata.tv_type == TVSystem.PAL else 'a800'
	
	return mame_system(system, slot, slot_options, has_keyboard=True)

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
	cart_type = game.metadata.specific_info.get('Mapper-Number', None)
	cart_type_name = game.metadata.specific_info.get('Mapper', None)

	if cart_type in unsupported_mappers:
		raise EmulationNotSupportedException('%s cart not supported' % cart_type_name)

	system = 'c64'

	if cart_type == 15:
		#For some reason, C64GS carts don't work on a regular C64 in MAME, and we have to use...  the thing specifically designed for playing games (but we normally wouldn't use this, since some cartridge games still need the keyboard, even if just for the menus, and that's why it actually sucks titty balls IRL.  But if it weren't for that, we totes heckin would)
		#Note that C64GS doesn't really work properly in MAME anyway, but the carts... not work... less than in the regular C64 driver
		system = 'c64gs'

	#Don't think we really need c64c unless we really want the different SID chip. Maybe that could be an option?

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'c64p'


	return mame_system(system, 'cart', {'joy1': 'joybstr', 'joy2': 'joybstr', 'iec8': ''}, True)

def mame_coleco_adam(game, _):
	slot_options = {}
	slot = None

	if game.metadata.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.Tape:
		slot = 'cass1'
		#Disable floppy drives if we aren't using them for a performance boost (332.27% without vs 240.35% with here, and you'll probably be turboing through the tape load, so yeah)
		slot_options['net4'] = ''
		slot_options['net5'] = ''
	else:
		#Should never happen (carts would just be ColecoVision, I think, but I could be wrong)
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')

	return mame_system('adam', slot, slot_options, has_keyboard=True)

def mame_colecovision(game, _):
	system = 'coleco'
	if game.metadata.tv_type == TVSystem.PAL:
		#This probably won't happen (officially, carts are supposed to support both NTSC and PAL), but who knows
		system = 'colecop'

	return mame_system(system, 'cart')

def mame_dreamcast(game, _):
	#Possibly dctream (Treamcast) could be useful here
	#dcdev doesn't run retail stuff
	if game.metadata.specific_info.get('Uses-Windows-CE', False):
		raise EmulationNotSupportedException('Windows CE-based games not supported')

	region_codes = game.metadata.specific_info.get('Region-Code')
	if SaturnRegionCodes.USA in region_codes:
		system = 'dc'
	elif SaturnRegionCodes.Japan in region_codes:
		system = 'dcjp'
	elif SaturnRegionCodes.Europe in region_codes:
		system = 'dceu'
	else:
		#Default to USA
		system = 'dc'
	
	#No interesting slot options...
	return mame_system(system, 'cdrom')

def mame_fm_towns_marty(game, _):
	if game.metadata.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.OpticalDisc:
		slot = 'cdrom'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_system('fmtmarty', slot)

def mame_game_boy(game, specific_config):
	#Do all of these actually work or are they just detected? (HuC1 and HuC3 are supposedly non-working, and are treated as MBC3?)
	#gb_slot.cpp also mentions MBC4, which isn't real
	supported_mappers = ['ROM only', 'MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC6', 'MBC7', 'Pocket Camera', 'Bandai TAMA5']
	detected_mappers = ['MMM01', 'MBC1 Multicart', 'Wisdom Tree', 'Li Cheng', 'Sintax']

	_verify_supported_mappers(game, supported_mappers, detected_mappers)

	#Not much reason to use gameboy, other than a green tinted screen. I guess that's the only difference
	system = 'gbcolor' if specific_config.get('use_gbc_for_dmg') else 'gbpocket'

	#Should be just as compatible as supergb but with better timing... I think
	super_gb_system = 'supergb2'

	is_colour = game.metadata.platform == 'Game Boy Color'
	is_sgb = game.metadata.specific_info.get('SGB-Enhanced', False)

	prefer_sgb = specific_config.get('prefer_sgb_over_gbc', False)
	if is_colour and is_sgb:
		system = super_gb_system if prefer_sgb else 'gbcolor'
	elif is_colour:
		system = 'gbcolor'
	elif is_sgb:
		system = super_gb_system

	return mame_system(system, 'cart')

def mame_game_gear(game, _):
	system = 'gamegear'
	if game.metadata.specific_info.get('Region-Code') == 'Japanese':
		system = 'gamegeaj'
	return mame_system(system, 'cart')

def mame_ibm_pcjr(game, _):
	if game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart1'
	elif game.metadata.media_type == MediaType.Floppy:
		#Floppy is the only other kind of rom we accept at this time
		slot = 'flop'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_system('ibmpcjr', slot, has_keyboard=True)

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

	return mame_system(system, 'cart', has_keyboard=uses_keyboard)

def mame_lynx(game, _):
	if game.metadata.media_type == MediaType.Cartridge and not game.metadata.specific_info.get('Headered', False):
		raise EmulationNotSupportedException('Needs to have .lnx header')

	slot = 'cart'

	if game.metadata.media_type == MediaType.Executable:
		slot = 'quik'

	return mame_system('lynx', slot)

def mame_master_system(game, _):
	tv_type = TVSystem.PAL #Seems a more sensible default at this point (there are also certain homebrews with less-than-detectable TV types that demand PAL)

	if game.metadata.tv_type in (TVSystem.NTSC, TVSystem.Agnostic):
		tv_type = TVSystem.NTSC

	if game.metadata.specific_info.get('Japanese-Only', False):
		system = 'smsj' #Still considered SMS1 for compatibility purposes. Seems to just be sg1000m3 but with built in FM, for all intents and purposes
		#"card" slot seems to not be used
	elif tv_type == TVSystem.PAL:
		system = 'sms1pal'
		if game.metadata.specific_info.get('SMS2-Only', False):
			system = 'smspal' #Master System 2 lacks expansion slots and card slot in case that ends up making a difference
	else:
		system = 'smsj' #Used over sms1 for FM sound on worldwide releases
		if game.metadata.specific_info.get('SMS2-Only', False):
			system = 'sms'
	#Not sure if Brazilian or Korean systems would end up being needed

	slot_options = {}
	peripheral = game.metadata.specific_info.get('Peripheral')
	#According to my own comments from earlier in master_system.py that I'm going to blindly believe, both controller ports are basically the same for this purpose
	controller = None
	if peripheral == SMSPeripheral.Lightgun:
		controller = 'lphaser'
	elif peripheral == SMSPeripheral.Paddle:
		#Don't use this without a Japanese system or the paddle goes haywire (definitely breaks with sms1)
		controller = 'paddle'
	elif peripheral == SMSPeripheral.Tablet:
		controller = 'graphic'
	elif peripheral == SMSPeripheral.SportsPad:
		#Uh oh, there's a sportspadjp as well. Uh oh, nobody told me there was regional differences. Uh oh, I'm not prepared for this at all. Uh oh. Oh shit. Oh fuck. Oh no.
		#I mean like.. they're both 2 button trackballs? Should be fine, I hope
		controller = 'sportspad'
	elif peripheral == SMSPeripheral.StandardController:
		controller = 'joypad'
	#There is also a multitap that adds 4 controller ports, it's called "Furrtek SMS Multitap" so I guess it's unofficial?
	#smsexp can be set to genderadp but I dunno what the point of that is
	
	#Might as well use the rapid fire thing
	if controller:
		slot_options['ctrl1'] = 'rapidfire'
		slot_options['ctrl2'] = 'rapidfire'
		slot_options['ctrl1:rapidfire:ctrl'] = controller
		slot_options['ctrl2:rapidfire:ctrl'] = controller

	return mame_system(system, 'cart', slot_options)

def mame_mega_cd(game, _):
	region_codes = game.metadata.specific_info.get('Region-Code')
	if region_codes:
		if MegadriveRegionCodes.USA in region_codes or MegadriveRegionCodes.World in region_codes or MegadriveRegionCodes.BrazilUSA in region_codes or MegadriveRegionCodes.JapanUSA in region_codes or MegadriveRegionCodes.USAEurope in region_codes:
			system = 'segacd'
		elif MegadriveRegionCodes.Japan in region_codes or MegadriveRegionCodes.Japan1 in region_codes:
			system = 'megacdj'
		elif MegadriveRegionCodes.Europe in region_codes or MegadriveRegionCodes.EuropeA in region_codes or MegadriveRegionCodes.Europe8 in region_codes:
			system = 'megacd'
		else:
			system = 'segacd'
	else:
		system = 'segacd'
		if game.metadata.tv_type == TVSystem.PAL:
			system = 'megacd'
	#megacda also exists (Asia/PAL), not sure if we need it (is that what EuropeA is for?)
	return mame_system(system, 'cdrom')

def mame_megadrive(game, _):
	#Can do Sonic & Knuckles + Sonic 2/3 lockon (IIRC)
	#Does do SVP
	#Doesn't emulate the Power Base Converter but you don't need to
	#Titan - Overdrive: Glitches out on the part with PCB that says "Blast Processing" and the Titan logo as well as the "Titan 512C Forever" part (doesn't even display "YOUR EMULATOR SUX" properly as Kega Fusion does with the unmodified binary)
	#md_slot.cpp claims that carts with EEPROM and Codemasters J-Cart games don't work, but it seems they do, maybe they don't save
	#Controllers are configured via Machine Configuration and hence are out of reach for poor little frontends
	#Pocket Monsters 2 displays blank screen after menu screen, although rom_lion3 does work, but it's not detected as that from fullpath
	#4in1 and 12in1 won't boot anything either because they aren't detected from fullpath as being rom_mcpir (but Super 15 in 1 works)
	#Overdrive 2 is supposed to use SSF2 bankswitching but isn't detected as rom_ssf2, actual Super Street Fighter 2 does work
	mapper = game.metadata.specific_info.get('Mapper')
	if mapper == 'rom_topf':
		#Doesn't seem to be detected via fullpath as being rom_topf, so it might work from software list
		raise EmulationNotSupportedException('Top Fighter 2000 MK VII not supported')
	if mapper == 'rom_yasech':
		#Looks like it's same here... nothing about it being unsupported in SL entry
		raise EmulationNotSupportedException('Ya Se Chuan Shuo not supported')
	if mapper == 'rom_kof99_pokemon':
		#This isn't a real mapper, Pocket Monsters uses rom_kof99 but it doesn't work (but KOF99 bootleg does)
		#Probably because it's detected as rom_99 when loaded from fullpath, so... it be like that sometimes
		raise EmulationNotSupportedException('Pocket Monsters not supported from fullpath')
	if mapper == 'rom_smw64':
		raise EmulationNotSupportedException('Super Mario World 64 not supported')
	if mapper == 'rom_cjmjclub':
		raise EmulationNotSupportedException('Chao Ji Mahjong Club not supported')
	if mapper == 'rom_soulb':
		#It looks like this should work, but loading it from fullpath results in an "Unknown slot option 'rom_soulblad' in slot 'mdslot'" error when it should be rom_soulb instead
		raise EmulationNotSupportedException('Soul Blade not supported')
	if mapper == 'rom_chinf3':
		raise EmulationNotSupportedException('Chinese Fighter 3 not supported')

	#Hmm. Most Megadrive emulators that aren't MAME have some kind of region preference thing where it's selectable between U->E->J or J->U->E or U->J->E or whatever.. because of how this works I'll have to make a decision, unless I feel like making a config thing for that, and I don't think I really need to do that.
	#I'll go with U->J->E for now
	region_codes = game.metadata.specific_info.get('Region-Code')
	if region_codes:
		if MegadriveRegionCodes.USA in region_codes or MegadriveRegionCodes.World in region_codes or MegadriveRegionCodes.BrazilUSA in region_codes or MegadriveRegionCodes.JapanUSA in region_codes or MegadriveRegionCodes.USAEurope in region_codes:
			#There is no purpose to using genesis_tmss other than making stuff not work for authenticity, apparently this is the only difference in MAME drivers
			system = 'genesis'
		elif MegadriveRegionCodes.Japan in region_codes or MegadriveRegionCodes.Japan1 in region_codes:
			system = 'megadrij'
		elif MegadriveRegionCodes.Europe in region_codes or MegadriveRegionCodes.EuropeA in region_codes or MegadriveRegionCodes.Europe8 in region_codes:
			system = 'megadriv'
		else:
			#Assume USA if unknown region code, although I'd be interested in the cases where there is a region code thing in the header but not any of the normal 3
			system = 'genesis'
	else:
		#This would happen if unlicensed/no TMSS stuff and so there is no region code info at all in the header
		#genesis and megadrij might not always be compatible...
		system = 'genesis'
		if game.metadata.tv_type == TVSystem.PAL:
			system = 'megadriv'
	return mame_system(system, 'cart')

def mame_msx1(game, _):
	system = 'svi738'
	#This one is in English and seems to work, so we'll go with that. I suppose ideally I would have a list of potential systems that all work, and then get the first one which is available, but that would require effort, so nah
	#Possible slot options: centronics is there to attach printers and such; if using a floppy can put bm_012 (MIDI interface) or moonsound (OPL4 sound card, does anything use that?) in the cart port but I'm not sure that's needed; the slots are the same for MSX2
	slot_options = {}
	if game.metadata.media_type == MediaType.Floppy:
		#Defaults to 35ssdd, but 720KB disks need this one instead
		slot_options['fdc:0'] = '35dd'
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart1'
	else:
		#Should not happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')

	return mame_system(system, slot, slot_options, has_keyboard=True)

def mame_msx2(game, _):
	system = 'hbf1xv'
	#This one is MSX2+ and seems to have all the features, fsa1wsx makes you press "0" to go to BASIC for disks
	slot_options = {}
	if game.metadata.media_type == MediaType.Floppy:
		#Defaults to 35ssdd, but 720KB disks need this one instead
		slot_options['fdc:0'] = '35dd'
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart1'
	else:
		#Should not happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')

	return mame_system(system, slot, slot_options, has_keyboard=True)

def mame_n64(game, _):
	if game.metadata.tv_type == TVSystem.PAL:
		raise EmulationNotSupportedException('NTSC only')

	return mame_system('n64', 'cart')

def mame_nes(game, _):
	if game.rom.extension == 'fds':
		#We don't need to detect TV type because the FDS was only released in Japan and so the Famicom can be used for everything
		return mame_system('fds', 'flop')

	#27 and 103 might be unsupported too?
	unsupported_ines_mappers = (29, 30, 55, 59, 60, 81, 84, 98,
	99, 100, 101, 102, 109, 110, 111, 122, 124, 125, 127, 128,
	129, 130, 131, 135, 151, 161, 169, 170, 174, 181, 219, 220,
	236, 237, 239, 247, 248, 251, 253)
	if game.metadata.specific_info.get('Header-Format', None) == 'iNES':
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: %d (%s)' % (mapper, game.metadata.specific_info.get('Mapper')))
	#TODO: Unsupported NES 2.0 and UNIF mappers, if any

	has_keyboard = False

	#There doesn't seem to be a way to know if we should use dendy, so I hope we don't actually need to
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'nespal'
	else:
		#There's both a "famicom" driver and also a "nes" driver which does include the Famicom (as well as NTSC NES), this seems to only matter for what peripherals can be connected
		system = 'nes'

	options = {}
	peripheral = game.metadata.specific_info.get('Peripheral')
	
	#NES: ctrl1 = 4score_p1p3 (multitap), joypad, miracle_piano, zapper; ctrl2 = 4score_p2p4, joypad, powerpad, vaus, zapper
	#PAL NES is the same
	#Famicom: exp = arcstick (arcade stick? Eh?), barcode_battler, family_trainer, fc_keyboard, hori_4p (multitap), hori_twin (multitap), joypad, konamihs (thing with 4 buttons), mj_panel, pachinko, partytap (quiz game thing?), subor_keyboard, vaus, zapper

	#For Famicom... hmm, I wonder if it could ever cause a problem where it's like, a Famicom game expects to use the zapper on the exp port and won't like being run on a NES with 2 zappers in the controller ports
	if peripheral == NESPeripheral.Zapper:
		#ctrl1 can have a gun, but from what I understand the games just want it in slot 2?
		options['ctrl2'] = 'zapper'
	elif peripheral == NESPeripheral.ArkanoidPaddle:
		options['ctrl2'] = 'vaus'
	elif peripheral == NESPeripheral.FamicomKeyboard:
		system = 'famicom'
		options['exp'] = 'fc_keyboard'
		has_keyboard = True
	elif peripheral == NESPeripheral.SuborKeyboard:
		system = 'sb486'
		has_keyboard = True
	elif peripheral == NESPeripheral.Piano:
		options['ctrl1'] = 'miracle_piano'
	elif peripheral == NESPeripheral.PowerPad:
		options['ctrl2'] = 'powerpad'
		#I dunno how to handle the Family Trainer for Famicom games, but I read from googling around that the Japanese games will run fine on a NES with an American Power Pad so that's basically what we're doing here

	#Power Glove and ROB aren't emulated, so you'll just have to use the normal controller

	return mame_system(system, 'cart', options, has_keyboard=has_keyboard)

def mame_odyssey2(game, _):
	system = 'odyssey2'

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'videopac'
	#system = 'jopac' if region == France could also be a thing? Hmm

	return mame_system(system, 'cart')

def mame_pc_engine(game, _):
	#TODO: Use specific_config or software list to get PCE CD BIOS, then do that (same system, but -cdrom slot instead and -cart goes to System Card; TurboGrafx System Card only works with tg16 but other combinations are fine)
	system = 'tg16'
	#USA system can run Japanese games, so maybe we don't need to switch to pce if Japan in regions; but USA games do need tg16 specifically
	if game.rom.extension == 'sgx':
		#It might be better to detect this differently like if software is in sgx.xml software list, or set Is-Supergrafx field that way in roms_metadata platform_helpers
		system = 'sgx'

	return mame_system(system, 'cart')

def mame_pico(game, _):
	region_codes = game.metadata.specific_info.get('Region-Code')
	if region_codes:
		if MegadriveRegionCodes.USA in region_codes or MegadriveRegionCodes.World in region_codes or MegadriveRegionCodes.BrazilUSA in region_codes or MegadriveRegionCodes.JapanUSA in region_codes or MegadriveRegionCodes.USAEurope in region_codes:
			system = 'picou'
		elif MegadriveRegionCodes.Japan in region_codes or MegadriveRegionCodes.Japan1 in region_codes:
			system = 'picoj'
		elif MegadriveRegionCodes.Europe in region_codes or MegadriveRegionCodes.EuropeA in region_codes or MegadriveRegionCodes.Europe8 in region_codes:
			system = 'pico'
		else:
			system = 'picoj' #Seems the most likely default
	else:
		system = 'picoj'
		if game.metadata.tv_type == TVSystem.PAL:
			system = 'pico'
	return mame_system(system, 'cart')

def mame_saturn(game, _):
	region_codes = game.metadata.specific_info.get('Region-Code')
	#Clones here are hisaturn and vsaturn, not sure how useful those would be
	if SaturnRegionCodes.USA in region_codes:
		system = 'saturn'
	elif SaturnRegionCodes.Japan in region_codes:
		system = 'saturnjp'
	elif SaturnRegionCodes.Europe in region_codes:
		system = 'saturneu'
	else:
		#Default to USA
		system = 'saturn'

	#TODO: Use ctrl1 and ctrl2 to set controllers (analog, joy_md3, joy_md6, joypad, keyboard, mouse, racing, segatap (???), trackball)
	#Dunno if the cart slot can be used for anything useful yet
	return mame_system(system, 'cdrom')

def mame_sord_m5(game, _):
	system = 'm5'
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'm5p'
		#Not sure what m5p_brno is about (two floppy drives?)

	#Hmm, no reason to take out the floppy drive, really... I think I was just fooling myself that it would improve performance. Also ram size really only needs to be set to 64K if that's detected as needed. Anyway I don't feel like touching things right now
	return mame_system(system, 'cart1', {'ramsize': '64K', 'upd765:0': ''}, True)

def mame_sg1000(game, _):
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

	return mame_system(system, slot, slot_options, has_keyboard)

def mame_sharp_x68000(game, _):
	if game.subroms:
		#FIXME: This won't work if the referenced m3u files have weird compression formats supported by 7z but not by MAME; but maybe that's your own fault
		floppy_slots = {}
		for i, individual_floppy in enumerate(game.subroms):
			floppy_slots['flop%d' % (i + 1)] = individual_floppy.path

		return mame_system('x68000', slot=None, slot_options=floppy_slots, has_keyboard=True)
	return mame_system('x68000', 'flop1', has_keyboard=True)

_have_sufami_software = None
_have_bsx_software = None
def mame_snes(game, specific_config):
	global _have_sufami_software, _have_bsx_software

	if game.rom.extension == 'st':
		if _have_sufami_software is None:
			_have_sufami_software = _is_software_available('snes', 'sufami')

		if _have_sufami_software:
			return mame_system('snes', 'cart2', {'cart': 'sufami'})

		bios_path = specific_config.get('sufami_turbo_bios_path', None)
		if not bios_path:
			raise EmulationNotSupportedException('Sufami Turbo BIOS not set up, check systems.ini')

		#We don't need to detect TV type because the Sufami Turbo (and also BS-X) was only released in Japan and so the Super Famicom can be used for everything
		return mame_system('snes', 'cart2', {'cart': bios_path})

	if game.rom.extension == 'bs':
		if _have_bsx_software is None:
			_have_bsx_software = _is_software_available('snes', 'bsxsore')

		if _have_bsx_software:
			return mame_system('snes', 'cart2', {'cart': 'bsxsore'})

		bios_path = specific_config.get('bsx_bios_path', None)
		if not bios_path:
			raise EmulationNotSupportedException('BS-X/Satellaview BIOS not set up, check systems.ini')
		return mame_system('snes', 'cart2', {'cart': bios_path})

	expansion_chip = game.metadata.specific_info.get('Expansion-Chip')
	if expansion_chip == ExpansionChip.ST018:
		raise EmulationNotSupportedException('{0} not supported'.format(expansion_chip))

	slot = game.metadata.specific_info.get('Slot')
	if slot:
		#These bootleg copy protection methods might work from software list, but from fullpath the carts aren't detected as using it, so they black screen
		if slot.endswith('_poke', '_sbld', '_tekken2', '_20col'):
			raise EmulationNotSupportedException('{0} mapper not supported'.format(slot))

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'snespal'
	else:
		#American SNES and Super Famicom are considered to be the same system, so that works out nicely
		system = 'snes'

	#TODO Set ctrl1/ctrl2: barcode_battler, joypad, miracle_piano, mouse, pachinko, sscope (also multitap, twintap which we don't need or maybe we do)

	return mame_system(system, 'cart')

def mame_super_cassette_vision(game, _):
	if game.metadata.specific_info.get('Has-Extra-RAM', False):
		raise EmulationNotSupportedException('RAM on cartridge not supported except from software list (game would malfunction)')

	system = 'scv'
	if game.metadata.tv_type == TVSystem.PAL:
		system = 'scv_pal'

	return mame_system(system, 'cart')

def mame_vic_20(game, _):
	size = game.rom.get_size()
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		raise EmulationNotSupportedException('Single-part >8K cart not supported: %d' % size)

	if game.metadata.tv_type == TVSystem.PAL:
		system = 'vic20p'
	else:
		system = 'vic20'

	return mame_system(system, 'cart', {'iec8': ''}, has_keyboard=True)

def mame_zx_spectrum(game, _):
	options = {}

	system = 'spec128' #Probably a good default
	
	machine = game.metadata.specific_info.get('Machine')
	if machine == ZXMachine.ZX48k:
		system = 'spectrum'
	elif machine == ZXMachine.ZX128k:
		system = 'spec128'
	elif machine == ZXMachine.ZX16k:
		system = 'spectrum'
		options['ramsize'] = '16K'
	elif machine == ZXMachine.SpectrumPlus2:
		system = 'specpls2'
	elif machine == ZXMachine.SpectrumPlus2A:
		system = 'specpl2a'
	elif machine == ZXMachine.SpectrumPlus3:
		system = 'specpls3'

	if game.metadata.media_type == MediaType.Floppy:
		system = 'specpls3'
		slot = 'flop1'
		#If only one floppy is needed, you can add -upd765:1 "" to the commmand line and use just "flop" instead of "flop1".
	elif game.metadata.media_type == MediaType.Snapshot:
		#We do need to plug in the Kempston interface ourselves, though; that's fine. Apparently how the ZX Interface 2 works is that it just maps joystick input to keyboard input, so we don't really need it, but I could be wrong and thinking of something else entirely.
		slot = 'dump'
		if system not in ('specpl2a', 'specpls3'):
			#Just to safeguard; +3 doesn't have stuff in the exp slot other than Multiface 3; as I understand it the real hardware is incompatible with normal stuff so that's why
			joystick_type = game.metadata.specific_info.get('Joystick-Type')
			if joystick_type == ZXJoystick.Kempton:
				options['exp'] = 'kempjoy'
			elif joystick_type in (ZXJoystick.SinclairLeft, ZXJoystick.SinclairRight):
				options['exp'] = 'intf2'
			elif joystick_type == ZXJoystick.Cursor:
				#This just adds a 1-button joystick which maps directions to 5678 and fire to 0
				options['exp'] = 'protek'
	elif game.metadata.media_type == MediaType.Cartridge:
		#This will automatically boot the game without going through any sort of menu, and since it's the Interface 2, they would all use the Interface 2 joystick. So that works nicely
		slot = 'cart'
		options['exp'] = 'intf2'
	elif game.metadata.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		#Should not happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')

	return mame_system(system, slot, options, True)

#Mednafen modules
def mednafen_apple_ii(game, _):
	machines = game.metadata.specific_info.get('Machine')
	if machines:
		if AppleIIHardware.AppleII not in machines and AppleIIHardware.AppleIIPlus not in machines:
			raise EmulationNotSupportedException('Only Apple II and II+ are supported, this needs ' + machines)

	required_ram = game.metadata.specific_info.get('Minimum-RAM')
	if required_ram and required_ram > 64:
		raise EmulationNotSupportedException('Needs at least {0} KB RAM'.format(required_ram))

	return mednafen_base('apple2')

def mednafen_game_gear(game, _):
	mapper = game.metadata.specific_info.get('Mapper')
	if mapper in ('Codemasters', 'EEPROM'):
		raise EmulationNotSupportedException('{0} mapper not supported'.format(mapper))
	return mednafen_base('gg')

def mednafen_gb(game, _):
	_verify_supported_mappers(game, ['ROM only', 'MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC7', 'HuC1', 'HuC3'], [])
	return mednafen_base('gb')

def mednafen_gba(game, _):
	if game.rom.get_size() > (32 * 1024 * 1024):
		raise EmulationNotSupportedException('64MB GBA Video carts not supported')
	return mednafen_base('gba')

def mednafen_lynx(game, _):
	if game.metadata.media_type == MediaType.Cartridge and not game.metadata.specific_info.get('Headered', False):
		raise EmulationNotSupportedException('Needs to have .lnx header')

	return mednafen_base('lynx')

def mednafen_megadrive(game, _):
	if game.metadata.specific_info.get('Uses-SVP', False):
		raise EmulationNotSupportedException('SVP chip not supported')

	mapper = game.metadata.specific_info.get('Mapper')
	unsupported_mappers = ('rom_mcpir', 'rom_sf002', 'rom_mjlov', 'rom_lion3', 'rom_kof99_pokemon', 'rom_squir', 'rom_sf004', 'rom_topf', 'rom_smw64', 'rom_lion2', 'rom_stm95', 'rom_cjmjclub', 'rom_pokestad', 'rom_soulb', 'rom_smb', 'rom_smb2', 'rom_chinf3')
	#Squirrel King does boot but you die instantly, that's interesting
	#Soul Blade freezes soon after starting a match?
	if mapper in unsupported_mappers:
		raise EmulationNotSupportedException(mapper + ' not supported')

	return mednafen_base('md')

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

	return mednafen_base('nes')

def mednafen_snes_faust(game, _):
	#Also does not support any other input except normal controller and multitap
	expansion_chip = game.metadata.specific_info.get('Expansion-Chip')
	if expansion_chip:
		if expansion_chip not in (ExpansionChip.CX4, ExpansionChip.SA_1, ExpansionChip.DSP_1, ExpansionChip.SuperFX, ExpansionChip.SuperFX2):
			raise EmulationNotSupportedException('{0} not supported'.format(expansion_chip))
	return mednafen_base('snes_faust')

#VICE
def vice_c64_base(game):
	#http://vice-emu.sourceforge.net/vice_7.html#SEC94
	#Eh, maybe I should sort this. Or maybe convert it into unsupported_cartridge_types which seems like it would be a smaller list.
	supported_cartridge_types = [0, 1, 50, 35, 30, 9, 15, 34, 21, 24, 25, 26, 52, 17, 32, 10, 44, 13, 3, 29, 45, 46, 7, 42, 39, 2, 51, 19, 14, 28, 38, 5, 43, 27, 12, 36, 23, 4, 47, 31, 22, 48, 8, 40, 20, 16, 11, 18]
	#Not sure if EasyFlash Xbank (33) was supposed to be included in the mention of EasyFlash being emulated? Guess I'll find out
	#I guess "REX 256K EPROM Cart" == Rex EP256 (27)?
	#RGCD, RR-Net MK3 are apparently emulated, whatever they are, but I dunno what number they're assigned to
	supported_cartridge_types += [41, 49, 37, 6] #Slot 0 and 1 carts (have passthrough, and maybe I should be handling them differently as they aren't really meant to be standalone things); also includes Double Quick Brown Box, ISEPIC, and RamCart
	if game.metadata.media_type == MediaType.Cartridge:
		cart_type = game.metadata.specific_info.get('Mapper-Number', None)
		cart_type_name = game.metadata.specific_info.get('Mapper', None)
		if cart_type:
			if cart_type not in supported_cartridge_types:
				raise EmulationNotSupportedException('Cart type %s not supported' % cart_type_name)

	args = ['-VICIIfull']
	if game.metadata.tv_type == TVSystem.NTSC:
		args += ['-model', 'ntsc']
	elif game.metadata.tv_type == TVSystem.PAL:
		args += ['-model', 'pal']
	args.append('$<path>')
	return args

def vice_c64(game, _):
	#x64 and x64sc have the same command line structure, just different exe names
	return LaunchParams('x64sc', vice_c64_base(game))

def vice_c64_fast(game, _):
	return LaunchParams('x64', vice_c64_base(game))

def vice_c128(game, _):
	args = ['-VDCfull']
	if game.metadata.tv_type == TVSystem.NTSC:
		args += ['-model', 'ntsc']
	elif game.metadata.tv_type == TVSystem.PAL:
		args += ['-model', 'pal']
	args.append('$<path>')
	return LaunchParams('x128', args)

def vice_pet(game, _):
	args = ['-CRTCfull']
	if game.metadata.tv_type == TVSystem.NTSC:
		args += ['-ntsc']
	elif game.metadata.tv_type == TVSystem.PAL:
		args += ['-pal']
	
	machine = game.metadata.specific_info.get('Machine')
	#The "Machine" field is set directly to the model argument, so that makes things a lot easier for me. Good thing I decided to do that
	if machine:
		args += ['-model', machine]

	ram_size = game.metadata.specific_info.get('Minimum-RAM')
	if ram_size:
		args += ['-ramsize', str(ram_size)]

	args.append('$<path>')
	return LaunchParams('xpet', args)

def vice_plus4(game, _):
	args = ['-TEDfull']
	if game.metadata.tv_type == TVSystem.NTSC:
		args += ['-model', 'plus4ntsc']
	elif game.metadata.tv_type == TVSystem.PAL:
		args += ['-model', 'plus4pal']
	args.append('$<path>')
	return LaunchParams('xplus4', args)

def vice_vic20(game, _):
	args = ['-VICfull']
	if game.metadata.tv_type == TVSystem.NTSC:
		args += ['-model', 'vic20ntsc']
	elif game.metadata.tv_type == TVSystem.PAL:
		args += ['-model', 'vic20pal']
	if game.metadata.media_type == MediaType.Cartridge:
		args.append('-cartgeneric')
		size = game.rom.get_size()
		if size > ((8 * 1024) + 2):
			#Frick
			#TODO: Support multiple parts with -cart2 -cartA etc; this will probably require a lot of convoluted messing around to know if a given ROM is actually the second part of a multi-part cart (probably using software lists) and using game.subroms etc
			raise EmulationNotSupportedException('Single-part >8K cart not supported: %d' % size)

	if game.metadata.specific_info.get('Peripheral') == 'Paddle':
		args += ['-controlport1device', '2']

	args.append('$<path>')
	return LaunchParams('xvic', args)

#Other emulators
def a7800(game, _):
	#Hmm, mostly the same as mame_a7800, except without the MAME
	if not game.metadata.specific_info.get('Headered', False):
		#This would only be supported via software list (although A7800 seems to have removed that anyway)
		raise EmulationNotSupportedException('No header')

	args = []
	if game.metadata.tv_type == TVSystem.PAL:
		args.append('a7800p')
	else:
		args.append('a7800')
	#There are also a7800u1, a7800u2, a7800pu1, a7800pu2 to change the colour palettes. Maybe that could be an specific_config option...

	global _have_hiscore_software
	if _have_hiscore_software is None:
		_have_hiscore_software = _is_highscore_cart_available()

	if _have_hiscore_software and game.metadata.specific_info.get('Uses-Hiscore-Cart', False):
		args += ['-cart1', 'hiscore', '-cart2', '$<path>']
	else:
		args += ['-cart', '$<path>']

	return LaunchParams('a7800', args)

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
	return LaunchParams('citra-qt', ['$<path>'])

def cxnes(game, _):
	allowed_mappers = [
		0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14,
		15, 16, 18, 19, 21, 22, 23, 24, 25, 26, 28, 29,
		30, 31, 32, 33, 34, 36, 37, 38, 39, 41, 44, 46,
		47, 48, 49, 58, 60, 61, 62, 64, 65, 66, 67, 68,
		69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 82,
		85, 86, 87, 88, 89, 90, 91, 93, 94, 95, 97, 99,
		105, 107, 112, 113, 115, 118, 119, 133, 137, 138, 139, 140,
		141, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153,
		154, 155, 158, 159, 166, 167, 178, 180, 182, 184, 185, 189,
		192, 193, 200, 201, 202, 203, 205, 206, 207, 209, 210, 211,
		218, 225, 226, 228, 230, 231, 232, 234, 240, 241, 245, 246,
	]

	if game.metadata.specific_info.get('Header-Format', None) == 'iNES':
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper not in allowed_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: %d (%s)' % (mapper, game.metadata.specific_info.get('Mapper')))

	#Could possibly do something involving --no-romcfg if there's no config found, otherwise the emulator pops up a message about that unless you disable romcfg entirely
	return LaunchParams('cxnes', ['-f', '$<path>'])

def dolphin(game, _):
	if game.metadata.specific_info.get('No-Disc-Magic', False):
		raise EmulationNotSupportedException('No disc magic')

	return LaunchParams('dolphin-emu', ['-b', '-e', '$<path>'])

def flycast(_, specific_config):
	env_vars = {}
	if specific_config.get('force_opengl_version', False):
		#Looks like this still needs to be here
		env_vars['MESA_GL_VERSION_OVERRIDE'] = '4.3'
	args = ['-config', 'x11:fullscreen=1']
	args.append('$<path>')
	#Executable name is still called Reicast, which means until I do the custom paths to emulators thing you can't really use both Flycast and Reicast as your emulator preference for Dreamcast (but then why would you need to do that)
	return LaunchParams('reicast', args, env_vars)

def fs_uae(game, specific_config):
	args = ['--fullscreen']
	if game.metadata.platform == 'Amiga CD32':
		args.extend(['--amiga_model=CD32', '--joystick_port_0_mode=cd32 gamepad', '--cdrom_drive_0=$<path>'])
	elif game.metadata.platform == 'Commodore CDTV':
		args.extend(['--amiga_model=CDTV', '--cdrom_drive_0=$<path>'])
	else:
		model = None
		machine = game.metadata.specific_info.get('Machine')
		if machine:
			amiga_models = {
				#All the models supported by FS-UAE --amiga_model argument
				'A500',
				'A500+',
				'A600',
				'A1000',
				'A1200',
				'A1200/20',
				'A3000',
				'A4000/40',
				#CDTV, CD32
			}		
			if machine in amiga_models:
				model = machine
			elif machine == 'A4000':
				model = 'A4000/40'
			else:
				raise EmulationNotSupportedException('FS-UAE does not emulate a ' + machine)
		else:
			chipset_models = {
				'OCS': 'A500', #Also A1000 (A2000 also has OCS but doesn't appear to be an option?)
				'ECS': 'A600', #Also A500+ (A3000 should work, but doesn't seem to be possible)
				'AGA': 'A4000/040', #Also 1200 (which only has 68EC020 CPU instead of 68040)
			}
			#TODO: It would be better if this didn't force specific models, but could look at what ROMs the user has for FS-UAE and determines which models are available that support the given chipset, falling back to backwards compatibility for newer models or throwing EmulationNotSupportedException as necessary

			#AGA is the default default if there's no default (use the most powerful machine available)
			chipset = game.metadata.specific_info.get('Chipset', specific_config.get('default_chipset', 'AGA'))
			model = chipset_models.get(chipset)

		if model:
			args.append('--amiga_model=%s' % model)

		#I can't figure out how to get these sorts of things to autoboot, or maybe they don't
		if game.metadata.specific_info.get('Requires-Hard-Disk', False):
			raise EmulationNotSupportedException('Requires a hard disk')
		if game.metadata.specific_info.get('Requires-Workbench', False):
			raise EmulationNotSupportedException('Requires Workbench')

		#Hmm... there is also --cpu=68060 which some demoscene productions use so maybe I should look into that...
		args.append('--floppy_drive_0=$<path>')
	if game.metadata.tv_type == TVSystem.NTSC:
		args.append('--ntsc_mode=1')
	return LaunchParams('fs-uae', args)

def gambatte(game, _):
	#I guess MBC1 Multicart only works if you tick the "Multicart compatibility" box
	#MMM01 technically works but only boots the first game instead of the menu, so it doesn't really work work
	_verify_supported_mappers(game, ['ROM only', 'MBC1', 'MBC2', 'MBC3', 'HuC1', 'MBC5'], ['MBC1 Multicart'])

	return LaunchParams('gambatte_qt', ['--full-screen', '$<path>'])

def gbe_plus(game, _):
	#In theory, only this should support Pocket Sonar (so far), but there's not really a way to detect that since it just claims to be MBC1 in the header...
	_verify_supported_mappers(game, ['ROM only', 'MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC6', 'MBC7', 'Pocket Camera', 'HuC1'], ['MBC1 Multicart'])
	return LaunchParams('gbe_plus_qt', ['$<path>'])

def kega_fusion(game, _):
	mapper = game.metadata.specific_info.get('Mapper')
	#rom_kof99: Pocket Monsters does work (game-specific hack, probably?), which is why in platform_metadata/megadrive I've treated it specially and called it rom_kof99_pokemon
	if mapper in ('aqlian', 'rom_sf002', 'rom_sf004', 'rom_smw64', 'rom_topf', 'rom_kof99', 'rom_cjmjclub', 'rom_pokestad', 'rom_soulb', 'rom_chinf3'):
		raise EmulationNotSupportedException(mapper + ' not supported')
	return LaunchParams('kega-fusion', ['-fullscreen', '$<path>'])

def medusa(game, _):
	if game.metadata.platform == 'DSi':
		raise EmulationNotSupportedException('DSi exclusive games and DSiWare not supported')
	if game.metadata.specific_info.get('Is-iQue', False):
		raise EmulationNotSupportedException('iQue DS not supported')

	if game.metadata.platform in ('Game Boy', 'Game Boy Color'):
		verify_mgba_mapper(game)

	args = ['-f']
	if game.metadata.platform != 'DS':
		#(for GB/GBA stuff only, otherwise BIOS is mandatory whether you like it or not)
		if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
			args.append('-C')
			args.append('useBios=0')

	args.append('$<path>')
	return LaunchParams('medusa-emu-qt', args)

def mgba(game, _):
	if game.metadata.platform in ('Game Boy', 'Game Boy Color'):
		verify_mgba_mapper(game)

	args = ['-f']
	if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
		args.append('-C')
		args.append('useBios=0')
	args.append('$<path>')
	return LaunchParams('mgba-qt', args)

def mupen64plus(game, specific_config):
	if game.metadata.specific_info.get('ROM-Format', None) == 'Unknown':
		raise EmulationNotSupportedException('Undetectable ROM format')

	args = ['--nosaveoptions', '--fullscreen']

	no_plugin = 1
	controller_pak = 2
	transfer_pak = 4
	rumble_pak = 5

	use_controller_pak = game.metadata.specific_info.get('Uses-Controller-Pak', False)
	use_transfer_pak = game.metadata.specific_info.get('Uses-Transfer-Pak', False)
	use_rumble_pak = game.metadata.specific_info.get('Force-Feedback', False)

	plugin = no_plugin

	if use_controller_pak and use_rumble_pak:
		plugin = controller_pak if specific_config.get('prefer_controller_pak_over_rumble', False) else rumble_pak
	elif use_controller_pak:
		plugin = controller_pak
	elif use_rumble_pak:
		plugin = rumble_pak
	elif use_transfer_pak:
		plugin = transfer_pak

	if plugin != no_plugin:
		#TODO: Only do this if using SDL plugin (i.e. not Raphnet raw plugin)
		args.extend(['--set', 'Input-SDL-Control1[plugin]=%d' % plugin])

	#TODO: If use_transfer_pak, put in a rom + save with --gb-rom-1 and --gb-ram-1 somehow... hmm... can't insert one at runtime with console UI (and I guess you're not supposed to hotplug carts with a real N64 + Transfer Pak) sooo, I'll have to have a think about the most user-friendly way for me to handle that as a frontend

	args.append('$<path>')
	return LaunchParams('mupen64plus', args)

def ppsspp(game, _):
	if game.metadata.specific_info.get('Is-UMD-Video', False):
		raise EmulationNotSupportedException('UMD video discs not supported')
	return LaunchParams('ppsspp-qt', ['$<path>'])

def reicast(game, specific_config):
	if game.metadata.specific_info.get('Uses-Windows-CE', False):
		raise EmulationNotSupportedException('Windows CE-based games not supported')
	env_vars = {}
	if specific_config.get('force_opengl_version', False):
		#This shouldn't be a thing, it's supposed to fall back to OpenGL 3.0 if 4.3 isn't supported (there was a commit that fixed an issue where it didn't), but then I guess that doesn't work for me so once again I have decided to do things the wrong way instead of what a normal sensible person would do, anyway somehow this... works just fine with this environment variable, although on a chipset only supporting 4.2 it by all logic shouldn't, and I don't really know why, because I'm not an OpenGL programmer or whatever, I'm just some Python-using dumbass
		env_vars['MESA_GL_VERSION_OVERRIDE'] = '4.3'
	args = ['-config', 'x11:fullscreen=1']
	if not game.metadata.specific_info.get('Supports-VGA', True):
		#Use RGB component instead (I think that should be compatible with everything, and would be better quality than composite, which should be 1)
		args += ['-config', 'config:Dreamcast.Cable=2']
	else:
		#This shouldn't be needed, as -config is supposed to be temporary, but it isn't and writes the component cable setting back to the config file, so we'll set it back
		args += ['-config', 'config:Dreamcast.Cable=0']
	args.append('$<path>')
	return LaunchParams('reicast', args, env_vars)

def snes9x(game, _):
	slot = game.metadata.specific_info.get('Slot')
	if slot:
		#There are a few bootleg things that will not work
		if slot.endswith('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col'):
			raise EmulationNotSupportedException('{0} mapper not supported'.format(slot))

	expansion_chip = game.metadata.specific_info.get('Expansion-Chip')
	if expansion_chip in (ExpansionChip.ST018, ExpansionChip.DSP_3):
		#ST018 is implemented enough here to boot to menu, but hangs when starting a match
		#DSP-3 looks like it's going to work and then when I played around a bit and the AI was starting its turn (I think?) the game hung to a glitchy mess so I guess not
		raise EmulationNotSupportedException('{0} not supported'.format(expansion_chip))
	return LaunchParams('snes9x-gtk', ['$<path>'])


#Game engines
def make_prboom_plus_command_line(_, specific_config):
	args = []
	if 'save_dir' in specific_config:
		args.append('-save')
		args.append(specific_config['save_dir'])

	args.append('-iwad')
	args.append('$<path>')
	return args

#DOS/Mac stuff
def basilisk_ii(app, specific_config):
	#This is all broken, I wouldn't even bother until I've messed with this a lot
	if 'arch' in app.config:
		if app.config['arch'] == 'ppc':
			raise EmulationNotSupportedException('PPC not supported')

	#This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	#Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	autoboot_txt_path = os.path.join(specific_config['shared_folder'], 'autoboot.txt')
	width = specific_config.get('default_width', 1920) #TODO Check the type to make sure it is int and use it as such. Right now, it's actually a string representing an int
	height = specific_config.get('default_height', 1080)
	if 'max_resolution' in app.config:
		width, height = app.config['max_resolution']
	#Can't do anything about colour depth at the moment (displaycolordepth is functional on some SDL1 builds, but not SDL2)
	#Or controls... but I swear I will find a way!!!!

	hfv_path, inner_path = app.path.split(':', 1)
	
	#If you're not using an SDL2 build of BasiliskII, you probably want to change dga to window! Well you really want to get an SDL2 build of BasiliskII, honestly, because I assume you do. Well the worst case scenario is that it still works, but it hecks your actual host resolution
	commands = [
		LaunchParams('sh', ['-c', 'echo {0} > {1}'.format(inner_path, autoboot_txt_path)]), #Hack because I can't be fucked refactoring MultiCommandLaunchParams to do pipey bois/redirecty bois
		LaunchParams('BasiliskII', ['--screen', 'dga/{0}/{1}'.format(width, height), '--extfs', specific_config['shared_folder'], '--disk', hfv_path]),
		LaunchParams('rm', [autoboot_txt_path])
	]
	return MultiCommandLaunchParams(commands)

def _get_dosbox_config(app, folder):
	if not os.path.isdir(folder):
		return None

	for conf in os.listdir(folder):
		path = os.path.join(folder, conf)
		name, _ = os.path.splitext(conf)
		if app.name in (name, name.replace(' - ', ': ')):
			return path

	return None

def _make_dosbox_config(app, specific_config):
	configwriter = configparser.ConfigParser(allow_no_value=True)
	configwriter.optionxform = str

	configwriter['sdl'] = {}
	configwriter['sdl']['fullscreen'] = 'true'
	configwriter['sdl']['fullresolution'] = 'desktop'
	#TODO: Set mapper file, which will of course require another separate directory to store crap

	if 'required_hardware' in app.config:
		if 'for_xt' in app.config['required_hardware']:
			if app.config['required_hardware']['for_xt']:
				configwriter['cpu'] = {}
				configwriter['cpu']['cycles'] = specific_config.get('slow_cpu_cycles', 477)

		if 'max_graphics' in app.config['required_hardware']:
			configwriter['dosbox'] = {}
			graphics = app.config['required_hardware']['max_graphics']
			configwriter['dosbox']['machine'] = 'svga_s3' if graphics == 'svga' else graphics

	name = io_utils.sanitize_name(app.name) + '.ini'
	folder = specific_config.get('dosbox_configs_path') #TODO default value ugh my code sucks sometimes
	path = os.path.join(folder, name)

	os.makedirs(folder, exist_ok=True)
	with open(path, 'wt') as config_file:
		configwriter.write(config_file)

	return path

def _make_dosbox_x_config(app, specific_config):
	configwriter = configparser.ConfigParser(allow_no_value=True)
	configwriter.optionxform = str

	configwriter['sdl'] = {}
	configwriter['sdl']['fullscreen'] = 'true'
	configwriter['sdl']['fullresolution'] = 'desktop'
	#TODO: Set mapper file, which will of course require another separate directory to store crap

	if 'required_hardware' in app.config:
		if 'for_xt' in app.config['required_hardware']:
			if app.config['required_hardware']['for_xt']:
				configwriter['cpu'] = {}
				configwriter['cpu']['cputype'] = '8086'
				configwriter['cpu']['cycles'] = specific_config.get('slow_cpu_cycles', 477)

		if 'max_graphics' in app.config['required_hardware']:
			configwriter['dosbox'] = {}
			graphics = app.config['required_hardware']['max_graphics']
			configwriter['dosbox']['machine'] = 'svga_s3' if graphics == 'svga' else graphics

	name = io_utils.sanitize_name(app.name) + '.ini'
	config_folder = specific_config.get('dosbox_x_configs_path')
	path = os.path.join(config_folder, name)

	#Need to do the autoexec thing manually, because DOSBox-X doesn't have that thing where you put a file in the command line and it autoexecs it
	folder, name = os.path.split(app.path)
	autoexec = [
		'MOUNT -u D:', #It's ours now. Surely there must be a better way to do this...
		'MOUNT D: {0}'.format(folder),
		'D:',
		name,
	]
	
	os.makedirs(config_folder, exist_ok=True)
	with open(path, 'wt') as config_file:
		configwriter.write(config_file)
		config_file.write('[autoexec]\n')
		for line in autoexec:
			config_file.write(line)
			config_file.write('\n')

	return path
	
def dosbox(app, specific_config):
	conf = _get_dosbox_config(app, specific_config.get('dosbox_configs_path'))
	if ('--regen-dos-config' in sys.argv) or not conf:
		conf = _make_dosbox_config(app, specific_config)

	return LaunchParams('dosbox', ['-exit', '-noautoexec', '-userconf', '-conf', conf, app.path])

def dosbox_x(app, specific_config):
	conf = _get_dosbox_config(app, specific_config.get('dosbox_x_configs_path'))
	if ('--regen-dos-config' in sys.argv) or not conf:
		conf = _make_dosbox_x_config(app, specific_config)

	#Hmm, interestingly the app path does nothing, but -exit still does something?
	return LaunchParams('dosbox-x', ['-exit', '-userconf', '-conf', conf])
