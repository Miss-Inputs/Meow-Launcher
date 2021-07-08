import os
import re
import shlex

from common_types import (EmulationNotSupportedException, MediaType,
                          NotARomException)
from launchers import LaunchParams, MultiCommandLaunchParams
from platform_types import (AppleIIHardware, Atari2600Controller,
                            GameBoyColourFlag, MegadriveRegionCodes,
                            NESPeripheral, SaturnRegionCodes, SMSPeripheral,
                            SNESExpansionChip, SwitchContentMetaType,
                            WiiTitleType, ZXJoystick, ZXMachine)

from .emulator_command_line_helpers import (_is_software_available,
                                            _verify_supported_gb_mappers,
                                            first_available_system,
                                            is_highscore_cart_available,
                                            mame_driver, mednafen_module,
                                            verify_mgba_mapper)
from .region_info import TVSystem
from .system_info import (arabic_msx1_drivers, arabic_msx2_drivers,
                          japanese_msx1_drivers, japanese_msx2_drivers,
                          working_msx1_drivers, working_msx2_drivers,
                          working_msx2plus_drivers)


#MAME drivers
def mame_32x(game, _, emulator_config):
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
		if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
			system = '32xe'
	return mame_driver(game, emulator_config, system, 'cart')

def mame_amiga_cd32(game, _, emulator_config):
	system = 'cd32'
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		#PAL is more likely if it is unknown
		system = 'cd32n'
	return mame_driver(game, emulator_config, system, 'cdrom')

def mame_amstrad_pcw(game, _, emulator_config):
	if game.metadata.specific_info.get('Requires-CPM'):
		#Nah too messy
		raise EmulationNotSupportedException('Needs CP/M and apparently I don''t feel like fiddling around with that or something')
	return mame_driver(game, emulator_config, 'pcw10', 'flop', has_keyboard=True)

def mame_apple_ii(game, _, emulator_config):
	slot_options = {'gameio': 'joy'}
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

	return mame_driver(game, emulator_config, system, 'flop1', slot_options, has_keyboard=True)

def mame_atari_2600(game, _, emulator_config):
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

	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'a2600p'
	else:
		system = 'a2600'

	return mame_driver(game, emulator_config, system, 'cart', slot_options=options)

def mame_atari_jaguar(game, _, emulator_config):
	if game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart'
	elif game.metadata.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_driver(game, emulator_config, 'jaguar', slot)

def mame_atari_7800(game, _, emulator_config):
	if not game.metadata.specific_info.get('Headered', False):
		#This would only be supported via software list
		raise EmulationNotSupportedException('No header')

	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'a7800p'
	else:
		system = 'a7800'

	if not hasattr(mame_atari_7800, 'have_hiscore_software'):
		mame_atari_7800.have_hiscore_software = is_highscore_cart_available()

	if mame_atari_7800.have_hiscore_software and game.metadata.specific_info.get('Uses-Hiscore-Cart', False):
		return mame_driver(game, emulator_config, system, 'cart2', {'cart1': 'hiscore'})

	return mame_driver(game, emulator_config, system, 'cart')

def mame_atari_8bit(game, system_config, emulator_config):
	slot_options = {}
	if game.metadata.media_type == MediaType.Cartridge:
		if game.metadata.specific_info.get('Headered', False):
			cart_type = game.metadata.specific_info['Mapper']
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
			basic_path = system_config.get('basic_path')
			if not basic_path:
				raise EmulationNotSupportedException('This software needs BASIC ROM to function')
			slot_options['cart1'] = basic_path

	machine = game.metadata.specific_info.get('Machine')
	if machine == 'XL':
		system = 'a800xlp' if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL else 'a800xl'
	elif machine == 'XE':
		system = 'a65xe' #No PAL XE machine in MAME?
	else:
		system = 'a800pal' if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL else 'a800'
	
	return mame_driver(game, emulator_config, system, slot, slot_options, has_keyboard=True)

def mame_c64(game, _, emulator_config):
	#While we're here building a command line, should mention that you have to manually put a joystick in the first
	#joystick port, because by default there's only a joystick in the second port.  Why the fuck is that the default?
	#Most games use the first port (although, just to be annoying, some do indeed use the second...  why????)
	#Anyway, might as well use this "Boostergrip" thingy, or really it's like using the C64GS joystick, because it just
	#gives us two extra buttons for any software that uses it (probably nothing), and the normal fire button works as
	#normal.  _Should_ be fine
	#(Super cool pro tip: Bind F1 to Start)

	#Explicitly listed as UNSUPPORTED in https://github.com/mamedev/mame/blob/master/src/lib/formats/cbm_crt.cpp
	unsupported_mappers = [1, 2, 6, 9, 20, 29, 30, 33, 34, 35, 36, 37, 38, 40, 42, 45, 46, 47, 50, 52, 54]
	#Not listed as unsupported, but from anecdotal experience doesn't seem to work. Should try these again one day
	unsupported_mappers += [32]
	#32 = EasyFlash. Well, at least it doesn't segfault. Just doesn't boot, even if I play with the dip switch that says "Boot". Maybe I'm missing something here?
	cart_type = game.metadata.specific_info.get('Mapper-Number', None)
	cart_type_name = game.metadata.specific_info.get('Mapper', None)

	if cart_type in unsupported_mappers:
		raise EmulationNotSupportedException('%s cart not supported' % cart_type_name)

	system = 'c64'

	#Don't think we really need c64c unless we really want the different SID chip. Maybe that could be an emulator option?
	#Don't think we really need c64gs either

	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'c64p'


	return mame_driver(game, emulator_config, system, 'cart', {'joy1': 'joybstr', 'joy2': 'joybstr', 'iec8': ''}, True)

def mame_coleco_adam(game, _, emulator_config):
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

	return mame_driver(game, emulator_config, 'adam', slot, slot_options, has_keyboard=True)

def mame_colecovision(game, _, emulator_config):
	system = 'coleco'
	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		#This probably won't happen (officially, carts are supposed to support both NTSC and PAL), but who knows
		system = 'colecop'

	return mame_driver(game, emulator_config, system, 'cart')

def mame_dreamcast(game, _, emulator_config):
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
	return mame_driver(game, emulator_config, system, 'cdrom')

def mame_fm_towns(game, _, emulator_config):
	#Hmm… does this really need to be here along with fmtmarty when they are mostly identical
	if game.metadata.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.OpticalDisc:
		slot = 'cdrom'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	
	#Give us 10 meganbytes of RAM because we can (some software requires 4MB ram for example)
	#Hopefully nothing requires 2MB explicitly or less
	options = {'ramsize': '10M'}
	#Vanilla fmtowns seems to be a bit crashy? It is all MACHINE_NOT_WORKING anyway so nothing is expected
	return mame_driver(game, emulator_config, 'fmtownsux', slot, options)

def mame_fm_towns_marty(game, _, emulator_config):
	if game.metadata.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.metadata.media_type == MediaType.OpticalDisc:
		slot = 'cdrom'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	
	#Give us 4 meganbytes of RAM just in case we need it (some do, see software list info=usage)
	#Hopefully nothing requires 2MB explicitly or less
	options = {'ramsize': '4M'}
	return mame_driver(game, emulator_config, 'fmtmarty', slot, options)

