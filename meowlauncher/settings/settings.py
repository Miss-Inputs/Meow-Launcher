"""Config options are defined here, other than those specific to emulators or platforms"""

import logging
from abc import abstractmethod
from argparse import ArgumentParser, BooleanOptionalAction
from collections.abc import Collection, Sequence
from pathlib import Path, PurePath
from typing import Literal, get_args

from class_doc import extract_docs_from_cls_obj
from pydantic import Field
from pydantic_settings import BaseSettings

from meowlauncher.common_paths import config_dir, data_dir

logger = logging.getLogger(__name__)
# TODO: Prolly use toml instead of ini, might be nicer
# TODO: Context manager to override settings, like matplotlib rc_context for example

_ignored_dirs_path = config_dir.joinpath('ignored_directories.txt')
# TODO: Surely there is some way for this to be nicer


def _load_ignored_directories() -> Collection[PurePath]:
	ignored_directories: set[PurePath] = set()

	try:
		with _ignored_dirs_path.open('rt', encoding='utf-8') as ignored_txt:
			ignored_directories.update(PurePath(line.strip()) for line in ignored_txt)
	except FileNotFoundError:
		pass

	return ignored_directories


ignored_directories = _load_ignored_directories()

# Might be handy to extend Pydantic's Path types to some kind of "file but might not exist"? Well that might be also not useful at all
# TODO: Custom validator for names of sources, emulators, etc


# TODO: ini_settings too:
# # _config_file_argument_parser = ArgumentParser(add_help=False)
# # #TODO: Load additional config files - but let this be specified in the main config file as an "include" etc - see also issue #146
# # _config_file_argument_parser.add_argument('--config-file', help='If provided, load config from here instead of config.ini')
# # args, self._remaining_args = _config_file_argument_parser.parse_known_args()
# #TODO: Nah that sucks because I don't want to do the arg parsing here

# _config_parser.read(self.options_file_name())
# if _config_parser.has_section(self.section()):
# 	for option, value in _config_parser.items(self.section()):
# 		if option not in _configs:
# 			logger.warning('Unknown config option %s in section %s (value: %s)', option, self.section(), value)
# 			continue
# 		config = _configs[option]
# 		self.values[option] = parse_value(value, config.type)


# TODO: Config.Config.customize_sources should return init_settings, argparser_settings, env_settings, some kind of extra settings, ini_settings


def _remove_optional(annotation: type | None):
	if not annotation:
		return None
	args = get_args(annotation)
	if len(args) == 2 and args[1] == type(None):
		return args[0]
	return annotation


def _field_name_to_cli_arg(s: str, prefix: str | None = None):
	option = s.replace('_', '-')
	if prefix:
		option = f'{prefix}:{option}'
	return f'--{option}'


class Settings(BaseSettings):
	"""Base class for instances of configuration. Define things with @configoption and get a parser, then update config.values

	Loads from stuff in this order:
	default value
	config.ini (or whatever --config-file specifies)
	(TODO) additional config files
	environment variables
	Command line arguments

	TODO: The tricky part then is emulator config and platform config - is there a nice way to get them to use this? I'd like to have them settable from the command line but like --duckstation:compat-db=<path> or something like that
	"""

	# TODO: Can we have env_prefix dynamically set from cls.prefix(), but the rest of this stays the same?
	model_config = {
		'env_file_encoding': 'utf-8',
		'env_prefix': 'MEOW_LAUNCHER_',
		'validate_assignment': True,
	}

	# @classmethod
	# def customize_sources(cls, _init_settings):
	# 	pass
	# TODO: Need an ini file settings source

	@classmethod
	@abstractmethod
	def section(cls) -> str:
		"""Section that should be used for reading this from options_file_name."""

	@classmethod
	def section_help(cls) -> str | None:
		"""Help text to be added to argument group"""
		return cls.__doc__

	@classmethod
	def prefix(cls) -> str | None:
		"""Prefix to be added to command line arguments for these options."""
		return None

	@classmethod
	def options_file_name(cls) -> str:
		"""Name of the file to load options from. Defaults to config.ini"""
		return 'config.ini'

	@classmethod
	def add_argparser_group(cls, argparser: ArgumentParser):
		"""Adds a group for this config to an ArgumentParser. See config for how to parse it - to avoid namespace collisions, the qualified name of this class is added"""
		group = (
			argparser
			if cls.section() == MainConfig.section()
			else argparser.add_argument_group(cls.section(), description=cls.section_help())
		)
		prefix = cls.prefix()
		docstrings = extract_docs_from_cls_obj(cls)

		for k, v in cls.model_fields.items():
			names = (k, v.alias) if v.alias else (k,)
			options = [_field_name_to_cli_arg(name, prefix) for name in names]

			description = v.description or (docstrings[k][0] if k in docstrings else None)
			destination_in_namespace = f'{cls.__qualname__}.{k}'

			default = v.get_default(call_default_factory=True)
			t = _remove_optional(v.annotation)
			if t == bool:
				group.add_argument(
					*options,
					action=BooleanOptionalAction,
					help=description,
					default=default,
					dest=destination_in_namespace,
					metavar=k,
				)
			elif t == Sequence[Path]:
				# TODO: It would be more useful to add to the default value
				group.add_argument(
					*options,
					nargs='*',
					type=Path,
					help=description,
					default=default,
					dest=destination_in_namespace,
					metavar=k,
				)
			elif t == Sequence[str]:
				group.add_argument(
					*options,
					nargs='*',
					help=description,
					default=default,
					dest=destination_in_namespace,
					metavar=k,
				)
			else:
				if not t:
					logger.warning('%s in %s has no type annotation, defaulting to str', k, cls)
				# Let Pydantic convert it to whatever fancy type for us
				t = str
				group.add_argument(
					*options,
					type=str,
					help=description,
					default=default,
					dest=destination_in_namespace,
					metavar=k,
				)
		return group


