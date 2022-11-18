import inspect
import logging
import os
import sys
from argparse import SUPPRESS, ArgumentParser, BooleanOptionalAction
from collections.abc import Collection, Sequence, Callable
from functools import wraps
from pathlib import Path, PurePath
import types
from typing import Any, Generic, TypeVar, get_args, get_origin
import typing

from meowlauncher.common_paths import config_dir, data_dir
from meowlauncher.util.utils import NoNonsenseConfigParser, sentence_case

from ._config_utils import parse_path_list, parse_value

__doc__ = """Config options are defined here, other than those specific to emulators or platforms"""
logger = logging.getLogger(__name__)

_main_config_path = config_dir.joinpath('config.ini')
_ignored_dirs_path = config_dir.joinpath('ignored_directories.txt')

def _load_ignored_directories() -> Collection[PurePath]:
	ignored_directories: set[PurePath] = set()

	try:
		with _ignored_dirs_path.open('rt', encoding='utf-8') as ignored_txt:
			ignored_directories.update(PurePath(line.strip()) for line in ignored_txt)
	except FileNotFoundError:
		pass

	if '--ignored-directories' in sys.argv:
		#TODO Move to get_command_line_arguments or otherwise somewhere else
		index = sys.argv.index('--ignored-directories')
		arg = sys.argv[index + 1]
		ignored_directories.update(parse_path_list(arg))

	return ignored_directories

ignored_directories = _load_ignored_directories()

T = TypeVar('T')
class ConfigProperty(Generic[T]):
	"""property decorator with some more attributes
	Damn here I was thinking "haha I'll never need to know how descriptors work" okay maybe I didn't need to do this"""
	def __init__(self, func: 'Callable[[Any], T]', section: str, readable_name: str | None) -> None:
		self.func = func
		self.section = section
		self.readable_name = readable_name or sentence_case(func.__name__.replace('_', ' '))
		self.description = func.__doc__ or self.readable_name
		self.type = inspect.get_annotations(func, eval_str=True).get('return', str)
		if isinstance(self.type, types.UnionType) or get_origin(self.type) == typing.Union:
			type_args = get_args(self.type)
			#Remove optional from the return type, as that's not what we use .type for, but I don't think we're allowed to simply import _UnionGenericAlias, so it gets confused with trying to handle __args__ directly, and also we do want to make sure we don't strip out the args from 
			#We'll just assume all unions and such are like this, don't be weird and type a config as str | int or something
			self.type = type_args[0]
	def __get__(self, __obj: Any, _: Any) -> T:
		return self.func(__obj)

S = TypeVar('S', bound='Config')
def configoption(section: str, readable_name: str | None = None) -> 'Callable[[Callable[[S], T]], ConfigProperty[T]]':
	"""
	Decorator: Marks this method as being a config option, which replaces it with a ConfigProperty instance; must be inside a Config
	Description is taken from docstring, readable_name is the function name in sentence case if not provided, default value is the original function return value"""
	def deco(func: 'Callable[[S], T]') -> 'ConfigProperty[T]':
		@wraps(func)
		def inner(self: S) -> T:
			return self.values.get(func.__name__, func(self))
		return ConfigProperty(inner, section, readable_name)
	return deco

