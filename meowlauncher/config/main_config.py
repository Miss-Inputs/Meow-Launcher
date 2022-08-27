import configparser
import logging
import sys
from collections.abc import Collection, Mapping, MutableMapping
from pathlib import Path, PurePath

from meowlauncher.common_paths import config_dir, data_dir
from meowlauncher.config_types import ConfigValueType, TypeOfConfigValue
from meowlauncher.util.io_utils import ensure_exist

from ._config_utils import (ConfigValue, parse_path_list, parse_string_list,
                            parse_value)

logger = logging.getLogger(__name__)

_main_config_path = config_dir.joinpath('config.ini')
_ignored_dirs_path = config_dir.joinpath('ignored_directories.txt')

def _convert_value_for_ini(value: TypeOfConfigValue) -> str:
	if value is None:
		return ''
	if isinstance(value, list):
		return ';'.join(value)
	return str(value)

_runtime_option_section = '<runtime option section>' #TODO: Can this be a sentinel-style object with ConfigValue section parameter having union str | that

_config_ini_values = {
	'output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, data_dir.joinpath('apps'), 'Output folder', 'Folder to put launchers'),
	'organized_output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, data_dir.joinpath('organized_apps'), 'Organized output folder', 'Folder to put subfolders in for the organized folders frontend'),
	'image_folder': ConfigValue('Paths', ConfigValueType.FolderPath, data_dir.joinpath('images'), 'Image folder', 'Folder to store images extracted from games with embedded images'),

	'get_series_from_name': ConfigValue('General', ConfigValueType.Bool, False, 'Get series from name', 'Attempt to get series from parsing name'),
	'use_other_images_as_icons': ConfigValue('General', ConfigValueType.StringList, (), 'Use other images as icons', 'If there is no icon, use these images as icons if they are there'),
	'sort_multiple_dev_names': ConfigValue('General', ConfigValueType.Bool, False, 'Sort multiple developer/publisher names', 'For games with multiple entities in developer/publisher field, sort alphabetically'),
	'wine_path': ConfigValue('General', ConfigValueType.String, 'wine', 'Wine path', 'Path to Wine executable for Windows games/emulators'),
	'wineprefix': ConfigValue('General', ConfigValueType.FolderPath, None, 'Wine prefix', 'Optional Wine prefix to use for Wine'),
	'simple_disambiguate': ConfigValue('General', ConfigValueType.Bool, True, 'Simple disambiguation', 'Use a simpler method of disambiguating games with same names'),
	'normalize_name_case': ConfigValue('General', ConfigValueType.Integer, 0, 'Normalize name case', 'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'),
	'logging_level': ConfigValue('General', ConfigValueType.String, logging.getLevelName(logger.getEffectiveLevel()), 'Logging level', 'Logging level (e.g. INFO, DEBUG, WARNING, etc)'),
	
	'skipped_source_files': ConfigValue('Arcade', ConfigValueType.StringList, (), 'Skipped source files', 'List of MAME source files to skip (not including extension)'),
	'exclude_non_arcade': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-arcade', 'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'),
	'exclude_pinball': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude pinball', 'Whether or not to skip pinball games (physical pinball, not video pinball)'),
	'exclude_system_drivers': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude system drivers', 'Skip machines used to launch other software (computers, consoles, etc)'),
	'exclude_non_working': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-working', 'Skip any driver marked as not working'),
	'non_working_whitelist': ConfigValue('Arcade', ConfigValueType.StringList, (), 'Non-working whitelist', 'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'),
	'use_xml_disk_cache': ConfigValue('Arcade', ConfigValueType.Bool, True, 'Use XML disk cache', 'Store machine XML files on disk, maybe there are some scenarios where you might get better performance with it off (slow home directory storage, or just particularly fast MAME -listxml)'),

	'force_create_launchers': ConfigValue('Steam', ConfigValueType.Bool, False, 'Force create launchers', 'Create launchers even for games which are\'nt launchable'),
	'warn_about_missing_icons': ConfigValue('Steam', ConfigValueType.Bool, False, 'Warn about missing icons', 'Spam console with debug messages about icons not existing or being missing'),
	'use_steam_as_platform': ConfigValue('Steam', ConfigValueType.Bool, True, 'Use Steam as platform', 'Set platform in metadata to Steam instead of underlying platform'),

	'skipped_subfolder_names': ConfigValue('Roms', ConfigValueType.StringList, (), 'Skipped subfolder names', 'Always skip these subfolders in every ROM dir'),
	'find_equivalent_arcade_games': ConfigValue('Roms', ConfigValueType.Bool, False, 'Find equivalent arcade games by name', 'Get metadata from MAME machines of the same name'),
	'max_size_for_storing_in_memory': ConfigValue('Roms', ConfigValueType.Integer, 1024 * 1024, 'Max size for storing in memory', 'Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup (unless it doesn\'t actually speed things up)'),
	'libretro_database_path': ConfigValue('Roms', ConfigValueType.FolderPath, None, 'libretro-database path', 'Path to libretro database for yoinking metadata from'),
	'libretro_frontend': ConfigValue('Roms', ConfigValueType.String, 'RetroArch', 'libretro frontend', 'Name of libretro frontend to use'),
	'libretro_cores_directory': ConfigValue('Roms', ConfigValueType.FolderPath, None, 'libretro cores directory', 'Path to search for libretro cores if not explicitly specified'),

	'use_original_platform': ConfigValue('ScummVM', ConfigValueType.Bool, False, 'Use original platform', 'Set the platform in metadata to the original platform instead of leaving blank'),
	'scummvm_config_path': ConfigValue('ScummVM', ConfigValueType.FilePath, Path('~/.config/scummvm/scummvm.ini').expanduser(), 'ScummVM config path', 'Path to scummvm.ini, if not the default'),
	'scummvm_exe_path': ConfigValue('ScummVM', ConfigValueType.FilePath, 'scummvm', 'ScummVM executable path', 'Path to scummvm executable, if not the default'),

	'gog_folders': ConfigValue('GOG', ConfigValueType.FolderPathList, (), 'GOG folders', 'Folders where GOG games are installed'),
	'use_gog_as_platform': ConfigValue('GOG', ConfigValueType.Bool, False, 'Use GOG as platform', 'Set platform in metadata to GOG instead of underlying platform'),
	'windows_gog_folders': ConfigValue('GOG', ConfigValueType.FolderPathList, (), 'Windows GOG folders', 'Folders where Windows GOG games are installed'),
	'use_system_dosbox': ConfigValue('GOG', ConfigValueType.Bool, True, 'Use system DOSBox', 'Use the version of DOSBox on this system instead of running Windows DOSBox through Wine'),
	'dosbox_path': ConfigValue('GOG', ConfigValueType.FilePath, "dosbox", 'DOSBox path', 'If using system DOSBox, executable name/path or just "dosbox" if left blank'),

	'itch_io_folders': ConfigValue('itch.io', ConfigValueType.FolderPathList, (), 'itch.io folders', 'Folders where itch.io games are installed'),
	'use_itch_io_as_platform': ConfigValue('itch.io', ConfigValueType.Bool, False, 'Use itch.io as platform', 'Set platform in metadata to itch.io instead of underlying platform'),

	#These shouldn't end up in config.ini as they're intended to be set per-run
	'print_times': ConfigValue(_runtime_option_section, ConfigValueType.Bool, False, 'Print times', 'Print how long it takes to do things'),
	'full_rescan': ConfigValue(_runtime_option_section, ConfigValueType.Bool, False, 'Full rescan', 'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'),
	'organize_folders': ConfigValue(_runtime_option_section, ConfigValueType.Bool, False, 'Organize folders', 'Use the organized folders frontend'),
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

def _get_command_line_arguments() -> Mapping[str, TypeOfConfigValue]:
	d: MutableMapping[str, TypeOfConfigValue] = {}
	for i, arg in enumerate(sys.argv):
		if not arg.startswith('--'):
			continue
		arg = arg[2:]

		for name, option in _config_ini_values.items():
			expected_arg = name.replace('_', '-')

			if option.type == ConfigValueType.Bool:
				if arg == '--no-' + expected_arg:
					d[name] = False
				elif arg == expected_arg:
					d[name] = True

			elif arg == expected_arg:
				value = sys.argv[i + 1]
				#TODO: If value = another argument starts with --, invalid?
				#if option.type == ConfigValueType.Bool: #or do I wanna do that
				#	d[name] = parse_command_line_bool(value)
				if option.type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
					d[name] = Path(value).expanduser()
				elif option.type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
					d[name] = parse_path_list(value)
				elif option.type == ConfigValueType.StringList:
					d[name] = parse_string_list(value)
				else:
					d[name] = value
	return d

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

			self.runtime_overrides = _get_command_line_arguments()
			parser = configparser.ConfigParser(interpolation=None)
			parser.optionxform = str #type: ignore[assignment]
			self.parser = parser
			ensure_exist(_main_config_path)
			self.parser.read(_main_config_path)

			self.ignored_directories = _load_ignored_directories()

		def __getattr__(self, name: str) -> TypeOfConfigValue:
			if name in self.values:
				if name in self.runtime_overrides:
					return self.runtime_overrides[name]
				config = _config_ini_values[name]

				if config.section == _runtime_option_section:
					return config.default_value

				section = self.parser[config.section]
				if name not in section:
					section[name] = _convert_value_for_ini(config.default_value)
					return config.default_value

				return parse_value(section, name, config.type, config.default_value)

			raise AttributeError(name)

	__instance = None

	@staticmethod
	def getConfig() -> __Config:
		if Config.__instance is None:
			Config.__instance = Config.__Config()
		return Config.__instance

main_config = Config().getConfig()