class MainConfig(Settings):
	"""General options not specific to anything else"""

	@classmethod
	def section(cls) -> str:
		return 'General'

	output_folder: Path = data_dir / 'apps'
	"""Folder where launchers go"""

	image_folder: Path = data_dir / 'images'
	"""Folder to store images extracted from games with embedded images"""

	organized_output_folder: Path = data_dir / 'organized_apps'
	"""Folder to put subfolders in for the organized folders frontend"""

	sources: Sequence[str] = Field(default_factory=list)
	"""If specified, only add games from GameSources with this name
	Useful for testing and such"""
	# TODO: Add validation so that Pydantic converts it to a GameSource for us (see add_games._get_game_source), though we will need to finish refactoring GOG/itch.io into being GameSources

	disambiguate: bool = True
	"""After adding games, add info in brackets to the end of the names of games that have the same name to identify them (such as what type or platform they are), defaults to true"""

	logging_level: str = Field(
		default_factory=lambda: logging.getLevelName(logger.getEffectiveLevel()), alias='log_level'
	)
	"""Logging level (e.g. INFO, DEBUG, WARNING, etc)"""
	# TODO: There must be some way to make Pydantic accept both an int or a str and convert the right way

	other_images_to_use_as_icons: Sequence[str] = Field(default_factory=list)
	"""If there is no icon, use these images as icons, if they are there"""

	full_rescan: bool = False
	"""Regenerate every launcher from scratch instead of just what's new and removing what's no longer there"""

	organize_folders: bool = False
	"""Use the organized folders frontend
	It sucks, so it's turned off by default"""

	get_series_from_name: bool = False
	"""Attempt to get series from parsing name
	This code also sucks, so it's turned off by default"""

	sort_multiple_dev_names: bool = False
	"""For games with multiple entities in developer/publisher field, sort alphabetically"""

	wine_path: Path = Path('wine')
	"""Path to Wine executable for Windows games/emulators
	TODO: This should just be a config for a global Runner"""

	wineprefix: Path | None = None
	"""Optional Wine prefix to use for Wine
	TODO: This should just be a config for a global Runner"""

	simple_disambiguate: bool = True
	"""Use a simpler method of disambiguating games with same names"""

	normalize_name_case: Literal[0, 1, 2, 3] = 0
	"""Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)"""
	# TODO: Should be an enum

	libretro_database_path: Path | None = None
	"""Path to libretro database for yoinking info from"""
	# Not sure if this should be in ROMsConfig instead…

	libretro_frontend: str | None = 'RetroArch'
	"""Name of libretro frontend to use"""
	# TODO: This should be the default if not specified for a particular core - but there is much fancy stuff to do there, which is all not really relevant until we have more LibretroFrontends

	libretro_cores_directory: Path = Path('/usr/lib/libretro')
	"""Path to search for libretro cores if not default of /usr/lib/libretro"""
	# TODO: This should look at retroarch.cfg for the default value (I guess)
	# TODO: Maybe this should be more than one directory? It's just to set the default path of LibretroCore, so it should look wherever it exists"""

	dosbox_path: Path = Path('dosbox')
	"""If using system DOSBox, executable name/path or just "dosbox" if left blank"""
	# TODO: Should also be a global Runner
