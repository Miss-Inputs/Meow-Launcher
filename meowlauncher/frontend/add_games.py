import datetime
import time
from collections.abc import Callable
import itertools
import operator
import functools

from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.game_sources import game_sources, gog, itch_io, steam
from meowlauncher.output.desktop_files import make_linux_desktop_for_launcher


def add_game_source(source: GameSource, progress_function: Callable[..., None]) -> int:
	time_started = time.perf_counter()
	count = 0
	
	progress_function('Adding ' + source.description)
	if isinstance(source, CompoundGameSource):
		count += sum(add_game_source(subsource, progress_function) for subsource in source.sources)
	else:
		for launcher in source.iter_launchers():
			count += 1
			make_linux_desktop_for_launcher(launcher)
	time_ended = time.perf_counter()
	time_taken = datetime.timedelta(seconds=time_ended - time_started)
	if count:
		progress_function(f'Added {count} {source.description} in {str(time_taken)} ({time_taken.total_seconds() / count} secs per game)')
	else:
		progress_function(f'Did not add any {source.description}')
	return count

def add_games(progress_function: Callable[..., None]=print):
	for game_source in game_sources:
		if not game_source.is_available:
			continue
		add_game_source(game_source, progress_function)
		#TODO: Should actually use blah_enabled in some way, or some equivalent basically
		
	progress_function('Adding Steam games')
	steam.process_steam()
	progress_function('Adding GOG games')
	gog.do_gog_games()
	progress_function('Adding itch.io games')
	itch_io.do_itch_io_games()
