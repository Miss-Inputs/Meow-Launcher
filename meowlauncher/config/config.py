import inspect
import logging
import os
import types
import typing
from abc import ABC, abstractmethod
from argparse import SUPPRESS, ArgumentParser, BooleanOptionalAction
from collections.abc import Callable, Collection, Mapping, Sequence
from functools import update_wrapper
from pathlib import Path, PurePath
from typing import Any, Generic, TypeVar, get_args, get_origin, overload

from meowlauncher.common_paths import config_dir, data_dir
from meowlauncher.util.utils import NoNonsenseConfigParser

from ._config_utils import parse_value

__doc__ = """Config options are defined here, other than those specific to emulators or platforms"""
logger = logging.getLogger(__name__)

_ignored_dirs_path = config_dir.joinpath('ignored_directories.txt')

def _load_ignored_directories() -> Collection[PurePath]:
	ignored_directories: set[PurePath] = set()

	try:
		with _ignored_dirs_path.open('rt', encoding='utf-8') as ignored_txt:
			ignored_directories.update(PurePath(line.strip()) for line in ignored_txt)
	except FileNotFoundError:
		pass

	return ignored_directories

ignored_directories = _load_ignored_directories()

T = TypeVar('T')
S = TypeVar('S', bound='Config')
class ConfigProperty(Generic[T]):
	"""Similar to property() with some more attributes, used with @configoption
	Damn here I was thinking "haha I'll never need to know how descriptors work" okay maybe I didn't need to do this
	
	Because decorators can't be bound to classmethods (as of 3.11 anyway), func needs a self, so we can't call it to get the default value from here…"""
	def __init__(self, func: 'Callable[[S], T]', readable_name: str | None) -> None:
		self.func = func
		self.readable_name = readable_name or func.__name__.replace('_', ' ').capitalize()
		self.description = func.__doc__ or self.readable_name
		self.type = inspect.get_annotations(func, eval_str=True).get('return', str)
		if isinstance(self.type, types.UnionType) or get_origin(self.type) == typing.Union:
			type_args = get_args(self.type)
			#Remove optional from the return type, as that's not what we use .type for, but I don't think we're allowed to simply import _UnionGenericAlias, so it gets confused with trying to handle __args__ directly, and also we do want to make sure we don't strip out the args from Sequence
			#We'll just assume all unions and such are like this, don't be weird and type a config as str | int or something
			self.type = type_args[0]
		
	def __get__(self, obj: S | None, _: type[S] | None) -> 'T | ConfigProperty[T]':
		if obj is None:
			return self
		return obj.values.get(self.func.__name__, self.func(obj))

@overload
def configoption(func: 'Callable[[S], T]', *, readable_name: str | None = None) -> ConfigProperty[T]: ...
@overload
def configoption(func: None=None, *, readable_name: str | None = None) -> 'Callable[[Callable[[S], T]], ConfigProperty[T]]': ...

def configoption(func: 'Callable[[S], T] | None' = None, *, readable_name: str | None = None):
	"""Decorator: Marks this method as being a config option, which replaces it with a ConfigProperty instance; must be inside a Config
	Description is taken from docstring, readable_name is the function name in sentence case if not provided, default value is the original function return value"""
	def deco(func: 'Callable[[S], T]') -> 'ConfigProperty[T]':
		wrapped = ConfigProperty(func, readable_name)
		return update_wrapper(wrapped, func)
	if func:
		return deco(func)
	return deco

