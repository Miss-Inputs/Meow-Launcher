from argparse import ArgumentParser
from typing import Any

from meowlauncher.settings.settings import MainConfig, Settings
from meowlauncher.game_sources import game_sources
from meowlauncher.version import __version__


def _setup_config():
	"""Initializes config with command line arguments, etc"""
	# game_source_config_classes = {
	# 	game_source
	# 	for game_source in (game_source.config_class() for game_source in game_sources)
	# 	if game_source
	# }
	game_source_settings = {source: source.config_class() for source in game_sources}
	settings_classes = {k: v for k, v in game_source_settings.items() if v}

	_main_config = MainConfig()

	parser = ArgumentParser(add_help=True, prog=f'python -m {__package__}')
	parser.add_argument('--version', action='version', version=__version__)

	option_to_config: dict[str, tuple[type, type[Settings], str]] = {}
	for key, cls in settings_classes.items():
		for k in cls.model_fields:
			option_to_config[f'{cls.__qualname__}.{k}'] = (key, cls, k)
		cls.add_argparser_group(parser)

	settings: dict[type, Settings] = {}
	for k, v in vars(parser.parse_intermixed_args()).items():
		key, cls, option_name = option_to_config[k]
		setattr(settings.setdefault(key, cls()), option_name, v)
	return _main_config, settings


main_config, current_config = _setup_config()