class Config():
	"""Base class for instances of configuration. Define things with @configoption and get a parser, then update config.values
	
	Loads from stuff in this order:
	default value
	config.ini (or whatever --config-file specifies)
	(TODO) additional config files
	environment variables
	Command line arguments
	
	TODO: We probably want each section to be for each Config instance, so MainConfig would be the General section (I guess there'd be a class variable somewhere), we would have a RomsConfig(Config) with section == ROMs or for everything else

	The tricky part then is emulator config and platform config - is there a nice way to get them to use this? I'd like to have them settable from the command line but it would need a prefix, --duckstation-compat-db=<path> or whatever
	"""
	def __init__(self) -> None:
		self._configs = {k: v for k, v in vars(self.__class__).items() if isinstance(v, ConfigProperty)}

		self._config_parser = NoNonsenseConfigParser()
		self.values: dict[str, Any] = {}
		self._config_file_argument_parser = ArgumentParser(add_help=False)
		#TODO: Load additional config files - but let this be specified in the main config file as an "include" etc - see also issue #146
		self._config_file_argument_parser.add_argument('--config-file', help='If provided, load config from here instead of config.ini')
		args, self._remaining_args = self._config_file_argument_parser.parse_known_args()
		
		self._config_parser.read(args.config_file if args.config_file else _main_config_path)
		for section in self._config_parser.sections():
			for option, value in self._config_parser.items(section):
				if option not in self._configs:
					#Hmm can't really spam this warning when YeOldeConfig is still there
					#logger.warning('Unknown config option %s in section %s (value: %s)', option, section, value)
					continue
				config = self._configs[option]
				self.values[option] = parse_value(value, config.type)

		for k, v in self._configs.items():
			env_var = os.getenv('MEOW_LAUNCHER' + k.upper())
			if env_var:
				self.values[k] = parse_value(env_var, v.type)

		self.parser = ArgumentParser(add_help=False, parents=[self._config_file_argument_parser])
		section_groups: dict[str, Any | ArgumentParser]  = {}
		#We lie somewhat to the type checker here because it bugs me that _ArgumentGroup is a private type and so we can't really type hint it with that, but this will be close enough
		for k, v in self._configs.items():
			group = section_groups.setdefault(v.section, self.parser.add_argument_group(v.section)) #Should have a description innit
			option = f'--{k.replace("_", "-")}'
			if v.type == bool:
				group.add_argument(option, action=BooleanOptionalAction, help=v.description, default=self.values.get(k, SUPPRESS), dest=k)
			elif v.type == Sequence[Path]:
				#TODO: It would be more useful to add to the default value
				group.add_argument(option, nargs='?', type=Path, help=v.description, default=self.values.get(k, SUPPRESS), dest=k)
			elif v.type == Sequence[str]:
				group.add_argument(option, nargs='?', help=v.description, default=self.values.get(k, SUPPRESS), dest=k)
			else:
				group.add_argument(option, type=v.type, help=v.description, default=self.values.get(k, SUPPRESS), dest=k)