def mame_game_boy(game, _, emulator_config):
	#Do all of these actually work or are they just detected? (HuC1 and HuC3 are supposedly non-working, and are treated as MBC3?)
	#gb_slot.cpp also mentions MBC4, which isn't real
	supported_mappers = ['MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC6', 'MBC7', 'Pocket Camera', 'Bandai TAMA5']
	detected_mappers = ['MMM01', 'MBC1 Multicart', 'Wisdom Tree', 'Li Cheng', 'Sintax']

	_verify_supported_gb_mappers(game, supported_mappers, detected_mappers)

	#Not much reason to use gameboy, other than a green tinted screen. I guess that's the only difference
	system = 'gbcolor' if emulator_config.options.get('use_gbc_for_dmg') else 'gbpocket'

	#Should be just as compatible as supergb but with better timing... I think
	super_gb_system = 'supergb2'

	is_colour = game.metadata.specific_info.get('Is-Colour', GameBoyColourFlag.No) in (GameBoyColourFlag.Required, GameBoyColourFlag.Yes)
	is_sgb = game.metadata.specific_info.get('SGB-Enhanced', False)

	prefer_sgb = emulator_config.options.get('prefer_sgb_over_gbc', False)
	if is_colour and is_sgb:
		system = super_gb_system if prefer_sgb else 'gbcolor'
	elif is_colour:
		system = 'gbcolor'
	elif is_sgb:
		system = super_gb_system

	return mame_driver(game, emulator_config, system, 'cart')

def mame_game_gear(game, _, emulator_config):
	system = 'gamegear'
	if game.metadata.specific_info.get('Region-Code') == 'Japanese':
		system = 'gamegeaj'
	return mame_driver(game, emulator_config, system, 'cart')

def mame_ibm_pcjr(game, _, emulator_config):
	if game.metadata.media_type == MediaType.Cartridge:
		slot = 'cart1'
	elif game.metadata.media_type == MediaType.Floppy:
		#Floppy is the only other kind of rom we accept at this time
		slot = 'flop'
	else:
		#Should never happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')
	return mame_driver(game, emulator_config, 'ibmpcjr', slot, has_keyboard=True)

def mame_intellivision(game, _, emulator_config):
	system = 'intv'

	uses_keyboard = False
	if game.metadata.specific_info.get('Uses-ECS', False):
		#This has a keyboard and Intellivoice module attached; -ecs.ctrl_port synth gives a music synthesizer instead of keyboard
		#Seemingly none of the prototype keyboard games use intvkbd, they just use this
		system = 'intvecs'
		uses_keyboard = True
	elif game.metadata.specific_info.get('Uses-Intellivoice', False):
		system = 'intvoice'

	return mame_driver(game, emulator_config, system, 'cart', has_keyboard=uses_keyboard)

def mame_lynx(game, _, emulator_config):
	if game.metadata.media_type == MediaType.Cartridge and not game.rom.extension == 'lyx' and not game.metadata.specific_info.get('Headered', False):
		raise EmulationNotSupportedException('Needs to have .lnx header')

	slot = 'cart'

	if game.metadata.media_type == MediaType.Executable:
		slot = 'quik'

	return mame_driver(game, emulator_config, 'lynx', slot)

def mame_master_system(game, _, emulator_config):
	tv_type = TVSystem.PAL #Seems a more sensible default at this point (there are also certain homebrews with less-than-detectable TV types that demand PAL)

	if game.metadata.specific_info.get('TV-Type') in (TVSystem.NTSC, TVSystem.Agnostic):
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

	return mame_driver(game, emulator_config, system, 'cart', slot_options)

def mame_mega_cd(game, _, emulator_config):
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
		if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
			system = 'megacd'
	#megacda also exists (Asia/PAL), not sure if we need it (is that what EuropeA is for?)
	return mame_driver(game, emulator_config, system, 'cdrom')

def mame_megadrive(game, _, emulator_config):
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
	if mapper == 'topf':
		#Doesn't seem to be detected via fullpath as being rom_topf, so it might work from software list
		raise EmulationNotSupportedException('Top Fighter 2000 MK VII not supported')
	if mapper == 'yasech':
		#Looks like it's same here... nothing about it being unsupported in SL entry
		raise EmulationNotSupportedException('Ya Se Chuan Shuo not supported')
	if mapper == 'kof99_pokemon':
		#This isn't a real mapper, Pocket Monsters uses rom_kof99 but it doesn't work (but KOF99 bootleg does)
		#Probably because it's detected as rom_99 when loaded from fullpath, so... it be like that sometimes
		raise EmulationNotSupportedException('Pocket Monsters not supported from fullpath')
	if mapper == 'smw64':
		raise EmulationNotSupportedException('Super Mario World 64 not supported')
	if mapper == 'cjmjclub':
		raise EmulationNotSupportedException('Chao Ji Mahjong Club not supported')
	if mapper == 'soulb':
		#It looks like this should work, but loading it from fullpath results in an "Unknown slot option 'rom_soulblad' in slot 'mdslot'" error when it should be rom_soulb instead
		raise EmulationNotSupportedException('Soul Blade not supported')
	if mapper == 'chinf3':
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
		if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
			system = 'megadriv'
	return mame_driver(game, emulator_config, system, 'cart')

def mame_microbee(game, _, emulator_config):
	system = 'mbeepc' #Either will do but this gives us colour (although mbeeppc seems to not play nicely with quickload)
	if game.metadata.media_type == MediaType.Executable:
		slot = 'quik1'
	elif game.metadata.media_type == MediaType.Floppy:
		system = 'mbee128'#We need a system with a floppy drive, this is apparently not working but it seems fine (the other floppy ones do not seem fine)
		slot = 'flop1'
	else:
		raise EmulationNotSupportedException('Unknown media type', game.metadata.media_type)
	return mame_driver(game, emulator_config, system, slot, has_keyboard=True)

def mame_msx1(game, _, emulator_config):
	#Possible slot options: centronics is there to attach printers and such; if using a floppy can put bm_012 (MIDI interface) or moonsound (OPL4 sound card, does anything use that?) in the cart port but I'm not sure that's needed; the slots are the same for MSX2
	if game.metadata.specific_info.get('Japanese-Only', False):
		if not hasattr(mame_msx1, 'japanese_msx1_system'):
			mame_msx1.japanese_msx1_system = first_available_system(japanese_msx1_drivers + japanese_msx2_drivers + working_msx2plus_drivers)
		if mame_msx1.japanese_msx1_system is None:
			raise EmulationNotSupportedException('No Japanese MSX1 driver available')
		system = mame_msx1.japanese_msx1_system
	elif game.metadata.specific_info.get('Arabic-Only', False):
		if not hasattr(mame_msx1, 'arabic_msx1_system'):
			mame_msx1.arabic_msx1_system = first_available_system(arabic_msx1_drivers + arabic_msx2_drivers)
		if mame_msx1.arabic_msx1_system is None:
			raise EmulationNotSupportedException('No Arabic MSX1 driver available')
		system = mame_msx1.arabic_msx1_system
	else:
		if not hasattr(mame_msx1, 'msx1_system'):
			mame_msx1.msx1_system = first_available_system(working_msx1_drivers + working_msx2_drivers + working_msx2plus_drivers)
		if mame_msx1.msx1_system is None:
			raise EmulationNotSupportedException('No MSX1 driver available')
		system = mame_msx1.msx1_system

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

	return mame_driver(game, emulator_config, system, slot, slot_options, has_keyboard=True)

