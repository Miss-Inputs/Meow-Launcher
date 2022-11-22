import datetime
import time
from collections.abc import Callable

from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.game_sources import game_sources, gog, itch_io
from meowlauncher.output.desktop_files import make_linux_desktop_for_launcher


def add_game_source(source: GameSource, progress_function: Callable[[str], None]) -> int:
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
		progress_function(f'Added {count} {source.description} in {time_taken} ({time_taken.total_seconds() / count} secs per game)')
	else:
		progress_function(f'Did not add any {source.description}')
	progress_function('-------')
	return count

def add_games(progress_function: Callable[[str], None]=print) -> None:
	total = 0
	for game_source_type in game_sources:
		game_source = game_source_type()
		if not game_source.is_available:
			continue
		total += add_game_source(game_source, progress_function)
		#TODO: Should actually use blah_enabled in some way, or some equivalent basically
	print(f'Added total of {total} games') #Well other than those down below but sshhh pretend they aren't there
		
	progress_function('Adding GOG games')
	gog.do_gog_games()
	progress_function('Adding itch.io games')
	itch_io.do_itch_io_games()
