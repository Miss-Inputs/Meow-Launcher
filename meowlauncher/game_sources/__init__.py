from typing import TYPE_CHECKING

from .dos import DOS
from .mac import Mac
from .mame_machines import MAME, MAMEInbuiltGames
from .roms import ROMs
from .scummvm import ScummVM
from .steam import Steam

if TYPE_CHECKING:
	from collections.abc import Collection

	from meowlauncher.game_source import GameSource

__doc__ = "Registry of all GameSources, so they can be iterated over to get each type and then instantiated and then you call iter_launchers"

game_sources: 'Collection[type[GameSource]]' = (
	DOS,
	Mac,
	MAME,
	MAMEInbuiltGames,
	ROMs,
	ScummVM,
	Steam,
)
