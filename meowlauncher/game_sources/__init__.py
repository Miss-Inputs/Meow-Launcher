import sys

from meowlauncher.game_source import GameSource

from .dos import DOS
from .mac import Mac
from .mame_machines import MAME, MAMEInbuiltGames
from .roms import ROMs
from .scummvm import ScummVM

_dos = DOS()
_mac = Mac()
_scummvm = ScummVM()

excluded_platforms = []
for arg in sys.argv:
	#TODO: Not comfy with sys.argv handling being here either but it's better than being in roms innit
	#Spose it could go in main_config
	if arg.startswith('--excluded-platforms='):
		excluded_platforms += arg.split('=', 1)[1].split(', ')
platform_list = None
if len(sys.argv) >= 2 and '--platforms' in sys.argv:
	arg_index = sys.argv.index('--platforms')
	if len(sys.argv) == 2:
		raise ValueError('--platforms requires an argument')

	platform_list = sys.argv[arg_index + 1].split(', ')

_roms = ROMs(platform_list, excluded_platforms)

driver_list = None
if '--drivers' in sys.argv:
	arg_index = sys.argv.index('--drivers')
	if len(sys.argv) == 2:
		raise ValueError('--drivers requires an argument')

	driver_list = sys.argv[arg_index + 1].split(',')
source_file = None
if '--source-file' in sys.argv:
	arg_index = sys.argv.index('--source-file')
	if len(sys.argv) == 2:
		raise ValueError('--source-file requires an argument')

	source_file = sys.argv[arg_index + 1]
	
_mame = MAME(driver_list, source_file)
_mame_inbuilt = MAMEInbuiltGames()

game_sources: list[GameSource] = [
	_dos,
	_mac,
	_scummvm,
	_roms,
	_mame,
	_mame_inbuilt,
]

game_types: dict[str, GameSource] = {
	#For remove_existing_games basically
	'DOS': _dos,
	'Mac': _mac,
	'ScummVM': _scummvm,
	'ROM': _roms,
	'Arcade': _mame,
	'MAME': _mame,
	'Inbuilt game': _mame_inbuilt,
}
