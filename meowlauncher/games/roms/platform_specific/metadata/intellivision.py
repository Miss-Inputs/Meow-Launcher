from typing import cast

from meowlauncher.games.mame_common.software_list import SoftwarePart
from meowlauncher.games.mame_common.software_list_info import (
    find_in_software_lists_with_custom_matcher, get_crc32_for_software_list)
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame


def _does_intellivision_part_match(part: SoftwarePart, data: bytes) -> bool:
	total_size = 0
	number_of_roms = 0

	offset = 0
	for data_area in part.data_areas.values():
		#'name' attribute here is actually where in the Intellivision memory map it gets loaded to, not the offset in the file like I keep thinking

		size = data_area.size

		if not data_area.roms:
			continue

		rom = data_area.roms[0]
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

def add_intellivision_info(game: ROMGame):
	#There's probably some way to get info from title screen in ROM, but I haven't explored that in ROMniscience yet
	#Input info: Keyboard Module, ECS (49 keys), or 12-key keypad + 3 buttons + dpad (I don't think it's actually a paddle unless I'm proven otherwise), or Music Synthesizer (49 keys) (TODO add this I'm tired right now)
	rom = cast(FileROM, game.rom)
	software = find_in_software_lists_with_custom_matcher(game.software_lists, _does_intellivision_part_match, [rom.read()])
	if software:
		software.add_standard_metadata(game.metadata)

		usage = software.get_info('usage')
		if usage == 'Uses Intellivoice':
			game.metadata.specific_info['Uses-Intellivoice'] = True
		elif usage in ('Requires ECS and Keyboard', 'Requires ECS and Intellivoice'):
			#Both of these are functionally the same for our intent and purpose, as MAME's intvecs driver always has a keyboard and Intellivoice module. I dunno if an Intellivision ECS without a keyboard is even a thing.
			game.metadata.specific_info['Uses-ECS'] = True

		#Other usage notes:
		#Will not run on Intellivision 2
		#This cart has unique Left and Right overlays
		#Requires ECS and Music Synthesizer

		#We don't have any reason to use the intv2 driver so that's not a worry; overlays aren't really a concern either, and I dunno about this music synthesizer thing
