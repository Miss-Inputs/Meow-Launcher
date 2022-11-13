import inspect
import logging
import sys
from argparse import SUPPRESS, ArgumentParser, BooleanOptionalAction
from collections.abc import Collection, Mapping, MutableMapping
from functools import wraps
from pathlib import Path, PurePath
from typing import Any

from meowlauncher.common_paths import config_dir, data_dir
from meowlauncher.util.io_utils import ensure_exist
from meowlauncher.util.utils import NoNonsenseConfigParser, sentence_case

from ._config_utils import ConfigValue, parse_path_list, parse_value, parse_string_list

logger = logging.getLogger(__name__)

_main_config_path = config_dir.joinpath('config.ini')
_ignored_dirs_path = config_dir.joinpath('ignored_directories.txt')

_runtime_option_section = '<runtime option section>' #TODO: Can this be a sentinel-style object with ConfigValue section parameter having union str | that

_config_ini_values = {
	'output_folder': ConfigValue('Paths', Path, data_dir.joinpath('apps'), 'Output folder', 'Folder to put launchers'),
	'organized_output_folder': ConfigValue('Paths', Path, data_dir.joinpath('organized_apps'), 'Organized output folder', 'Folder to put subfolders in for the organized folders frontend'),
	'image_folder': ConfigValue('Paths', Path, data_dir.joinpath('images'), 'Image folder', 'Folder to store images extracted from games with embedded images'),

	'get_series_from_name': ConfigValue('General', bool, False, 'Get series from name', 'Attempt to get series from parsing name'),
	'use_other_images_as_icons': ConfigValue('General', list[str], (), 'Use other images as icons', 'If there is no icon, use these images as icons if they are there'),
	'sort_multiple_dev_names': ConfigValue('General', bool, False, 'Sort multiple developer/publisher names', 'For games with multiple entities in developer/publisher field, sort alphabetically'),
	'wine_path': ConfigValue('General', str, 'wine', 'Wine path', 'Path to Wine executable for Windows games/emulators'),
	'wineprefix': ConfigValue('General', Path, None, 'Wine prefix', 'Optional Wine prefix to use for Wine'),
	'simple_disambiguate': ConfigValue('General', bool, True, 'Simple disambiguation', 'Use a simpler method of disambiguating games with same names'),
	'normalize_name_case': ConfigValue('General', int, 0, 'Normalize name case', 'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'), #TODO: Good case for an enum to be used here, even if argparse docs say don't use that with choices etc
	'logging_level': ConfigValue('General', str, logging.getLevelName(logger.getEffectiveLevel()), 'Logging level', 'Logging level (e.g. INFO, DEBUG, WARNING, etc)'),

	#TODO: This should be some kind of per-source options, whichever the best way to do that might be
	
	'skipped_source_files': ConfigValue('Arcade', list[str], (), 'Skipped source files', 'List of MAME source files to skip (not including extension)'),
	'exclude_non_arcade': ConfigValue('Arcade', bool, False, 'Exclude non-arcade', 'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'),
	'exclude_pinball': ConfigValue('Arcade', bool, False, 'Exclude pinball', 'Whether or not to skip pinball games (physical pinball, not video pinball)'),
	'exclude_system_drivers': ConfigValue('Arcade', bool, False, 'Exclude system drivers', 'Skip machines used to launch other software (computers, consoles, etc)'),
	'exclude_non_working': ConfigValue('Arcade', bool, False, 'Exclude non-working', 'Skip any driver marked as not working'),
	'non_working_whitelist': ConfigValue('Arcade', list[str], (), 'Non-working whitelist', 'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'),
	'use_xml_disk_cache': ConfigValue('Arcade', bool, True, 'Use XML disk cache', 'Store machine XML files on disk, maybe there are some scenarios where you might get better performance with it off (slow home directory storage, or just particularly fast MAME -listxml)'),

	'force_create_launchers': ConfigValue('Steam', bool, False, 'Force create launchers', 'Create launchers even for games which are\'nt launchable'),
	'warn_about_missing_icons': ConfigValue('Steam', bool, False, 'Warn about missing icons', 'Spam console with debug messages about icons not existing or being missing'),
	'use_steam_as_platform': ConfigValue('Steam', bool, True, 'Use Steam as platform', 'Set platform in metadata to Steam instead of underlying platform'),

	'skipped_subfolder_names': ConfigValue('Roms', list[str], (), 'Skipped subfolder names', 'Always skip these subfolders in every ROM dir'),
	'find_equivalent_arcade_games': ConfigValue('Roms', bool, False, 'Find equivalent arcade games by name', 'Get metadata from MAME machines of the same name'),
	'max_size_for_storing_in_memory': ConfigValue('Roms', int, 1024 * 1024, 'Max size for storing in memory', 'Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup (unless it doesn\'t actually speed things up)'),
	'libretro_database_path': ConfigValue('Roms', Path, None, 'libretro-database path', 'Path to libretro database for yoinking metadata from'),
	'libretro_frontend': ConfigValue('Roms', str, 'RetroArch', 'libretro frontend', 'Name of libretro frontend to use'),
	'libretro_cores_directory': ConfigValue('Roms', Path, None, 'libretro cores directory', 'Path to search for libretro cores if not explicitly specified'),

	'use_original_platform': ConfigValue('ScummVM', bool, False, 'Use original platform', 'Set the platform in metadata to the original platform instead of leaving blank'),
	'scummvm_config_path': ConfigValue('ScummVM', Path, Path('~/.config/scummvm/scummvm.ini').expanduser(), 'ScummVM config path', 'Path to scummvm.ini, if not the default'),
	'scummvm_exe_path': ConfigValue('ScummVM', Path, 'scummvm', 'ScummVM executable path', 'Path to scummvm executable, if not the default'),

	'gog_folders': ConfigValue('GOG', list[Path], (), 'GOG folders', 'Folders where GOG games are installed'),
	'use_gog_as_platform': ConfigValue('GOG', bool, False, 'Use GOG as platform', 'Set platform in metadata to GOG instead of underlying platform'),
	'windows_gog_folders': ConfigValue('GOG', list[Path], (), 'Windows GOG folders', 'Folders where Windows GOG games are installed'),
	'use_system_dosbox': ConfigValue('GOG', bool, True, 'Use system DOSBox', 'Use the version of DOSBox on this system instead of running Windows DOSBox through Wine'),
	'dosbox_path': ConfigValue('GOG', Path, "dosbox", 'DOSBox path', 'If using system DOSBox, executable name/path or just "dosbox" if left blank'),

	'itch_io_folders': ConfigValue('itch.io', list[Path], (), 'itch.io folders', 'Folders where itch.io games are installed'),
	'use_itch_io_as_platform': ConfigValue('itch.io', bool, False, 'Use itch.io as platform', 'Set platform in metadata to itch.io instead of underlying platform'),

	#These shouldn't end up in config.ini as they're intended to be set per-run
	'print_times': ConfigValue(_runtime_option_section, bool, False, 'Print times', 'Print how long it takes to do things'),
	'full_rescan': ConfigValue(_runtime_option_section, bool, False, 'Full rescan', 'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'),
	'organize_folders': ConfigValue(_runtime_option_section, bool, False, 'Organize folders', 'Use the organized folders frontend'),
}
#Hmm... debug could be called 'verbose' and combined with --super_debug used in disambiguate to become verbosity_level or just verbose for short, which could have an integer argument, and it _could_ be in config.ini I guess... ehh whatevs

