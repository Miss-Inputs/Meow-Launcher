import inspect
import logging
import os
import sys
from argparse import SUPPRESS, ArgumentParser, BooleanOptionalAction
from collections.abc import Collection, Mapping, MutableMapping, Sequence, Callable
from functools import wraps
from pathlib import Path, PurePath
from typing import Any, Generic, TypeVar

from meowlauncher.common_paths import config_dir, data_dir
from meowlauncher.util.io_utils import ensure_exist
from meowlauncher.util.utils import NoNonsenseConfigParser, sentence_case

from ._config_utils import ConfigValue, parse_path_list, parse_config_section_value, parse_value

__doc__ = """Config options are defined here, other than those specific to emulators or platforms"""
logger = logging.getLogger(__name__)

_main_config_path = config_dir.joinpath('config.ini')
_ignored_dirs_path = config_dir.joinpath('ignored_directories.txt')

_runtime_option_section = '<runtime option section>' #TODO: Can this be a sentinel-style object with ConfigValue section parameter having union str | that

_config_ini_values = {
	'get_series_from_name': ConfigValue('General', bool, False, 'Get series from name', 'Attempt to get series from parsing name'),
	'sort_multiple_dev_names': ConfigValue('General', bool, False, 'Sort multiple developer/publisher names', 'For games with multiple entities in developer/publisher field, sort alphabetically'),
	'wine_path': ConfigValue('General', str, 'wine', 'Wine path', 'Path to Wine executable for Windows games/emulators'),
	'wineprefix': ConfigValue('General', Path, None, 'Wine prefix', 'Optional Wine prefix to use for Wine'),
	'simple_disambiguate': ConfigValue('General', bool, True, 'Simple disambiguation', 'Use a simpler method of disambiguating games with same names'),
	'normalize_name_case': ConfigValue('General', int, 0, 'Normalize name case', 'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'), #TODO: Good case for an enum to be used here, even if argparse docs say don't use that with choices etc

	#TODO: This should be some kind of per-source options, whichever the best way to do that might be
	
	'skipped_source_files': ConfigValue('Arcade', Sequence[str], (), 'Skipped source files', 'List of MAME source files to skip (not including extension)'),
	'exclude_non_arcade': ConfigValue('Arcade', bool, False, 'Exclude non-arcade', 'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'),
	'exclude_pinball': ConfigValue('Arcade', bool, False, 'Exclude pinball', 'Whether or not to skip pinball games (physical pinball, not video pinball)'),
	'exclude_system_drivers': ConfigValue('Arcade', bool, False, 'Exclude system drivers', 'Skip machines used to launch other software (computers, consoles, etc)'),
	'exclude_non_working': ConfigValue('Arcade', bool, False, 'Exclude non-working', 'Skip any driver marked as not working'),
	'non_working_whitelist': ConfigValue('Arcade', Sequence[str], (), 'Non-working whitelist', 'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'),
	'use_xml_disk_cache': ConfigValue('Arcade', bool, True, 'Use XML disk cache', 'Store machine XML files on disk, maybe there are some scenarios where you might get better performance with it off (slow home directory storage, or just particularly fast MAME -listxml)'),

	'force_create_launchers': ConfigValue('Steam', bool, False, 'Force create launchers', 'Create launchers even for games which are\'nt launchable'),
	'warn_about_missing_icons': ConfigValue('Steam', bool, False, 'Warn about missing icons', 'Spam console with debug messages about icons not existing or being missing'),
	'use_steam_as_platform': ConfigValue('Steam', bool, True, 'Use Steam as platform', 'Set platform in game info to Steam instead of underlying platform'),

	'skipped_subfolder_names': ConfigValue('Roms', Sequence[str], (), 'Skipped subfolder names', 'Always skip these subfolders in every ROM dir'),
	'find_equivalent_arcade_games': ConfigValue('Roms', bool, False, 'Find equivalent arcade games by name', 'Get info from MAME machines of the same name'),
	'max_size_for_storing_in_memory': ConfigValue('Roms', int, 1024 * 1024, 'Max size for storing in memory', 'Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup (unless it doesn\'t actually speed things up)'),
	'libretro_database_path': ConfigValue('Roms', Path, None, 'libretro-database path', 'Path to libretro database for yoinking info from'),
	'libretro_frontend': ConfigValue('Roms', str, 'RetroArch', 'libretro frontend', 'Name of libretro frontend to use'),
	'libretro_cores_directory': ConfigValue('Roms', Path, None, 'libretro cores directory', 'Path to search for libretro cores if not explicitly specified'),

	'use_original_platform': ConfigValue('ScummVM', bool, False, 'Use original platform', 'Set the platform in game info to the original platform instead of leaving blank'),
	'scummvm_config_path': ConfigValue('ScummVM', Path, Path('~/.config/scummvm/scummvm.ini').expanduser(), 'ScummVM config path', 'Path to scummvm.ini, if not the default'),
	'scummvm_exe_path': ConfigValue('ScummVM', Path, 'scummvm', 'ScummVM executable path', 'Path to scummvm executable, if not the default'),

	'gog_folders': ConfigValue('GOG', list[Path], (), 'GOG folders', 'Folders where GOG games are installed'),
	'use_gog_as_platform': ConfigValue('GOG', bool, False, 'Use GOG as platform', 'Set platform in game info to GOG instead of underlying platform'),
	'windows_gog_folders': ConfigValue('GOG', list[Path], (), 'Windows GOG folders', 'Folders where Windows GOG games are installed'),
	'use_system_dosbox': ConfigValue('GOG', bool, True, 'Use system DOSBox', 'Use the version of DOSBox on this system instead of running Windows DOSBox through Wine'),
	'dosbox_path': ConfigValue('GOG', Path, "dosbox", 'DOSBox path', 'If using system DOSBox, executable name/path or just "dosbox" if left blank'),

	'itch_io_folders': ConfigValue('itch.io', list[Path], (), 'itch.io folders', 'Folders where itch.io games are installed'),
	'use_itch_io_as_platform': ConfigValue('itch.io', bool, False, 'Use itch.io as platform', 'Set platform in game info to itch.io instead of underlying platform'),

	#These shouldn't end up in config.ini as they're intended to be set per-run
	'print_times': ConfigValue(_runtime_option_section, bool, False, 'Print times', 'Print how long it takes to do things'),
	'full_rescan': ConfigValue(_runtime_option_section, bool, False, 'Full rescan', 'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'),
	'organize_folders': ConfigValue(_runtime_option_section, bool, False, 'Organize folders', 'Use the organized folders frontend'),
}