def mame_msx2(game, _, emulator_config):
	if game.metadata.specific_info.get('Japanese-Only', False):
		if not hasattr(mame_msx2, 'japanese_msx2_system'):
			mame_msx2.japanese_msx2_system = first_available_system(japanese_msx2_drivers + working_msx2plus_drivers)
		if mame_msx2.japanese_msx2_system is None:
			raise EmulationNotSupportedException('No Japanese MSX2 driver available')
		system = mame_msx2.japanese_msx2_system
	elif game.metadata.specific_info.get('Arabic-Only', False):
		if not hasattr(mame_msx2, 'arabic_msx2_system'):
			mame_msx2.arabic_msx2_system = first_available_system(arabic_msx2_drivers)
		if mame_msx2.arabic_msx2_system is None:
			raise EmulationNotSupportedException('No Arabic MSX2 driver available')
		system = mame_msx2.arabic_msx2_system
	else:
		if not hasattr(mame_msx2, 'msx2_system'):
			mame_msx2.msx2_system = first_available_system(working_msx2_drivers + working_msx2plus_drivers)
		if mame_msx2.msx2_system is None:
			raise EmulationNotSupportedException('No MSX2 driver available')
		system = mame_msx2.msx2_system

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

	return mame_driver(game, emulator_config, system, slot, slot_options, has_keyboard=True)

def mame_msx2plus(game, _, emulator_config):
	if not hasattr(mame_msx2plus, 'msx2plus_system'):
		mame_msx2plus.msx2plus_system = first_available_system(working_msx2plus_drivers)
	if mame_msx2plus.msx2plus_system is None:
		raise EmulationNotSupportedException('No MSX2+ driver available')
	system = mame_msx2plus.msx2plus_system

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

	return mame_driver(game, emulator_config, system, slot, slot_options, has_keyboard=True)

def mame_n64(game, _, emulator_config):
	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		raise EmulationNotSupportedException('NTSC only')

	return mame_driver(game, emulator_config, 'n64', 'cart')

def mame_nes(game, _, emulator_config):
	if game.rom.extension == 'fds':
		#We don't need to detect TV type because the FDS was only released in Japan and so the Famicom can be used for everything
		#TODO: This isn't really right, should set controllers
		return mame_driver(game, emulator_config, 'fds', 'flop')

	unsupported_ines_mappers = (27, 29, 30, 55, 59, 60, 81, 84, 98,
	99, 100, 101, 102, 103, 109, 110, 111, 122, 124, 125, 127, 128,
	129, 130, 131, 135, 151, 161, 169, 170, 174, 181, 219, 220,
	236, 237, 239, 247, 248, 251, 253)
	supported_unif_mappers = ('DREAMTECH01', 'NES-ANROM', 'NES-AOROM', 'NES-CNROM', 'NES-NROM', 'NES-NROM-128', 'NES-NROM-256', 'NES-NTBROM', 'NES-SLROM', 'NES-TBROM', 'NES-TFROM', 'NES-TKROM', 'NES-TLROM', 'NES-UOROM', 'UNL-22211', 'UNL-KOF97', 'UNL-SA-NROM', 'UNL-VRC7', 'UNL-T-230', 'UNL-CC-21', 'UNL-AX5705', 'UNL-SMB2J', 'UNL-8237', 'UNL-SL1632', 'UNL-SACHEN-74LS374N', 'UNL-TC-U01-1.5M', 'UNL-SACHEN-8259C', 'UNL-SA-016-1M', 'UNL-SACHEN-8259D', 'UNL-SA-72007', 'UNL-SA-72008', 'UNL-SA-0037', 'UNL-SA-0036', 'UNL-SA-9602B', 'UNL-SACHEN-8259A', 'UNL-SACHEN-8259B', 'BMC-190IN1', 'BMC-64IN1NOREPEAT', 'BMC-A65AS', 'BMC-GS-2004', 'BMC-GS-2013', 'BMC-NOVELDIAMOND9999999IN1', 'BMC-SUPER24IN1SC03', 'BMC-SUPERHIK8IN1', 'BMC-T-262', 'BMC-WS', 'BMC-N625092')
	if game.metadata.specific_info.get('Header-Format', None) in ('iNES', 'NES 2.0'):
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers or mapper >= 256:
			raise EmulationNotSupportedException('Unsupported mapper: {0} ({1})'.format(mapper, game.metadata.specific_info.get('Mapper')))
	if game.metadata.specific_info.get('Header-Format', None) == 'UNIF':
		mapper = game.metadata.specific_info.get('Mapper')
		if mapper not in supported_unif_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: {0}'.format(mapper))

	has_keyboard = False

	if game.metadata.specific_info.get('Is-Dendy', False):
		system = 'dendy'
	elif game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
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

	return mame_driver(game, emulator_config, system, 'cart', options, has_keyboard=has_keyboard)

def mame_odyssey2(game, _, emulator_config):
	system = 'odyssey2'

	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'videopac'
	#system = 'videopacf' if region == France could also be a thing? Hmm

	return mame_driver(game, emulator_config, system, 'cart')

def mame_pc_engine(game, _, emulator_config):
	#TODO: Use system_config or software list to get PCE CD BIOS, then do that (same system, but -cdrom slot instead and -cart goes to System Card; TurboGrafx System Card only works with tg16 but other combinations are fine)
	system = 'tg16'
	#USA system can run Japanese games, so maybe we don't need to switch to pce if Japan in regions; but USA games do need tg16 specifically
	if game.rom.extension == 'sgx':
		#It might be better to detect this differently like if software is in sgx.xml software list, or set Is-Supergrafx field that way in roms_metadata platform_helpers
		system = 'sgx'

	return mame_driver(game, emulator_config, system, 'cart')

def mame_pico(game, _, emulator_config):
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
		if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
			system = 'pico'
	return mame_driver(game, emulator_config, system, 'cart')

def mame_saturn(game, _, emulator_config):
	#Default to USA
	system = 'saturn'
	region_codes = game.metadata.specific_info.get('Region-Code')
	if region_codes:
		#Clones here are hisaturn and vsaturn, not sure how useful those would be
		if SaturnRegionCodes.USA in region_codes:
			system = 'saturn'
		elif SaturnRegionCodes.Japan in region_codes:
			system = 'saturnjp'
		elif SaturnRegionCodes.Europe in region_codes:
			system = 'saturneu'

	#TODO: Use ctrl1 and ctrl2 to set controllers (analog, joy_md3, joy_md6, joypad, keyboard, mouse, racing, segatap (???), trackball)
	#Dunno if the cart slot can be used for anything useful yet
	return mame_driver(game, emulator_config, system, 'cdrom')

def mame_sord_m5(game, _, emulator_config):
	system = 'm5'
	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'm5p'
		#Not sure what m5p_brno is about (two floppy drives?)

	#ramsize can be set to 64K pre-0.227
	return mame_driver(game, emulator_config, system, 'cart1', has_keyboard=True)

def mame_sg1000(game, _, emulator_config):
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

	return mame_driver(game, emulator_config, system, slot, slot_options, has_keyboard)

