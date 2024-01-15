from pathlib import Path
from typing import TYPE_CHECKING

import meowlauncher.games.specific_behaviour.emulator_command_lines as command_lines
from meowlauncher.emulator import (
	BaseEmulatorConfig,
	Emulator,
	EmulatorStatus,
	LibretroCore,
	LibretroFrontend,
	StandardEmulator,
)
from meowlauncher.emulator_helpers import (
	BaseMAMEDriverConfig,
	mame_driver,
	mednafen_module,
	simple_gb_emulator,
	simple_mega_drive_emulator,
	standalone_emulator,
	vice_emulator,
)
from meowlauncher.exceptions import EmulationNotSupportedError
from meowlauncher.games.dos import DOSApp
from meowlauncher.games.mac import MacApp
from meowlauncher.launch_command import LaunchCommand, rom_path_argument
from meowlauncher.runner import HostPlatform

from .format_info import (
	atari_2600_cartridge_extensions,
	generic_cart_extensions,
	mame_cdrom_formats,
	mame_floppy_formats,
)

if TYPE_CHECKING:
	from collections.abc import Collection, Sequence

	from meowlauncher.emulated_game import EmulatedGame
	from meowlauncher.game import Game
	from meowlauncher.games.mame.mame_game import ArcadeGame
	from meowlauncher.games.roms.rom_game import ROMGame


class BsnesConfig(BaseEmulatorConfig):
	"""Options for all variants of bsnes (standalone, bsnes-hd beta, libretro cores)"""

	@classmethod
	def section(cls) -> str:
		return 'bsnes'

	@classmethod
	def prefix(cls) -> str:
		return 'bsnes'

	@classmethod
	def config_file_name(cls) -> str:
		return 'emulators'

	sgb_incompatible_with_gbc: bool = True
	'Consider Super Game Boy as incompatible with carts with any GBC compatibility, even if they are DMG compatible'

	sgb_enhanced_only: bool = False
	'Consider Super Game Boy to only support games that are specifically enhanced for it'


class DuckStationConfig(BaseEmulatorConfig):
	@classmethod
	def section(cls) -> str:
		return 'DuckStation'

	@classmethod
	def prefix(cls) -> str:
		return 'duckstation'

	@classmethod
	def config_file_name(cls) -> str:
		return 'emulators'

	compatibility_xml_path: Path | None = None
	'Path to where compatibility.xml is installed'
	# Could this be autodetected?

	gamedb_path: Path | None = None
	'Path to where gamedb.json is installed'

	compatibility_threshold: int = 2
	"Don't try and launch any game with this compatibility rating or lower"
	consider_unknown_games_incompatible: bool = False
	"Consider games incompatible if they aren't in the compatibility database at all"


class RPCS3Config(BaseEmulatorConfig):
	require_compat_entry: bool = False
	'Do not make launchers for games which are not in the compatibility database at all'
	compat_threshold: int = 0
	'Games that are under this level of compatibility will not get launchers made; 1 = Loadable 2 = Intro 3 = Ingame 4 = Playable (all the way through)'
	# TODO: Take RPCS3Compatibility out of ps3.py and use that


class MAMEGameBoyConfig(BaseMAMEDriverConfig):
	use_gbc_for_dmg: bool = True
	"""Use MAME GBC driver for DMG games"""
	prefer_sgb_over_gbc: bool = False
	'If a game is both SGB and GBC enhanced, use MAME SGB driver instead of GBC'


class DuckStation(StandardEmulator):
	config: DuckStationConfig

	@classmethod
	def exe_name(cls) -> str:
		return 'duckstation-qt'

	@classmethod
	def supported_extensions(cls) -> 'Collection[str]':
		return {'bin', 'img', 'cue', 'chd', 'exe', 'm3u', 'iso'}

	@classmethod
	def config_class(cls) -> type[DuckStationConfig]:
		return DuckStationConfig

	def check_game(self, game: 'ROMGame') -> None:
		if (
			self.config.consider_unknown_games_incompatible
			and 'DuckStation Compatibility' not in game.info.specific_info
		):
			raise EmulationNotSupportedError('Not in compatibility DB')
		threshold = self.config.compatibility_threshold
		if threshold:
			game_compat = game.info.specific_info.get('DuckStation Compatibility')
			if game_compat and game_compat < threshold:
				raise EmulationNotSupportedError(f'Game is only {game_compat.name} status')
		super().check_game(game)

	def get_game_command(self, _) -> LaunchCommand:
		return LaunchCommand(self.exe_path, ['-batch', '-fullscreen', rom_path_argument])


