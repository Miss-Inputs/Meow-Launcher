import configparser
import os
import sys
from typing import Any

from meowlauncher.common_paths import config_dir, data_dir
from meowlauncher.common_types import ConfigValueType
from meowlauncher.io_utils import ensure_exist

from ._config_utils import (ConfigValue, parse_path_list, parse_string_list,
                            parse_value)

_main_config_path = os.path.join(config_dir, 'config.ini')
_ignored_dirs_path = os.path.join(config_dir, 'ignored_directories.txt')

def parse_command_line_bool(value: str) -> bool:
	#I swear there was some inbuilt way to do this oh well
	lower = value.lower()
	if lower in ('yes', 'true', 'on', 't', 'y', 'yeah'):
		return True
	if lower in ('no', 'false', 'off', 'f', 'n', 'nah', 'nope'):
		return False

	raise TypeError(value)

def convert_value_for_ini(value: Any) -> str:
	if value is None:
		return ''
	if isinstance(value, list):
		return ';'.join(value)
	return str(value)


runtime_option_section = '<runtime option section>'

_config_ini_values = {
	'output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(data_dir, 'apps'), 'Output folder', 'Folder to put launchers'),
	'organized_output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(data_dir, 'organized_apps'), 'Organized output folder', 'Folder to put subfolders in for the organized folders frontend'),
	'image_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(data_dir, 'images'), 'Image folder', 'Folder to store images extracted from games with embedded images'),

	'get_series_from_name': ConfigValue('General', ConfigValueType.Bool, False, 'Get series from name', 'Attempt to get series from parsing name'),
	'use_other_images_as_icons': ConfigValue('General', ConfigValueType.StringList, [], 'Use other images as icons', 'If there is no icon, use these images as icons if they are there'),
	'sort_multiple_dev_names': ConfigValue('General', ConfigValueType.Bool, False, 'Sort multiple developer/publisher names', 'For games with multiple entities in developer/publisher field, sort alphabetically'),
	'wine_path': ConfigValue('General', ConfigValueType.FilePath, 'wine', 'Wine path', 'Path to Wine executable for Windows games/emulators'),
	'wineprefix': ConfigValue('General', ConfigValueType.FolderPath, None, 'Wine prefix', 'Optional Wine prefix to use for Wine'),
	'simple_disambiguate': ConfigValue('General', ConfigValueType.Bool, True, 'Simple disambiguation', 'Use a simpler method of disambiguating games with same names'),
	'normalize_name_case': ConfigValue('General', ConfigValueType.Integer, 0, 'Normalize name case', 'Apply title case to uppercase things (1: only if whole title is uppercase, 2: capitalize individual uppercase words, 3: title case the whole thing regardless)'),
	
	'skipped_source_files': ConfigValue('Arcade', ConfigValueType.StringList, [], 'Skipped source files', 'List of MAME source files to skip (not including extension)'),
	'exclude_non_arcade': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-arcade', 'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'),
	'exclude_pinball': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude pinball', 'Whether or not to skip pinball games (physical pinball, not video pinball)'),
	'exclude_system_drivers': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude system drivers', 'Skip machines used to launch other software (computers, consoles, etc)'),
	'exclude_non_working': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-working', 'Skip any driver marked as not working'),
	'non_working_whitelist': ConfigValue('Arcade', ConfigValueType.StringList, [], 'Non-working whitelist', 'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'),

	'force_create_launchers': ConfigValue('Steam', ConfigValueType.Bool, False, 'Force create launchers', 'Create launchers even for games which are\'nt launchable'),
	'warn_about_missing_icons': ConfigValue('Steam', ConfigValueType.Bool, False, 'Warn about missing icons', 'Spam console with debug messages about icons not existing or being missing'),
	'use_steam_as_platform': ConfigValue('Steam', ConfigValueType.Bool, True, 'Use Steam as platform', 'Set platform in metadata to Steam instead of underlying platform'),

	'skipped_subfolder_names': ConfigValue('Roms', ConfigValueType.StringList, [], 'Skipped subfolder names', 'Always skip these subfolders in every ROM dir'),
	'find_equivalent_arcade_games': ConfigValue('Roms', ConfigValueType.Bool, False, 'Find equivalent arcade games by name', 'Get metadata from MAME machines of the same name'),
	'find_software_by_name': ConfigValue('Roms', ConfigValueType.StringList, [], 'Systems to find software by name', 'For these platforms, use the filename to match something in the software list'), #TODO This should be a global option for each system
	'find_software_by_product_code': ConfigValue('Roms', ConfigValueType.StringList, [], 'Systems to find software by serial', 'For these platforms, use the product code/serial to match something in the software list'), #TODO This should be a global option for each system
	'max_size_for_storing_in_memory': ConfigValue('Roms', ConfigValueType.Integer, 32 * 1024 * 1024, 'Max size for storing in memory', 'Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup'),
	'libretro_database_path': ConfigValue('Roms', ConfigValueType.FolderPath, None, 'libretro-database path', 'Path to libretro database for yoinking metadata from'),
	'libretro_frontend': ConfigValue('Roms', ConfigValueType.String, 'RetroArch', 'libretro frontend', 'Name of libretro frontend to use'),
	'libretro_cores_directory': ConfigValue('Roms', ConfigValueType.FolderPath, None, 'libretro cores directory', 'Path to search for libretro cores if not explicitly specified'),

	'use_original_platform': ConfigValue('ScummVM', ConfigValueType.Bool, False, 'Use original platform', 'Set the platform in metadata to the original platform instead of leaving blank'),
	'scummvm_config_path': ConfigValue('ScummVM', ConfigValueType.FilePath, os.path.expanduser('~/.config/scummvm/scummvm.ini'), 'ScummVM config path', 'Path to scummvm.ini, if not the default'),

	'gog_folders': ConfigValue('GOG', ConfigValueType.FolderPathList, [], 'GOG folders', 'Folders where GOG games are installed'),
	'use_gog_as_platform': ConfigValue('GOG', ConfigValueType.Bool, False, 'Use GOG as platform', 'Set platform in metadata to GOG instead of underlying platform'),
	'windows_gog_folders': ConfigValue('GOG', ConfigValueType.FolderPathList, [], 'Windows GOG folders', 'Folders where Windows GOG games are installed'),
	'use_system_dosbox': ConfigValue('GOG', ConfigValueType.Bool, True, 'Use system DOSBox', 'Use the version of DOSBox on this system instead of running Windows DOSBox through Wine'),
	'dosbox_path': ConfigValue('GOG', ConfigValueType.FilePath, "dosbox", 'DOSBox path', 'If using system DOSBox, executable name/path or just "dosbox" if left blank'),

	'itch_io_folders': ConfigValue('itch.io', ConfigValueType.FolderPathList, [], 'itch.io folders', 'Folders where itch.io games are installed'),
	'use_itch_io_as_platform': ConfigValue('itch.io', ConfigValueType.Bool, False, 'Use itch.io as platform', 'Set platform in metadata to itch.io instead of underlying platform'),

	#These shouldn't end up in config.ini as they're intended to be set per-run
	'debug': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Debug', 'Enable debug mode, which is really verbose mode, oh well'),
	'print_times': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Print times', 'Print how long it takes to do things'),
	'full_rescan': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Full rescan', 'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'),
	'organize_folders': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Organize folders', 'Use the organized folders frontend'),
}
#Hmm... debug could be called 'verbose' and combined with --super_debug used in disambiguate to become verbosity_level or just verbose for short, which could have an integer argument, and it _could_ be in config.ini I guess... ehh whatevs