class Config(ABC):
	"""Base class for instances of configuration. Define things with @configoption and get a parser, then update config.values
	
	Loads from stuff in this order:
	default value
	config.ini (or whatever --config-file specifies)
	(TODO) additional config files
	environment variables
	Command line arguments
	
	TODO: The tricky part then is emulator config and platform config - is there a nice way to get them to use this? I'd like to have them settable from the command line but it would need a prefix, --duckstation-compat-db=<path> or whatever
	"""
	_instance = None
	def __new__(cls):
		if not cls._instance:
			cls._instance = super(Config, cls).__new__(cls)
			cls._instance._inited = False
		return cls._instance

	@classmethod
	def get_configs(cls) -> Mapping[str, ConfigProperty[Any]]:
		"""Gets all the ConfigProperty objects in this class.
		Uses dir() and getattr() so that it works with inheritance"""
		return {k: getattr(cls, k) for k in dir(cls) if isinstance(getattr(cls, k), ConfigProperty)}
		#return {k: v for k, v in vars(cls).items() if isinstance(v, ConfigProperty)}

	def __init__(self) -> None:
		self._inited: bool
		if self._inited:
			#Apparently this is how singletons work and have always worked, as this is called repeatedly otherwise and self.values is set again to {} and that defeats the purpose
			return
		self._inited = True
		_configs = self.get_configs()

		_config_parser = NoNonsenseConfigParser()
		self.values: dict[str, Any] = {}
		# _config_file_argument_parser = ArgumentParser(add_help=False)
		# #TODO: Load additional config files - but let this be specified in the main config file as an "include" etc - see also issue #146
		# _config_file_argument_parser.add_argument('--config-file', help='If provided, load config from here instead of config.ini')
		# args, self._remaining_args = _config_file_argument_parser.parse_known_args()
		#TODO: Nah that sucks because I don't want to do the arg parsing here
		
		_config_parser.read(self.options_file_name())
		if _config_parser.has_section(self.section()):
			for option, value in _config_parser.items(self.section()):
				if option not in _configs:
					logger.warning('Unknown config option %s in section %s (value: %s)', option, self.section(), value)
					continue
				config = _configs[option]
				self.values[option] = parse_value(value, config.type)

		prefix = self.prefix()
		for k, v in _configs.items():
			env_var = os.getenv(f'MEOW_LAUNCHER_{prefix.upper().replace("-", "_") + "_" if prefix else ""}{k.upper()}')
			if env_var:
				self.values[k] = parse_value(env_var, v.type)

	def add_argparser_group(self, argparser: ArgumentParser) -> None:
		"""Adds a group for this config to an ArgumentParser. See __main__ for how to parse it - to avoid namespace collisions, the qualified name of this class is added"""
		group = argparser.add_argument_group(self.section(), description=self.section_help())
		prefix = self.prefix()
		for k, v in self.get_configs().items():
			option = k.replace("_", "-")
			if prefix:
				option = f'{prefix}-{option}'
			option = f'--{option}'
			description = v.description.splitlines()[0]
			destination_in_namespace = f'{self.__class__.__qualname__}.{k}'
			if v.type == bool:
				group.add_argument(option, action=BooleanOptionalAction, help=description, default=self.values.get(k, SUPPRESS), dest=destination_in_namespace, metavar=k)
			elif v.type == Sequence[Path]:
				#TODO: It would be more useful to add to the default value
				group.add_argument(option, nargs='*', type=Path, help=description, default=self.values.get(k, SUPPRESS), dest=destination_in_namespace, metavar=k)
			elif v.type == Sequence[str]:
				group.add_argument(option, nargs='*', help=description, default=self.values.get(k, SUPPRESS), dest=destination_in_namespace, metavar=k)
			else:
				group.add_argument(option, type=v.type, help=description, default=self.values.get(k, SUPPRESS), dest=destination_in_namespace, metavar=k)

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

class MainConfig(Config):
	"""General options not specific to anything else"""

	@classmethod
	def section(cls) -> str:
		return 'General'
		
	@configoption
	def output_folder(self) -> Path:
		"""Folder where launchers go"""
		return data_dir.joinpath('apps')

	@configoption
	def image_folder(self) -> Path:
		'Folder to store images extracted from games with embedded images'
		return data_dir.joinpath('images')

	@configoption
	def organized_output_folder(self) -> Path:
		'Folder to put subfolders in for the organized folders frontend'
		return data_dir.joinpath('organized_apps')

	@configoption
	def sources(self) ->  Sequence[str]:
		"""If specified, only add games from GameSources with this name
		Useful for testing and such"""
		return []

	@configoption
	def disambiguate(self) -> bool:
		"""After adding games, add info in brackets to the end of the names of games that have the same name to identify them (such as what type or platform they are), defaults to true"""
		return True

	@configoption
	def logging_level(self) -> str:
		"""Logging level (e.g. INFO, DEBUG, WARNING, etc)"""
		return str(logging.getLevelName(logger.getEffectiveLevel()))

	@configoption
	def other_images_to_use_as_icons(self) -> Sequence[str]:
		"""If there is no icon, use these images as icons, if they are there"""
		return []

	@configoption
	def full_rescan(self) -> bool:
		"""Regenerate every launcher from scratch instead of just what's new and removing what's no longer there"""
		return False

	@configoption
	def organize_folders(self) -> bool:
		"""Use the organized folders frontend
		It sucks, so it's turned off by default"""
		return False

	@configoption
	def get_series_from_name(self) -> bool:
		'Attempt to get series from parsing name'
		return False

	@configoption
	def sort_multiple_dev_names(self) -> bool:
		'For games with multiple entities in developer/publisher field, sort alphabetically'
		return False

	@configoption
	def wine_path(self) -> Path:
		"""Path to Wine executable for Windows games/emulators
		TODO: This should just be a config for a global Runner"""
		return Path('wine')

	@configoption
	def wineprefix(self) -> Path | None:
		"""Optional Wine prefix to use for Wine
		TODO: This should just be a config for a global Runner"""
		return None

	@configoption
	def simple_disambiguate(self) -> bool:
		'Use a simpler method of disambiguating games with same names'
		return True

	@configoption
	def normalize_name_case(self) -> int:
		'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'
		return 0 #TODO: Good case for an enum to be used here, even if argparse docs say don't use that with choices etc

	@configoption
	def libretro_database_path(self) -> Path | None:
		'Path to libretro database for yoinking info from'
		#Not sure if this should be in ROMsConfig instead…
		return None

	@configoption
	def libretro_frontend(self) -> str | None:
		"""Name of libretro frontend to use
		TODO: This should be a default and you can specify things instead"""
		return 'RetroArch'

	@configoption
	def libretro_cores_directory(self) -> Path:
		"""Path to search for libretro cores if not default of /usr/lib/libretro
		TODO: This should look at retroarch.cfg for the default value (I guess)
		TODO: Maybe this should be more than one directory? It's just to set the default path of LibretroCore, so it should look wherever it exists"""
		return Path('/usr/lib/libretro')

	@configoption
	def dosbox_path(self) -> Path:
		'If using system DOSBox, executable name/path or just "dosbox" if left blank'
		return Path('dosbox')

main_config = MainConfig()