standalone_emulators: 'Collection[type[StandardEmulator]]' = {
	# TODO: A lot of info in the comments is very probably out of date
	standalone_emulator(
		'A7800', 'a7800', command_lines.a7800, {'bin', 'a78'}, {'7z', 'zip'}
	),  # Forked directly from MAME with alterations to a7800.cpp driver, so will more or less work the same way as that. Executable name might be a7800.Linux-x86_64 depending on how it's installed... hmm
	standalone_emulator(
		'bsnes',
		'bsnes',
		command_lines.bsnes,
		{'sfc', 'smc', 'st', 'bs', 'gb', 'gbc'},
		{'7z', 'zip'},
		config_class=BsnesConfig,
	),
	standalone_emulator(
		'cxNES', 'cxnes', command_lines.cxnes, {'nes', 'fds', 'unf', 'unif'}, {'7z', 'zip'}
	),  # Or is it good? Have not tried it in a fair bit
	standalone_emulator(
		'Dolphin',
		'dolphin-emu',
		command_lines.dolphin,
		{'iso', 'ciso', 'gcm', 'gcz', 'tgc', 'elf', 'dol', 'wad', 'wbfs', 'm3u', 'wia', 'rvz', '/'},
		check_game_func=command_lines.dolphin_check,
	),
	DuckStation,
	standalone_emulator(
		'Flycast',
		'flycast',
		['-config', 'window:fullscreen=yes', rom_path_argument],
		{'gdi', 'cdi', 'chd', 'cue'},
	),
	standalone_emulator(
		'FS-UAE', 'fs-uae', command_lines.fs_uae, {'iso', 'cue', 'adf', 'ipf', 'lha'}
	),  # Note that .ipf files need a separately downloadable plugin. We could detect the presence of that, I guess
	simple_gb_emulator(
		# --gba-cgb-mode[=0] and --force-dmg-mode[=0] may be useful in obscure situations, but that would probably require a specific thing that notes some GBC games are incompatible with GBA mode (Pocket Music) or GB incompatible with GBC (R-Type, also Pocket Sonar but that wouldn't work anyway)
		# I guess MBC1 Multicart only works if you tick the "Multicart compatibility" box
		# MMM01 technically works but only boots the first game instead of the menu, so it doesn't really work work
		'Gambatte',
		'gambatte_qt',
		['--full-screen', rom_path_argument],
		{'MBC1', 'MBC2', 'MBC3', 'HuC1', 'MBC5'},
		{'MBC1 Multicart'},
		{'gb', 'gbc'},
		{'zip'},
	),
	standalone_emulator('GBE+', 'gbe_plus_qt', command_lines.gbe_plus, {'gb', 'gbc', 'gba'}),
	# In theory, only this should support Pocket Sonar (so far), but there's not really a way to detect that since it just claims to be MBC1 in the header...
	# Also in theory recognizes any extension and assumes Game Boy if not .gba or .nds, but that would be screwy
	simple_mega_drive_emulator(
		'Kega Fusion',
		'kega-fusion',
		['-fullscreen', rom_path_argument],
		{
			'aqlian',
			'sf002',
			'sf004',
			'smw64',
			'topf',
			'kof99',
			'cjmjclub',
			'pokestad',
			'soulb',
			'chinf3',
		},
		{'bin', 'gen', 'md', 'smd', 'sgd', 'gg', 'sms', 'iso', 'cue', 'sg', 'sc', '32x'},
		{'zip'},
	),
	# rom_kof99: Pocket Monsters does work (game-specific hack, probably?), which is why in platform_info/megadrive I've treated it specially and called it rom_kof99_pokemon
	# May support other CD formats for Mega CD other than iso, cue? Because it's closed source, can't really have a look, but I'm just going to presume it's only those two
	standalone_emulator(
		'mGBA',
		'mgba-qt',
		command_lines.mgba,
		{'gb', 'gbc', 'gba', 'srl', 'bin', 'mb', 'gbx'},
		{'7z', 'zip'},
	),  # Doesn't really do GBX but it will ignore the footer
	standalone_emulator(
		'melonDS', 'melonDS', command_lines.melonds, {'nds', 'srl'}
	),  # Supports .dsi too, but I'm acting as though it doesn't, because it's too screwy
	standalone_emulator(
		'Mupen64Plus', 'mupen64plus', command_lines.mupen64plus, {'z64', 'v64', 'n64'}
	),
	standalone_emulator(
		'PCSX2', 'pcsx2', command_lines.pcsx2, {'iso', 'cso', 'bin', 'elf', 'irx', 'chd'}, {'gz'}
	),  # Only reads the bin of bin/cues and not the cue
	standalone_emulator(
		'Pico-8', 'pico8', ['-windowed', '0', '-run', rom_path_argument], {'p8', 'p8.png'}
	),
	standalone_emulator(
		'PokeMini', 'PokeMini', command_lines.pokemini, {'min'}, {'zip'}
	),  # Normally just puts the config files in the current directory, so this cd's to ~/.config/PokeMini first
	standalone_emulator('PPSSPP', 'ppsspp-qt', command_lines.ppsspp, {'iso', 'pbp', 'cso', '/'}),
	standalone_emulator('Reicast', 'reicast', command_lines.reicast, {'gdi', 'cdi', 'chd'}),
	standalone_emulator(
		'Ruffle', 'ruffle', None, {'swf'}, status=EmulatorStatus.Imperfect
	),  # No way to start off in fullscreen…
	standalone_emulator(
		'SimCoupe',
		'simcoupe',
		['-fullscreen', 'yes', rom_path_argument],
		{'mgt', 'sad', 'dsk', 'sbt'},
		{'zip', 'gz'},
	),
	standalone_emulator(
		'Snes9x', 'snes9x-gtk', command_lines.snes9x, {'sfc', 'smc', 'swc'}, {'zip', 'gz'}
	),  # Can't set fullscreen mode from the command line so you have to set up that yourself (but it will do that automatically); GTK port can't do Sufami Turbo or Satellaview from command line due to lacking multi-cart support that Windows has (Unix non-GTK doesn't like being in fullscreen etc)
	standalone_emulator(
		# TODO: This will need to be moved out of this list and made into a normal class so Atari 2600 info can use it (and it can have a listrominfo() function)
		'Stella',
		'stella',
		['-fullscreen', '1', rom_path_argument],
		{'a26', 'bin', 'rom'}.union(atari_2600_cartridge_extensions),
		{'gz', 'zip'},
	),
	standalone_emulator(
		# Joystick support not so great, otherwise it plays perfectly well with keyboard.union(mouse); except the other issue where it doesn't really like running in fullscreen when more than one monitor is around (to be precise, it stops that second monitor updating). Can I maybe utilize some kind of wrapper?  I guess it's okay because it's not like I don't have a mouse and keyboard though the multi-monitor thing really is not okay
		'PrBoom+',
		'prboom-plus',
		command_lines.prboom_plus,
		{'wad'},
		status=EmulatorStatus.Janky,
	),
	standalone_emulator(
		'Cemu',
		'Cemu.exe',
		command_lines.cemu,
		{'wud', 'wux', 'rpx', '/'},
		host_platform=HostPlatform.Windows,
		status=EmulatorStatus.Experimental,
	),
	standalone_emulator(
		'Citra',
		'citra-qt',
		command_lines.citra,
		{'3ds', 'cxi', '3dsx'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	# No fullscreen from command line
	standalone_emulator(
		'Medusa',
		'medusa-emu-qt',
		command_lines.medusa,
		{'nds', 'gb', 'gbc', 'gba'},
		{'7z', 'zip'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	standalone_emulator(
		'RPCS3',
		'rpcs3',
		command_lines.rpcs3,
		{'/', 'elf', 'self', 'bin'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
		config_class=RPCS3Config,
	),
	standalone_emulator(
		'Xemu', 'xemu', command_lines.xemu, {'iso'}, status=EmulatorStatus.Experimental
	),  # Requires the game partition to be separated out of the disc image
	standalone_emulator(
		'Yuzu',
		'yuzu',
		command_lines.yuzu,
		{'xci', 'nsp', 'nro', 'nso', 'nca', 'elf', 'kip'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	vice_emulator('C64', 'x64sc', command_lines.vice_c64),
	# x64 and x64sc have the same command line structure, just different exe names
	vice_emulator('C64 Fast', 'x64', command_lines.vice_c64),
	vice_emulator('VIC-20', 'xvic', command_lines.vice_vic20),
	vice_emulator('Commodore PET', 'xpet', command_lines.vice_pet),
	vice_emulator('Plus/4', 'xplus4', command_lines.vice_plus4),
	vice_emulator('C128', 'x128', command_lines.vice_c128),
	mednafen_module(
		# Seems fine but no Apple IIe/128K?
		'Apple II',
		{'woz', 'dsk', 'po', 'do', 'd13', '2mg'},
		'apple2',
		check_game_func=command_lines.mednafen_apple_ii_check,
	),
	mednafen_module(
		'Lynx', {'lnx', 'o'}, command_lines.mednafen_lynx
	),  # Based on Handy, but that hasn't been updated in 14 years, so I guess this probably has some more updates
	mednafen_module(
		'Neo Geo Pocket', {'ngp', 'npc', 'ngc'}, 'ngp'
	),  # Based off NeoPop, which hasn't been updated in 15 years, so presumably with improvements. Does say that this is unsuitable for homebrew development (due to lack of accuracy) and MAME is more suitable for that, so believe that if you want
	mednafen_module('NES', {'nes', 'fds', 'unf'}, command_lines.mednafen_nes),
	# Based off FCEU, so not quite cycle-accurate but it works
	mednafen_module('PC Engine', {'pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u'}, 'pce'),
	mednafen_module(
		# Do NOT specify a FX-SCSI BIOS
		'PC-FX',
		{'iso', 'cue', 'toc', 'ccd', 'm3u'},
		'pcfx',
	),
	mednafen_module('PlayStation', {'iso', 'cue', 'exe', 'toc', 'ccd', 'm3u', 'psx'}, 'psx'),
	mednafen_module('Virtual Boy', {'bin', 'vb', 'vboy'}, 'vb'),
	mednafen_module(
		'WonderSwan', {'ws', 'wsc', 'bin', 'pc2'}, 'wswan'
	),  # Based on Cygne, definitely heavily modified by now
	mame_driver(
		'Amstrad GX4000', ('gx4000', 'cart'), {'bin', 'cpr'}, status=EmulatorStatus.Imperfect
	),
	# MT06201 (issue with emulated monochrome monitor), MT6509 lists various compatibility issues
	mame_driver('APF-MP1000', ('apfm1000', 'cart'), {'bin'}),
	mame_driver(
		'Apple II',
		command_lines.mame_apple_ii,
		mame_floppy_formats.union({'nib', 'do', 'po', 'woz', '2mg'}),
	),  # nib support only >= 0.229
	mame_driver(
		'Apple IIgs',
		('apple2gsr1', 'flop3'),
		mame_floppy_formats.union({'2mg', '2img', 'dc', 'woz'}),
		slot_options={'gameio': 'joy'},
		has_keyboard=True,
	),
	# Rev 1 is needed because some stuff doesn't work on rev 3 (happens in real life), flop1 and flop2 are for Apple II-not-GS software
	# ramsize can go up to 8M if need be and there are a lot of slot options (4play might be useful for our 1337 pro gaming purposes? arcbd sounds cool?)
	mame_driver(
		'Apple III', ('apple3', 'flop1'), mame_floppy_formats.union({'do', 'po'}), has_keyboard=True
	),
	mame_driver('Arcadia 2001', ('arcadia', 'cart'), {'bin'}),
	# Can also use bndarc for Bandai version but that doesn't seem to make any difference at all
	# MT06642: Wrong background colours
	mame_driver('Astrocade', ('astrocde', 'cart'), {'bin'}, slot_options={'exp': 'rl64_ram'}),
	# There's a keypad there which is used for game selection/setup, otherwise it just uses a paddle with a button (the actual controllers IRL were wacky, but for emulation purposes are otherwise pretty normal).  Hopefully adding that RAM expansion won't hurt?  Some games (Chicken) seem to be broken anyway with expansion or without whoops
	mame_driver(
		'Atari 2600',
		command_lines.mame_atari_2600,
		{'bin', 'a26'},
		check_func=command_lines.mame_atari_2600_check,
	),
	mame_driver(
		'Atari 5200',
		('a5200', 'cart'),
		{'bin', 'rom', 'car', 'a52'},
		status=EmulatorStatus.Imperfect,
	),
	# Could use -sio casette -cass *.wav if there was ever a game that came as a .wav which apparently could be a thing in theory (or is that just there because Atari 8-bit computers can do that)
	# MT06972: Nondescript input issues; MT07248: Galaxian doesn't work
	mame_driver(
		'Atari 7800',
		command_lines.mame_atari_7800,
		{'a78'},
		check_func=command_lines.mame_atari_7800_check,
	),
	mame_driver('Atari 8-bit', command_lines.mame_atari_8bit, {'bin', 'rom', 'car', 'atr', 'dsk'}),
	# Has issues with XEGS carts that it should be able to load (because they do run on the real system) but it says it doesn't because they should be run on XEGS instead, and then doesn't support a few cart types anyway; otherwise fine
	mame_driver('Bandai Super Vision 8000', ('sv8000', 'cart'), {'bin'}),
	mame_driver('BBC Bridge Companion', ('bbcbc', 'cart'), {'bin'}),
	mame_driver('Casio PV-1000', ('pv1000', 'cart'), {'bin'}),
	mame_driver('Champion 2711', ('unichamp', 'cart'), generic_cart_extensions),
	mame_driver('Channel F', ('channelf', 'cart'), {'bin', 'chf'}),
	mame_driver('ColecoVision', command_lines.mame_colecovision, {'bin', 'col', 'rom'}),
	# MT06554: Roller controller is inaccurate
	mame_driver(
		'Coleco Adam', command_lines.mame_coleco_adam, {'wav', 'ddp'}.union(mame_floppy_formats)
	),
	# Both disks and tapes autoboot. Woohoo!
	mame_driver(
		'Entex Adventure Vision', ('advision', 'cart'), {'bin'}, status=EmulatorStatus.Imperfect
	),
	mame_driver('FM-7', ('fm77av', 'flop1'), mame_floppy_formats, has_keyboard=True),
	# Tapes work, but they require run"" and then pressing play on the tape, the latter not being Lua-autoboot-scriptable yet.
	# Difference between fm7 and fmnew7 seems to be that the latter boots into BASIC by default (there's dip switches involved) instead of DOS, which seems to be required for tapes to work; and disks just autoboot anyway. FM-77AV is used here despite its allegedly imperfect graphics as there are games which won't work on earlier systems and there doesn't seem to be a programmatic way to tell, and it seems backwards compatibility is fine
	# Joystick only works with fm7/fmnew7 -centronics dsjoy... whoops; not sure what the builtin joystick does then
	mame_driver('G7400', ('g7400', 'cart'), {'bin', 'rom'}),
	# There is also an unreleased odyssey3 prototype if that is useful for USA (presumably unreleased) games, also jotac for France
	# Should this be merged with Odyssey 2 if it's compatible like that?
	mame_driver('Gamate', ('gamate', 'cart'), {'bin'}),
	mame_driver(
		'Game Boy',
		command_lines.mame_game_boy,
		{'bin', 'gb', 'gbc'},
		MAMEGameBoyConfig,
		EmulatorStatus.Imperfect,
	),
	# This supports some bootleg mappers that other emus tend to not; fails on really fancy tricks like the Demotronic trick (it does run the demo, but the effect doesn't look right); and has sound issues with GBC (MT06441, MT04949)
	# There are comments in the source file that point out that Super Game Boy should be part of the snes driver with the BIOS cart inserted, rather than a separate system, so that might not exist in the future
	mame_driver('Game.com', ('gamecom', 'cart1'), {'bin', 'tgc'}),
	# I don't know what the other cart slot does, or if you can use two at once, or how that would work if you could. Hopefully I don't need it for anything.
	mame_driver('Game Gear', command_lines.mame_game_gear, {'bin', 'gg'}),
	mame_driver('Epoch Game Pocket Computer', ('gamepock', 'cart'), {'bin'}),
	mame_driver('GBA', ('gba', 'cart'), {'bin', 'gba'}),
	# Does not let you do GBA-enhanced GBC games
	mame_driver(
		'IBM PCjr', command_lines.mame_ibm_pcjr, mame_floppy_formats.union({'img', 'bin', 'jrc'})
	),
	mame_driver('Intellivision', command_lines.mame_intellivision, {'bin', 'int', 'rom', 'itv'}),
	mame_driver(
		'Jupiter Ace',
		('jupace', 'dump'),
		{'ace'},
		slot_options={'ramsize': '48K'},
		has_keyboard=True,
	),
	mame_driver('Lynx', command_lines.mame_lynx, {'lnx', 'lyx', 'o'}),
	# Could be weird where rotation is involved
	mame_driver('Magnavox Odyssey²', command_lines.mame_odyssey2, {'bin', 'rom'}),
	mame_driver('Master System', command_lines.mame_master_system, {'bin', 'sms'}),
	mame_driver('Mattel Juice Box', ('juicebox', 'memcard'), {'smc'}),
	mame_driver('Mega Drive', command_lines.mame_megadrive, {'bin', 'md', 'smd', 'gen'}),
	mame_driver('Mega Duck', ('megaduck', 'cart'), {'bin'}),
	mame_driver('Memorex VIS', ('vis', 'cdrom'), mame_cdrom_formats),
	mame_driver('MSX', command_lines.mame_msx1, generic_cart_extensions.union(mame_floppy_formats)),
	mame_driver(
		'MSX2', command_lines.mame_msx2, generic_cart_extensions.union(mame_floppy_formats)
	),
	mame_driver(
		'MSX2+', command_lines.mame_msx2plus, generic_cart_extensions.union(mame_floppy_formats)
	),
	mame_driver('Neo Geo CD', ('neocdz', 'cdrom'), mame_cdrom_formats),
	# Don't think it has region lock so I should never need to use neocdzj? (neocd doesn't work, apparently because it thinks it has the drive tray open constantly)
	mame_driver('Neo Geo Pocket', ('ngpc', 'cart'), {'bin', 'ngp', 'npc', 'ngc'}),
	mame_driver('NES', command_lines.mame_nes, {'nes', 'unf', 'unif', 'fds'}),
	# Supports a lot of mappers actually, probably not as much as Mesen or puNES would, but it's up there; also a lot of cool peripherals
	mame_driver('Nichibutsu My Vision', ('myvision', 'cart'), {'bin'}),
	mame_driver('PC Engine', command_lines.mame_pc_engine, {'pce', 'bin', 'sgx'}),
	mame_driver(
		'SAM Coupé',
		('samcoupe', 'flop1'),
		mame_floppy_formats,
		autoboot_script='sam_coupe',
		has_keyboard=True,
	),
	mame_driver(
		'SG-1000',
		command_lines.mame_sg1000,
		{'bin', 'sg', 'sc', 'sf', 'sf7'}.union(mame_floppy_formats),
	),
	mame_driver(
		'Sharp X1', ('x1turbo40', 'flop1'), mame_floppy_formats.union({'2d'}), has_keyboard=True
	),
	# x1turbo doesn't work, and I'm not sure what running x1 over x1turbo40 would achieve (hope there's no compatibility shenanigans)
	mame_driver(
		# It doesn't really support m3u, but I'm going to make it so it does (multi-disk games seem fairly common)
		# All the other models of X68000 (x68030, x68ksupr, x68kxvi) don't work yet
		'Sharp X68000',
		command_lines.mame_sharp_x68000,
		mame_floppy_formats.union({'xdf', 'hdm', '2hd', 'dim', 'm3u'}),
	),
	mame_driver('SNES', command_lines.mame_snes, {'sfc', 'bs', 'st', 'smc', 'swc'}),
	mame_driver('Sord M5', command_lines.mame_sord_m5, {'bin'}),
	mame_driver('Super Cassette Vision', command_lines.mame_super_cassette_vision, {'bin'}),
	mame_driver('SVI-3x8', ('svi328', 'cart'), {'bin', 'rom'}),
	mame_driver('Squale', ('squale', 'cart'), {'bin'}, has_keyboard=True),
	mame_driver('Tandy CoCo', ('coco3', 'cart'), {'ccc', 'rom', 'bin'}, has_keyboard=True),
	# There is a coco3p, but it apparently runs at 60Hz too, so I'm not sure if it's needed
	mame_driver(
		'Thomson MO5', ('mo5', 'flop1'), {'fd', 'sap'}.union(mame_floppy_formats), has_keyboard=True
	),
	# Cartridges do not work (or on MO6) but floppies do autoboot, cassettes do not like to load either (would need to type LOAD and enter but then it plays it for you, but then stops because I guess it's broken) (MO6 is broken as well); qd would not work without setting the floppy type to quad density in Machine Configuration which we cannot do programmatically
	# Use mo5e for export version or mo5nr for network version (I don't know what they would be useful for)
	mame_driver(
		'Tomy Tutor', ('tutor', 'cart'), {'bin'}, has_keyboard=True, autoboot_script='tomy_tutor'
	),
	# There is pyuuta if you want to read Japanese instead
	mame_driver('VC 4000', ('vc4000', 'cart'), {'bin', 'rom'}),
	# There's like 30 different clones of this, and most of them aren't even clones in the MAME sense, they're literally hardware clones. But they're apparently all software-compatible, although the cartridges aren't hardware-compatible, they just contain the same software... so this all gets confusing. Anyway, the software list with all these is named "vc4000" so I guess that's the "main" one, so we'll use that. Seems that all models use 50Hz display so there shouldn't need to be model switching based on TV type
	# TODO: Quickload slot (.pgm, .tvc)
	mame_driver('Vectrex', ('vectrex', 'cart'), {'bin', 'gam', 'vec'}),
	# Includes overlays as selectable artwork, but that has to be done by the user from the menu
	mame_driver(
		'VIC-10',
		('vic10', 'cart'),
		{'crt', '80', 'e0'},
		has_keyboard=True,
		slot_options={'joy1': 'joy', 'joy2': 'joy'},
	),
	# More similar to the C64 (works and performs just as well as that driver) than the VIC-20, need to plug a joystick into both ports because once again games can use either port and thanks I hate it. At least there's only one TV type
	# Sometimes I see this called the Commodore MAX Machine or Ultimax or VC-10, but... well, I'm not sure where the VIC-10 name comes from other than that's what the driver's called
	mame_driver('VIC-20', command_lines.mame_vic_20, {'20', '40', '60', '70', 'a0', 'b0', 'crt'}),
	mame_driver('V.Smile', ('vsmile', 'cart'), generic_cart_extensions),
	mame_driver('V.Smile Motion', ('vsmilem', 'cart'), generic_cart_extensions),
	# No motion controls, but the games are playable without them
	mame_driver(
		'VZ-200',
		('vz200', 'dump'),
		{'vz'},
		slot_options={'io': 'joystick', 'mem': 'laser_64k'},
		has_keyboard=True,
	),
	# In the Laser 200/Laser 210 family, but Dick Smith variant should do.
	# Joystick interface doesn't seem to be used by any games, but I guess it does more than leaving the IO slot unfilled. That sucks, because otherwise no game ever uses the keyboard consistently, because of course not. Even modern homebrew games. Why y'all gotta be like that?
	# Some games will need you to type RUN to run them, not sure how to detect that.
	mame_driver('Watara Supervision', ('svision', 'cart'), {'bin', 'ws', 'sv'}),
	# I've been told the sound is that horrible on a real system; there are "TV Link" variant systems but that just makes the colours look even worse (they're all inverted and shit)
	mame_driver('WonderSwan', ('wscolor', 'cart'), {'ws', 'wsc', 'bin', 'pc2'}),
	# Could also be weird where rotation is involved, but at least it selects the right way around on startup
	mame_driver(
		'ZX Spectrum',
		command_lines.mame_zx_spectrum,
		{
			'ach',
			'frz',
			'plusd',
			'prg',
			'sem',
			'sit',
			'sna',
			'snp',
			'snx',
			'sp',
			'z80',
			'zx',
			'bin',
			'rom',
			'raw',
			'scr',
		}.union(mame_floppy_formats),
	),
	# .trd would be doable with -exp beta128, but that only autoboots on Spectrum 48K (128K needs 128 Basic > "randomize usr 15616" > j > enter) and everything is designed for 128K
	# .opu .opd might work with -exp opus, but that seems to only work on 48K and one must type "run"
	# ----- The experimental section. The emulators are still here, it's just so you, the fabulous and wonderful end user, can have more information on how to manage expectations. Or something like that.
	mednafen_module(
		# Based off an old version of VisualBoyAdvance
		'Game Boy',
		{'gb', 'gbc'},
		command_lines.mednafen_gb,
		status=EmulatorStatus.Imperfect,
	),
	mednafen_module(
		# Apparently "a low-priority system in terms of proactive maintenance and bugfixes". This is based off SMS Plus
		'Game Gear',
		{'gg'},
		command_lines.mednafen_game_gear,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mednafen_module(
		'GBA', {'gba'}, command_lines.mednafen_gba, status=EmulatorStatus.Imperfect
	),  # Based off an old version of VisualBoyAdvance
	mednafen_module(
		# Apparently "a low-priority system in terms of proactive maintenance and bugfixes". Based off SMS Plus
		'Master System',
		{'sms', 'bin'},
		'sms',
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mednafen_module(
		# Based off Genesis Plus and an older GPL version of Genesis Plus GX, with all GPL-incompatible cores replaced with alternatives (sound chip emulation from Gens, Z80 from FUSE). Apparently "should still be considered experimental; there are still likely timing bugs in the 68K emulation code, the YM2612 emulation code is not particularly accurate, and the VDP code has timing-related issues."
		'Mega Drive',
		{'md', 'bin', 'gen', 'smd', 'sgd'},
		command_lines.mednafen_megadrive,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mednafen_module(
		# Forked from 0.8.x pce with speed-accuracy tradeoffs
		'PC Engine Fast',
		{'pce', 'sgx', 'iso', 'cue', 'ccd', 'toc', 'm3u'},
		'pce_fast',
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mednafen_module(
		# Doesn't do .iso for whatever strange reason, which is a bit unfortunate. Might do .bin executables? Probably not
		'Saturn',
		{'cue', 'toc', 'ccd', 'm3u'},
		'ss',
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mednafen_module(
		'SNES', {'sfc', 'smc', 'swc'}, 'snes', status=EmulatorStatus.ExperimentalButSeemsOkay
	),  # Based on bsnes v0.059; appears it doesn't do Sufami Turbo or Satellaview
	mednafen_module(
		'SNES-Faust',
		{'sfc', 'smc', 'swc'},
		command_lines.mednafen_snes_faust,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		'32X',
		command_lines.mame_32x,
		{'32x', 'bin'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	# Higher host CPU requirements than what you might expect
	mame_driver(
		'Amstrad PCW',
		('pcw10', 'flop'),
		mame_floppy_formats,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
		check_func=command_lines.mame_amstrad_pcw_check,
		has_keyboard=True,
	),
	mame_driver(
		# Supports savestate but otherwise emulation = preliminary
		'Bandai RX-78',
		('rx78', 'cart'),
		{'bin', 'rom'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
		has_keyboard=True,
	),
	mame_driver(
		# Not the same as the PV-1000, albeit similar. Driver marked as non-working but it seems alright, other than it's supposed to have joysticks and doesn't (so you just set up a gamepad to map to emulated cursor keys) which maybe is why
		'Casio PV-2000',
		('pv2000', 'cart'),
		{'bin'},
		has_keyboard=True,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		'CD-i',
		('cdimono1', 'cdrom'),
		mame_cdrom_formats,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),  # This is the only CD-i model that works according to wisdom passed down the ages (is it still true or does other stuff work now?), and it says it's imperfect graphics/sound, no digital video stuff
	mame_driver(
		# This doesn't save the RTC so you have to set that every time you boot it up, which would be too annoying… but this development BIOS instantly boots up whatever game is in the flash; claims to have no sound but it does do the sound? Unless it's supposed to have more sound than just beep
		'Dreamcast VMU',
		('svmu', 'quik'),
		{'vms', 'bin'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
		slot_options={'bios': 'dev1004'},
	),
	mame_driver(
		'FM Towns',
		command_lines.mame_fm_towns,
		mame_cdrom_formats.union(mame_floppy_formats).union({'bin'}),
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		# As it says right there in the fmtowns.cpp comments: "Issues: Video emulation is far from complete." and still marked not working, but it seems okay for a few games actually; creating floppies (for games that make you do that) seems like a weird time
		'FM Towns Marty',
		command_lines.mame_fm_towns_marty,
		mame_cdrom_formats.union(mame_floppy_formats).union({'bin'}),
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		# Not working and imperfect sound
		'Gachinko Contest! Slot Machine TV',
		('gcslottv', 'cart'),
		generic_cart_extensions,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		'GameKing',
		('gameking', 'cart'),
		{'bin', 'gk'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		'GameKing 3',
		('gamekin3', 'cart'),
		{'bin', 'gk3'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver('GP32', ('gp32', 'memc'), {'smc'}, status=EmulatorStatus.ExperimentalButSeemsOkay),
	# Bad performance (60-ish% on i5-9600kf) but otherwise might kinda work?
	mame_driver(
		# Hmm... says not working and imperfect sound. I guess it does run the games, though
		'Hartung Game Master',
		('gmaster', 'cart'),
		{'bin'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		'Microbee',
		command_lines.mame_microbee,
		{'mwb', 'com', 'bee'}.union(mame_floppy_formats),
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	mame_driver(
		'PC-6001',
		('pc6001', 'cart1'),
		{'bin', 'rom'},
		has_keyboard=True,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	# Preliminary and notes in source file comments it doesn't load tapes yet (the cart2 slot seems to be a hack that does that)
	# Use pc6001a for USA version if needed, pc6001mk2 and pc6001sr might also do something, pc6601 should have a floppy drive but doesn't yet
	mame_driver(
		'PC-88',
		('pc8801', 'flop1'),
		mame_floppy_formats,
		has_keyboard=True,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	# TODO: Tapes, and potentially look into other models. All the PC-88 models claim to be broken, but the base one plays the games, so that's good enough in my book
	mame_driver(
		'Sharp MZ-2000',
		('mz2200', 'flop1'),
		mame_floppy_formats.union({'2d'}),
		has_keyboard=True,
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	# Autoboots floppies unless they have more than one thing to boot on them, which I guess makes sense
	# Apparently not working (mz2000 is not either), so I dunno
	mame_driver(
		'Sony SMC-777',
		('smc777', 'flop1'),
		mame_floppy_formats.union({'1dd'}),
		status=EmulatorStatus.ExperimentalButSeemsOkay,
		has_keyboard=True,
	),
	mame_driver(
		'Uzebox', ('uzebox', 'cart'), {'bin', 'uze'}, status=EmulatorStatus.ExperimentalButSeemsOkay
	),
	mame_driver(
		'V.Tech Socrates',
		('socrates', 'cart'),
		{'bin'},
		status=EmulatorStatus.ExperimentalButSeemsOkay,
	),
	# Marked as not working.union(imperfect) sound, possibly because of missing speech (also mouse is missing)
	mame_driver(
		'Amiga CD32',
		command_lines.mame_amiga_cd32,
		mame_cdrom_formats,
		status=EmulatorStatus.Experimental,
	),
	# Hmm boots only a few things I guess
	mame_driver(
		# The controller is part of the keyboard, and it's treated as though the only thing is the keyboard so it gets way too weird to set up. This makes about as much sense as I worded it; anyway it works
		'CreatiVision',
		('crvision', 'cart'),
		{'bin', 'rom'},
		has_keyboard=True,
		status=EmulatorStatus.Janky,
	),
	mame_driver(
		# Sloooow, marked as non-working.union(imperfect) sound
		'Dreamcast',
		command_lines.mame_dreamcast,
		mame_cdrom_formats,
		status=EmulatorStatus.Experimental,
	),
	mame_driver(
		# Sound Blaster 1.5 is added here primarily just to give this a joystick, but then that seems to not work anyway... also, there's DIP switches you might need to set in order for video output to work (it's set to monochrome by default and not CGA)
		'IBM PC',
		('ibm5150', 'flop1'),
		mame_floppy_formats.union({'img'}),
		status=EmulatorStatus.Janky,
		slot_options={'isa5': 'sblaster1_5'},
		has_keyboard=True,
	),
	mame_driver(
		# Hmm. Mostly not working. Some stuff does though
		'Jaguar',
		command_lines.mame_atari_jaguar,
		{'j64', 'rom', 'bin', 'abs', 'cof', 'jag', 'prg'},
		status=EmulatorStatus.Experimental,
	),
	mame_driver('KC-85', ('kc85_3', 'quik'), {'kcc'}, status=EmulatorStatus.Experimental),
	# All marked as MACHINE_NOT_WORKING (some stuff doesn't seem to have sound or boot)
	mame_driver(
		# Controllers aren't emulated yet (and they're necessary for a lot of things)
		'Mattel Aquarius',
		('aquarius', 'cart'),
		{'bin', 'rom'},
		status=EmulatorStatus.Experimental,
		has_keyboard=True,
	),
	mame_driver(
		# Not going to bother about handling the cards, since logically you want to use those in the middle of the game and so you'd swap those in and out with the MAME file management menu
		# No sound and a bit slow (the latter is made worse with this console having shit loading speed)
		'Mattel HyperScan',
		('hyprscan', 'cdrom'),
		mame_cdrom_formats,
		status=EmulatorStatus.Experimental,
	),
	mame_driver(
		# Hmm sometimes works and sometimes does not (when does it not? Elaborate, past self)
		'Mega CD',
		command_lines.mame_mega_cd,
		mame_cdrom_formats,
		status=EmulatorStatus.Experimental,
	),
	mame_driver(
		# System name was "microtan" prior to 0.212
		# Aagggh, none of these inputs seem to be working properly (to the point where I can't just assume the games were like that)... maybe I'm doing it wrong, I don't know…
		'Microtan 65',
		('mt65', 'dump'),
		{'dmp', 'm65'},
		has_keyboard=True,
		status=EmulatorStatus.Experimental,
	),
	mame_driver(
		# You probably want to use the software list for this so it can detect controls properly, also needs artwork that doesn't seem to be available anywhere
		'Microvision',
		('microvsn', 'cart'),
		generic_cart_extensions,
		status=EmulatorStatus.Janky,
	),
	mame_driver(
		# Emulates a NTSC console only so PAL games will probably tell you off or otherwise not work properly; also no rumble/mempak/etc for you. Very slow on even modern systems. Marked as non-working.union(imperfect) graphics
		'N64',
		command_lines.mame_n64,
		{'v64', 'z64', 'rom', 'n64', 'bin'},
		status=EmulatorStatus.Experimental,
	),
	mame_driver(
		'Pokémon Mini', ('pokemini', 'cart'), {'bin', 'min'}, status=EmulatorStatus.Experimental
	),
	# Wouldn't recommend yet as it has no sound, even if most people would probably turn the sound off in real life, also some stuff doesn't work
	mame_driver(
		'Saturn', command_lines.mame_saturn, mame_cdrom_formats, status=EmulatorStatus.Experimental
	),
	# Non-working, imperfect sound; crashes on quite a few games and hangs to white screen sometimes
	mame_driver('Sega Pico', command_lines.mame_pico, {'bin', 'md'}, status=EmulatorStatus.Janky),
	# Seems like a lot of stuff doesn't get anywhere? Probably needs the book part
	mame_driver('Select-a-Game', ('sag', 'cart'), {'bin'}, status=EmulatorStatus.Janky),
	# Is now a separate system as of 0.221 instead of sag_whatever individual machines
	# See also Microvision, is similarly janky with needing artwork
	mame_driver("Super A'Can", ('supracan', 'cart'), {'bin'}, status=EmulatorStatus.Experimental),
	# Some things work, except with no sound, so... nah
	mame_driver(
		'TRS-80',
		('trs80l2', 'quik'),
		{'cmd'},
		status=EmulatorStatus.Experimental,
		has_keyboard=True,
	),
	# trs80 only has tapes I guess, there are lots of clones of trs80l2
	# I didn't manage to figure out disks, tapes of course require typing non-programmatically-typeable things
	# TRS-80 Model 3 is there but sound seems to not work for backwards compatibility so like I dunno, still need to figure out if I want it as a separate system entirely
	mame_driver(
		# Seems to crash on some titles, also everything in software list is supported=no?
		'V.Smile Baby',
		('vsmileb', 'cart'),
		{'u1', 'u3', 'bin'},
		status=EmulatorStatus.Experimental,
	),
	mame_driver(
		# Has some hella glitchy graphics and I'm not gonna call it a playable experience at this point (also it does say not working)
		'VideoBrain',
		('vidbrain', 'cart'),
		{'bin'},
		status=EmulatorStatus.Experimental,
		has_keyboard=True,
	),
	mame_driver(
		'Videoton TVC',
		('tvc64', 'cart'),
		{'bin', 'rom', 'crt'},
		status=EmulatorStatus.Experimental,
		has_keyboard=True,
	),
	mame_driver('Virtual Boy', ('vboy', 'cart'), {'bin', 'vb'}, status=EmulatorStatus.Experimental),
	# Doesn't do red/blue stereo 3D, instead just outputing two screens side by side (you can go cross-eyed to see the 3D effect, but that'll hurt your eyes after a while (just like in real life)). Also has a bit of graphical glitches here and there and a lot of software list items are unsupported
	# TODO PlayStation: Would require proper region code detection, which would require looking at ISO9660 stuff properly. Anyway it is MACHINE_NOT_WORKING and often doesn't play the games (see https://mametesters.org/view.php?id=7127)
	# Just here for future use or the fun of creating launchers really; these straight up don't work:
	mame_driver(
		# Should switch to 3do_pal when needed, but it doesn't really matter at this point
		'3DO',
		('3do', 'cdrom'),
		mame_cdrom_formats,
		status=EmulatorStatus.Borked,
	),
	mame_driver(
		# Inputs are not defined and it just spams random inputs (the game plays itself!!!1)
		'Buzztime Home Trivia System',
		('buzztime', 'cart'),
		{'bin'},
		status=EmulatorStatus.Borked,
	),
	mame_driver(
		# Doesn't load carts anymore
		'C64',
		command_lines.mame_c64,
		{'80', 'a0', 'e0', 'crt'},
		status=EmulatorStatus.Borked,
		check_func=command_lines.mame_c64_check,
	),
	mame_driver('Casio Loopy', ('casloopy', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	# Just shows corrupted graphics (and has no controls defined), basically just a skeleton even if it looks like it isn't
	mame_driver(
		'Commodore CDTV', ('cdtv', 'cdrom'), mame_cdrom_formats, status=EmulatorStatus.Borked
	),
	# This one works less than CD32; just takes you to the default boot screen like no CD was inserted
	mame_driver('Copera', ('copera', 'cart'), {'bin', 'md'}, status=EmulatorStatus.Borked),
	# Displays the logo and then displays nothing
	mame_driver('GoGo TV Video Vision', ('tvgogo', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver(
		'Jaguar CD', ('jaguarcd', 'cdrom'), mame_cdrom_formats, status=EmulatorStatus.Borked
	),  # Also has cartridge port, as it is a Jaguar addon
	mame_driver('Koei PasoGo', ('pasogo', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	# No sound yet, and apparently the rest doesn't work either (I'll take their word for it so I don't have to play weird board games I don't understand)
	mame_driver('Tomy Prin-C', ('princ', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	# Skeleton driver that displays a green background and then doesn't go anywhere
	# Doesn't even display graphics, I'm just feeling like adding stuff at this point
	mame_driver(
		'Advanced Pico Beena', ('beena', 'cart'), {'bin'}, status=EmulatorStatus.Borked
	),  # Segfaults
	mame_driver('C2 Color', ('c2color', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver('Didj', ('didj', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver('Konami Picno', ('picno', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver('LeapPad', ('leappad', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver(
		'Leapster', ('leapster', 'cart'), {'bin'}, status=EmulatorStatus.Borked
	),  # Sometimes crashes, appears to be executing the CPU and printing debug stuff
	mame_driver('MobiGo', ('mobigo', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver('Monon Color', ('mononcol', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver('My First LeapPad', ('mfleappad', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver('Pippin', ('pippin', 'cdrom'), mame_cdrom_formats, status=EmulatorStatus.Borked),
	mame_driver(
		'Pocket Challenge W', ('pockchal', 'cart'), {'bin', 'pcw'}, status=EmulatorStatus.Borked
	),
	mame_driver('V.Reader', ('vreader', 'cart'), {'bin'}, status=EmulatorStatus.Borked),
	mame_driver(
		'V.Smile Pro', ('vsmilpro', 'cdrom'), mame_cdrom_formats, status=EmulatorStatus.Borked
	),
	# TODO: Comments from systems that indicate I feel the need to create an autoboot for stuff (because I guess typing arcane shit just sucks too much, and yeah it does make me think that some tapes_are_okay or menus_are_okay option is needed)
	# z88: 	#Marked as not working due to missing expansion interface and serial port and other things, not sure how important that would be... anyway, I'd need to do an autoboot thing to press the key to start the thing, because otherwise it's annoying to navigate every time, and then... hmm, I guess I dunno what actually is a function of things not working yet
	# mo6: #Floppies work (and cassettes and carts have same problem as MO5), but this time we need to press the F1 key and I don't waaaanna do that myself
	# to7/to8: 	#Fuck I hate this. Carts need to press 1 on TO7 or press the button with the lightpen on TO8/9 and also they suck, floppies need BASIC cart inserted on TO7 (and then the same method to boot that cart) or press B on TO8/9, tapes are a shitload of fuck right now (same broken as MO5/MO6), not all of this seems to be cross compatible so might need to separate systems or work out what's going on there
	# ti99_4a: 	#Carts need to press the any key and then 2 to actually load them. Floppies are the most asinine irritating thing ever fuck it Actually if we can detect that a floppy has Extended BASIC autoboot that could work with an autoboot script in the same way that cartridges work
	# studio2: #This console sucks and I hate it, anyway; I'd need to make multiple autoboot scripts that press F3 and then combinations of buttons depending on software list > usage somehow? God fuck I hate this console so much. PAL games (and some homebrew stuff) need mpt02
	# bbcb: The key combination to boot a floppy is Shift+Break which is rather awkward to press, so I want an autoboot script
	# electron: Same
	# galaxy/galaxyp:  #This needs tape control automation to work with tapes (type OLD, then play tape, then RUN); dumps just need to press enter because MAME will type "RUN" for you. But not enter for you. Dunno why. Anyway, we'd go with those and make an autoboot script (maybe just -autoboot_command '\n' would work with suitable delay). galaxy is regular system, galaxyp is an upgraded one which appears to be completely backwards compatible
	# abc80: #Requires "RUN " and the program name, where the program name is completely arbitrary and variable, so there's not really any way to do it automatically and programmatically
	# pdp1: MAME needs us to press control panel key.union(read) in, and then it does the thing and all is well
	# zx81: 	#Gotta press J and then Shift+P twice to type LOAD "" and then enter, and then start the tape, and then wait and then press run, and it seems if you screw up any step at all you gotta reset the whole thing baaggghghh which is why I haven't bothered trying more of this
	# einstein: Works fine but you need to type in the name of the program (this isn't in the usage field of SL)
	# Have not gotten around to trying:
	# atom
	# CPC/CPC+
	# pcw16 	#Marked as MACHINE_NOT_WORKING and MAME pcw.cpp mentions needing an OS rescue disk, probably doesn't work conveniently or at all
	# apfimag
	# bbcm
	# sorcerer:	#Would need automated tape loading to do anything interesting (carts and floppies are just BASIC/OS stuff, also what even is the file type for floppies?) hnmn so probably not
	# fc100
	# mtx512
	# vector06: 	#MAME driver is marked as working but clones are not; needs to hold F2 then press F11 then F12 to boot from cartridge so that may be wacky; and I can't get that working, not sure if floppies/tapes do work
	# mc10 hmm tapes tho
	# cd2650
	# instruct
	# pipbug
	# nascom/nascom2c
	# cgenie
	# CBM-II
	# compis
	# ep128 #hhhhh needs isdos from software list for floppies I think
	# dragon64
	# elfii
	# Have not gotten around to trying and don't feel like it (give me games or give me death)
	# x07 (video expansion is not there)
	# zorba
	# wmbullet
	# Do the thing idiot:
	# TODO: Commodore PET can work with MAME by using -quik and autoboot, apparently?
	# TODO PC-98 does somewhat work, but I probably want to filter out stuff that requires HDD install (only some stuff autoboots from floppy)
	# TODO: Put Acorn Archimedes MAME driver in there anyway, even if I need to click the thing, I think that is not too unreasonable
}
standalone_emulators_by_name = {emu.name(): emu for emu in standalone_emulators}

libretro_cores: 'Collection[type[LibretroCore]]' = {
	# 	LibretroCore('81', '81', None, {'p', 'tzx', 't81'}),
	# 	LibretroCore('Beetle Cygne', 'mednafen_cygne', None, {'ws', 'wsc', 'pc2'}),
	# 	LibretroCore('Beetle NeoPop', 'mednafen_ngp', None, {'ngp', 'ngc', 'ngpc', 'npc'}),
	# 	LibretroCore(
	# 		'Beetle PCE Fast',
	# 			# 		'mednafen_pce_fast',
	# 		None,
	# 		{'pce', 'cue', 'ccd', 'toc', 'm3u', 'chd'},
	# 	),
	# 	LibretroCore(
	# 		'Beetle PCE',
	# 			# 		'mednafen_pce',
	# 		None,
	# 		{'pce', 'cue', 'ccd', 'sgx', 'toc', 'm3u', 'chd'},
	# 	),
	# 	LibretroCore(
	# 		'Beetle PC-FX',
	# 			# 		'mednafen_pcfx',
	# 		None,
	# 		{'cue', 'ccd', 'toc', 'chd', 'm3u'},
	# 	),
	# 	LibretroCore(
	# 		'Beetle PSX HW',
	# 			# 		'mednafen_psx_hw',
	# 		None,
	# 		{'cue', 'chd', 'ccd', 'toc', 'm3u', 'exe', 'pbp'},
	# 	),  # needs_fullpath=true
	# 	LibretroCore(
	# 		'Beetle Saturn',
	# 			# 		'mednafen_saturn',
	# 		None,
	# 		{'cue', 'chd', 'ccd', 'toc', 'm3u'},
	# 	),  # needs_fullpath=true
	# 	LibretroCore('Beetle VB', 'mednafen_vb', None, {'vb', 'vboy', 'bin'}),
	# 	LibretroCore(
	# 		'BlastEm',
	# 			# 		'blastem',
	# 		command_lines.blastem,
	# 		{'md', 'bin', 'smd', 'gen', 'sms'},
	# 	),  # Does not claim to support Master System in info file, but does
	# 	LibretroCore(
	# 		'blueMSX',
	# 			# 		'bluemsx',
	# 		None,
	# 		{'dsk', 'rom', 'ri', 'mx1', 'mx2', 'col', 'cas', 'sg', 'sc', 'm3u'},
	# 	),  # Turbo-R does not work, also does not do any dual cartridge shenanigans, or battery saves; needs_fullpath=true
	# 	LibretroCore(
	# 		'bsnes',
	# 			# 		'bsnes',
	# 		command_lines.bsnes_libretro,
	# 		{'sfc', 'smc', 'gb', 'gbc', 'bs'},
	# 		configs=_bsnes_options,
	# 	),
	# 	LibretroCore(
	# 		'bsnes-hd beta',
	# 			# 		'bsnes_hd_beta',
	# 		command_lines.bsnes_libretro,
	# 		{'sfc', 'smc', 'gb', 'gbc', 'bs'},
	# 		configs=_bsnes_options,
	# 	),  # Does not claim to support .bs, but does
	# 	LibretroCore(
	# 		'Caprice32',
	# 			# 		'cap32',
	# 		None,
	# 		{'dsk', 'sna', 'tap', 'cdt', 'voc', 'cpr', 'm3u'},
	# 	),  # cpr will need game override to 6128+, if setting that globally disks won't autoboot; m3u is there to specify load command and not multiple disks; needs_fullpath=true
	# 	LibretroCore('ChaiLove', 'chailove', None, {'chai', 'chailove'}),  # needs_fullpath=true
	# 	LibretroCore('Dinothawr', 'dinothawr', None, {'game'}),
	# 	LibretroCore('fMSX', 'fmsx', None, {'rom', 'mx1', 'mx2', 'dsk', 'm3u', 'cas', 'fdi'}),
	# 	LibretroCore('FreeChaF', 'freechaf', None, {'bin', 'chf'}),
	# 	LibretroCore('FreeIntv', EmulatorStatus.Janky, 'freeintv', None, {'int', 'bin', 'rom'}),
	# 	LibretroCore(
	# 		'FreeJ2ME', EmulatorStatus.Imperfect, 'freej2me', None, {'jar'}
	# 	),  # Seems to require a JDK
	# 	LibretroCore('FUSE', 'fuse', None, {'tzx', 'tap', 'z80', 'rzx', 'scl', 'trd', 'dsk'}),
	# 	LibretroCore(
	# 		'Gearboy',
	# 			# 		'gearboy',
	# 		simple_gb_emulator([], {'MBC1', 'MBC2', 'MBC3', 'MBC5'}, {'MBC1 Multicart'}),
	# 		{'gb', 'dmg', 'gbc', 'cgb', 'sgb'},
	# 	),
	# 	LibretroCore(
	# 		'Genesis Plus GX',
	# 			# 		'genesis_plus_gx',
	# 		command_lines.genesis_plus_gx,
	# 		{
	# 			'mdx',
	# 			'md',
	# 			'smd',
	# 			'gen',
	# 			'bin',
	# 			'cue',
	# 			'iso',
	# 			'sms',
	# 			'bms',
	# 			'gg',
	# 			'sg',
	# 			'68k',
	# 			'chd',
	# 			'm3u',
	# 		},
	# 	),  # needs_fullpath=true (but is that just for CD)
	# 	LibretroCore(
	# 		'Hatari', 'hatari', None, {'st', 'msa', 'stx', 'dim', 'm3u'}
	# 	),  # Theoretically supports .ipf but that is not compiled in with the build from the core downloader; needs_fullpath=true
	# 	LibretroCore('LowRes NX', 'lowresnx', None, {'nx'}),
	# 	LibretroCore('Mesen', 'mesen', command_lines.mesen, {'nes', 'fds', 'unf', 'unif'}),
	# 	LibretroCore(
	# 		'melonDS', 'melonds', command_lines.melonds, {'nds'}
	# 	),  # Still no DSi or iQue, OpenGL renderer makes aspect ratio go weird unless using hybrid layout
	# 	LibretroCore('mGBA', 'mgba', command_lines.mgba, {'gb', 'gbc', 'gba'}),
	# 	LibretroCore(
	# 		'Mu', EmulatorStatus.Janky, 'mu', None, {'prc', 'pqa', 'img', 'pdb'}
	# 	),  # Still need to select application manually from emulated menu
	# 	LibretroCore(
	# 		'Mupen64Plus-Next',
	# 			# 		'mupen64plus_next',
	# 		None,
	# 		{'n64', 'v64', 'z64', 'bin', 'u1'},
	# 	),  # TODO: Command line function to reject roms with no detectable endianness
	# 	LibretroCore('NeoCD', 'neocd', None, {'cue', 'chd'}),
	# 	LibretroCore('O2EM', 'o2em', None, {'bin'}),
	# 	LibretroCore(
	# 		'Opera', EmulatorStatus.Imperfect, 'opera', None, {'iso', 'chd', 'bin', 'cue'}
	# 	),  # needs_fullpath=true
	# 	LibretroCore(
	# 		'PicoDrive',
	# 			# 		'picodrive',
	# 		simple_md_emulator([], {'pokestad', 'lion3'}),
	# 		{'bin', 'gen', 'smd', 'md', '32x', 'chd', 'cue', 'iso', 'sms', '68k', 'm3u'},
	# 	),  # Lion King 3 is automatically detected but no other games using the same mapper work, so I guess we will pretend it's not a working mapper; needs_fullpath=true (for CDs?)
	# 	LibretroCore('PokeMini', 'pokemini', None, {'min'}),
	# 	LibretroCore('Potator', 'potator', None, {'bin', 'sv'}),
	# 	LibretroCore('ProSystem', 'prosystem', command_lines.prosystem, {'a78', 'bin'}),
	# 	LibretroCore(
	# 		'PUAE',
	# 			# 		'puae',
	# 		None,
	# 		{
	# 			'adf',
	# 			'adz',
	# 			'dms',
	# 			'fdi',
	# 			'ipf',
	# 			'hdf',
	# 			'hdz',
	# 			'lha',
	# 			'slave',
	# 			'info',
	# 			'cue',
	# 			'ccd',
	# 			'nrg',
	# 			'mds',
	# 			'iso',
	# 			'chd',
	# 			'uae',
	# 			'm3u',
	# 			'rp9',
	# 		},
	# 	),  # Does require you to switch between RetroPad and CD32 pad accordingly…; needs_fullpath=true
	# 	LibretroCore(
	# 		'PX68k',
	# 			# 		'px68k',
	# 		None,
	# 		{'dim', 'img', 'd88', '88d', 'hdm', 'dup', '2hd', 'xdf', 'hdf', 'cmd', 'm3u'},
	# 	),  # needs_fullpath=true (tricky thing is that it might overwrite your uncompressed files if you leave them uncompressed? or something)
	# 	LibretroCore(
	# 		'SameBoy',
	# 			# 		'sameboy',
	# 		simple_gb_emulator(
	# 			[],
	# 			{'MBC1', 'MBC2', 'MBC3', 'MBC5', 'HuC1', 'HuC3', 'Pocket Camera'},
	# 			{'MBC1 Multicart'},
	# 		),
	# 		{'gb', 'gbc'},
	# 	),
	# 	LibretroCore('SameDuck', 'sameduck', None, {'bin'}),
	# 	LibretroCore('Stella', 'stella', None, {'a26', 'bin'}),
	# 	LibretroCore('Uzem', 'uzem', None, {'uze'}),
	# 	LibretroCore('Vecx', 'vecx', None, {'vec', 'bin'}),
	# 	LibretroCore(
	# 		'VeMUlator', EmulatorStatus.Imperfect, 'vemulator', None, {'vms', 'dci', 'bin'}
	# 	),  # Does a heckin bzzzz with a lot of things
	# 	LibretroCore(
	# 		'Virtual Jaguar',
	# 		EmulatorStatus.Imperfect,
	# 		'virtualjaguar',
	# 		None,
	# 		{'j64', 'jag', 'rom', 'abs', 'cof', 'bin', 'prg'},
	# 	),
	# 	LibretroCore(
	# 		'X Millennium',
	# 			# 		'x1',
	# 		None,
	# 		{'dx1', '2d', '2hd', 'tfd', 'd88', '88d', 'hdm', 'xdf', 'dup', 'cmd'},
	# 	),  # Claims to support tap but doesn't
}
libretro_cores_by_name = {core.name(): core for core in libretro_cores}


class DOSBoxStagingConfig(BaseEmulatorConfig):
	@classmethod
	def section(cls) -> str:
		return 'DOSBox Staging'

	@classmethod
	def prefix(cls) -> str:
		return 'dosbox_staging'

	cycles_for_477_mhz: int = 245
	'CPU cycles to use to get as close as possible to 4.77MHz'
	noautoexec: bool = False
	'Do not load [autoexec] section in config file'
	overlay_path: Path | None = None
	'If set to something, use a subfolder of this path as an overlay so save games etc are written there'


class DOSBoxStaging(Emulator[DOSApp]):
	@classmethod
	def name(cls) -> str:
		return 'DOSBox Staging'

	@classmethod
	def exe_name(cls) -> str:
		return 'dosbox'

	@classmethod
	def config_class(cls) -> type[DOSBoxStagingConfig]:
		return DOSBoxStagingConfig

	def get_game_command(self, game: DOSApp) -> LaunchCommand:
		return command_lines.dosbox_staging(game, self)


class DOSBox_X(Emulator[DOSApp]):
	@classmethod
	def name(cls) -> str:
		return 'DOSBox-X'

	@classmethod
	def exe_name(cls) -> str:
		return 'dosbox-x'

	def get_game_command(self, game: DOSApp) -> LaunchCommand:
		return command_lines.dosbox_x(game, self)


dos_emulators: 'Collection[type[Emulator[DOSApp]]]' = {DOSBoxStaging, DOSBox_X}


class BasiliskIIConfig(BaseEmulatorConfig):
	@classmethod
	def section(cls) -> str:
		return 'BasiliskII'

	@classmethod
	def prefix(cls) -> str:
		return 'basilisk_ii'

	skip_if_ppc_enhanced: bool = False
	'If the app has ppc_enhanced = true in its config ie. it performs better or has some extra functionality on PPC, do not use BasiliskII for it'


class BasiliskII(Emulator[MacApp]):
	@classmethod
	def name(cls) -> str:
		return 'BasiliskII'

	@classmethod
	def exe_name(cls) -> str:
		return 'BasiliskII'

	@classmethod
	def config_class(cls) -> type[BasiliskIIConfig]:
		return BasiliskIIConfig

	@classmethod
	def status(cls) -> EmulatorStatus:
		return EmulatorStatus.Janky

	def get_game_command(self, game: MacApp) -> LaunchCommand:
		return command_lines.basilisk_ii(game, self)


class SheepShaver(Emulator[MacApp]):
	@classmethod
	def name(cls) -> str:
		return 'SheepShaver'

	@classmethod
	def exe_name(cls) -> str:
		return 'SheepShaver'

	@classmethod
	def status(cls) -> EmulatorStatus:
		return EmulatorStatus.Janky

	def get_game_command(self, game: MacApp) -> LaunchCommand:
		return command_lines.sheepshaver(game, self)


mac_emulators: 'Collection[type[Emulator[MacApp]]]' = {BasiliskII, SheepShaver}

# libretro_frontends = {
# 	LibretroFrontend('RetroArch', 'retroarch', command_lines.retroarch, {'7z', 'zip'})
# }

# Basically this is here for the purpose of generating configs
# TODO: Return an iterator and make a "has config" interface so we don't have to invent _JustHereForConfigValues
all_emulators: 'Sequence[type[Emulator[Game]]]' = (
	*standalone_emulators,
	*dos_emulators,
	*mac_emulators,
)
# libretro_cores, libretro_frontends
# all_emulators: 'MutableSequence[Emulator | LibretroFrontend]' = _standalone_emulators
# all_emulators: 'MutableSequence[Emulator[EmulatedGame] | LibretroFrontend]' = []
# all_emulators: 'MutableSequence[Emulator[EmulatedGame] | LibretroFrontend | _JustHereForConfigValues]' = []
# all_emulators += standalone_emulators
# all_emulators += _libretro_cores
# all_emulators += _dos_emulators
# all_emulators += _mac_emulators
# all_emulators += _libretro_frontends