def get_config_ini_options() -> dict[str, dict[str, ConfigValue]]:
	opts: dict[str, dict[str, ConfigValue]] = {}
	for k, v in _config_ini_values.items():
		if v.section == runtime_option_section:
			continue
		if v.section not in opts:
			opts[v.section] = {}
		opts[v.section][k] = v
	return opts

def get_runtime_options():
	return {name: opt for name, opt in _config_ini_values.items() if opt.section == runtime_option_section}

def get_command_line_arguments() -> dict[str, Any]:
	d: dict[str, Any] = {}
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
					d[name] = os.path.expanduser(value)
				elif option.type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
					d[name] = parse_path_list(value)
				elif option.type == ConfigValueType.StringList:
					d[name] = parse_string_list(value)
				else:
					d[name] = value
	return d

def load_ignored_directories():
	ignored_directories = []

	try:
		with open(_ignored_dirs_path, 'rt') as ignored_txt:
			ignored_directories += ignored_txt.read().splitlines()
	except FileNotFoundError:
		pass

	if '--ignored-directories' in sys.argv:
		#TODO Move to get_command_line_arguments or otherwise somewhere else
		index = sys.argv.index('--ignored-directories')
		arg = sys.argv[index + 1]
		for ignored_dir in parse_path_list(arg):
			ignored_directories.append(ignored_dir)

	ignored_directories = [dir if dir.endswith(os.sep) else dir + os.sep for dir in ignored_directories if dir.strip()]

	return ignored_directories

def write_ignored_directories(ignored_dirs):
	try:
		with open(_ignored_dirs_path, 'wt') as ignored_txt:
			for ignored_dir in ignored_dirs:
				ignored_txt.write(ignored_dir)
				ignored_txt.write('\n')
	except OSError as oe:
		print('AAaaaa!!! Failed to write ignored directories file!!', oe)

def write_new_main_config(new_config):
	write_new_config(new_config, _main_config_path)

def write_new_config(new_config, config_file_path):
	parser = configparser.ConfigParser(interpolation=None)
	parser.optionxform = str
	ensure_exist(config_file_path)
	parser.read(config_file_path)
	for section, configs in new_config.items():
		if section not in parser:
			parser.add_section(section)
		for name, value in configs.items():
			parser[section][name] = convert_value_for_ini(value)

	try:
		with open(config_file_path, 'wt') as ini_file:
			parser.write(ini_file)
	except OSError as ex:
		print('Oh no!!! Failed to write', config_file_path, '!!!!11!!eleven!!', ex)

class Config():
	class __Config():
		def __init__(self):
			self.values = {}
			for name, config in _config_ini_values.items():
				self.values[name] = config.default_value

			self.runtime_overrides = get_command_line_arguments()
			self.reread_config()

		def reread_config(self):
			parser = configparser.ConfigParser(interpolation=None)
			parser.optionxform = str
			self.parser = parser
			ensure_exist(_main_config_path)
			self.parser.read(_main_config_path)

			self.ignored_directories = load_ignored_directories()

		def rewrite_config(self):
			with open(_main_config_path, 'wt') as f:
				self.parser.write(f)

		def __getattr__(self, name):
			if name in self.values:
				if name in self.runtime_overrides:
					return self.runtime_overrides[name]
				config = _config_ini_values[name]

				if config.section == runtime_option_section:
					return config.default_value

				if config.section not in self.parser:
					self.parser.add_section(config.section)
					self.rewrite_config()

				section = self.parser[config.section]
				if name not in section:
					section[name] = convert_value_for_ini(config.default_value)
					self.rewrite_config()
					return config.default_value

				return parse_value(section, name, config.type, config.default_value)

			raise AttributeError(name)

	__instance = None

	@staticmethod
	def getConfig():
		if Config.__instance is None:
			Config.__instance = Config.__Config()
		return Config.__instance

main_config = Config().getConfig()
