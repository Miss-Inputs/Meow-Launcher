from argparse import ArgumentParser
from collections.abc import Collection

from meowlauncher.game_sources.settings import SteamConfig
from meowlauncher.games.mame.mame_config import ArcadeMAMEConfig
from meowlauncher.games.roms.roms_config import ROMsConfig
from meowlauncher.games.scummvm.scummvm_config import ScummVMConfig
from meowlauncher.settings.settings import MainConfig, Settings
from meowlauncher.version import __version__

settings_classes: Collection[type[Settings]] = {
	ArcadeMAMEConfig,
	ROMsConfig,
	SteamConfig,
	ScummVMConfig,
}


def _setup_config():
	"""Initializes config with command line arguments, etc"""
	# game_source_config_classes = {
	# 	game_source
	# 	for game_source in (game_source.config_class() for game_source in game_sources)
	# 	if game_source
	# }

	_main_config = MainConfig()

	parser = ArgumentParser(add_help=True, prog=f'python -m {__package__}')
	parser.add_argument('--version', action='version', version=__version__)

	option_to_config: dict[str, tuple[type[Settings], str]] = {}
	for cls in settings_classes:
		for k in cls.model_fields:
			option_to_config[f'{cls.__qualname__}.{k}'] = (cls, k)
		cls.add_argparser_group(parser)

	settings: dict[type, Settings] = {}
	for k, v in vars(parser.parse_intermixed_args()).items():
		cls, option_name = option_to_config[k]
		setattr(settings.setdefault(cls, cls()), option_name, v)
	return _main_config, settings


main_config, current_config = _setup_config()
