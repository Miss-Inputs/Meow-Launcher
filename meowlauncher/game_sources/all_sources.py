"Registry of all GameSources, so they can be iterated over to get each type and then instantiated and then you call iter_launchers"
from typing import TYPE_CHECKING

from .arcade import Arcade, MAMEInbuiltGames
from .dos import DOS
from .mac import Mac
from .roms import ROMs
from .scummvm import ScummVM
from .steam import Steam

if TYPE_CHECKING:
	from collections.abc import Sequence

	from meowlauncher.game_source import GameSource

__all__ = ['game_sources']

game_sources: 'Sequence[type[GameSource]]' = (
	DOS,
	Mac,
	MAMEInbuiltGames,
	ROMs,
	ScummVM,
	Steam,
	Arcade,
)
