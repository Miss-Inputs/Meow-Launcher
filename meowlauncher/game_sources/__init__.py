from meowlauncher.game_source import GameSource
from .dos import DOSGameSource
from .mac import MacGameSource

_dos = DOSGameSource()
_mac = MacGameSource()

game_sources: list[GameSource] = [
	_dos,
	_mac,
]

game_types: dict[str, GameSource] = {
	#For remove_existing_games basically
	'DOS': _dos,
	'Mac': _mac,
}
