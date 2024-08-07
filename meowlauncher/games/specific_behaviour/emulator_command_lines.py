import logging
import os
import re
import shlex
from collections.abc import Collection, Mapping
from functools import cache
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, cast

from meowlauncher.common_types import ByteAmount, MediaType
from meowlauncher.data.emulated_platforms import (
	arabic_msx1_drivers,
	arabic_msx2_drivers,
	japanese_msx1_drivers,
	japanese_msx2_drivers,
	working_msx1_drivers,
	working_msx2_drivers,
	working_msx2plus_drivers,
)
from meowlauncher.exceptions import EmulationNotSupportedError, NotActuallyLaunchableGameError
from meowlauncher.games.common.emulator_command_line_helpers import (
	_is_software_available,
	first_available_romset,
	is_highscore_cart_available,
	mame_driver_base,
	mednafen_module_launch,
	verify_mgba_mapper,
	verify_supported_gb_mappers,
)
from meowlauncher.games.roms.rom import FileROM, FolderROM, M3UPlaylist
from meowlauncher.launch_command import LaunchCommand, MultiLaunchCommands, rom_path_argument
from meowlauncher.platform_types import (
	AppleIIHardware,
	Atari2600Controller,
	GameBoyColourFlag,
	MegadriveRegionCodes,
	NESPeripheral,
	SaturnDreamcastRegionCodes,
	SMSPeripheral,
	SNESExpansionChip,
	SwitchContentMetaType,
	WiiTitleType,
	ZXJoystick,
	ZXMachine,
)
from meowlauncher.util.region_info import TVSystem

if TYPE_CHECKING:
	from meowlauncher.config_types import TypeOfConfigValue
	from meowlauncher.data.emulators import BsnesLibretro, DOSBoxStaging
	from meowlauncher.emulator import Emulator, LibretroCore, StandardEmulator
	from meowlauncher.emulator_helpers import BaseMAMEDriver
	from meowlauncher.games.dos import DOSApp
	from meowlauncher.games.mac import MacApp
	from meowlauncher.games.mame.mame_game import ArcadeGame
	from meowlauncher.games.roms.rom_game import ROMGame

	PlatformConfigOptions = Mapping[str, TypeOfConfigValue]

logger = logging.getLogger(__name__)


