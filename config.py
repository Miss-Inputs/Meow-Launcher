import os
import configparser
import sys

from common_types import ConfigValueType
from io_utils import ensure_exist
from info.system_info import systems, games_with_engines, computer_systems

app_name = 'Meow Launcher'

#TODO: Get this in a less hardcody cross-platform way, I guess
_config_dir = os.path.expanduser(os.path.join('~/.config/', app_name.replace(' ', '')))
_data_dir = os.path.expanduser(os.path.join('~/.local/share/', app_name.replace(' ', '')))
cache_dir = os.path.expanduser(os.path.join('~/.cache/', app_name.replace(' ', '')))

#Static paths I guess
_main_config_path = os.path.join(_config_dir, 'config.ini')
_ignored_dirs_path = os.path.join(_config_dir, 'ignored_directories.txt')
#TODO: Do I really want this to be in the source file like that? Ehhhhh
_name_consistency_path = os.path.join(os.path.dirname(__file__), 'name_consistency.ini')
_system_config_path = os.path.join(_config_dir, 'systems.ini')

mac_ini_path = os.path.join(_config_dir, 'mac.ini')
dos_ini_path = os.path.join(_config_dir, 'dos.ini')

def parse_string_list(value):
	if not value:
		return []
	return [item for item in value.split(';') if item]

def parse_path_list(value):
	if not value:
		return []
	return [os.path.expanduser(p) for p in parse_string_list(value)]

def parse_value(section, name, value_type, default_value):
	if value_type == ConfigValueType.Bool:
		return section.getboolean(name, default_value)
	elif value_type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
		return os.path.expanduser(section[name])
	elif value_type == ConfigValueType.StringList:
		return parse_string_list(section[name])
	elif value_type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
		return parse_path_list(section[name])
	return section[name]

def parse_command_line_bool(value):
	#I swear there was some inbuilt way to do this oh well
	lower = value.lower()
	if lower in ('yes', 'true', 'on', 't', 'y', 'yeah'):
		return True
	elif lower in ('no', 'false', 'off', 'f', 'n', 'nah', 'nope'):
		return False

	raise TypeError(value)

def convert_value_for_ini(value):
	if value is None:
		return ''
	if isinstance(value, list):
		return ';'.join(value)
	return str(value)

class ConfigValue():
	def __init__(self, section, value_type, default_value, name, description):
		self.section = section
		self.type = value_type
		self.default_value = default_value
		self.name = name #This is for humans to read!
		self.description = description

runtime_option_section = '<runtime option section>'

_config_ini_values = {
	'output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(_data_dir, 'apps'), 'Output folder', 'Folder to put launchers'),
	'organized_output_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(_data_dir, 'organized_apps'), 'Organized output folder', 'Folder to put subfolders in for the organized folders frontend'),
	'image_folder': ConfigValue('Paths', ConfigValueType.FolderPath, os.path.join(_data_dir, 'images'), 'Image folder', 'Folder to store images extracted from games with embedded images'),

	'catlist_path': ConfigValue('Arcade', ConfigValueType.FilePath, None, 'catlist.ini path', 'Path to MAME catlist.ini'),
	'languages_path': ConfigValue('Arcade', ConfigValueType.FilePath, None, 'languages.ini path', 'Path to MAME languages.ini'),
	'skipped_source_files': ConfigValue('Arcade', ConfigValueType.StringList, [], 'Skipped source files', 'List of MAME source files to skip (not including extension)'),
	'memcard_path': ConfigValue('Arcade', ConfigValueType.FolderPath, None, 'Memory card path', 'Path to store memory cards for arcade systems which support that'),
	'exclude_non_arcade': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude non-arcade', 'Whether or not to skip MAME systems categorized as not being arcade or anything specific'), #TODO This description sucks
	'exclude_pinball': ConfigValue('Arcade', ConfigValueType.Bool, False, 'Exclude pinball', 'Whether or not to skip pinball games'),

	'mac_db_path': ConfigValue('Mac', ConfigValueType.FilePath, None, 'mac_db.json path', 'Path to mac_db.json from ComputerGameDB'),
	'launchers_for_unknown_mac_apps': ConfigValue('Mac', ConfigValueType.Bool, False, 'Launchers for unknown apps', 'Whether or not to create launchers for Mac programs that are found but not in the database'),

	'dos_db_path': ConfigValue('DOS', ConfigValueType.FilePath, None, 'dos_db.json path', 'Path to dos_db.json from ComputerGameDB'),
	'launchers_for_unknown_dos_apps': ConfigValue('DOS', ConfigValueType.Bool, False, 'Launchers for unknown apps', 'Whether or not to create launchers for DOS programs that are found but not in the database'),
	#TODO: Should be in specific_config as it is inherently specific to the emulator (DOSBox) and not the platform
	'dosbox_configs_path': ConfigValue('DOS', ConfigValueType.FolderPath, os.path.join(_data_dir, 'dosbox_configs'), 'DOSBox configs path', 'Folder to store DOSBox per-application configuration files'),

	#These shouldn't end up in config.ini as they're intended to be set per-run
	'debug': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Debug', 'Enable debug mode, which is really verbose mode, oh well'),
	'print_times': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Print times', 'Print how long it takes to do things'),
	'full_rescan': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Full rescan', 'Regenerate every launcher from scratch instead of just what\'s new and removing what\'s no longer there'),
	'organize_folders': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Organize folders', 'Use the organized folders frontend'),
	'extra_folders': ConfigValue(runtime_option_section, ConfigValueType.Bool, False, 'Extra folders', 'Create additional folders for organized folders frontend beyond the usual')
}
#Hmm... debug could be called 'verbose' and combined with --super_debug used in disambiguate to become verbosity_level or just verbose for short, which could have an integer argument, and it _could_ be in config.ini I guess... ehh whatevs