def mame_sharp_x68000(game, _, emulator_config):
	if game.subroms:
		#This won't work if the referenced m3u files have weird compression formats supported by 7z but not by MAME; but maybe that's your own fault
		floppy_slots = {}
		for i, individual_floppy in enumerate(game.subroms):
			floppy_slots['flop%d' % (i + 1)] = individual_floppy.path

		return mame_driver(game, emulator_config, 'x68000', slot=None, slot_options=floppy_slots, has_keyboard=True)
	return mame_driver(game, emulator_config, 'x68000', 'flop1', has_keyboard=True)

def mame_snes(game, system_config, emulator_config):
	if game.rom.extension == 'st':
		if not hasattr(mame_snes, 'have_sufami_software'):
			mame_snes.have_sufami_software = _is_software_available('snes', 'sufami')

		if mame_snes.have_sufami_software:
			return mame_driver(game, emulator_config, 'snes', 'cart2', {'cart': 'sufami'})

		bios_path = system_config.get('sufami_turbo_bios_path', None)
		if not bios_path:
			raise EmulationNotSupportedException('Sufami Turbo BIOS not set up, check systems.ini')

		#We don't need to detect TV type because the Sufami Turbo (and also BS-X) was only released in Japan and so the Super Famicom can be used for everything
		return mame_driver(game, emulator_config, 'snes', 'cart2', {'cart': bios_path})

	if game.rom.extension == 'bs':
		if not hasattr(mame_snes, 'have_bsx_software'):
			mame_snes.have_bsx_software = _is_software_available('snes', 'bsxsore')

		if mame_snes.have_bsx_software:
			return mame_driver(game, emulator_config, 'snes', 'cart2', {'cart': 'bsxsore'})

		bios_path = system_config.get('bsx_bios_path', None)
		if not bios_path:
			raise EmulationNotSupportedException('BS-X/Satellaview BIOS not set up, check systems.ini')
		return mame_driver(game, emulator_config, 'snes', 'cart2', {'cart': bios_path})

	expansion_chip = game.metadata.specific_info.get('Expansion-Chip')
	if expansion_chip == SNESExpansionChip.ST018:
		raise EmulationNotSupportedException('{0} not supported'.format(expansion_chip))

	slot = game.metadata.specific_info.get('Slot')
	if slot:
		#These bootleg copy protection methods might work from software list, but from fullpath the carts aren't detected as using it, so they black screen
		if slot.endswith(('_poke', '_sbld', '_tekken2', '_20col')):
			raise EmulationNotSupportedException('{0} mapper not supported'.format(slot))

	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'snespal'
	else:
		#American SNES and Super Famicom are considered to be the same system, so that works out nicely
		system = 'snes'

	#TODO Set ctrl1/ctrl2: barcode_battler, joypad, miracle_piano, mouse, pachinko, sscope (also multitap, twintap which we don't need or maybe we do)

	return mame_driver(game, emulator_config, system, 'cart')

def mame_super_cassette_vision(game, _, emulator_config):
	if game.metadata.specific_info.get('Has-Extra-RAM', False):
		raise EmulationNotSupportedException('RAM on cartridge not supported except from software list (game would malfunction)')

	system = 'scv'
	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'scv_pal'

	return mame_driver(game, emulator_config, system, 'cart')

def mame_vic_20(game, _, emulator_config):
	size = game.rom.get_size()
	if size > ((8 * 1024) + 2):
		#It too damn big (only likes 8KB with 2 byte header at most)
		raise EmulationNotSupportedException('Single-part >8K cart not supported: %d' % size)

	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		system = 'vic20p'
	else:
		system = 'vic20'

	return mame_driver(game, emulator_config, system, 'cart', {'iec8': ''}, has_keyboard=True)

def mame_zx_spectrum(game, _, emulator_config):
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
		if game.rom.get_size() != 0x4000:
			raise EmulationNotSupportedException('Whoops 16KB only thank you')
		slot = 'cart'
		options['exp'] = 'intf2'
	elif game.metadata.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		#Should not happen
		raise NotARomException('Media type ' + game.metadata.media_type + ' unsupported')

	return mame_driver(game, emulator_config, system, slot, options, has_keyboard=True)

#Mednafen modules
def mednafen_apple_ii(game, _, emulator_config):
	machines = game.metadata.specific_info.get('Machine')
	if machines:
		if AppleIIHardware.AppleII not in machines and AppleIIHardware.AppleIIPlus not in machines:
			raise EmulationNotSupportedException('Only Apple II and II+ are supported, this needs ' + machines)

	required_ram = game.metadata.specific_info.get('Minimum-RAM')
	if required_ram and required_ram > 64:
		raise EmulationNotSupportedException('Needs at least {0} KB RAM'.format(required_ram))

	return mednafen_module('apple2', exe_path=emulator_config.exe_path)

def mednafen_game_gear(game, _, emulator_config):
	mapper = game.metadata.specific_info.get('Mapper')
	if mapper in ('Codemasters', 'EEPROM'):
		raise EmulationNotSupportedException('{0} mapper not supported'.format(mapper))
	return mednafen_module('gg', exe_path=emulator_config.exe_path)

def mednafen_gb(game, _, emulator_config):
	_verify_supported_gb_mappers(game, ['MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC7', 'HuC1', 'HuC3'], [])
	return mednafen_module('gb', exe_path=emulator_config.exe_path)

def mednafen_gba(game, _, emulator_config):
	if game.rom.get_size() > (32 * 1024 * 1024):
		raise EmulationNotSupportedException('64MB GBA Video carts not supported')
	return mednafen_module('gba', exe_path=emulator_config.exe_path)

def mednafen_lynx(game, _, emulator_config):
	if game.metadata.media_type == MediaType.Cartridge and not game.metadata.specific_info.get('Headered', False):
		raise EmulationNotSupportedException('Needs to have .lnx header')

	return mednafen_module('lynx', exe_path=emulator_config.exe_path)

def mednafen_megadrive(game, _, emulator_config):
	if game.metadata.specific_info.get('Expansion-Chip', None) == 'SVP':
		raise EmulationNotSupportedException('SVP chip not supported')

	mapper = game.metadata.specific_info.get('Mapper')
	unsupported_mappers = ('mcpir', 'sf002', 'mjlov', 'lion3', 'kof99_pokemon', 'squir', 'sf004', 'topf', 'smw64', 'lion2', 'stm95', 'cjmjclub', 'pokestad', 'soulb', 'smb', 'smb2', 'chinf3')
	#Squirrel King does boot but you die instantly, that's interesting
	#Soul Blade freezes soon after starting a match?
	if mapper in unsupported_mappers:
		raise EmulationNotSupportedException(mapper + ' not supported')

	return mednafen_module('md', exe_path=emulator_config.exe_path)