class MainConfig(Config):
	"""General options not specific to anything else"""
		
	@configoption('Paths')
	def output_folder(self) -> Path:
		"""Folder where launchers go"""
		return data_dir.joinpath('apps')

	@configoption('Paths')
	def image_folder(self) -> Path:
		'Folder to store images extracted from games with embedded images'
		return data_dir.joinpath('images')

	@configoption('Paths')
	def organized_output_folder(self) -> Path:
		'Folder to put subfolders in for the organized folders frontend'
		return data_dir.joinpath('organized_apps')

	@configoption('General')
	def logging_level(self) -> str:
		"""Logging level (e.g. INFO, DEBUG, WARNING, etc)"""
		return str(logging.getLevelName(logger.getEffectiveLevel()))

	@configoption('General')
	def other_images_to_use_as_icons(self) -> Sequence[str]:
		"""If there is no icon, use these images as icons, if they are there"""
		return []

	@configoption('General') #TODO: Some kind of "don't put in the config.ini" attribute if we ever make code again that generates a template config.ini
	def print_times(self) -> bool:
		'Print how long it takes to do things'
		return False

	#These shouldn't end up in config.ini as they're intended to be set per-run
	@configoption('General')
	def full_rescan(self) -> bool:
		'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'
		return False
	@configoption('General')
	def organize_folders(self) -> bool:
		'Use the organized folders frontend'
		return False

	@configoption('General')
	def get_series_from_name(self) -> bool:
		'Attempt to get series from parsing name'
		return False

	@configoption('General')
	def sort_multiple_dev_names(self) -> bool:
		'For games with multiple entities in developer/publisher field, sort alphabetically'
		return False

	@configoption('General')
	def wine_path(self) -> str:
		'Path to Wine executable for Windows games/emulators'
		return 'wine'

	@configoption('General')
	def wineprefix(self) -> Path | None:
		'Optional Wine prefix to use for Wine'
		return None

	@configoption('General')
	def simple_disambiguate(self) -> bool:
		'Use a simpler method of disambiguating games with same names'
		return True

	@configoption('General')
	def normalize_name_case(self) -> int:
		'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'
		return 0 #TODO: Good case for an enum to be used here, even if argparse docs say don't use that with choices etc

	#TODO: This should be some kind of per-source options, whichever the best way to do that might be
	
	@configoption('Arcade')
	def skipped_source_files(self) -> Sequence[str]:
		'List of MAME source files to skip (not including extension)'
		return ()

	@configoption('Arcade')
	def exclude_non_arcade(self) -> bool:
		'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'
		return False

	@configoption('Arcade')
	def exclude_pinball(self) -> bool:
		'Whether or not to skip pinball games (physical pinball, not video pinball)'
		return False

	@configoption('Arcade')
	def exclude_system_drivers(self) -> bool:
		'Skip machines used to launch other software (computers, consoles, etc)'
		return False

	@configoption('Arcade')
	def exclude_non_working(self) -> bool:
		'Skip any driver marked as not working'
		return False

	@configoption('Arcade')
	def non_working_whitelist(self) -> Sequence[str]:
		'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'
		return ()

	@configoption('Arcade')
	def use_xml_disk_cache(self) -> bool:
		'Store machine XML files on disk, maybe there are some scenarios where you might get better performance with it off (slow home directory storage, or just particularly fast MAME -listxml)'
		return True

	@configoption('Steam')
	def force_create_launchers(self) -> bool:
		'Create launchers even for games which are\'nt launchable'
		return False

	@configoption('Steam')
	def warn_about_missing_icons(self) -> bool:
		'Spam console with debug messages about icons not existing or being missing'
		return False

	@configoption('Steam')
	def use_steam_as_platform(self) -> bool:
		'Set platform in game info to Steam instead of underlying platform'
		return True

	@configoption('Roms')
	def skipped_subfolder_names(self) -> Sequence[str]:
		'Always skip these subfolders in every ROM dir'
		return ()

	@configoption('Roms')
	def find_equivalent_arcade_games(self) -> bool:
		'Get info from MAME machines of the same name'
		return False

	@configoption('Roms')
	def max_size_for_storing_in_memory(self) -> int:
		'Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup (unless it doesn\'t actually speed things up)'
		return 1024 * 1024

	@configoption('Roms')
	def libretro_database_path(self) -> Path | None:
		'Path to libretro database for yoinking info from'
		return None

	@configoption('Roms')
	def libretro_frontend(self) -> str | None:
		'Name of libretro frontend to use'
		return 'RetroArch'

	@configoption('Roms')
	def libretro_cores_directory(self) -> Path | None:
		'Path to search for libretro cores if not explicitly specified'
		return None

	@configoption('ScummVM')
	def use_original_platform(self) -> bool:
		'Set the platform in game info to the original platform instead of leaving blank'
		return False

	@configoption('ScummVM')
	def scummvm_config_path(self) -> Path:
		'Path to scummvm.ini, if not the default'
		return Path('~/.config/scummvm/scummvm.ini').expanduser()

	@configoption('ScummVM')
	def scummvm_exe_path(self) -> Path:
		'Path to scummvm executable, if not the default'
		return Path('scummvm')

	@configoption('GOG')
	def gog_folders(self) -> Sequence[Path]:
		'Folders where GOG games are installed'
		return ()

	@configoption('GOG')
	def use_gog_as_platform(self) -> bool:
		'Set platform in game info to GOG instead of underlying platform'
		return False

	@configoption('GOG')
	def windows_gog_folders(self) -> Sequence[Path]:
		'Folders where Windows GOG games are installed'
		return ()

	@configoption('GOG')
	def use_system_dosbox(self) -> bool:
		'Use the version of DOSBox on this system instead of running Windows DOSBox through Wine'
		return True

	@configoption('GOG')
	def dosbox_path(self) -> Path:
		'If using system DOSBox, executable name/path or just "dosbox" if left blank'
		return Path('dosbox')

	@configoption('itch.io')
	def itch_io_folders(self) -> Sequence[Path]:
		'Folders where itch.io games are installed'
		return ()

	@configoption('itch.io')
	def use_itch_io_as_platform(self) -> bool:
		'Set platform in game info to itch.io instead of underlying platform'
		return False

main_config = MainConfig()