def get_config_ini_options() -> Mapping[str, Mapping[str, ConfigValue]]:
	opts: MutableMapping[str, MutableMapping[str, ConfigValue]] = {}
	for k, v in _config_ini_values.items():
		if v.section == _runtime_option_section:
			continue
		opts.setdefault(v.section, {})[k] = v
	return opts

def get_runtime_options() -> Mapping[str, ConfigValue]:
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
		elif option.type in {list[Path], list[Path]}:
			group.add_argument(f'--{name}', nargs='?', type=Path, help=option.description, default=SUPPRESS)
		elif option.type == list[str]:
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

class Config():
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

				#hmm whoops need to rewrite parse_value but emulator_config etc also uses it
				#This is a bit of a mess now lol
				if config.type == Path:
					return Path(section[name]).expanduser()
				if config.type == list[str]:
					return parse_string_list(section[name])
				if config.type == list[Path]:
					return parse_path_list(section[name])
				if config.type == bool:
					return section.getboolean(name)
				if config.type == int:
					return section.getint(name)
				return config.type(section[name])
				
			raise AttributeError(name)

	__instance = None

	@staticmethod
	def getConfig() -> __Config:
		if Config.__instance is None:
			Config.__instance = Config.__Config()
		return Config.__instance

main_config = Config().getConfig()

def configoption(section: str, readable_name: str | None = None):
	"""TODO: It's a surprise tool that will help us later"""
	def deco(func): #TODO: Because we put properties on Callable that aren't there, this would be a pain in the arse to type hint…
		@wraps(func)
		def inner():
			func.section = section
			func.readable_name = readable_name or sentence_case(func.__name__)
			func.description = func.__doc__ or func.readable_name
			func.type = inspect.get_annotations(func)['return']
			return func
		return inner
	return deco
