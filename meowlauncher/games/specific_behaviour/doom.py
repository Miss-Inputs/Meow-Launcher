from typing import TYPE_CHECKING

from meowlauncher.common_types import SaveType
if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.metadata import Metadata


def add_doom_rom_file_info(rom: 'FileROM', metadata: 'Metadata'):
	magic = rom.read(amount=4)
	if magic == b'PWAD':
		metadata.specific_info['Is PWAD?'] = True
	
	metadata.save_type = SaveType.Internal
	