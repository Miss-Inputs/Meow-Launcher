import datetime
import logging
import time
from collections.abc import Sequence

from meowlauncher.config.main_config import main_config
from meowlauncher.game_source import CompoundGameSource, GameSource
from meowlauncher.game_sources import game_sources, gog, itch_io, mame_software
from meowlauncher.output.desktop_files import make_linux_desktop_for_launcher

__doc__ = """The important part that actually scans games and creates launchers. The logger here outputs progress messages so it may be useful to add a handler to it, for GUIs or if printed output might look nicer that way"""

logger = logging.getLogger(__name__)

def add_game_source(source: GameSource) -> int:
	"""Add all games from a single game source.
	Returns how many games were successfully added"""
	time_started = time.perf_counter()
	count = 0
	
	logger.info('Adding %s', source.description())
	if isinstance(source, CompoundGameSource):
		count += sum(add_game_source(subsource) for subsource in source.sources)
	else:
		for launcher in source.iter_launchers():
			count += 1
			make_linux_desktop_for_launcher(launcher, source.game_type())

	time_ended = time.perf_counter()
	time_taken = datetime.timedelta(seconds=time_ended - time_started)

	if count:
		logger.info('Added %d %s in %s (%s per game)', count, source.description(), time_taken, time_taken / count)
	else:
		logger.warning('Did not add any %s', source.description())
	logger.info('-' * 10)
	return count

def _get_game_source(name: str) -> type[GameSource] | None:
	return next((source for source in game_sources if name in {source.name(), source.__name__, source.name().lower().replace(' ', '_'), source.__name__.lower()}), None)

def add_games() -> int:
	"""Add all the games. Returns total amount of games successfully added"""
	total = 0
	
	source_names = main_config.sources
	do_mame_software = False
	sources: Sequence[type[GameSource]]
	if source_names:
		source_names = list(source_names)
		#TODO: Remove this once they are proper GameSources
		do_gog = False
		do_itch_io = False
		try:
			source_names.remove('GOG')
		except KeyError:
			pass
		else:
			do_gog = True
		try:
			source_names.remove('gog')
		except KeyError:
			pass
		else:
			do_gog = True
		try:
			source_names.remove('itch.io')
		except KeyError:
			pass
		else:
			do_itch_io = True
		try:
			source_names.remove('mame_software')
		except KeyError:
			pass
		else:
			do_mame_software = True

		sources = []
		for source_name in source_names:
			source_type = _get_game_source(source_name)
			if not source_type:
				logging.warning('Unknown game source: %s', source_name)
				continue
			sources.append(source_type)
			
	else:
		do_gog = True
		do_itch_io = True
		sources = game_sources

	for game_source_type in sources:
		game_source = game_source_type()
		if not game_source.is_available:
			logger.warning('%s was specified, but it is not available', game_source.name())
			continue
		total += add_game_source(game_source)
	logger.info('Added total of %d games', total) #Well other than those down below but sshhh pretend they aren't there

	if do_gog:		
		logger.info('Adding GOG games')
		gog.do_gog_games()
	if do_itch_io:		
		logger.info('Adding itch.io games')
		itch_io.do_itch_io_games()
	if do_mame_software:
		logger.info('Adding MAME software, which is not finished yet and this might not work')
		mame_software.add_mame_software()

	return total
