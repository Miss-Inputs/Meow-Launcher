from typing import cast

from meowlauncher.common_types import SaveType
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame


def add_doom_metadata(game: ROMGame):
	magic = cast(FileROM, game.rom).read(amount=4)
	if magic == b'PWAD':
		game.metadata.specific_info['Is-PWAD'] = True
	
	game.metadata.save_type = SaveType.Internal
	