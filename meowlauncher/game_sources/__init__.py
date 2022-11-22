from typing import TYPE_CHECKING

from .dos import DOS
from .mac import Mac
from .mame_machines import MAME, MAMEInbuiltGames
from .roms import ROMs
from .scummvm import ScummVM
from .steam import Steam

if TYPE_CHECKING:
	from collections.abc import Collection, Mapping
	from meowlauncher.game_source import GameSource

_dos = DOS
_mac = Mac
_scummvm = ScummVM
_steam = Steam
_roms = ROMs
_mame = MAME
_mame_inbuilt = MAMEInbuiltGames

game_sources: 'Collection[type[GameSource]]' = (
	_dos,
	_mac,
	_mame,
	_mame_inbuilt,
	_roms,
	_scummvm,
	_steam,
)