def mednafen_nes(game, _, emulator_config):
	#Mapper 30, 38 aren't in the documentation but they do exist in the source code
	unsupported_ines_mappers = (14, 20, 27, 28, 29, 31, 35, 36, 39, 43, 50,
		53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 81, 83, 84, 91, 98, 100,
		102, 103, 104, 106, 108, 109, 110, 111, 116, 136, 137, 138, 139, 141,
		142, 143, 181, 183, 186, 187, 188, 191, 192, 211, 212, 213, 214, 216,
		218, 219, 220, 221, 223, 224, 225, 226, 227, 229, 230, 231, 233, 235,
		236, 237, 238, 239, 243, 245)
	unsupported_ines_mappers += tuple(range(120, 133))
	unsupported_ines_mappers += tuple(range(145, 150))
	unsupported_ines_mappers += tuple(range(161, 180))
	unsupported_ines_mappers += tuple(range(194, 206))
	supported_unif_mappers = ('BTR', 'PNROM', 'PEEOROM', 'TC-U01-1.5M', 'Sachen-8259B', 'Sachen-8259A', 'Sachen-74LS374N', 'SA-016-1M', 'SA-72007', 'SA-72008', 'SA-0036', 'SA-0037', 'H2288', '8237', 'MB-91', 'NINA-06', 'NINA-03', 'NINA-001', 'HKROM', 'EWROM', 'EKROM', 'ELROM', 'ETROM', 'SAROM', 'SBROM', 'SCROM', 'SEROM', 'SGROM', 'SKROM', 'SLROM', 'SL1ROM', 'SNROM', 'SOROM', 'TGROM', 'TR1ROM', 'TEROM', 'TFROM', 'TLROM', 'TKROM', 'TSROM', 'TLSROM', 'TKSROM', 'TQROM', 'TVROM', 'AOROM', 'CPROM', 'CNROM', 'GNROM', 'NROM', 'RROM', 'RROM-128', 'NROM-128', 'NROM-256', 'MHROM', 'UNROM', 'MARIO1-MALEE2', 'Supervision16in1', 'NovelDiamond9999999in1', 'Super24in1SC03', 'BioMiracleA', '603-5052')

	if game.metadata.specific_info.get('Header-Format', None) in ('iNES', 'NES 2.0'):
		mapper = game.metadata.specific_info['Mapper-Number']
		if mapper in unsupported_ines_mappers or mapper >= 256:
			#Does not actually seem to check for NES 2.0 header extensions at all, according to source
			raise EmulationNotSupportedException('Unsupported mapper: {0} ({1})'.format(mapper, game.metadata.specific_info.get('Mapper')))
	if game.metadata.specific_info.get('Header-Format', None) == 'UNIF':
		mapper = game.metadata.specific_info.get('Mapper')
		if mapper not in supported_unif_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: {0}'.format(mapper))

	return mednafen_module('nes', exe_path=emulator_config.exe_path)

def mednafen_snes_faust(game, _, emulator_config):
	#Also does not support any other input except normal controller and multitap
	expansion_chip = game.metadata.specific_info.get('Expansion-Chip')
	if expansion_chip:
		if expansion_chip not in (SNESExpansionChip.CX4, SNESExpansionChip.SA_1, SNESExpansionChip.DSP_1, SNESExpansionChip.SuperFX, SNESExpansionChip.SuperFX2, SNESExpansionChip.DSP_2, SNESExpansionChip.S_DD1):
			raise EmulationNotSupportedException('{0} not supported'.format(expansion_chip))
	return mednafen_module('snes_faust', exe_path=emulator_config.exe_path)

#VICE
def vice_c64(game, _, emulator_config):
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
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		args += ['-model', 'ntsc']
	elif game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		args += ['-model', 'pal']
	args.append('$<path>')

	return LaunchParams(emulator_config.exe_path, args)

def vice_c128(game, _, emulator_config):
	args = ['-VDCfull']
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		args += ['-model', 'ntsc']
	elif game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		args += ['-model', 'pal']
	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

def vice_pet(game, _, emulator_config):
	args = ['-CRTCfull']
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		args += ['-ntsc']
	elif game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		args += ['-pal']
	
	machine = game.metadata.specific_info.get('Machine')
	#The "Machine" field is set directly to the model argument, so that makes things a lot easier for me. Good thing I decided to do that
	if machine:
		args += ['-model', machine]

	ram_size = game.metadata.specific_info.get('Minimum-RAM')
	if ram_size:
		args += ['-ramsize', str(ram_size)]

	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

def vice_plus4(game, _, emulator_config):
	args = ['-TEDfull']
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		args += ['-model', 'plus4ntsc']
	elif game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		args += ['-model', 'plus4pal']
	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

def vice_vic20(game, _, emulator_config):
	args = ['-VICfull']
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		args += ['-model', 'vic20ntsc']
	elif game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
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
	return LaunchParams(emulator_config.exe_path, args)

#Other emulators
def a7800(game, _, emulator_config):
	#Hmm, mostly the same as mame_a7800, except without the MAME
	if not game.metadata.specific_info.get('Headered', False):
		#This would only be supported via software list (although A7800 seems to have removed that anyway)
		raise EmulationNotSupportedException('No header')

	args = []
	if game.metadata.specific_info.get('TV-Type') == TVSystem.PAL:
		args.append('a7800p')
	else:
		args.append('a7800')
	#There are also a7800u1, a7800u2, a7800pu1, a7800pu2 to change the colour palettes. Maybe that could be an emulator_config option...

	if not hasattr(a7800, 'have_hiscore_software'):
		a7800.have_hiscore_software = is_highscore_cart_available()

	if a7800.have_hiscore_software and game.metadata.specific_info.get('Uses-Hiscore-Cart', False):
		args += ['-cart1', 'hiscore', '-cart2', '$<path>']
	else:
		args += ['-cart', '$<path>']

	return LaunchParams(emulator_config.exe_path, args)

def bsnes(game, system_config, emulator_config):
	if game.system_name == 'Game Boy':
		sgb_bios_path = system_config.get('super_game_boy_bios_path', None)
		if not sgb_bios_path:
			raise EmulationNotSupportedException('Super Game Boy BIOS not set up, check systems.ini')
		colour_flag = game.metadata.specific_info.get('Is-Colour', GameBoyColourFlag.No)
		if colour_flag == GameBoyColourFlag.Required:
			raise EmulationNotSupportedException('Super Game Boy is not compatible with GBC-only games')
		if colour_flag == GameBoyColourFlag.Yes and emulator_config.options.get('sgb_incompatible_with_gbc', True):
			raise EmulationNotSupportedException('We do not want to play a colour game with a Super Game Boy')
		if emulator_config.options.get('sgb_enhanced_only', False) and not game.metadata.specific_info.get('SGB-Enhanced', False):
			raise EmulationNotSupportedException('We do not want to play a non-SGB enhanced game with a Super Game Boy')

		#Pocket Camera is also supported by the SameBoy core, but I'm leaving it out here because bsnes doesn't do the camera
		_verify_supported_gb_mappers(game, ['MBC1', 'MBC2', 'MBC3', 'MBC5', 'HuC1', 'HuC3'], [])

		return LaunchParams(emulator_config.exe_path, ['--fullscreen', sgb_bios_path, '$<path>'])

	if game.rom.extension == 'st':
		bios_path = system_config.get('sufami_turbo_bios_path', None)
		if not bios_path:
			raise EmulationNotSupportedException('Sufami Turbo BIOS not set up, check systems.ini')
		#We need two arguments (and the second argument has to exist), otherwise when you actually launch it you get asked for something to put in slot B and who says we ever wanted to put anything in slot B
		#Can also use /dev/null but that's not portable and even if I don't care about that, it just gives me bad vibes
		return LaunchParams(emulator_config.exe_path, ['--fullscreen', bios_path, '$<path>', '$<path>'])

	#Oh it can just launch Satellaview without any fancy options huh

	slot = game.metadata.specific_info.get('Slot')
	if slot:
		#There are a few bootleg things that will not work
		if slot.endswith(('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col')):
			raise EmulationNotSupportedException('{0} mapper not supported'.format(slot))
	
	return LaunchParams(emulator_config.exe_path, ['--fullscreen', '$<path>'])

