import logging
from typing import TYPE_CHECKING, Any, cast

from meowlauncher import input_info
from meowlauncher.common_types import SaveType
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.util.region_info import TVSystem

from .common.atari_controllers import xegs_gun

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

standard_gamepad = input_info.NormalController()
standard_gamepad.dpads = 1
standard_gamepad.face_buttons = 2
input_types = {
	1: standard_gamepad,
	# The rest only have one button, for the record
	2: xegs_gun,
	3: input_info.Paddle(),  # Is this valid? Some games which have this seem to actually use the lightgun
	4: input_info.Trackball(),  # Is this a valid value?
}


def _add_atari_7800_header_info(
	rom_path_for_warning: Any, game_info: 'GameInfo', header: bytes
) -> None:
	game_info.input_info.set_inited()

	header_version = header[0]
	game_info.specific_info['Header Format'] = f'A78 (v{header_version})'
	# Magic: 1-17, we already checked that or else we wouldn't be here
	game_info.add_alternate_name(
		header[17:49]
		.rstrip(b'\0 ' if header_version < 3 else b'\0')
		.decode('ascii', errors='backslashreplace'),
		'Header Title',
	)
	# ROM size excluding header: Big endian 49-53
	# Special cart type: 53
	# Cart type: 54

	left_input_type = header[55]
	right_input_type = header[56]

	left_controller_option = None
	right_controller_option = None
	if left_input_type != 0:
		left_controller_option = input_info.InputOption()
		if left_input_type in input_types:
			left_controller_option.inputs.append(input_types[left_input_type])
		else:
			left_controller_option.inputs.append(input_info.Custom(f'Unknown {left_input_type}'))

	if right_input_type != 0:
		right_controller_option = input_info.InputOption()
		if right_input_type in input_types:
			right_controller_option.inputs.append(input_types[right_input_type])
		else:
			right_controller_option.inputs.append(input_info.Custom(f'Unknown {right_input_type}'))

	if left_controller_option and right_controller_option:
		number_of_players = 2  # I guess?
		game_info.input_info.input_options.append(left_controller_option)
	elif right_controller_option and not left_controller_option:
		number_of_players = 1
		game_info.specific_info['Swap Ports?'] = True
		game_info.input_info.input_options.append(right_controller_option)
	elif left_controller_option and not right_controller_option:
		number_of_players = 1
		game_info.input_info.input_options.append(left_controller_option)
	else:
		number_of_players = 0
	game_info.specific_info['Number of Players'] = number_of_players

	tv_type = header[57]

	if tv_type == 1:
		game_info.specific_info['TV Type'] = TVSystem.PAL
	elif tv_type == 0:
		game_info.specific_info['TV Type'] = TVSystem.NTSC
	else:
		logger.info('Unexpected TV type %s in %s', tv_type, rom_path_for_warning)
		game_info.specific_info['Invalid TV Type?'] = True

	save_type = header[58]
	if save_type == 0:
		game_info.save_type = SaveType.Nothing
	elif save_type == 1:
		# High Score Cart, an unreleased device that ends up being supported by some games (apparently). Just saves high scores so don't get too excited.
		# You plug the High Score Cart into the 7800 and then the game into the High Score Cart, so I guess this is the easiest thing to call it.
		game_info.save_type = SaveType.Internal
		game_info.specific_info['Uses Hiscore Cart?'] = True
	elif save_type == 2:
		# AtariVox/SaveKey. Both are third party products which plug into the controller port, so what else can you call them except memory cards?
		game_info.save_type = SaveType.MemoryCard
	else:
		logger.info('Unexpected save type byte %s in %s', save_type, rom_path_for_warning)

	# Reserved: 59-63
	# Expansion module required: 64


def add_atari_7800_custom_info(game: 'ROMGame') -> None:
	header = cast(FileROM, game.rom).read(amount=128)
	if header[1:10] == b'ATARI7800':
		game.info.specific_info['Headered?'] = True
		cast(FileROM, game.rom).header_length_for_crc_calculation = 128
		_add_atari_7800_header_info(game.rom.path, game.info, header)
	else:
		game.info.specific_info['Headered?'] = False

	software = game.get_software_list_entry()
	if software:
		software.add_standard_info(game.info)
		game.info.add_notes(software.get_info('usage'))
		# Don't need sharedfeat > compatibility to get TV type or feature > peripheral, unheadered roms won't work anyway
