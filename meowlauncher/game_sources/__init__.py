from meowlauncher.game_source import GameSource
from .dos import DOS
from .mac import Mac
from .scummvm import ScummVM

_dos = DOS()
_mac = Mac()
_scummvm = ScummVM()

game_sources: list[GameSource] = [
	_dos,
	_mac,
	_scummvm,
]

game_types: dict[str, GameSource] = {
	#For remove_existing_games basically
	'DOS': _dos,
	'Mac': _mac,
	'ScummVM': _scummvm,
}