def cemu(game, __, emulator_config):
	title_id = game.metadata.specific_info.get('Title-ID')
	if title_id:
		category = title_id[4:8]
		if category == '000C':
			raise NotARomException('Cannot boot DLC')
		if category == '000E':
			raise NotARomException('Cannot boot update')

	if game.rom.is_folder:
		path = game.rom.relevant_files['rpx']
	else:
		path = '$<path>'
	return LaunchParams(emulator_config.exe_path, ['-f', '-g', 'Z:{0}'.format(path)])

def citra(game, _, emulator_config):
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
	return LaunchParams(emulator_config.exe_path, ['$<path>'])

def cxnes(game, _, emulator_config):
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
	return LaunchParams(emulator_config.exe_path, ['-f', '$<path>'])

def dolphin(game, _, emulator_config):
	if game.metadata.specific_info.get('No-Disc-Magic', False):
		raise EmulationNotSupportedException('No disc magic')

	title_type = game.metadata.specific_info.get('Title-Type')
	if title_type:
		if title_type not in (WiiTitleType.Channel, WiiTitleType.GameWithChannel, WiiTitleType.SystemChannel, WiiTitleType.HiddenChannel):
			#Technically Wii Menu versions are WiiTitleType.System but can be booted, but eh
			raise NotARomException('Cannot boot a {0}'.format(title_type.name))

	if game.rom.is_folder:
		#Homebrew
		path = game.rom.relevant_files['boot.dol']
	else:
		path = '$<path>'
	return LaunchParams(emulator_config.exe_path, ['-b', '-e', path])

def duckstation(game, _, emulator_config):
	if emulator_config.options.get('consider_unknown_games_incompatible', False) and 'DuckStation-Compatibility' not in game.metadata.specific_info:
		raise EmulationNotSupportedException('Not in compatibility DB')
	threshold = emulator_config.options.get('compatibility_threshold')
	if threshold:
		game_compat = game.metadata.specific_info.get('DuckStation-Compatibility')
		if game_compat:
			if game_compat.value < threshold:
				raise EmulationNotSupportedException('Game is only {0} status'.format(game_compat.name))

	return LaunchParams(emulator_config.exe_path, ['-batch', '-fullscreen', '$<path>'])

def fs_uae(game, system_config, emulator_config):
	args = ['--fullscreen']
	if game.system_name == 'Amiga CD32':
		args.extend(['--amiga_model=CD32', '--joystick_port_0_mode=cd32 gamepad', '--cdrom_drive_0=$<path>'])
	elif game.system_name == 'Commodore CDTV':
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
			chipset = game.metadata.specific_info.get('Chipset', system_config.get('default_chipset', 'AGA'))
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
	if game.metadata.specific_info.get('TV-Type') == TVSystem.NTSC:
		args.append('--ntsc_mode=1')
	return LaunchParams(emulator_config.exe_path, args)

def gbe_plus(game, _, emulator_config):
	if game.system_name == 'Game Boy':
		#In theory, only this should support Pocket Sonar (so far), but there's not really a way to detect that since it just claims to be MBC1 in the header...
		_verify_supported_gb_mappers(game, ['MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC6', 'MBC7', 'Pocket Camera', 'HuC1'], ['MBC1 Multicart'])
	return LaunchParams(emulator_config.exe_path, ['$<path>'])

def medusa(game, _, emulator_config):
	if game.system_name == 'DSi':
		raise EmulationNotSupportedException('DSi exclusive games and DSiWare not supported')
	if game.metadata.specific_info.get('Is-iQue', False):
		raise EmulationNotSupportedException('iQue DS not supported')

	if game.system_name == 'Game Boy':
		verify_mgba_mapper(game)

	args = ['-f']
	if game.system_name != 'DS':
		#(for GB/GBA stuff only, otherwise BIOS is mandatory whether you like it or not)
		if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
			args.append('-C')
			args.append('useBios=0')

	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

def melonds(game, _, emulator_config):
	if game.system_name == 'DSi':
		raise EmulationNotSupportedException("DSi is too experimental so let's say for all intents and purposes it doesn't work")
	if game.metadata.specific_info.get('Is-iQue', False):
		#Maybe it is if you use an iQue firmware?
		raise EmulationNotSupportedException('iQue DS not supported')

	#No argument for fullscreen here yet
	#It looks like you can pass a GBA cart via the second argument, so that might get interesting

	return LaunchParams(emulator_config.exe_path, ['$<path>'])

def mgba(game, _, emulator_config):
	if game.system_name == 'Game Boy':
		verify_mgba_mapper(game)

	args = ['-f']
	if not game.metadata.specific_info.get('Nintendo-Logo-Valid', True):
		args.append('-C')
		args.append('useBios=0')
	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

def mupen64plus(game, system_config, emulator_config):
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
		plugin = controller_pak if system_config.get('prefer_controller_pak_over_rumble', False) else rumble_pak
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
	return LaunchParams(emulator_config.exe_path, args)

def pokemini(_, __, emulator_config):
	return MultiCommandLaunchParams(
		[LaunchParams('mkdir', ['-p', os.path.expanduser('~/.config/PokeMini')]), 
		LaunchParams('cd', [os.path.expanduser('~/.config/PokeMini')])], 
		LaunchParams(emulator_config.exe_path, ['-fullscreen', '$<path>']),
		[]
	)

def ppsspp(game, _, emulator_config):
	if game.metadata.specific_info.get('PlayStation-Category') == 'UMD Video':
		raise EmulationNotSupportedException('UMD video discs not supported')
	return LaunchParams(emulator_config.exe_path, ['$<path>'])

def reicast(game, _, emulator_config):
	if game.metadata.specific_info.get('Uses-Windows-CE', False):
		raise EmulationNotSupportedException('Windows CE-based games not supported')
	args = ['-config', 'x11:fullscreen=1']
	if not game.metadata.specific_info.get('Supports-VGA', True):
		#Use RGB component instead (I think that should be compatible with everything, and would be better quality than composite, which should be 1)
		args += ['-config', 'config:Dreamcast.Cable=2']
	else:
		#This shouldn't be needed, as -config is supposed to be temporary, but it isn't and writes the component cable setting back to the config file, so we'll set it back
		args += ['-config', 'config:Dreamcast.Cable=0']
	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

def rpcs3(game, _, emulator_config):
	if game.metadata.specific_info.get('Should-Not-Be-Bootable', False):
		raise NotARomException('Cannot boot', game.metadata.specific_info.get('PlayStation-Category', 'this'))
	if emulator_config.options.get('require_compat_entry', False) and 'RPCS3-Compatibility' not in game.metadata.specific_info:
		raise EmulationNotSupportedException('Not in compatibility DB')
	threshold = emulator_config.options.get('compat_threshold')
	if threshold:
		game_compat = game.metadata.specific_info.get('RPCS3-Compatibility')
		if game_compat:
			if game_compat.value < threshold:
				raise EmulationNotSupportedException('Game ({0}) is only {1} status'.format(game.metadata.names.get('Banner-Title'), game_compat.name))

	#It's clever enough to boot folders specified as a path
	return LaunchParams(emulator_config.exe_path, ['--no-gui', '$<path>'])