def get_config_ini_options():
	opts = {}
	for k, v in _config_ini_values.items():
		if v.section == runtime_option_section:
			continue
		if v.section not in opts:
			opts[v.section] = {}
		opts[v.section][k] = v
	return opts

def get_runtime_options():
	return {name: opt for name, opt in _config_ini_values.items() if opt.section == runtime_option_section}

def get_command_line_arguments():
	d = {}
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

	ignored_directories = [dir if dir.endswith(os.sep) else dir + os.sep for dir in ignored_directories]

	return ignored_directories

def write_ignored_directories(ignored_dirs):
	try:
		with open(_ignored_dirs_path, 'wt') as ignored_txt:
			for ignored_dir in ignored_dirs:
				ignored_txt.write(ignored_dir)
				ignored_txt.write('\n')
	except OSError as oe:
		print('AAaaaa!!! Failed to write ignored directories file!!', oe)

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

main_config = Config.getConfig()

def load_name_replacement():
	#Sometimes, we want to mess around with : being in the title, so that can't be a delimiter since it needs to appear inside "keys". I'd have to restructure the whole config file to not be an .ini at all otherwise. Hopefully, nothing will have an equals sign in the title.
	parser = configparser.ConfigParser(delimiters=('='), allow_no_value=True)
	parser.optionxform = str
	if not os.path.isfile(_name_consistency_path):
		print('oh no')
		return
	parser.read(_name_consistency_path)

	for k, v in parser['Name Replacement'].items():
		name_replacement.append((k, v))
	for k, v in parser['Add "The"'].items():
		add_the.append(k)
	for k, v in parser['Subtitle Removal'].items():
		subtitle_removal.append((k, v))

#For when I do a hecking disagreement about how names should be formatted, and if subtitles should be in the title or
#not.  This probably annoys purists, but I think it makes things less confusing at the end of the day
#TODO: Review the practicality of just changing normalize_name to remove all spaces and punctuation.  Would that cause
#any false positives at all?  Though there would still be use for this part here
name_replacement = []
#Add "The " in front of these things (but not if there's already "The " in front of them of course)
add_the = []
#Only check for this at the start of a thing
subtitle_removal = []
load_name_replacement()

class SystemConfig():
	def __init__(self, name):
		self.name = name
		self.paths = []
		self.chosen_emulators = []
		self.specific_config = {}

	@property
	def is_available(self):
		return bool(self.paths)

class SystemConfigs():
	class __SystemConfigs():
		def __init__(self):
			self.parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			self.parser.optionxform = str

			ensure_exist(_system_config_path)
			self.parser.read(_system_config_path)

			self.init_configs()

		def rewrite_config(self):
			with open(_system_config_path, 'wt') as f:
				self.parser.write(f)

		def init_configs(self):
			self.configs = {}
			for k, v in systems.items():
				self.init_config(k, v.specific_configs, add_if_not_exist=not v.is_unsupported)
			for k, v in games_with_engines.items():
				self.init_config(k, v.specific_configs)
			for k, v in computer_systems.items():
				self.init_config(k, v.specific_configs)

		def init_config(self, name, specific_configs, add_if_not_exist=True):
			self.configs[name] = SystemConfig(name)
			if name not in self.parser:
				if add_if_not_exist:
					self.parser.add_section(name)
					self.rewrite_config()
				else:
					return
			section = self.parser[name]

			if 'paths' not in section:
				section['paths'] = ''
				self.rewrite_config()
			if 'emulators' not in section:
				section['emulators'] = ''
				self.rewrite_config()
			self.configs[name].paths = parse_path_list(section['paths'])
			emulator_choices = parse_string_list(section['emulators'])
			#I'm bad at variable names I'm very sorry
			chosen_emulators = []
			for chosen_emulator in emulator_choices:
				if chosen_emulator in ('MAME', 'Mednafen'):
					#Allow for convenient shortcut
					chosen_emulator = '{0} ({1})'.format(chosen_emulator, name)
				chosen_emulators.append(chosen_emulator)
			self.configs[name].chosen_emulators = chosen_emulators
			for specific_config_name, specific_config in specific_configs.items():
				if specific_config_name not in section:
					section[specific_config_name] = convert_value_for_ini(specific_config.default_value)
					self.rewrite_config()
				self.configs[name].specific_config[specific_config_name] = parse_value(section, specific_config_name, specific_config.type, specific_config.default_value)

	__instance = None

	@staticmethod
	def getConfigs():
		if SystemConfigs.__instance is None:
			SystemConfigs.__instance = SystemConfigs.__SystemConfigs()
		return SystemConfigs.__instance

system_configs = SystemConfigs.getConfigs()

#--regen-dos-config is used in emulator_command_lines... should I move it here?
