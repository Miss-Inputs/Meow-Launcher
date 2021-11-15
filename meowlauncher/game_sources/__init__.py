import sys

from meowlauncher.game_source import GameSource
from meowlauncher.game_sources.roms import ROMs

from .dos import DOS
from .mac import Mac
from .scummvm import ScummVM

_dos = DOS()
_mac = Mac()
_scummvm = ScummVM()

excluded_platforms = []
for arg in sys.argv:
	#TODO: Not comfy with sys.argv handling being here either but it's better than being in roms innit
	if arg.startswith('--excluded-platforms='):
		excluded_platforms += arg.split('=', 1)[1].split(', ')
platform_list = None
if len(sys.argv) >= 2 and '--platforms' in sys.argv:
	arg_index = sys.argv.index('--platforms')
	if len(sys.argv) == 2:
		raise ValueError('--platforms requires an argument')

	platform_list = sys.argv[arg_index + 1].split(', ')

_roms = ROMs(platform_list, excluded_platforms)

game_sources: list[GameSource] = [
	_dos,
	_mac,
	_scummvm,
	_roms,
]

game_types: dict[str, GameSource] = {
	#For remove_existing_games basically
	'DOS': _dos,
	'Mac': _mac,
	'ScummVM': _scummvm,
	'ROM': _roms,
}