def snes9x(game, _, emulator_config):
	slot = game.metadata.specific_info.get('Slot')
	if slot:
		#There are a few bootleg things that will not work
		if slot.endswith(('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col')):
			raise EmulationNotSupportedException('{0} mapper not supported'.format(slot))

	expansion_chip = game.metadata.specific_info.get('Expansion-Chip')
	if expansion_chip in (SNESExpansionChip.ST018, SNESExpansionChip.DSP_3):
		#ST018 is implemented enough here to boot to menu, but hangs when starting a match
		#DSP-3 looks like it's going to work and then when I played around a bit and the AI was starting its turn (I think?) the game hung to a glitchy mess so I guess not
		raise EmulationNotSupportedException('{0} not supported'.format(expansion_chip))
	return LaunchParams(emulator_config.exe_path, ['$<path>'])

def xemu(game, __, emulator_config):
	#Values yoinked from extract-xiso, I hope they don't mind
	global_lseek_offset = 0xfd90000
	xgd3_lseek_offset = 0x2080000
	xiso_header_offset = 0x10000
	xiso_string = b'MICROSOFT*XBOX*MEDIA'

	#Checking for this stuff inside the emulator-command-line-maker seems odd, but it doesn't make sense to make a metadata helper for it either
	size = game.rom.get_size()
	good = False
	for possible_location in (xiso_header_offset, global_lseek_offset + xiso_header_offset, xgd3_lseek_offset + xiso_header_offset):
		if size < possible_location:
			continue
		magic = game.rom.read(seek_to=possible_location, amount=20)
		if magic == xiso_string:
			good = True
			break
	if not good:
		raise EmulationNotSupportedException('Probably a Redump-style dump, you need to extract the game partition')
	#This still doesn't guarantee it'll be seen as a valid disc…

	return LaunchParams(emulator_config.exe_path, ['-full-screen', '-dvd_path', '$<path>'])

def yuzu(game, __, emulator_config):
	title_type = game.metadata.specific_info.get('Title-Type')
	if title_type in ('Patch', 'AddOnContent', SwitchContentMetaType.Patch, SwitchContentMetaType.AddOnContent):
		#If we used the .cnmt.xml, it will just be a string
		raise NotARomException('Cannot boot a {0}'.format(title_type))
	return LaunchParams(emulator_config.exe_path, ['-f', '-g', '$<path>'])

#Game engines
def prboom_plus(game, system_config, emulator_config):
	if game.metadata.specific_info.get('Is-PWAD', False):
		raise NotARomException('Is PWAD and not IWAD')

	args = []
	save_dir = system_config.get('save_dir')
	if save_dir:
		args.append('-save')
		args.append(save_dir)

	args.append('-iwad')
	args.append('$<path>')
	return LaunchParams(emulator_config.exe_path, args)

#DOS/Mac stuff
def _macemu_args(app, autoboot_txt_path, emulator_config):
	args = []
	if not app.is_on_cd:
		args += ['--disk', app.hfv_path]
	if 'max_resolution' in app.info:
		width, height = app.info['max_resolution']
		args += ['--screen', 'dga/{0}/{1}'.format(width, height)]
	
	if app.cd_path:
		args += ['--cdrom', app.cd_path]
	for other_cd_path in app.other_cd_paths:
		args += ['--cdrom', other_cd_path]

	app_path = app.metadata.specific_info.get('Carbon-Path', app.path)
	pre_commands = [
		LaunchParams('sh', ['-c', 'echo {0} > {1}'.format(shlex.quote(app_path), shlex.quote(autoboot_txt_path))]), #Hack because I can't be fucked refactoring MultiCommandLaunchParams to do pipey bois/redirecty bois
		#TODO: Actually could we just have a WriteAFileLaunchParams or something
	]
	if 'max_bit_depth' in app.info:
		#--displaycolordepth doesn't work or doesn't do what I think it does, so we are setting depth from inside the thing instead
		#This requires some AppleScript extension known as GTQ Programming Suite until I one day figure out a better way to do this
		pre_commands += [
			LaunchParams('sh', ['-c', 'echo {0} >> {1}'.format(app.info['max_bit_depth'], shlex.quote(autoboot_txt_path))])
		]
	return MultiCommandLaunchParams(pre_commands, LaunchParams(emulator_config.exe_path, args), [LaunchParams('rm', [autoboot_txt_path])])

def basilisk_ii(app, _, emulator_config):
	if app.metadata.specific_info.get('Architecture') == 'PPC':
		raise EmulationNotSupportedException('PPC not supported')
	if app.info.get('ppc_enhanced', False) and emulator_config.options.get('skip_if_ppc_enhanced', False):
		raise EmulationNotSupportedException('PPC enhanced')

	#This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	#Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	shared_folder = None
	try:
		with open(os.path.expanduser('~/.basilisk_ii_prefs'), 'rt') as f:
			for line in f.readlines():
				if line.startswith('extfs '):
					shared_folder = line[6:-1]
					break
	except FileNotFoundError:
		pass
	if not shared_folder:
		raise EmulationNotSupportedException('You need to set up your shared folder first')

	autoboot_txt_path = os.path.join(shared_folder, 'autoboot.txt')
	return _macemu_args(app, autoboot_txt_path, emulator_config)

def sheepshaver(app, _, emulator_config):
	#This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	#Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	shared_folder = None
	try:
		with open(os.path.expanduser('~/.sheepshaver_prefs'), 'rt') as f:
			for line in f.readlines():
				if line.startswith('extfs '):
					shared_folder = line[6:-1]
					break
	except FileNotFoundError:
		pass
	if not shared_folder:
		raise EmulationNotSupportedException('You need to set up your shared folder first')

	autoboot_txt_path = os.path.join(shared_folder, 'autoboot.txt')

	return _macemu_args(app, autoboot_txt_path, emulator_config)
	
mount_line_regex = re.compile(r'^MOUNT ([A-Z]) ')
def _last_unused_dosbox_drive(dosbox_config_path, used_letters=None):
	automounted_letters = []
	with open(dosbox_config_path, 'rt') as f:
		found_autoexec = False
		for line in f.readlines():
			line = line.rstrip()
			if line == '[autoexec]':
				found_autoexec = True
				continue
			if found_autoexec:
				mount_line_match = mount_line_regex.match(line)
				if mount_line_match:
					automounted_letters.append(mount_line_match[1])
	
	for letter in 'CDEFGHIJKLMNOPQRSTVWXY':
		if used_letters:
			if letter in used_letters:
				continue
		if letter not in automounted_letters:
			return letter
	raise EmulationNotSupportedException('Oh no you are automounting too many drives and we have no room for another one')

