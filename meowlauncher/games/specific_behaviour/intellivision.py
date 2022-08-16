from typing import TYPE_CHECKING, cast

from meowlauncher.games.mame_common.software_list_find_utils import (
    find_in_software_lists_with_custom_matcher, get_crc32_for_software_list)
from meowlauncher.games.roms.rom import FileROM

from .simple_software_info import add_intellivision_software_info

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import SoftwarePart
	from meowlauncher.games.roms.rom_game import ROMGame


def _does_intellivision_part_match(part: 'SoftwarePart', data: bytes) -> bool:
	total_size = 0
	number_of_roms = 0

	offset = 0
	for data_area in part.data_areas.values():
		#'name' attribute here is actually where in the Intellivision memory map it gets loaded to, not the offset in the file like I keep thinking

		size = data_area.size
		if not size:
			continue

		if not data_area.roms:
			continue

		rom = next(iter(data_area.roms))
		number_of_roms += 1
		total_size += size

		crc32 = rom.crc32
		segment = data[offset: offset + size]
		segment_crc32 = get_crc32_for_software_list(segment)
		if segment_crc32 != crc32:
			return False

		offset += size

	if number_of_roms == 0:
		return False

	if total_size != len(data):
		return False

	return True

def add_intellivision_custom_info(game: 'ROMGame') -> None:
	#There's probably some way to get info from title screen in ROM, but I haven't explored that in ROMniscience yet
	#Input info: Keyboard Module, ECS (49 keys), or 12-key keypad + 3 buttons + dpad (I don't think it's actually a paddle unless I'm proven otherwise), or Music Synthesizer (49 keys) (TODO add this I'm tired right now)
	rom = cast(FileROM, game.rom)
	software = find_in_software_lists_with_custom_matcher(game.related_software_lists, _does_intellivision_part_match, [rom.read()])
	if software:
		add_intellivision_software_info(software, game.metadata)