# MAME drivers
def mame_32x(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	region_codes = game.info.specific_info.get('Region Code')
	if region_codes:
		if (
			MegadriveRegionCodes.USA in region_codes
			or MegadriveRegionCodes.World in region_codes
			or MegadriveRegionCodes.BrazilUSA in region_codes
			or MegadriveRegionCodes.JapanUSA in region_codes
			or MegadriveRegionCodes.USAEurope in region_codes
		):
			system = '32x'
		elif (
			MegadriveRegionCodes.Japan in region_codes
			or MegadriveRegionCodes.Japan1 in region_codes
		):
			system = '32xj'
		elif (
			MegadriveRegionCodes.Europe in region_codes
			or MegadriveRegionCodes.EuropeA in region_codes
			or MegadriveRegionCodes.Europe8 in region_codes
		):
			system = '32xe'
		else:
			system = '32x'
	else:
		system = '32x'
		if game.info.specific_info.get('TV Type') == TVSystem.PAL:
			system = '32xe'
	return mame_driver_base(game, emulator, system, 'cart')


def mame_amiga_cd32(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'cd32'
	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		# PAL is more likely if it is unknown
		system = 'cd32n'
	return mame_driver_base(game, emulator, system, 'cdrom')


def mame_amstrad_pcw_check(game: 'ROMGame', _):
	if game.info.specific_info.get('Requires CP/M?'):
		# Nah too messy
		raise EmulationNotSupportedError(
			"Needs CP/M and apparently I don't feel like fiddling around with that or something"
		)


def mame_apple_ii(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	slot_options = {'gameio': 'joy'}
	if game.info.specific_info.get('Uses Mouse?', False):
		slot_options['sl4'] = 'mouse'
	system = 'apple2e'  # Probably a safe default
	compatible_machines = game.info.specific_info.get('Machine')
	if compatible_machines:
		if AppleIIHardware.AppleIIE in compatible_machines:
			system = 'apple2e'
		elif AppleIIHardware.AppleIIC in compatible_machines:
			system = 'apple2c'
		elif AppleIIHardware.AppleIICPlus in compatible_machines:
			system = 'apple2cp'
		elif AppleIIHardware.AppleIIEEnhanced in compatible_machines:
			system = 'apple2ee'  # Should this go first if it's supported? Not sure what it does
		elif AppleIIHardware.AppleIIC in compatible_machines:
			system = 'apple2c'
		elif AppleIIHardware.AppleIIPlus in compatible_machines:
			system = 'apple2p'
		else:
			# Not using Apple III / Apple III+ here, or Apple IIgs; or base model Apple II since that doesn't autoboot and bugger that
			raise EmulationNotSupportedError("We don't use" + str(compatible_machines))

	return mame_driver_base(game, emulator, system, 'flop1', slot_options, has_keyboard=True)


def mame_atari_2600_check(game: 'ROMGame', emulator: 'BaseMAMEDriver'):
	rom = cast(FileROM, game.rom)
	size = rom.size
	# https://github.com/mamedev/mame/blob/master/src/devices/bus/vcs/vcs_slot.cpp#L188
	if size not in {
		0x800,
		0x1000,
		0x2000,
		0x28FF,
		0x2900,
		0x3000,
		0x4000,
		0x8000,
		0x10000,
		0x80000,
	}:
		raise EmulationNotSupportedError(f'ROM size not supported: {size}')

	if game.info.specific_info.get('Uses Supercharger', False):
		# MAME does support Supercharger tapes with scharger software list and -cass, but it requires playing the tape, so we pretend it doesn't in accordance with me not liking to press the play tape button; and this is making me think I want some kind of manual_tape_load_okay option that enables this and other MAME drivers but anyway that's another story
		raise EmulationNotSupportedError('Requires Supercharger')


def mame_atari_2600(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	left = game.info.specific_info.get('Left Peripheral')
	right = game.info.specific_info.get('Right Peripheral')

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

	system = 'a2600p' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'a2600'

	return mame_driver_base(game, emulator, system, 'cart', slot_options=options)


def mame_atari_jaguar(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.info.media_type == MediaType.Cartridge:
		slot = 'cart'
	elif game.info.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		# Should not happen
		raise AssertionError(f'Media type {game.info.media_type} unsupported')
	return mame_driver_base(game, emulator, 'jaguar', slot)


def mame_atari_7800_check(game: 'ROMGame', emulator: 'BaseMAMEDriver'):
	if not game.info.specific_info.get('Headered?', False):
		# This would only be supported via software list
		raise EmulationNotSupportedError('No header')


def mame_atari_7800(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'a7800p' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'a7800'

	if is_highscore_cart_available() and game.info.specific_info.get('Uses Hiscore Cart', False):  # type: ignore[attr-defined]
		return mame_driver_base(game, emulator, system, 'cart2', {'cart1': 'hiscore'})

	return mame_driver_base(game, emulator, system, 'cart')


def mame_atari_8bit(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	slot_options = {}
	system = None
	if game.info.media_type == MediaType.Cartridge:
		if game.info.specific_info.get('Headered?', False):
			cart_type = game.info.specific_info['Mapper']
			if cart_type in {13, 14, 23, 24, 25} or (33 <= cart_type <= 38):
				raise EmulationNotSupportedError(f'XEGS cart: {cart_type}')

			# You probably think this is a bad way to do this...  I guess it is, but hopefully I can take some out as they become supported
			if (
				cart_type in {5, 17, 22, 41, 42, 43, 45, 46, 47, 48, 49, 53, 57, 58, 59, 60, 61}
				or (26 <= cart_type <= 32)
				or (54 <= cart_type <= 56)
			):
				raise EmulationNotSupportedError(f'Unsupported cart type: {cart_type}')

			if cart_type in {4, 6, 7, 16, 19, 20}:
				# raise EmulationNotSupportedException(f'Atari 5200 cart (will probably work if put in the right place): {cart_type}')
				logger.debug(
					'%s is using MAME Atari 8-bit, but using Atari 5200 cart type %d',
					game,
					cart_type,
				)
				system = 'a5200'
		else:
			rom = cast(FileROM, game.rom)
			size = rom.size
			# 8KB files are treated as type 1, 16KB as type 2, everything else is unsupported for now
			if size > ((16 * 1024) + 16):
				raise EmulationNotSupportedError(
					f'No header and size = {size}, cannot be recognized as a valid cart yet (treated as XL/XE)'
				)

		slot = 'cart1' if game.info.specific_info.get('Slot', 'Left') == 'Left' else 'cart2'
	else:
		slot = 'flop1'
		if game.info.specific_info.get('Requires BASIC?', False):
			basic_path = cast(Path | None, game.platform_config.options.get('basic_path'))
			if not basic_path:
				raise EmulationNotSupportedError('This software needs BASIC ROM to function')
			slot_options['cart1'] = str(basic_path.resolve())

	machine = game.info.specific_info.get('Machine')
	if machine in {'XL', 'XL/XE'}:
		system = 'a800xlp' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'a800xl'
	elif machine == 'XE':
		# No PAL XE machine in MAME? (a800xe is what 65XE was marketed as in Germany/Czechoslovakia)
		# xegs is repackaged 65XE with removeable keyboard etc
		system = 'a65xe'
	elif machine == '130XE':
		# Note: Not working, but seems to be okay
		system = 'a130xe'

	if not system:
		# Sensible enough default, though XL/XE machines will still work to play ordinary non-XE carts
		system = 'a800pal' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'a800'

	return mame_driver_base(game, emulator, system, slot, slot_options, has_keyboard=True)


def mame_c64_check(game: 'ROMGame', _):
	# Explicitly listed as UNSUPPORTED in https://github.com/mamedev/mame/blob/master/src/lib/formats/cbm_crt.cpp
	unsupported_mappers = [
		1,
		2,
		6,
		9,
		20,
		29,
		30,
		33,
		34,
		35,
		36,
		37,
		38,
		40,
		42,
		45,
		46,
		47,
		50,
		52,
		54,
	]
	# Not listed as unsupported, but from anecdotal experience doesn't seem to work. Should try these again one day
	unsupported_mappers += [32]
	# 32 = EasyFlash. Well, at least it doesn't segfault. Just doesn't boot, even if I play with the dip switch that says "Boot". Maybe I'm missing something here?
	cart_type = game.info.specific_info.get('Mapper Number', None)
	cart_type_name = game.info.specific_info.get('Mapper', None)

	if cart_type in unsupported_mappers:
		raise EmulationNotSupportedError(f'{cart_type} ({cart_type_name}) cart not supported')


def mame_c64(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	"""By default, first joystick port does not contain a joystick, but second one does
	I guess we might as well use this Boostergrip joystick for 2 extra buttons, which is probably fine and maybe marginally useful
	"""
	system = 'c64'

	# Don't think we really need c64c unless we really want the different SID chip. Maybe that could be an emulator option?
	# Don't think we really need c64gs either

	if game.info.specific_info.get('TV Type') == TVSystem.PAL:
		system = 'c64p'

	return mame_driver_base(
		game,
		emulator,
		system,
		'cart',
		{'joy1': 'joybstr', 'joy2': 'joybstr', 'iec8': ''},
		has_keyboard=True,
	)


def mame_coleco_adam(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	slot_options = {}
	slot = None

	if game.info.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.info.media_type == MediaType.Tape:
		slot = 'cass1'
		# Disable floppy drives if we aren't using them for a performance boost (332.27% without vs 240.35% with here, and you'll probably be turboing through the tape load, so yeah)
		slot_options['net4'] = ''
		slot_options['net5'] = ''
	elif game.info.media_type == MediaType.Cartridge:
		slot = 'cart1'
	else:
		raise EmulationNotSupportedError(f'Media type {game.info.media_type} unsupported')

	return mame_driver_base(game, emulator, 'adam', slot, slot_options, has_keyboard=True)


def mame_colecovision(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'coleco'
	if game.info.specific_info.get('TV Type') == TVSystem.PAL:
		# This probably won't happen (officially, carts are supposed to support both NTSC and PAL), but who knows
		system = 'colecop'

	return mame_driver_base(game, emulator, system, 'cart')


def mame_dreamcast(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	"""MAME Dreamcast driver, selects correct one based on region code
	Maybe dctream (Treamcast) could be useful here as an option?
	dcdev doesn't run retail stuff
	:raises EmulationNotSupportedException: Windows CE games (I think that's still right?)"""
	if game.info.specific_info.get('Uses Windows CE?', False):
		raise EmulationNotSupportedError('Windows CE-based games not supported')

	region_codes = game.info.specific_info.get('Region Code')
	if region_codes and SaturnDreamcastRegionCodes.USA in region_codes:
		system = 'dc'
	elif region_codes and SaturnDreamcastRegionCodes.Japan in region_codes:
		system = 'dcjp'
	elif region_codes and SaturnDreamcastRegionCodes.Europe in region_codes:
		system = 'dceu'
	else:
		# Default to USA
		system = 'dc'

	# No interesting slot options...
	return mame_driver_base(game, emulator, system, 'cdrom')


def mame_fm_towns(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	"""Hmm… does this really need to be here along with fmtmarty when they are mostly identical"""
	if game.info.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.info.media_type == MediaType.OpticalDisc:
		slot = 'cdrom'
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	# Give us 10 meganbytes of RAM because we can (some software requires 4MB ram for example)
	# Hopefully nothing requires 2MB explicitly or less
	options = {'ramsize': '10M'}
	# Vanilla fmtowns seems to be a bit crashy? It is all MACHINE_NOT_WORKING anyway so nothing is expected
	return mame_driver_base(game, emulator, 'fmtownsux', slot, options)


def mame_fm_towns_marty(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.info.media_type == MediaType.Floppy:
		slot = 'flop1'
	elif game.info.media_type == MediaType.OpticalDisc:
		slot = 'cdrom'
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	# Give us 4 meganbytes of RAM just in case we need it (some do, see software list info=usage)
	# Hopefully nothing requires 2MB explicitly or less
	options = {'ramsize': '4M'}
	return mame_driver_base(game, emulator, 'fmtmarty', slot, options)


def mame_game_boy(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	# Do all of these actually work or are they just detected? (HuC1 and HuC3 are supposedly non-working, and are treated as MBC3?)
	# gb_slot.cpp also mentions MBC4, which isn't real
	supported_mappers = {
		'MBC1',
		'MBC2',
		'MBC3',
		'MBC5',
		'MBC6',
		'MBC7',
		'Pocket Camera',
		'Bandai TAMA5',
	}
	detected_mappers = {'MMM01', 'MBC1 Multicart', 'Wisdom Tree', 'Li Cheng', 'Sintax'}

	verify_supported_gb_mappers(game, supported_mappers, detected_mappers)

	# Not much reason to use gameboy, other than a green tinted screen. I guess that's the only difference
	system = 'gbcolor' if emulator.config.use_gbc_for_dmg else 'gbpocket'

	# Should be just as compatible as supergb but with better timing... I think
	super_gb_system = 'supergb2'

	is_colour = (
		game.info.specific_info.get('Is Colour?', GameBoyColourFlag.No) != GameBoyColourFlag.No
	)
	is_sgb = game.info.specific_info.get('SGB Enhanced?', False)

	prefer_sgb = emulator.config.prefer_sgb_over_gbc
	if is_colour and is_sgb:
		system = super_gb_system if prefer_sgb else 'gbcolor'
	elif is_colour:
		system = 'gbcolor'
	elif is_sgb:
		system = super_gb_system

	return mame_driver_base(game, emulator, system, 'cart')


def mame_game_gear(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'gamegear'
	if game.info.specific_info.get('Region Code') == 'Japanese':
		system = 'gamegeaj'
	return mame_driver_base(game, emulator, system, 'cart')


def mame_ibm_pcjr(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.info.media_type == MediaType.Cartridge:
		slot = 'cart1'
	elif game.info.media_type == MediaType.Floppy:
		# Floppy is the only other kind of rom we accept at this time
		slot = 'flop'
	else:
		raise EmulationNotSupportedError(f'Media type {game.info.media_type} unsupported')
	return mame_driver_base(game, emulator, 'ibmpcjr', slot, has_keyboard=True)


def mame_intellivision(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'intv'

	uses_keyboard = False
	if game.info.specific_info.get('Uses ECS?', False):
		# This has a keyboard and Intellivoice module attached; -ecs.ctrl_port synth gives a music synthesizer instead of keyboard
		# Seemingly none of the prototype keyboard games use intvkbd, they just use this
		system = 'intvecs'
		uses_keyboard = True
	elif game.info.specific_info.get('Uses Intellivoice?', False):
		system = 'intvoice'

	return mame_driver_base(game, emulator, system, 'cart', has_keyboard=uses_keyboard)


def mame_lynx(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if (
		game.info.media_type == MediaType.Cartridge
		and not game.rom.extension == 'lyx'
		and not game.info.specific_info.get('Headered?', False)
	):
		raise EmulationNotSupportedError('Needs to have .lnx header')

	slot = 'cart'

	if game.info.media_type == MediaType.Executable:
		slot = 'quik'

	return mame_driver_base(game, emulator, 'lynx', slot)


def mame_master_system(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	tv_type: TVSystem = TVSystem.PAL  # Seems a more sensible default at this point (there are also certain homebrews with less-than-detectable TV types that demand PAL)

	if game.info.specific_info.get('TV Type') in {TVSystem.NTSC, TVSystem.Agnostic}:
		tv_type = TVSystem.NTSC

	if game.info.specific_info.get('Japanese Only?', False):
		system = 'smsj'  # Still considered SMS1 for compatibility purposes. Seems to just be sg1000m3 but with built in FM, for all intents and purposes
		# "card" slot seems to not be used
	elif tv_type == TVSystem.PAL:
		system = 'sms1pal'
		if game.info.specific_info.get('SMS2 Only?', False):
			system = 'smspal'  # Master System 2 lacks expansion slots and card slot in case that ends up making a difference
	else:
		system = 'smsj'  # Used over sms1 for FM sound on worldwide releases
		if game.info.specific_info.get('SMS2 Only?', False):
			system = 'sms'
	# Not sure if Brazilian or Korean systems would end up being needed

	slot_options = {}
	peripheral = game.info.specific_info.get('Peripheral')
	# According to my own comments from earlier in master_system.py that I'm going to blindly believe, both controller ports are basically the same for this purpose
	controller = None
	if peripheral == SMSPeripheral.Lightgun:
		controller = 'lphaser'
	elif peripheral == SMSPeripheral.Paddle:
		# Don't use this without a Japanese system or the paddle goes haywire (definitely breaks with sms1)
		controller = 'paddle'
	elif peripheral == SMSPeripheral.Tablet:
		controller = 'graphic'
	elif peripheral == SMSPeripheral.SportsPad:
		# Uh oh, there's a sportspadjp as well. Uh oh, nobody told me there was regional differences. Uh oh, I'm not prepared for this at all. Uh oh. Oh shit. Oh fuck. Oh no.
		# I mean like.. they're both 2 button trackballs? Should be fine, I hope
		controller = 'sportspad'
	elif peripheral == SMSPeripheral.StandardController:
		controller = 'joypad'
	# There is also a multitap that adds 4 controller ports, it's called "Furrtek SMS Multitap" so I guess it's unofficial?
	# smsexp can be set to genderadp but I dunno what the point of that is

	# Might as well use the rapid fire thing
	if controller:
		slot_options['ctrl1'] = 'rapidfire'
		slot_options['ctrl2'] = 'rapidfire'
		slot_options['ctrl1:rapidfire:ctrl'] = controller
		slot_options['ctrl2:rapidfire:ctrl'] = controller

	return mame_driver_base(game, emulator, system, 'cart', slot_options)


def mame_mega_cd(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	region_codes = game.info.specific_info.get('Region Code')
	if region_codes:
		if (
			MegadriveRegionCodes.USA in region_codes
			or MegadriveRegionCodes.World in region_codes
			or MegadriveRegionCodes.BrazilUSA in region_codes
			or MegadriveRegionCodes.JapanUSA in region_codes
			or MegadriveRegionCodes.USAEurope in region_codes
		):
			system = 'segacd'
		elif (
			MegadriveRegionCodes.Japan in region_codes
			or MegadriveRegionCodes.Japan1 in region_codes
		):
			system = 'megacdj'
		elif (
			MegadriveRegionCodes.Europe in region_codes
			or MegadriveRegionCodes.EuropeA in region_codes
			or MegadriveRegionCodes.Europe8 in region_codes
		):
			system = 'megacd'
		else:
			system = 'segacd'
	else:
		system = 'segacd'
		if game.info.specific_info.get('TV Type') == TVSystem.PAL:
			system = 'megacd'
	# megacda also exists (Asia/PAL), not sure if we need it (is that what EuropeA is for?)
	return mame_driver_base(game, emulator, system, 'cdrom')


def mame_megadrive(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	# Can do Sonic & Knuckles + Sonic 2/3 lockon (IIRC)
	# Does do SVP
	# Doesn't emulate the Power Base Converter but you don't need to
	# Titan - Overdrive: Glitches out on the part with PCB that says "Blast Processing" and the Titan logo as well as the "Titan 512C Forever" part (doesn't even display "YOUR EMULATOR SUX" properly as Kega Fusion does with the unmodified binary)
	# md_slot.cpp claims that carts with EEPROM and Codemasters J-Cart games don't work, but it seems they do, maybe they don't save
	# Controllers are configured via Machine Configuration and hence are out of reach for poor little frontends
	# Pocket Monsters 2 displays blank screen after menu screen, although rom_lion3 does work, but it's not detected as that from fullpath
	# 4in1 and 12in1 won't boot anything either because they aren't detected from fullpath as being rom_mcpir (but Super 15 in 1 works)
	# Overdrive 2 is supposed to use SSF2 bankswitching but isn't detected as rom_ssf2, actual Super Street Fighter 2 does work
	mapper = game.info.specific_info.get('Mapper')
	if mapper == 'topf':
		# Doesn't seem to be detected via fullpath as being rom_topf, so it might work from software list
		raise EmulationNotSupportedError('Top Fighter 2000 MK VII not supported')
	if mapper == 'yasech':
		# Looks like it's same here... nothing about it being unsupported in SL entry
		raise EmulationNotSupportedError('Ya Se Chuan Shuo not supported')
	if mapper == 'kof99_pokemon':
		# This isn't a real mapper, Pocket Monsters uses rom_kof99 but it doesn't work (but KOF99 bootleg does)
		# Probably because it's detected as rom_99 when loaded from fullpath, so... it be like that sometimes
		raise EmulationNotSupportedError('Pocket Monsters not supported from fullpath')
	if mapper == 'smw64':
		raise EmulationNotSupportedError('Super Mario World 64 not supported')
	if mapper == 'cjmjclub':
		raise EmulationNotSupportedError('Chao Ji Mahjong Club not supported')
	if mapper == 'soulb':
		# It looks like this should work, but loading it from fullpath results in an "Unknown slot option 'rom_soulblad' in slot 'mdslot'" error when it should be rom_soulb instead
		raise EmulationNotSupportedError('Soul Blade not supported')
	if mapper == 'chinf3':
		raise EmulationNotSupportedError('Chinese Fighter 3 not supported')

	# Hmm. Most Megadrive emulators that aren't MAME have some kind of region preference thing where it's selectable between U->E->J or J->U->E or U->J->E or whatever.. because of how this works I'll have to make a decision, unless I feel like making a config thing for that, and I don't think I really need to do that.
	# I'll go with U->J->E for now
	region_codes = game.info.specific_info.get('Region Code')
	if region_codes:
		if (
			MegadriveRegionCodes.USA in region_codes
			or MegadriveRegionCodes.World in region_codes
			or MegadriveRegionCodes.BrazilUSA in region_codes
			or MegadriveRegionCodes.JapanUSA in region_codes
			or MegadriveRegionCodes.USAEurope in region_codes
		):
			# There is no purpose to using genesis_tmss other than making stuff not work for authenticity, apparently this is the only difference in MAME drivers
			system = 'genesis'
		elif (
			MegadriveRegionCodes.Japan in region_codes
			or MegadriveRegionCodes.Japan1 in region_codes
		):
			system = 'megadrij'
		elif (
			MegadriveRegionCodes.Europe in region_codes
			or MegadriveRegionCodes.EuropeA in region_codes
			or MegadriveRegionCodes.Europe8 in region_codes
		):
			system = 'megadriv'
		else:
			# Assume USA if unknown region code, although I'd be interested in the cases where there is a region code thing in the header but not any of the normal 3
			system = 'genesis'
	else:
		# This would happen if unlicensed/no TMSS stuff and so there is no region code info at all in the header
		# genesis and megadrij might not always be compatible...
		system = 'genesis'
		if game.info.specific_info.get('TV Type') == TVSystem.PAL:
			system = 'megadriv'
	return mame_driver_base(game, emulator, system, 'cart')


def mame_microbee(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'mbeepc'  # Either will do but this gives us colour (although mbeeppc seems to not play nicely with quickload)
	if game.info.media_type == MediaType.Executable:
		slot = 'quik1'
	elif game.info.media_type == MediaType.Floppy:
		system = 'mbee128'  # We need a system with a floppy drive, this is apparently not working but it seems fine (the other floppy ones do not seem fine)
		slot = 'flop1'
	else:
		raise EmulationNotSupportedError(f'Unknown media type: {game.info.media_type}')
	return mame_driver_base(game, emulator, system, slot, has_keyboard=True)


@cache
def _first_available_japanese_msx1_romset():
	return first_available_romset(
		japanese_msx1_drivers, japanese_msx2_drivers, working_msx2plus_drivers
	)


@cache
def _first_available_arabic_msx1_romset():
	return first_available_romset(arabic_msx1_drivers, arabic_msx2_drivers)


def mame_msx1(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	"""Possible slot options: centronics is there to attach printers and such; if using a floppy can put bm_012 (MIDI interface) or moonsound (OPL4 sound card, does anything use that?) in the cart port but I'm not sure that's needed; the slots are the same for MSX2
	:raises EmulationNotSupportedException: If no appropriate romset is available"""
	if game.info.specific_info.get('Japanese Only?', False):
		if _first_available_japanese_msx1_romset() is None:
			raise EmulationNotSupportedError('No Japanese MSX1 driver available')
		system = _first_available_japanese_msx1_romset()
	elif game.info.specific_info.get('Arabic Only?', False):
		if _first_available_arabic_msx1_romset() is None:
			raise EmulationNotSupportedError('No Arabic MSX1 driver available')
		system = _first_available_arabic_msx1_romset()
	else:
		if not hasattr(mame_msx1, 'msx1_system'):
			mame_msx1.msx1_system = first_available_romset(
				working_msx1_drivers.union(working_msx2_drivers).union(working_msx2plus_drivers)
			)  # type: ignore[attr-defined]
		if mame_msx1.msx1_system is None:  # type: ignore[attr-defined]
			raise EmulationNotSupportedError('No MSX1 driver available')
		system = mame_msx1.msx1_system  # type: ignore[attr-defined]

	slot_options = {}
	if game.info.media_type == MediaType.Floppy:
		# Defaults to 35ssdd, but 720KB disks need this one instead
		slot_options['fdc:0'] = '35dd'
		slot = 'flop1'
	elif game.info.media_type == MediaType.Cartridge:
		slot = 'cart1'
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	return mame_driver_base(game, emulator, system, slot, slot_options, has_keyboard=True)


def mame_msx2(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.info.specific_info.get('Japanese Only?', False):
		if not hasattr(mame_msx2, 'japanese_msx2_system'):
			mame_msx2.japanese_msx2_system = first_available_romset(
				japanese_msx2_drivers.union(working_msx2plus_drivers)
			)  # type: ignore[attr-defined]
		if mame_msx2.japanese_msx2_system is None:  # type: ignore[attr-defined]
			raise EmulationNotSupportedError('No Japanese MSX2 driver available')
		system = mame_msx2.japanese_msx2_system  # type: ignore[attr-defined]
	elif game.info.specific_info.get('Arabic Only?', False):
		if not hasattr(mame_msx2, 'arabic_msx2_system'):
			mame_msx2.arabic_msx2_system = first_available_romset(arabic_msx2_drivers)  # type: ignore[attr-defined]
		if mame_msx2.arabic_msx2_system is None:  # type: ignore[attr-defined]
			raise EmulationNotSupportedError('No Arabic MSX2 driver available')
		system = mame_msx2.arabic_msx2_system  # type: ignore[attr-defined]
	else:
		if not hasattr(mame_msx2, 'msx2_system'):
			mame_msx2.msx2_system = first_available_romset(
				working_msx2_drivers.union(working_msx2plus_drivers)
			)  # type: ignore[attr-defined]
		if mame_msx2.msx2_system is None:  # type: ignore[attr-defined]
			raise EmulationNotSupportedError('No MSX2 driver available')
		system = mame_msx2.msx2_system  # type: ignore[attr-defined]

	slot_options = {}
	if game.info.media_type == MediaType.Floppy:
		# Defaults to 35ssdd, but 720KB disks need this one instead
		slot_options['fdc:0'] = '35dd'
		slot = 'flop1'
	elif game.info.media_type == MediaType.Cartridge:
		slot = 'cart1'
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	return mame_driver_base(game, emulator, system, slot, slot_options, has_keyboard=True)


def mame_msx2plus(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if not hasattr(mame_msx2plus, 'msx2plus_system'):
		mame_msx2plus.msx2plus_system = first_available_romset(working_msx2plus_drivers)  # type: ignore[attr-defined]
	if mame_msx2plus.msx2plus_system is None:  # type: ignore[attr-defined]
		raise EmulationNotSupportedError('No MSX2+ driver available')
	system = mame_msx2plus.msx2plus_system  # type: ignore[attr-defined]

	slot_options = {}
	if game.info.media_type == MediaType.Floppy:
		# Defaults to 35ssdd, but 720KB disks need this one instead
		slot_options['fdc:0'] = '35dd'
		slot = 'flop1'
	elif game.info.media_type == MediaType.Cartridge:
		slot = 'cart1'
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	return mame_driver_base(game, emulator, system, slot, slot_options, has_keyboard=True)


def mame_n64_check(game: 'ROMGame', _):
	if game.info.specific_info.get('TV Type') == TVSystem.PAL:
		raise EmulationNotSupportedError('NTSC only')


def mame_nes(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.rom.extension == 'fds':
		# We don't need to detect TV type because the FDS was only released in Japan and so the Famicom can be used for everything
		# TODO: This isn't really right, should set controllers
		return mame_driver_base(game, emulator, 'fds', 'flop')

	unsupported_ines_mappers = (
		27,
		29,
		30,
		55,
		59,
		60,
		81,
		84,
		98,
		99,
		100,
		101,
		102,
		103,
		109,
		110,
		111,
		122,
		124,
		125,
		127,
		128,
		129,
		130,
		131,
		135,
		151,
		161,
		169,
		170,
		174,
		181,
		219,
		220,
		236,
		237,
		239,
		247,
		248,
		251,
		253,
	)
	supported_unif_mappers = (
		'DREAMTECH01',
		'NES-ANROM',
		'NES-AOROM',
		'NES-CNROM',
		'NES-NROM',
		'NES-NROM-128',
		'NES-NROM-256',
		'NES-NTBROM',
		'NES-SLROM',
		'NES-TBROM',
		'NES-TFROM',
		'NES-TKROM',
		'NES-TLROM',
		'NES-UOROM',
		'UNL-22211',
		'UNL-KOF97',
		'UNL-SA-NROM',
		'UNL-VRC7',
		'UNL-T-230',
		'UNL-CC-21',
		'UNL-AX5705',
		'UNL-SMB2J',
		'UNL-8237',
		'UNL-SL1632',
		'UNL-SACHEN-74LS374N',
		'UNL-TC-U01-1.5M',
		'UNL-SACHEN-8259C',
		'UNL-SA-016-1M',
		'UNL-SACHEN-8259D',
		'UNL-SA-72007',
		'UNL-SA-72008',
		'UNL-SA-0037',
		'UNL-SA-0036',
		'UNL-SA-9602B',
		'UNL-SACHEN-8259A',
		'UNL-SACHEN-8259B',
		'BMC-190IN1',
		'BMC-64IN1NOREPEAT',
		'BMC-A65AS',
		'BMC-GS-2004',
		'BMC-GS-2013',
		'BMC-NOVELDIAMOND9999999IN1',
		'BMC-SUPER24IN1SC03',
		'BMC-SUPERHIK8IN1',
		'BMC-T-262',
		'BMC-WS',
		'BMC-N625092',
	)
	if game.info.specific_info.get('Header Format', None) in {'iNES', 'NES 2.0'}:
		mapper = game.info.specific_info['Mapper Number']
		if mapper in unsupported_ines_mappers or mapper >= 256:
			raise EmulationNotSupportedError(
				f'Unsupported mapper: {mapper} ({game.info.specific_info.get("Mapper")})'
			)
	if game.info.specific_info.get('Header Format', None) == 'UNIF':
		mapper = game.info.specific_info.get('Mapper')
		if mapper not in supported_unif_mappers:
			raise EmulationNotSupportedError(f'Unsupported mapper: {mapper}')

	has_keyboard = False

	if game.info.specific_info.get('Is Dendy?', False):
		system = 'dendy'
	elif game.info.specific_info.get('TV Type') == TVSystem.PAL:
		system = 'nespal'
	else:
		# There's both a "famicom" driver and also a "nes" driver which does include the Famicom (as well as NTSC NES), this seems to only matter for what peripherals can be connected
		system = 'nes'

	options = {}
	peripheral = game.info.specific_info.get('Peripheral')

	# NES: ctrl1 = 4score_p1p3 (multitap), joypad, miracle_piano, zapper; ctrl2 = 4score_p2p4, joypad, powerpad, vaus, zapper
	# PAL NES is the same
	# Famicom: exp = arcstick (arcade stick? Eh?), barcode_battler, family_trainer, fc_keyboard, hori_4p (multitap), hori_twin (multitap), joypad, konamihs (thing with 4 buttons), mj_panel, pachinko, partytap (quiz game thing?), subor_keyboard, vaus, zapper

	# For Famicom... hmm, I wonder if it could ever cause a problem where it's like, a Famicom game expects to use the zapper on the exp port and won't like being run on a NES with 2 zappers in the controller ports
	if peripheral == NESPeripheral.Zapper:
		# ctrl1 can have a gun, but from what I understand the games just want it in slot 2?
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
		# I dunno how to handle the Family Trainer for Famicom games, but I read from googling around that the Japanese games will run fine on a NES with an American Power Pad so that's basically what we're doing here

	# Power Glove and ROB aren't emulated, so you'll just have to use the normal controller

	return mame_driver_base(game, emulator, system, 'cart', options, has_keyboard=has_keyboard)


def mame_odyssey2(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'odyssey2'

	if game.info.specific_info.get('TV Type') == TVSystem.PAL:
		system = 'videopac'
	# system = 'videopacf' if region == France could also be a thing? Hmm

	return mame_driver_base(game, emulator, system, 'cart')


def mame_pc_engine(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	# TODO: Use platform_config or software list to get PCE CD BIOS, then do that (same system, but -cdrom slot instead and -cart goes to System Card; TurboGrafx System Card only works with tg16 but other combinations are fine)
	system = 'tg16'
	# USA system can run Japanese games, so maybe we don't need to switch to pce if Japan in regions; but USA games do need tg16 specifically
	if game.rom.extension == 'sgx':
		# It might be better to detect this differently like if software is in sgx.xml software list, or set Is-Supergrafx field that way in roms_metadata platform_helpers
		system = 'sgx'

	return mame_driver_base(game, emulator, system, 'cart')


def mame_pico(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	region_codes = game.info.specific_info.get('Region Code')
	if region_codes:
		if (
			MegadriveRegionCodes.USA in region_codes
			or MegadriveRegionCodes.World in region_codes
			or MegadriveRegionCodes.BrazilUSA in region_codes
			or MegadriveRegionCodes.JapanUSA in region_codes
			or MegadriveRegionCodes.USAEurope in region_codes
		):
			system = 'picou'
		elif (
			MegadriveRegionCodes.Japan in region_codes
			or MegadriveRegionCodes.Japan1 in region_codes
		):
			system = 'picoj'
		elif (
			MegadriveRegionCodes.Europe in region_codes
			or MegadriveRegionCodes.EuropeA in region_codes
			or MegadriveRegionCodes.Europe8 in region_codes
		):
			system = 'pico'
		else:
			system = 'picoj'  # Seems the most likely default
	else:
		system = 'picoj'
		if game.info.specific_info.get('TV Type') == TVSystem.PAL:
			system = 'pico'
	return mame_driver_base(game, emulator, system, 'cart')


def mame_saturn(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	# Default to USA
	system = 'saturn'
	region_codes = game.info.specific_info.get('Region Code')
	if region_codes:
		# Clones here are hisaturn and vsaturn, not sure how useful those would be
		if SaturnDreamcastRegionCodes.USA in region_codes:
			system = 'saturn'
		elif SaturnDreamcastRegionCodes.Japan in region_codes:
			system = 'saturnjp'
		elif SaturnDreamcastRegionCodes.Europe in region_codes:
			system = 'saturneu'

	# TODO: Use ctrl1 and ctrl2 to set controllers (analog, joy_md3, joy_md6, joypad, keyboard, mouse, racing, segatap (???), trackball)
	# Dunno if the cart slot can be used for anything useful yet
	return mame_driver_base(game, emulator, system, 'cdrom')


def mame_sord_m5(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	system = 'm5'
	if game.info.specific_info.get('TV Type') == TVSystem.PAL:
		system = 'm5p'
		# Not sure what m5p_brno is about (two floppy drives?)

	# ramsize can be set to 64K pre-0.227
	# Dunno what the second cart slot is used for
	# Also has flop slot (generic extensions) and cass slot (.wav/.cas)?
	return mame_driver_base(game, emulator, system, 'cart1', has_keyboard=True)


def mame_sg1000(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	slot_options = {}
	has_keyboard = False

	ext = game.rom.extension
	if game.info.media_type == MediaType.Floppy:
		system = 'sf7000'
		slot = 'flop'
		has_keyboard = True
		# There are standard Centronics and RS-232 ports/devices available with this, but would I really need them?
	elif ext == 'sc':
		# SC-3000H is supposedly identical except it has a mechanical keyboard. Not sure why sc3000h is a separate driver, but oh well
		system = 'sc3000'
		slot = 'cart'
		has_keyboard = True
	elif ext in {'bin', 'sg'}:
		# Use original system here. Mark II seems to have no expansion and it should just run Othello Multivision stuff?
		system = 'sg1000'
		slot = 'cart'
		slot_options[
			'sgexp'
		] = 'fm'  # Can also put sk1100 in here. Can't detect yet what uses which though
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	return mame_driver_base(game, emulator, system, slot, slot_options, has_keyboard=has_keyboard)


def mame_sharp_x68000(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if isinstance(game.rom, M3UPlaylist):
		# This won't work if the referenced m3u files have weird compression formats supported by 7z but not by MAME; but maybe that's your own fault
		floppy_slots = {
			f'flop{i+1}': str(individual_floppy.path)
			for i, individual_floppy in enumerate(game.rom.subroms)
		}

		return mame_driver_base(
			game, emulator, 'x68000', slot=None, slot_options=floppy_slots, has_keyboard=True
		)
	return mame_driver_base(game, emulator, 'x68000', 'flop1', has_keyboard=True)


def mame_snes(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.rom.extension == 'st':
		if _is_software_available('snes', 'sufami'):
			return mame_driver_base(game, emulator, 'snes', 'cart2', {'cart': 'sufami'})

		bios_path = cast(
			Path | None, game.platform_config.options.get('sufami_turbo_bios_path', None)
		)
		if not bios_path:
			raise EmulationNotSupportedError('Sufami Turbo BIOS not set up, check platforms.ini')

		# We don't need to detect TV type because the Sufami Turbo (and also BS-X) was only released in Japan and so the Super Famicom can be used for everything
		return mame_driver_base(game, emulator, 'snes', 'cart2', {'cart': str(bios_path)})

	if game.rom.extension == 'bs':
		if _is_software_available('snes', 'bsxsore'):
			return mame_driver_base(game, emulator, 'snes', 'cart2', {'cart': 'bsxsore'})

		bios_path = cast(Path | None, game.platform_config.options.get('bsx_bios_path', None))
		if not bios_path:
			raise EmulationNotSupportedError(
				'BS-X/Satellaview BIOS not set up, check platforms.ini'
			)
		return mame_driver_base(game, emulator, 'snes', 'cart2', {'cart': str(bios_path)})

	expansion_chip = game.info.specific_info.get('Expansion Chip')
	if expansion_chip == SNESExpansionChip.ST018:
		raise EmulationNotSupportedError(f'{expansion_chip} not supported')

	slot = game.info.specific_info.get('Slot')
	if slot and (slot.endswith(('_poke', '_sbld', '_tekken2', '_20col'))):
		# These bootleg copy protection methods might work from software list, but from fullpath the carts aren't detected as using it, so they black screen
		raise EmulationNotSupportedError(f'{slot} mapper not supported')

	# American SNES and Super Famicom are considered to be the same system, so that works out nicely
	system = 'snespal' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'snes'

	# TODO Set ctrl1/ctrl2: barcode_battler, joypad, miracle_piano, mouse, pachinko, sscope (also multitap, twintap which we don't need or maybe we do)

	return mame_driver_base(game, emulator, system, 'cart')


def mame_super_cassette_vision(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	if game.info.specific_info.get('Has Extra RAM?', False):
		raise EmulationNotSupportedError(
			'RAM on cartridge not supported except from software list (game would malfunction)'
		)

	system = 'scv'
	if game.info.specific_info.get('TV Type') == TVSystem.PAL:
		system = 'scv_pal'

	return mame_driver_base(game, emulator, system, 'cart')


def mame_vic_20(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	size = cast(FileROM, game.rom).size
	if size > ((8 * 1024) + 2):
		# It too damn big (only likes 8KB with 2 byte header at most)
		raise EmulationNotSupportedError(f'Single-part >8K cart not supported: {size}')

	system = 'vic20p' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'vic20'

	return mame_driver_base(game, emulator, system, 'cart', {'iec8': ''}, has_keyboard=True)


def mame_zx_spectrum(game: 'ROMGame', emulator: 'BaseMAMEDriver') -> LaunchCommand:
	options = {}

	system = None

	machine = game.info.specific_info.get('Machine')
	# TODO: Make this something like "compatible_systems", so you can just use the closest one, instead of assuming user has all of them
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

	if not system:
		recommended_ram: ByteAmount | None = game.info.specific_info.get('Recommended RAM')
		if recommended_ram is not None:
			# TODO: Fallback to minimum RAM if this machine is not found
			# I don't think we need to set ramsize, unless it turns out this really means maximum
			if recommended_ram <= (48 * 1024):
				system = 'spectrum'
			elif recommended_ram <= (128 * 1024):
				system = 'spec128'

	if game.info.media_type == MediaType.Floppy:
		if not system:
			system = 'specpls3'
		slot = 'flop1'
		# If only one floppy is needed, you can add -upd765:1 "" to the commmand line and use just "flop" instead of "flop1".
	elif game.info.media_type == MediaType.Snapshot:
		# We do need to plug in the Kempston interface ourselves, though; that's fine. Apparently how the ZX Interface 2 works is that it just maps joystick input to keyboard input, so we don't really need it, but I could be wrong and thinking of something else entirely.
		slot = 'dump'
		if system not in {'specpl2a', 'specpls3'}:
			# Just to safeguard; +3 doesn't have stuff in the exp slot other than Multiface 3; as I understand it the real hardware is incompatible with normal stuff so that's why
			joystick_type = game.info.specific_info.get('Joystick Type')
			if joystick_type == ZXJoystick.Kempton:
				options['exp'] = 'kempjoy'
			elif joystick_type in {ZXJoystick.SinclairLeft, ZXJoystick.SinclairRight}:
				options['exp'] = 'intf2'
			elif joystick_type == ZXJoystick.Cursor:
				# This just adds a 1-button joystick which maps directions to 5678 and fire to 0
				options['exp'] = 'protek'
	elif game.info.media_type == MediaType.Cartridge:
		# This will automatically boot the game without going through any sort of menu, and since it's the Interface 2, they would all use the Interface 2 joystick. So that works nicely
		if cast(FileROM, game.rom).size != 0x4000:
			raise EmulationNotSupportedError('Whoops 16KB only thank you')
		slot = 'cart'
		options['exp'] = 'intf2'
	elif game.info.media_type == MediaType.Executable:
		slot = 'quik'
	else:
		raise AssertionError(f'Media type {game.info.media_type} unsupported')

	if not system:
		system = 'spec128'  # Probably a good default

	return mame_driver_base(game, emulator, system, slot, options, has_keyboard=True)


# Mednafen modules
def mednafen_apple_ii_check(game: 'ROMGame', _):
	machines = game.info.specific_info.get('Machine')
	if machines and (
		AppleIIHardware.AppleII not in machines and AppleIIHardware.AppleIIPlus not in machines
	):
		raise EmulationNotSupportedError(
			f'Only Apple II and II+ are supported, this needs {machines}'
		)

	required_ram = game.info.specific_info.get('Minimum RAM')
	if required_ram and required_ram > (64 * 1024):
		raise EmulationNotSupportedError(f'Needs at least {required_ram} RAM')


def mednafen_game_gear(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	mapper = game.info.specific_info.get('Mapper')
	if mapper in {'Codemasters', 'EEPROM'}:
		raise EmulationNotSupportedError(f'{mapper} mapper not supported')
	return mednafen_module_launch('gg', exe_path=emulator.exe_path)


def mednafen_gb(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	verify_supported_gb_mappers(
		game, {'MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC7', 'HuC1', 'HuC3'}, set()
	)
	return mednafen_module_launch('gb', exe_path=emulator.exe_path)


def mednafen_gba(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if cast(FileROM, game.rom).size > (32 * 1024 * 1024):
		raise EmulationNotSupportedError('64MB GBA Video carts not supported')
	return mednafen_module_launch('gba', exe_path=emulator.exe_path)


def mednafen_lynx(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.info.media_type == MediaType.Cartridge and not game.info.specific_info.get(
		'Headered?', False
	):
		raise EmulationNotSupportedError('Needs to have .lnx header')

	return mednafen_module_launch('lynx', exe_path=emulator.exe_path)


def mednafen_megadrive(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.info.specific_info.get('Expansion Chip', None) == 'SVP':
		raise EmulationNotSupportedError('SVP chip not supported')

	mapper = game.info.specific_info.get('Mapper')
	unsupported_mappers = {
		'mcpir',
		'sf002',
		'mjlov',
		'lion3',
		'kof99_pokemon',
		'squir',
		'sf004',
		'topf',
		'smw64',
		'lion2',
		'stm95',
		'cjmjclub',
		'pokestad',
		'soulb',
		'smb',
		'smb2',
		'chinf3',
	}
	# Squirrel King does boot but you die instantly, that's interesting
	# Soul Blade freezes soon after starting a match?
	if mapper in unsupported_mappers:
		raise EmulationNotSupportedError(mapper + ' not supported')

	return mednafen_module_launch('md', exe_path=emulator.exe_path)


def mednafen_nes(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	# Mapper 30, 38 aren't in the documentation but they do exist in the source code
	unsupported_ines_mappers = {
		14,
		20,
		27,
		28,
		29,
		31,
		35,
		36,
		39,
		43,
		50,
		53,
		54,
		55,
		56,
		57,
		58,
		59,
		60,
		61,
		62,
		63,
		81,
		83,
		84,
		91,
		98,
		100,
		102,
		103,
		104,
		106,
		108,
		109,
		110,
		111,
		116,
		136,
		137,
		138,
		139,
		141,
		142,
		143,
		181,
		183,
		186,
		187,
		188,
		191,
		192,
		211,
		212,
		213,
		214,
		216,
		218,
		219,
		220,
		221,
		223,
		224,
		225,
		226,
		227,
		229,
		230,
		231,
		233,
		235,
		236,
		237,
		238,
		239,
		243,
		245,
	}
	unsupported_ines_mappers.update(range(120, 133))
	unsupported_ines_mappers.update(range(145, 150))
	unsupported_ines_mappers.update(range(161, 180))
	unsupported_ines_mappers.update(range(194, 206))
	supported_unif_mappers = {
		'BTR',
		'PNROM',
		'PEEOROM',
		'TC-U01-1.5M',
		'Sachen-8259B',
		'Sachen-8259A',
		'Sachen-74LS374N',
		'SA-016-1M',
		'SA-72007',
		'SA-72008',
		'SA-0036',
		'SA-0037',
		'H2288',
		'8237',
		'MB-91',
		'NINA-06',
		'NINA-03',
		'NINA-001',
		'HKROM',
		'EWROM',
		'EKROM',
		'ELROM',
		'ETROM',
		'SAROM',
		'SBROM',
		'SCROM',
		'SEROM',
		'SGROM',
		'SKROM',
		'SLROM',
		'SL1ROM',
		'SNROM',
		'SOROM',
		'TGROM',
		'TR1ROM',
		'TEROM',
		'TFROM',
		'TLROM',
		'TKROM',
		'TSROM',
		'TLSROM',
		'TKSROM',
		'TQROM',
		'TVROM',
		'AOROM',
		'CPROM',
		'CNROM',
		'GNROM',
		'NROM',
		'RROM',
		'RROM-128',
		'NROM-128',
		'NROM-256',
		'MHROM',
		'UNROM',
		'MARIO1-MALEE2',
		'Supervision16in1',
		'NovelDiamond9999999in1',
		'Super24in1SC03',
		'BioMiracleA',
		'603-5052',
	}

	if game.info.specific_info.get('Header Format', None) in {'iNES', 'NES 2.0'}:
		mapper = game.info.specific_info['Mapper Number']
		if mapper in unsupported_ines_mappers or mapper >= 256:
			# Does not actually seem to check for NES 2.0 header extensions at all, according to source
			raise EmulationNotSupportedError(
				f'Unsupported mapper: {mapper} ({game.info.specific_info.get("Mapper")})'
			)
	if game.info.specific_info.get('Header Format', None) == 'UNIF':
		mapper = game.info.specific_info.get('Mapper')
		if mapper not in supported_unif_mappers:
			raise EmulationNotSupportedError(f'Unsupported mapper: {mapper}')

	return mednafen_module_launch('nes', exe_path=emulator.exe_path)


def mednafen_snes_faust(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	# Also does not support any other input except normal controller and multitap
	expansion_chip = game.info.specific_info.get('Expansion Chip')
	if expansion_chip and expansion_chip not in {
		SNESExpansionChip.CX4,
		SNESExpansionChip.SA_1,
		SNESExpansionChip.DSP_1,
		SNESExpansionChip.SuperFX,
		SNESExpansionChip.SuperFX2,
		SNESExpansionChip.DSP_2,
		SNESExpansionChip.S_DD1,
	}:
		raise EmulationNotSupportedError(f'{expansion_chip} not supported')
	return mednafen_module_launch('snes_faust', exe_path=emulator.exe_path)


# VICE
def vice_c64(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	"""http://vice-emu.sourceforge.net/vice_7.html#SEC94
	:raises EmulationNotSupportedException: If cart type unsupported"""
	# Eh, maybe I should sort this. Or maybe convert it into unsupported_cartridge_types which seems like it would be a smaller list.
	supported_cartridge_types = {
		0,
		1,
		50,
		35,
		30,
		9,
		15,
		34,
		21,
		24,
		25,
		26,
		52,
		17,
		32,
		10,
		44,
		13,
		3,
		29,
		45,
		46,
		7,
		42,
		39,
		2,
		51,
		19,
		14,
		28,
		38,
		5,
		43,
		27,
		12,
		36,
		23,
		4,
		47,
		31,
		22,
		48,
		8,
		40,
		20,
		16,
		11,
		18,
		# Not sure if EasyFlash Xbank (33) was supposed to be included in the mention of EasyFlash being emulated? Guess I'll find out
		# I guess "REX 256K EPROM Cart" == Rex EP256 (27)?
		# RGCD, RR-Net MK3 are apparently emulated, whatever they are, but I dunno what number they're assigned to
		41,
		49,
		37,
		6,
	}  # Slot 0 and 1 carts (have passthrough, and maybe I should be handling them differently as they aren't really meant to be standalone things); also includes Double Quick Brown Box, ISEPIC, and RamCart
	if game.info.media_type == MediaType.Cartridge:
		cart_type = game.info.specific_info.get('Mapper Number', None)
		cart_type_name = game.info.specific_info.get('Mapper', None)
		if cart_type and cart_type not in supported_cartridge_types:
			raise EmulationNotSupportedError(
				f'Cart type {cart_type} ({cart_type_name}) not supported'
			)

	args = ['-VICIIfull']
	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		args += ['-model', 'ntsc']
	elif game.info.specific_info.get('TV Type') == TVSystem.PAL:
		args += ['-model', 'pal']
	args.append(rom_path_argument)

	return LaunchCommand(emulator.exe_path, args)


def vice_c128(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['-VDCfull']
	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		args += ['-model', 'ntsc']
	elif game.info.specific_info.get('TV Type') == TVSystem.PAL:
		args += ['-model', 'pal']
	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def vice_pet(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['-CRTCfull']
	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		args += ['-ntsc']
	elif game.info.specific_info.get('TV Type') == TVSystem.PAL:
		args += ['-pal']

	machine = game.info.specific_info.get('Machine')
	# The "Machine" field is set directly to the model argument, so that makes things a lot easier for me. Good thing I decided to do that
	if machine:
		args += ['-model', machine]

	ram_size = game.info.specific_info.get('Minimum RAM')
	if ram_size:
		# TODO: Ensure this is one of 4K (default) / 8K / 16K / 32K
		args += ['-ramsize', f'{ram_size // 1024}K']

	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def vice_plus4(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['-TEDfull']
	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		args += ['-model', 'plus4ntsc']
	elif game.info.specific_info.get('TV Type') == TVSystem.PAL:
		args += ['-model', 'plus4pal']
	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def vice_vic20(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['-VICfull']
	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		args += ['-model', 'vic20ntsc']
	elif game.info.specific_info.get('TV Type') == TVSystem.PAL:
		args += ['-model', 'vic20pal']
	if game.info.media_type == MediaType.Cartridge:
		args.append('-cartgeneric')
		size = cast(FileROM, game.rom).size
		if size > ((8 * 1024) + 2):
			# Frick
			# TODO: Support multiple parts with -cart2 -cartA etc; this will probably require a lot of convoluted messing around to know if a given ROM is actually the second part of a multi-part cart (probably using software lists) and using game.roms.subroms etc
			raise EmulationNotSupportedError(f'Single-part >8K cart not supported: {size}')

	if game.info.specific_info.get('Peripheral') == 'Paddle':
		args += ['-controlport1device', '2']

	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


# Other emulators
def a7800(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	"""Hmm, mostly the same as mame_a7800, except without the MAME
	:raises EmulationNotSupportedException: if headerless"""
	if not game.info.specific_info.get('Headered?', False):
		# This would only be supported via software list (although A7800 seems to have removed that anyway)
		raise EmulationNotSupportedError('No header')

	args = ['a7800p' if game.info.specific_info.get('TV Type') == TVSystem.PAL else 'a7800']
	# There are also a7800u1, a7800u2, a7800pu1, a7800pu2 to change the colour palettes. Maybe that could be an emulator_config option...

	if not hasattr(a7800, 'have_hiscore_software'):
		a7800.have_hiscore_software = is_highscore_cart_available()  # type: ignore[attr-defined]

	if a7800.have_hiscore_software and game.info.specific_info.get('Uses Hiscore Cart', False):  # type: ignore[attr-defined]
		args += ['-cart1', 'hiscore', '-cart2', rom_path_argument]
	else:
		args += ['-cart', rom_path_argument]

	return LaunchCommand(emulator.exe_path, args)


def bsnes(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.platform.name == 'Game Boy':
		sgb_bios_path = cast(
			Path | None, game.platform_config.options.get('super_game_boy_bios_path', None)
		)
		if not sgb_bios_path:
			raise EmulationNotSupportedError('Super Game Boy BIOS not set up, check platforms.ini')
		colour_flag = game.info.specific_info.get('Is Colour?', GameBoyColourFlag.No)
		if colour_flag == GameBoyColourFlag.Required:
			raise EmulationNotSupportedError('Super Game Boy is not compatible with GBC-only games')
		if colour_flag == GameBoyColourFlag.Yes and emulator.config.sgb_incompatible_with_gbc:
			raise EmulationNotSupportedError(
				'We do not want to play a colour game with a Super Game Boy'
			)
		if emulator.config.sgb_enhanced_only and not game.info.specific_info.get(
			'SGB Enhanced?', False
		):
			raise EmulationNotSupportedError(
				'We do not want to play a non-SGB enhanced game with a Super Game Boy'
			)

		# Pocket Camera is also supported by the SameBoy core, but I'm leaving it out here because bsnes doesn't do the camera
		verify_supported_gb_mappers(game, {'MBC1', 'MBC2', 'MBC3', 'MBC5', 'HuC1', 'HuC3'}, set())

		return LaunchCommand(
			emulator.exe_path, ['--fullscreen', str(sgb_bios_path), rom_path_argument]
		)

	if game.rom.extension == 'st':
		bios_path = cast(
			Path | None, game.platform_config.options.get('sufami_turbo_bios_path', None)
		)
		if not bios_path:
			raise EmulationNotSupportedError('Sufami Turbo BIOS not set up, check platforms.ini')
		# We need two arguments (and the second argument has to exist), otherwise when you actually launch it you get asked for something to put in slot B and who says we ever wanted to put anything in slot B
		# Can also use /dev/null but that's not portable and even if I don't care about that, it just gives me bad vibes
		return LaunchCommand(
			emulator.exe_path,
			['--fullscreen', str(bios_path), rom_path_argument, rom_path_argument],
		)

	# Oh it can just launch Satellaview without any fancy options huh

	slot = game.info.specific_info.get('Slot')
	if slot and (slot.endswith(('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col'))):
		# There are a few bootleg things that will not work
		raise EmulationNotSupportedError(f'{slot} mapper not supported')

	return LaunchCommand(emulator.exe_path, ['--fullscreen', rom_path_argument])


def cemu(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	title_id = game.info.specific_info.get('Title ID')
	if title_id:
		category = title_id[4:8]
		if category == '000C':
			raise NotActuallyLaunchableGameError('Cannot boot DLC')
		if category == '000E':
			raise NotActuallyLaunchableGameError('Cannot boot update')

	path = (
		str(game.rom.relevant_files['rpx'])
		if isinstance(game.rom, FolderROM)
		else rom_path_argument
	)
	return LaunchCommand(emulator.exe_path, ['-f', '-g', f'Z:{path}'])


def citra(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.rom.extension != '3dsx':
		if not game.info.specific_info.get('Decrypted', True):
			raise EmulationNotSupportedError('ROM is encrypted')
		if not game.info.specific_info.get('Is CXI?', True):
			raise EmulationNotSupportedError('Not CXI')
		if not game.info.specific_info.get('Has SMDH?', False):
			raise EmulationNotSupportedError('No icon (SMDH), probably an applet')
		if game.info.product_code and game.info.product_code[3:6] == '-U-':
			# Ignore update data, which either are pointless (because you install them in Citra and then when you run the main game ROM, it has all the updates applied) or do nothing
			# I feel like there's probably a better way of doing this whoops
			raise NotActuallyLaunchableGameError('Update data, not actual game')
	return LaunchCommand(emulator.exe_path, [rom_path_argument])


def cxnes(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	allowed_mappers = {
		0,
		1,
		2,
		3,
		4,
		5,
		7,
		9,
		10,
		11,
		13,
		14,
		15,
		16,
		18,
		19,
		21,
		22,
		23,
		24,
		25,
		26,
		28,
		29,
		30,
		31,
		32,
		33,
		34,
		36,
		37,
		38,
		39,
		41,
		44,
		46,
		47,
		48,
		49,
		58,
		60,
		61,
		62,
		64,
		65,
		66,
		67,
		68,
		69,
		70,
		71,
		73,
		74,
		75,
		76,
		77,
		78,
		79,
		80,
		82,
		85,
		86,
		87,
		88,
		89,
		90,
		91,
		93,
		94,
		95,
		97,
		99,
		105,
		107,
		112,
		113,
		115,
		118,
		119,
		133,
		137,
		138,
		139,
		140,
		141,
		143,
		144,
		145,
		146,
		147,
		148,
		149,
		150,
		151,
		152,
		153,
		154,
		155,
		158,
		159,
		166,
		167,
		178,
		180,
		182,
		184,
		185,
		189,
		192,
		193,
		200,
		201,
		202,
		203,
		205,
		206,
		207,
		209,
		210,
		211,
		218,
		225,
		226,
		228,
		230,
		231,
		232,
		234,
		240,
		241,
		245,
		246,
	}

	if game.info.specific_info.get('Header Format', None) == 'iNES':
		mapper = game.info.specific_info['Mapper Number']
		if mapper not in allowed_mappers:
			raise EmulationNotSupportedError(
				f'Unsupported mapper: {mapper} ({game.info.specific_info.get("Mapper")})'
			)

	# Could possibly do something involving --no-romcfg if there's no config found, otherwise the emulator pops up a message about that unless you disable romcfg entirely
	return LaunchCommand(emulator.exe_path, ['-f', rom_path_argument])


def dolphin_check(game: 'ROMGame', _):
	if game.info.specific_info.get('No Disc Magic?', False):
		raise EmulationNotSupportedError('No disc magic')
	title_type = game.info.specific_info.get('Title Type')
	if title_type and title_type not in {
		WiiTitleType.Channel,
		WiiTitleType.DiscWithChannel,
		WiiTitleType.SystemChannel,
		WiiTitleType.HiddenChannel,
	}:
		# Technically Wii Menu versions are WiiTitleType.System but can be booted, but eh
		raise NotActuallyLaunchableGameError(f'Cannot boot a {title_type.name}')


def dolphin(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	return LaunchCommand(
		emulator.exe_path,
		[
			'-b',
			'-e',
			str(cast(FolderROM, game.rom).relevant_files['boot.dol'])
			if game.rom.is_folder
			else rom_path_argument,
		],
	)


def fs_uae(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['--fullscreen']
	model = None

	if game.platform.name == 'Amiga CD32':
		model = 'CD32'
	elif game.platform.name == 'Commodore CDTV':
		model = 'CDTV'
	else:
		machine = game.info.specific_info.get('Machine')
		if machine:
			supported_models = (
				# All the models supported by FS-UAE --amiga_model argument, although we will fiddle with the actual argument later
				# Ordered by what I presume is best to not quite as good, or rather: What would we try first
				'CD32',
				'A4000/40',
				'A4000',
				'A1200/20',
				'A1200',
				'A3000',
				'A600',
				'A500+',
				'CDTV',
				'A1000',
				'A500',
			)
			if isinstance(machine, str):
				if machine in supported_models:
					model = machine
				else:
					raise EmulationNotSupportedError(f'FS-UAE does not emulate a {machine}')
			elif isinstance(machine, Collection):
				for supported_model in supported_models:
					if supported_model in machine:
						model = supported_model
						break
				else:
					raise EmulationNotSupportedError(f'FS-UAE does not emulate any of {machine}')

		else:
			# TODO: It would be better if this didn't force specific models, but could look at what ROMs the user has for FS-UAE and determines which models are available that support the given chipset, falling back to backwards compatibility for newer models or throwing EmulationNotSupportedException as necessary

			# We don't need to specify a model if there's no reason to! Only use OCS if it's explicitly specified as such
			chipset = game.info.specific_info.get('Chipset')
			if chipset:
				if 'AGA' in chipset:
					model = 'A4000'  # Or A1200, which only has 68EC020 instead of 68040, so it's not as cool
				elif 'ECS' in chipset:
					model = 'A600'  # Or A500+
				elif 'OCS' in chipset:
					model = 'A1000'  # Or A500
	# I can't figure out how to get these sorts of things to autoboot, or maybe they don't
	# Okay, so I haven't really looked into it sshhh
	if game.info.specific_info.get('Requires Hard Disk?', False):
		raise EmulationNotSupportedError('Requires a hard disk')
	if game.info.specific_info.get('Requires Workbench?', False):
		raise EmulationNotSupportedError('Requires Workbench')

	if model:
		if model == 'A4000':
			model = 'A4000/40'  # A4000 by itself isn't a valid value, just to be annoying
		args.append(f'--amiga_model={model}')
		# if model == 'CD32': #Okay, turns out you shouldn't actually need that
		# 	args.append('--joystick_port_0_mode=cd32 gamepad')

	if game.info.media_type == MediaType.Floppy:
		args.append(f'--floppy_drive_0={rom_path_argument}')
	elif game.info.media_type == MediaType.OpticalDisc:
		args.append(f'--cdrom_drive_0={rom_path_argument}')
	elif game.info.media_type in {MediaType.HardDisk, MediaType.Digital}:
		# TODO: WHDLoad requires the "slave name" (big :/ moment) as an argument
		args.append(f'--hard_drive_0={rom_path_argument}')
	else:
		raise EmulationNotSupportedError(f'Not sure how to launch {game.info.media_type} yet')
	# TODO: Can also mount folders and zipped folders as hard drives, which will probably be useful for something
	# TODO: Use multiple floppy images

	cpu_requirement = game.info.specific_info.get('Minimum CPU')
	if cpu_requirement:
		# TODO: Validate this is 68000, 68010, 68(EC)020/030/040/060, 68(LC)040/060, 68040-NOMMU, 68060-NOMMU
		# TODO: --accelerator=bizzard-ppc or whichever one it is for PowerPC
		args.append(f'--cpu={cpu_requirement}')

	if game.info.specific_info.get('TV Type') == TVSystem.NTSC:
		args.append('--ntsc_mode=1')
	return LaunchCommand(emulator.exe_path, args)


def gbe_plus(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.platform.name == 'Game Boy':
		# In theory, only this should support Pocket Sonar (so far), but there's not really a way to detect that since it just claims to be MBC1 in the header...
		verify_supported_gb_mappers(
			game,
			{'MBC1', 'MBC2', 'MBC3', 'MBC5', 'MBC6', 'MBC7', 'Pocket Camera', 'HuC1'},
			{'MBC1 Multicart'},
		)
	return LaunchCommand(emulator.exe_path, [rom_path_argument])


def medusa(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.platform.name == 'DSi':
		raise EmulationNotSupportedError('DSi exclusive games and DSiWare not supported')
	if game.info.specific_info.get('Is iQue?', False):
		raise EmulationNotSupportedError('iQue DS not supported')

	if game.platform.name == 'Game Boy':
		verify_mgba_mapper(game)

	args = ['-f']
	if (game.platform.name != 'DS') and (
		not game.info.specific_info.get('Nintendo Logo Valid?', True)
	):
		# (for GB/GBA stuff only, otherwise BIOS is mandatory whether you like it or not)
		args.append('-C')
		args.append('useBios=0')

	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def melonds_check(game: 'ROMGame', _):
	if game.platform.name == 'DSi':
		raise EmulationNotSupportedError(
			"DSi is too experimental so let's say for all intents and purposes it doesn't work"
		)
	if game.info.specific_info.get('Is iQue?', False):
		# Maybe it is if you use an iQue firmware?
		raise EmulationNotSupportedError('iQue DS not supported')


def melonds(_, emulator: 'StandardEmulator') -> LaunchCommand:
	# No argument for fullscreen here yet
	# It looks like you can pass a GBA cart via the second argument, so that might get interesting

	return LaunchCommand(emulator.exe_path, [rom_path_argument])


def mgba_check(game: 'ROMGame', _):
	if game.platform.name == 'Game Boy':
		verify_mgba_mapper(game)


def mgba(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['-f']
	if not game.info.specific_info.get('Nintendo Logo Valid?', True):
		args.append('-C')
		args.append('useBios=0')
	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def mupen64plus(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.info.specific_info.get('ROM Format', None) == 'Unknown':
		raise EmulationNotSupportedError('Undetectable ROM format')

	args = ['--nosaveoptions', '--fullscreen']

	no_plugin = 1
	controller_pak = 2
	transfer_pak = 4
	rumble_pak = 5

	use_controller_pak = game.info.specific_info.get('Uses Controller Pak?', False)
	use_transfer_pak = game.info.specific_info.get('Uses Transfer Pak?', False)
	use_rumble_pak = game.info.specific_info.get('Force Feedback?', False)

	plugin = no_plugin

	if use_controller_pak and use_rumble_pak:
		plugin = (
			controller_pak
			if game.platform_config.options.get('prefer_controller_pak_over_rumble', False)
			else rumble_pak
		)
	elif use_controller_pak:
		plugin = controller_pak
	elif use_rumble_pak:
		plugin = rumble_pak
	elif use_transfer_pak:
		plugin = transfer_pak

	if plugin != no_plugin:
		# TODO: Only do this if using SDL plugin (i.e. not Raphnet raw plugin)
		args.extend(['--set', f'Input-SDL-Control1[plugin]={plugin}'])

	# TODO: If use_transfer_pak, put in a rom + save with --gb-rom-1 and --gb-ram-1 somehow... hmm... can't insert one at runtime with console UI (and I guess you're not supposed to hotplug carts with a real N64 + Transfer Pak) sooo, I'll have to have a think about the most user-friendly way for me to handle that as a frontend

	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def pokemini(_, emulator: 'StandardEmulator') -> LaunchCommand:
	return MultiLaunchCommands(
		[
			# TODO: Can there be some kind of "create this as the working directory if it doesn't exist" option in LaunchCommand instead?
			LaunchCommand(PurePath('mkdir'), ['-p', Path('~/.config/PokeMini').expanduser()]),
			LaunchCommand(PurePath('cd'), [Path('~/.config/PokeMini').expanduser()]),
		],
		LaunchCommand(emulator.exe_path, ['-fullscreen', rom_path_argument]),
		[],
	)


def pcsx2(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	args = ['--nogui', '--fullscreen']
	if game.rom.extension == 'elf':
		args.append('--elf=' + rom_path_argument)
	elif game.rom.extension == 'irx':
		# Presume this works? Never seen one in the wild
		args.append('--irx=' + rom_path_argument)
	else:
		args.append(rom_path_argument)

	# Put in --fullboot if certain games need it and can't be overriden otherwise
	return LaunchCommand(emulator.exe_path, args)


def ppsspp(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.info.specific_info.get('PlayStation Category') == 'UMD Video':
		raise EmulationNotSupportedError('UMD video discs not supported')

	return LaunchCommand(
		emulator.exe_path,
		[
			str(cast(FolderROM, game.rom).relevant_files['pbp'])
			if game.rom.is_folder
			else rom_path_argument
		],
	)


def reicast(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.info.specific_info.get('Uses Windows CE?', False):
		raise EmulationNotSupportedError('Windows CE-based games not supported')
	args = ['-config', 'x11:fullscreen=1']
	if not game.info.specific_info.get('Supports VGA?', True):
		# Use RGB component instead (I think that should be compatible with everything, and would be better quality than composite, which should be 1)
		args += ['-config', 'config:Dreamcast.Cable=2']
	else:
		# This shouldn't be needed, as -config is supposed to be temporary, but it isn't and writes the component cable setting back to the config file, so we'll set it back
		args += ['-config', 'config:Dreamcast.Cable=0']
	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


def rpcs3(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if not game.info.specific_info.get('Bootable?', True):
		raise NotActuallyLaunchableGameError(
			f'Cannot boot {game.info.specific_info.get("PlayStation Category", "this")}'
		)
	if (
		emulator_config.options.get('require_compat_entry', False)
		and 'RPCS3 Compatibility' not in game.info.specific_info
	):
		raise EmulationNotSupportedError('Not in compatibility DB')
	threshold = emulator_config.options.get('compat_threshold')
	if threshold:
		game_compat = game.info.specific_info.get('RPCS3 Compatibility')
		if game_compat and game_compat.value < threshold:
			raise EmulationNotSupportedError(
				f'Game ({game.name}) is only {game_compat.name} status'
			)

	# It's clever enough to boot folders specified as a path
	return LaunchCommand(emulator.exe_path, ['--no-gui', rom_path_argument])


def snes9x(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	slot = game.info.specific_info.get('Slot')
	if slot:
		# There are a few bootleg things that will not work
		if slot.endswith(('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col')):
			raise EmulationNotSupportedError(f'{slot} mapper not supported')

	expansion_chip = game.info.specific_info.get('Expansion Chip')
	if expansion_chip in {SNESExpansionChip.ST018, SNESExpansionChip.DSP_3}:
		# ST018 is implemented enough here to boot to menu, but hangs when starting a match
		# DSP-3 looks like it's going to work and then when I played around a bit and the AI was starting its turn (I think?) the game hung to a glitchy mess so I guess not
		raise EmulationNotSupportedError(f'{expansion_chip} not supported')
	return LaunchCommand(emulator.exe_path, [rom_path_argument])


def xemu(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	# Values yoinked from extract-xiso, I hope they don't mind
	global_lseek_offset = 0xFD90000
	xgd3_lseek_offset = 0x2080000
	xiso_header_offset = 0x10000
	xiso_string = b'MICROSOFT*XBOX*MEDIA'

	# Checking for this stuff inside the emulator-command-line-maker seems odd, but it doesn't make sense to make a metadata helper for it either
	rom = cast(FileROM, game.rom)
	size = rom.size
	good = False
	for possible_location in (
		xiso_header_offset,
		global_lseek_offset + xiso_header_offset,
		xgd3_lseek_offset + xiso_header_offset,
	):
		if size < possible_location:
			continue
		magic = rom.read(seek_to=possible_location, amount=20)
		if magic == xiso_string:
			good = True
			break
	if not good:
		raise EmulationNotSupportedError(
			'Probably a Redump-style dump, you need to extract the game partition'
		)
	# This still doesn't guarantee it'll be seen as a valid disc…

	return LaunchCommand(emulator.exe_path, ['-full-screen', '-dvd_path', rom_path_argument])


def yuzu(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	title_type = game.info.specific_info.get('Title Type')
	if title_type in {
		'Patch',
		'AddOnContent',
		SwitchContentMetaType.Patch,
		SwitchContentMetaType.AddOnContent,
	}:
		# If we used the .cnmt.xml, it will just be a string
		raise NotActuallyLaunchableGameError(f'Cannot boot a {title_type}')
	return LaunchCommand(emulator.exe_path, ['-f', '-g', rom_path_argument])


# Game engines
def prboom_plus(game: 'ROMGame', emulator: 'StandardEmulator') -> LaunchCommand:
	if game.info.specific_info.get('Is PWAD?', False):
		raise NotActuallyLaunchableGameError('Is PWAD and not IWAD')

	args = []
	save_dir = cast(Path | None, game.platform_config.options.get('save_dir'))
	if save_dir:
		args.append('-save')
		args.append(str(save_dir))

	args.append('-iwad')
	args.append(rom_path_argument)
	return LaunchCommand(emulator.exe_path, args)


# DOS/Mac stuff
def _macemu_args(
	app: 'MacApp', autoboot_txt_path: str, emulator: 'Emulator[MacApp]'
) -> LaunchCommand:
	args = []
	if not app.is_on_cd:
		args += ['--disk', str(app.hfv_path)]
	if 'max_resolution' in app.json:
		width, height = app.json['max_resolution']
		args += ['--screen', f'dga/{width}/{height}']

	if app.cd_path:
		args += ['--cdrom', str(app.cd_path)]
	for other_cd_path in app.other_cd_paths:
		args += ['--cdrom', str(other_cd_path)]

	app_path = app.info.specific_info.get('Carbon Path', app.path)
	pre_commands = [
		LaunchCommand(
			PurePath('sh'),
			['-c', f'echo {shlex.quote(app_path)} > {shlex.quote(autoboot_txt_path)}'],
		)  # Hack because I can't be fucked refactoring MultiCommandLaunchCommand to do pipey bois/redirecty bois
		# TODO: Actually could we just have a WriteAFileLaunchCommand or something
	]
	if 'max_bit_depth' in app.json:
		# --displaycolordepth doesn't work or doesn't do what I think it does, so we are setting depth from inside the thing instead
		# This requires some AppleScript extension known as GTQ Programming Suite until I one day figure out a better way to do this
		pre_commands += [
			LaunchCommand(
				PurePath('sh'),
				['-c', f'echo {app.json["max_bit_depth"]} >> {shlex.quote(autoboot_txt_path)}'],
			)
		]
	return MultiLaunchCommands(
		pre_commands,
		LaunchCommand(emulator.exe_path, args),
		[LaunchCommand(PurePath('rm'), [autoboot_txt_path])],
	)


def basilisk_ii(app: 'MacApp', emulator: 'Emulator[MacApp]') -> LaunchCommand:
	if app.info.specific_info.get('Architecture') == 'PPC':
		raise EmulationNotSupportedError('PPC not supported')
	if app.json.get('ppc_enhanced', False) and emulator_config.options.get(
		'skip_if_ppc_enhanced', False
	):
		raise EmulationNotSupportedError('PPC enhanced')

	# This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	# Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	shared_folder = None
	try:
		with Path('~/.basilisk_ii_prefs').expanduser().open('rt', encoding='utf-8') as f:
			for line in f:
				if line.startswith('extfs '):
					shared_folder = Path(line[6:-1])
					break
	except FileNotFoundError:
		pass
	if not shared_folder:
		raise EmulationNotSupportedError('You need to set up your shared folder first')

	autoboot_txt_path = str(shared_folder / 'autoboot.txt')
	return _macemu_args(app, autoboot_txt_path, emulator)


def sheepshaver(app: 'MacApp', emulator: 'Emulator[MacApp]') -> LaunchCommand:
	# This requires a script inside the Mac OS environment's startup items folder that reads "Unix:autoboot.txt" and launches whatever path is referred to by the contents of that file. That's ugly, but there's not really any other way to do it. Like, at all. Other than having separate bootable disk images. You don't want that. Okay, so I don't want that.
	# Ideally, HFS manipulation would be powerful enough that we could just slip an alias into the Startup Items folder ourselves and delete it afterward. That doesn't fix the problem of automatically shutting down (still need a script for that), unless we don't create an alias at all and we create a script or something on the fly that launches that path and then shuts down, but yeah. Stuff and things.
	shared_folder = None
	try:
		with Path('~/.sheepshaver_prefs').open('rt', encoding='utf-8') as f:
			for line in f:
				if line.startswith('extfs '):
					shared_folder = Path(line[6:-1])
					break
	except FileNotFoundError:
		pass
	if not shared_folder:
		raise EmulationNotSupportedError('You need to set up your shared folder first')

	autoboot_txt_path = str(shared_folder / 'autoboot.txt')

	return _macemu_args(app, autoboot_txt_path, emulator)


_mount_line_regex = re.compile(r'^MOUNT ([A-Z]) ')


def _last_unused_dosbox_drive(
	dosbox_config_path: Path, used_letters: 'Collection[str] | None' = None
) -> str:
	automounted_letters = []
	with dosbox_config_path.open('rt', encoding='utf-8') as f:
		found_autoexec = False
		for line in f:
			line = line.rstrip()
			if line == '[autoexec]':
				found_autoexec = True
				continue
			if found_autoexec:
				mount_line_match = _mount_line_regex.match(line)
				if mount_line_match:
					automounted_letters.append(mount_line_match[1])

	for letter in 'CDEFGHIJKLMNOPQRSTVWXY':
		if used_letters and letter in used_letters:
			continue
		if letter not in automounted_letters:
			return letter
	raise EmulationNotSupportedError(
		'Oh no you are automounting too many drives and we have no room for another one'
	)


def dosbox_staging(app: 'DOSApp', emulator: 'DOSBoxStaging') -> LaunchCommand:
	args = ['-fullscreen', '-exit']
	noautoexec = emulator.config.noautoexec.options['noautoexec']
	if noautoexec:
		args.append('-noautoexec')

	if 'required_hardware' in app.json:
		if 'for_xt' in app.json['required_hardware']:
			if app.json['required_hardware']['for_xt']:
				# machine=cga?
				cycles_for_about_477 = emulator_config.options['cycles_for_477_mhz']
				args += ['-c', f'config -set "cpu cycles {cycles_for_about_477}"']

		if 'max_graphics' in app.json['required_hardware']:
			graphics = app.json['required_hardware']['max_graphics']
			machine = 'svga_s3' if graphics == 'svga' else graphics
			args += ['-machine', machine]

	drive_letter = 'C'
	cd_drive_letter = 'D'

	if not noautoexec:
		config_file_location = Path('~/.config/dosbox/dosbox-staging.conf').expanduser()
		try:
			cd_drive_letter = _last_unused_dosbox_drive(config_file_location, ['C'])
			drive_letter = _last_unused_dosbox_drive(
				config_file_location, ['C', cd_drive_letter] if app.cd_path else None
			)
		except OSError:
			pass

	overlay_path = cast(Path | None, emulator_config.options['overlay_path'])

	if app.cd_path:
		# I hope you don't put double quotes in the CD paths (not sure what the proper way to do that would be anyway? 999 layers of escaping?)
		imgmount_args = f'"{app.cd_path}"'
		if app.other_cd_paths:
			imgmount_args += ' ' + ' '.join(f'"{cd_path}"' for cd_path in app.other_cd_paths)
		args += ['-c', f'IMGMOUNT -ro {cd_drive_letter} -t cdrom {imgmount_args}']

	ensure_exist_command = None  # Used to ensure overlay dir exists… hmm
	if app.is_on_cd:
		app_exec = app.path
		if app.args:
			app_exec += ' ' + ' '.join(shlex.quote(arg) for arg in app.args)
		args += ['-c', cd_drive_letter + ':', '-c', app_exec, '-c', 'exit']
	elif drive_letter == 'C' and not overlay_path:
		args.append(app.path)
	else:
		# Gets tricky if autoexec already mounts a C drive because launching something from the command line normally that way just assumes C is a fine drive to use
		# This also makes exit not work normally
		host_folder, exe_name = os.path.split(app.path)
		args += '-c', f'MOUNT {drive_letter} "{host_folder}"'
		if overlay_path:
			overlay_subfolder = overlay_path.joinpath(app.name)
			ensure_exist_command = LaunchCommand(
				PurePath('mkdir'), ['-p', str(overlay_subfolder.resolve())]
			)
			args += ['-c', f'MOUNT -t overlay {drive_letter} "{overlay_subfolder.resolve()!s}"']
		args += ['-c', drive_letter + ':']
		if app.args:
			args += ['-c', exe_name + ' ' + ' '.join(shlex.quote(arg) for arg in app.args)]
		else:
			args += ['-c', exe_name]
		args += ['-c', 'exit']

	launch_command = LaunchCommand(emulator.exe_path, args)
	if ensure_exist_command:
		return MultiLaunchCommands([ensure_exist_command], launch_command, [])
	return launch_command


def dosbox_x(app: 'DOSApp', emulator: 'Emulator[DOSApp]') -> LaunchCommand:
	confs = {}

	if app.is_on_cd:
		raise EmulationNotSupportedError('This might not work from CD I think unless it does')
	# TODO: Does this even support -c? I can't remember

	if 'required_hardware' in app.json:
		if 'for_xt' in app.json['required_hardware']:
			if app.json['required_hardware']['for_xt']:
				# confs['cputype'] = '8086'
				# This doesn't even work anyway, it's just the best we can do I guess
				confs['machine'] = 'cga'
				confs['cycles'] = 'fixed 315'

		if 'max_graphics' in app.json['required_hardware']:
			graphics = app.json['required_hardware']['max_graphics']
			confs['machine'] = 'svga_s3' if graphics == 'svga' else graphics

	args = ['-exit', '-noautoexec', '-fullscreen', '-fastlaunch']
	for k, v in confs.items():
		args.append('-set')
		args.append(f'{k}={v}')

	return LaunchCommand(emulator.exe_path, [*args, app.path])


# Libretro frontends
def retroarch(
	_, __, core_config: 'EmulatorConfig', frontend_config: 'EmulatorConfig'
) -> LaunchCommand:
	return LaunchCommand(
		frontend_config.exe_path, ['-f', '-L', str(core_config.exe_path), rom_path_argument]
	)


# Libretro cores
# Note that these only ever check things
def genesis_plus_gx(game: 'ROMGame', _) -> None:
	if game.platform.name == 'Mega CD' and game.info.specific_info.get('32X Only?', False):
		raise EmulationNotSupportedError('32X not supported')


def blastem(game: 'ROMGame', _) -> None:
	if game.platform.name == 'Mega Drive':
		if game.info.specific_info.get('Expansion Chip', None) == 'SVP':
			# This should work, but doesn't?
			raise EmulationNotSupportedError('Seems SVP chip not supported?')
		mapper = game.info.specific_info.get('Mapper')
		if mapper and mapper not in {
			# Some probably only work with rom.db being there, this assumes it is
			# Some bootleg mappers don't seem to have any indication that they should work but seem to
			'EEPROM',
			'J-Cart',
			'J-Cart + EEPROM',
			'ssf2',
			'cslam',
			'hardbl95',
			'blara',
			'mcpir',
			'realtec',
			'sbubl',
			'squir',
			'elfwor',
			'kof99',
			'smouse',
			'sk',
		}:
			raise EmulationNotSupportedError(mapper)


def mesen(game: 'ROMGame', _) -> None:
	unsupported_mappers = {124, 237, 256, 257, 389}
	unsupported_mappers.update(
		{
			271,
			295,
			308,
			315,
			322,
			327,
			335,
			337,
			338,
			339,
			340,
			341,
			342,
			344,
			345,
			350,
			524,
			525,
			526,
			527,
			528,
		}
	)  # if I am reading MapperFactory.cpp correctly these are explicitly unsupported?
	unsupported_mappers.update({267, 269, 270, 272, 273})
	unsupported_mappers.update(range(275, 283))
	unsupported_mappers.update(
		{291, 293, 294, 296, 297, 310, 311, 316, 318, 321, 330, 334, 343, 347}
	)
	unsupported_mappers.update(range(351, 366))
	unsupported_mappers.update(range(367, 513))
	unsupported_mappers.update({514, 515, 516, 517, 520, 523})
	# I guess 186 (StudyBox) might also count as unsupported but it's meant to be a BIOS
	# Also Mindkids 143-in-1 but I'm not sure what number that is/what the UNIF name is
	unsupported_unif_mappers = [
		'KONAMI-QTAI',
		' BMC-10-24-C-A1',
		'BMC-13in1JY110',
		'BMC-81-01-31-C',
		'UNL-KS7010',
		'UNL-KS7030',
		'UNL-OneBus',
		'UNL-PEC-586',
		'UNL-SB-2000',
		'UNL-Transformer',
		'WAIXING-FS005',
	]
	if game.info.specific_info.get('Header Format', None) in {'iNES', 'NES 2.0'}:
		mapper = game.info.specific_info.get('Mapper Number')
		assert isinstance(
			mapper, int
		), 'Somehow, Mapper Number was set to something other than an int, or None'
		if mapper in unsupported_mappers or mapper > 530:
			raise EmulationNotSupportedError(
				f'Unsupported mapper: {mapper} ({game.info.specific_info.get("Mapper")})'
			)
	if game.info.specific_info.get('Header Format', None) == 'UNIF':
		mapper = game.info.specific_info.get('Mapper')
		if mapper in unsupported_unif_mappers:
			raise EmulationNotSupportedError(f'Unsupported mapper: {mapper}')


def prosystem(game: 'ROMGame', _) -> None:
	if not game.info.specific_info.get('Headered?', False):
		# Seems to support unheadered if and only if in the internal database? Assume it isn't otherwise that gets weird
		raise EmulationNotSupportedError('No header')


def bsnes_libretro(game: 'ROMGame', emulator: 'BsnesLibretro') -> None:
	if game.platform.name == 'Game Boy':
		colour_flag = game.info.specific_info.get('Is Colour?', GameBoyColourFlag.No)
		if colour_flag == GameBoyColourFlag.Required:
			raise EmulationNotSupportedError('Super Game Boy is not compatible with GBC-only games')
		if colour_flag == GameBoyColourFlag.Yes and emulator.config.sgb_incompatible_with_gbc:
			raise EmulationNotSupportedError(
				'We do not want to play a colour game with a Super Game Boy'
			)
		if emulator.config.sgb_enhanced_only and not game.info.specific_info.get(
			'SGB Enhanced?', False
		):
			raise EmulationNotSupportedError(
				'We do not want to play a non-SGB enhanced game with a Super Game Boy'
			)

		# Pocket Camera is also supported by the SameBoy core, but I'm leaving it out here because bsnes doesn't do the camera
		verify_supported_gb_mappers(game, {'MBC1', 'MBC2', 'MBC3', 'MBC5', 'HuC1', 'HuC3'}, set())
		return

	if game.rom.extension == 'st':
		raise EmulationNotSupportedError('No Sufami Turbo for libretro core')

	slot = game.info.specific_info.get('Slot')
	# Presume this is the same as with standalone
	if slot and slot.endswith(('_bugs', '_pija', '_poke', '_sbld', '_tekken2', '_20col')):
		raise EmulationNotSupportedError(f'{slot} mapper not supported')

def picodrive_libretro(game: 'ROMGame', _):
	mapper = game.info.specific_info.get('Mapper')
	if mapper and mapper in {'pokestad', 'lion3'}:
		raise EmulationNotSupportedError(f'{mapper} not supported')