def dosbox_staging(app, _, emulator_config):
	args = ['-fullscreen', '-exit']
	noautoexec = emulator_config.options['noautoexec']
	if noautoexec:
		args.append('-noautoexec')
	

	if 'required_hardware' in app.info:
		if 'for_xt' in app.info['required_hardware']:
			if app.info['required_hardware']['for_xt']:
				#machine=cga?
				cycles_for_about_477 = emulator_config.options['cycles_for_477_mhz']
				args += ['-c', 'config -set "cpu cycles {0}"'.format(cycles_for_about_477)]

		if 'max_graphics' in app.info['required_hardware']:
			graphics = app.info['required_hardware']['max_graphics']
			machine = 'svga_s3' if graphics == 'svga' else graphics
			args += ['-machine', machine]
	
	drive_letter = 'C'
	cd_drive_letter = 'D'
	
	if not noautoexec:
		config_file_location = os.path.expanduser('~/.config/dosbox/dosbox-staging.conf')
		print(config_file_location)
		try:
			drive_letter = _last_unused_dosbox_drive(config_file_location)
			cd_drive_letter = _last_unused_dosbox_drive(config_file_location, [drive_letter])
		except OSError:
			pass
		
	if app.cd_path:
		#I hope you don't put double quotes in the CD paths
		imgmount_args = '"{0}"'.format(app.cd_path)
		if app.other_cd_paths:
			imgmount_args += ' '  + ' '.join('"{0}"'.format(cd_path) for cd_path in app.other_cd_paths)
		args += ['-c', 'IMGMOUNT {0} -t cdrom {1}'.format(cd_drive_letter, imgmount_args)]
	
	if app.is_on_cd:
		args += ['-c', cd_drive_letter + ':', '-c', app.path, '-c', 'exit']
	else:
		if drive_letter == 'C':
			args.append(app.path)
		else:
			#Gets tricky if autoexec already mounts a C drive because launching something from the command line normally that way just assumes C is a fine drive to use
			#This also makes exit not work normally
			host_folder, exe_name = os.path.split(app.path)
			args += ['-c', 'MOUNT {0} "{1}"'.format(drive_letter, host_folder), '-c', drive_letter + ':', '-c', exe_name, '-c', 'exit']

	return LaunchParams(emulator_config.exe_path, args)

def dosbox_x(app, _, emulator_config):
	confs = {}

	if app.is_on_cd:
		raise EmulationNotSupportedException('This might not work from CD I think unless it does')
	#TODO: Does this even support -c? I can't remember

	if 'required_hardware' in app.info:
		if 'for_xt' in app.info['required_hardware']:
			if app.info['required_hardware']['for_xt']:
				#confs['cputype'] = '8086'
				#This doesn't even work anyway, it's just the best we can do I guess
				confs['machine'] = 'cga'
				confs['cycles'] = 'fixed 315'

		if 'max_graphics' in app.info['required_hardware']:
			graphics = app.info['required_hardware']['max_graphics']
			confs['machine'] = 'svga_s3' if graphics == 'svga' else graphics

	args = ['-exit', '-noautoexec', '-fullscreen', '-fastlaunch']
	for k, v in confs.items():
		args.append('-set')
		args.append('{0}={1}'.format(k, v))

	return LaunchParams(emulator_config.exe_path, args + [app.path])

#Libretro frontends
def retroarch(_, __, emulator_config, frontend_config):
	if not emulator_config.exe_path:
		raise EmulationNotSupportedException('libretro core path is not explicitly specified and libretro_cores_directory is not set')
	return LaunchParams(frontend_config.exe_path, ['-f', '-L', emulator_config.exe_path, '$<path>'])
 
#Libretro cores
def genesis_plus_gx(game, _, __):
	if game.system_name == 'Mega CD':
		if game.metadata.specific_info.get('32X-Only', False):
			raise EmulationNotSupportedException('32X not supported')

def blastem(game, _, __):
	if game.system_name == 'Mega Drive':
		if game.metadata.specific_info.get('Expansion-Chip', None) == 'SVP':
			#This should work, but doesn't?
			raise EmulationNotSupportedException('Seems SVP chip not supported?')
		mapper = game.metadata.specific_info.get('Mapper')
		if mapper:
			#Some probably only work with rom.db being there, this assumes it is
			#Some bootleg mappers don't seem to have any indication that they should work but seem to
			if mapper not in ('EEPROM', 'J-Cart', 'J-Cart + EEPROM', 'ssf2', 'cslam', 'hardbl95', 'blara',
			'mcpir', 'realtec', 'sbubl', 'squir', 'elfwor', 'kof99', 'smouse', 'sk'):
				raise EmulationNotSupportedException(mapper)

def mesen(game, _, __):
	unsupported_mappers = [124, 237, 256, 257, 389]
	unsupported_mappers += [271, 295, 308, 315, 322, 327, 335, 337, 338, 339, 340, 341, 342, 344, 345, 350, 524, 525, 526, 527, 528] #if I am reading MapperFactory.cpp correctly these are explicitly unsupported?
	unsupported_mappers += [267, 269, 270, 272, 273] + list(range(275, 283)) + [291, 293, 294, 296, 297, 310, 311, 316, 318, 321, 330, 334, 343, 347] + list(range(351, 366)) + list(range(367, 513)) + [514, 515, 516, 517, 520, 523]
	#I guess 186 (StudyBox) might also count as unsupported but it's meant to be a BIOS
	#Also Mindkids 143-in-1 but I'm not sure what number that is/what the UNIF name is
	unsupported_unif_mappers = ['KONAMI-QTAI', ' BMC-10-24-C-A1', 'BMC-13in1JY110', 'BMC-81-01-31-C', 
		'UNL-KS7010', 'UNL-KS7030', 'UNL-OneBus', 'UNL-PEC-586', 'UNL-SB-2000', 'UNL-Transformer', 'WAIXING-FS005']
	if game.metadata.specific_info.get('Header-Format', None) in ('iNES', 'NES 2.0'):
		mapper = game.metadata.specific_info.get('Mapper-Number')
		if mapper in unsupported_mappers or mapper > 530:
			raise EmulationNotSupportedException('Unsupported mapper: {0} {1}'.format(mapper, game.metadata.specific_info.get('Mapper')))
	if game.metadata.specific_info.get('Header-Format', None) == 'UNIF':
		mapper = game.metadata.specific_info.get('Mapper')
		if mapper in unsupported_unif_mappers:
			raise EmulationNotSupportedException('Unsupported mapper: {0}'.format(mapper))
	
def prosystem(game, _, __):
	if not game.metadata.specific_info.get('Headered', False):
		#Seems to support unheadered if and only if in the internal database? Assume it isn't otherwise that gets weird
		raise EmulationNotSupportedException('No header')

def bsnes_libretro(game, _, emulator_config):
	if game.system_name == 'Game Boy':
		colour_flag = game.metadata.specific_info.get('Is-Colour', GameBoyColourFlag.No)
		if colour_flag == GameBoyColourFlag.Required:
			raise EmulationNotSupportedException('Super Game Boy is not compatible with GBC-only games')
		if colour_flag == GameBoyColourFlag.Yes and emulator_config.options.get('sgb_incompatible_with_gbc', True):
			raise EmulationNotSupportedException('We do not want to play a colour game with a Super Game Boy')
		if emulator_config.options.get('sgb_enhanced_only', False) and not game.metadata.specific_info.get('SGB-Enhanced', False):
			raise EmulationNotSupportedException('We do not want to play a non-SGB enhanced game with a Super Game Boy')

		#Pocket Camera is also supported by the SameBoy core, but I'm leaving it out here because bsnes doesn't do the camera
		_verify_supported_gb_mappers(game, ['MBC1', 'MBC2', 'MBC3', 'MBC5', 'HuC1', 'HuC3'], [])
		return

	if game.rom.extension == 'st':
		raise EmulationNotSupportedException('No Sufami Turbo for libretro core')
		
	slot = game.metadata.specific_info.get('Slot')
	if slot:
		#Presume this is the same as with standalone
		if slot.endswith(('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col')):
			raise EmulationNotSupportedException('{0} mapper not supported'.format(slot))