def get_config_ini_options() -> Mapping[str, Mapping[str, ConfigValue]]:
	"""Returns the config definitions other than those intended to be set at runtime: {section: {name: ConfigValue}}
	We're getting rid of this one"""
	opts: MutableMapping[str, MutableMapping[str, ConfigValue]] = {}
	for k, v in _config_ini_values.items():
		if v.section == _runtime_option_section:
			continue
		opts.setdefault(v.section, {})[k] = v
	return opts

def get_runtime_options() -> Mapping[str, ConfigValue]:
	"""Returns the config definitions only intended to be used at runtime as command line args, which means they don't go in config.ini
	We're getting rid of this one, and that distinction"""
	return {name: opt for name, opt in _config_ini_values.items() if opt.section == _runtime_option_section}

def get_command_line_arguments() -> ArgumentParser:
	"""Use with parents= kwarg of ArgumentParser
	Hmm still not sure if this is the best way…"""
	p = ArgumentParser()
	section_groups: dict[str, Any | ArgumentParser]  = {}
	#We lie somewhat to the type checker here because it bugs me that _ArgumentGroup is a private type and so we can't really type hint it with that, but this will be close enough
	for name, option in _config_ini_values.items():
		name = name.replace('_', '-')
		section = option.section
		group = section_groups.setdefault(section, p.add_argument_group(section)) #Should have a description innit
		if option.type == bool:
			group.add_argument(f'--{name}', action=BooleanOptionalAction, help=option.description, default=SUPPRESS)
		elif option.type == Sequence[Path]:
			group.add_argument(f'--{name}', nargs='?', type=Path, help=option.description, default=SUPPRESS)
		elif option.type == Sequence[str]:
			group.add_argument(f'--{name}', nargs='?', help=option.description, default=SUPPRESS)
		else:
			group.add_argument(f'--{name}', type=option.type, help=option.description, default=SUPPRESS)
	return p

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

class YeOldeConfig():
	"""Singleton which holds config
	This will be reworked and that is a threat"""
	class __Config():
		def __init__(self) -> None:
			self.values = {}
			for name, config in _config_ini_values.items():
				self.values[name] = config.default_value

			#For now, just parse what is known… ideally we want ArgumentParser to be the main thing
			borf = get_command_line_arguments().parse_known_intermixed_args()
			self.runtime_overrides = vars(borf[0])
			parser = NoNonsenseConfigParser()
			self.parser = parser
			ensure_exist(_main_config_path)
			self.parser.read(_main_config_path)

			self.ignored_directories = _load_ignored_directories()

		def __getattr__(self, name: str) -> Any:
			if name in self.values:
				if name in self.runtime_overrides:
					return self.runtime_overrides[name]
				config = _config_ini_values[name]

				if config.section == _runtime_option_section:
					return config.default_value

				section = self.parser[config.section]
				if name not in section:
					return config.default_value

				return parse_config_section_value(section, name, config.type, config.default_value)
				
			raise AttributeError(name)

	__instance = None

	@staticmethod
	def getConfig() -> __Config:
		if YeOldeConfig.__instance is None:
			YeOldeConfig.__instance = YeOldeConfig.__Config()
		return YeOldeConfig.__instance

old_main_config = YeOldeConfig().getConfig()

T = TypeVar('T')
class ConfigProperty(Generic[T]):
	"""property decorator with some more attributes
	Damn here I was thinking "haha I'll never need to know how descriptors work" okay maybe I didn't need to do this"""
	def __init__(self, func: 'Callable[[Any], T]', section: str, readable_name: str | None) -> None:
		self.func = func
		self.section = section
		self.readable_name = readable_name or sentence_case(func.__name__.replace('_', ' '))
		self.description = func.__doc__ or self.readable_name
		self.type = inspect.get_annotations(func).get('return', str)
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
 
main_config = MainConfig()
