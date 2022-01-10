import sys
from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING

from .dos import DOS
from .mac import Mac
from .mame_machines import MAME, MAMEInbuiltGames
from .roms import ROMs
from .scummvm import ScummVM
from .steam import Steam

if TYPE_CHECKING:
	from meowlauncher.game_source import GameSource

_dos = DOS()
_mac = Mac()
_scummvm = ScummVM()
_steam = Steam()

_excluded_platforms = None
for arg in sys.argv:
	#TODO: Not comfy with sys.argv handling being here either but it's better than being in roms innit
	#Spose it could go in main_config
	if arg.startswith('--excluded-platforms='):
		_excluded_platforms = arg.split('=', 1)[1].split(', ')
platform_list = None
if len(sys.argv) >= 2 and '--platforms' in sys.argv:
	arg_index = sys.argv.index('--platforms')
	if len(sys.argv) == 2:
		raise ValueError('--platforms requires an argument')

	platform_list = sys.argv[arg_index + 1].split(', ')

_roms = ROMs(platform_list, _excluded_platforms)

_driver_list_arg = None
if '--drivers' in sys.argv:
	arg_index = sys.argv.index('--drivers')
	if len(sys.argv) == 2:
		raise ValueError('--drivers requires an argument')

	_driver_list_arg = sys.argv[arg_index + 1].split(',')
_source_file_arg = None
if '--source-file' in sys.argv:
	arg_index = sys.argv.index('--source-file')
	if len(sys.argv) == 2:
		raise ValueError('--source-file requires an argument')

	_source_file_arg = sys.argv[arg_index + 1]
	
_mame = MAME(_driver_list_arg, _source_file_arg)
_mame_inbuilt = MAMEInbuiltGames()

#The order is not really important here, I guess, you only ever need to be iterating through it
game_sources: Collection['GameSource'] = {
	_dos,
	_mac,
	_mame,
	_mame_inbuilt,
	_roms,
	_scummvm,
	_steam,
}

game_types: Mapping[str, 'GameSource'] = {
	#For remove_existing_games basically
	#TODO: Hmm can we just get this from some property of GameSource instead
	'DOS': _dos,
	'Mac': _mac,
	'ScummVM': _scummvm,
	'ROM': _roms,
	'Arcade': _mame,
	'MAME': _mame,
	'Inbuilt game': _mame_inbuilt,
	'Steam': _steam,
}
