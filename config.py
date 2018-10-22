import os
import configparser
from enum import Enum, auto

from io_utils import ensure_exist
from info.system_info import systems, games_with_engines, computer_systems

app_name = 'CrappyGameLauncher'

#TODO: Get this in a less hardcody cross-platform way, I guess
_config_dir = os.path.expanduser(os.path.join('~/.config/', app_name))
_data_dir = os.path.expanduser(os.path.join('~/.local/share/', app_name))

#Static paths I guess
_main_config_path = os.path.join(_config_dir, 'config.ini')
_ignored_dirs_path = os.path.join(_config_dir, 'ignored_directories.txt')
#TODO: Do I really want this to be in the source file like that? Ehhhhh
_name_consistency_path = os.path.join(os.path.dirname(__file__), 'name_consistency.ini')
_emulator_config_path = os.path.join(_config_dir, 'emulators.ini')

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

def convert_value_for_ini(value):
	if value is None:
		return ''
	if isinstance(value, list):
		return ';'.join(value)
	return str(value)

class ConfigValueType(Enum):
	Bool = auto()
	Path = auto()
	String = auto()
	StringList = auto()
	PathList = auto()

class ConfigValue():
	def __init__(self, section, value_type, default_value, command_line_option):
		self.section = section
		self.type = value_type
		self.default_value = default_value
		self.command_line_option = command_line_option

_config_ini_values = {
	'output_folder': ConfigValue('Paths', ConfigValueType.Path, os.path.join(_data_dir, 'apps'), 'output-folder'),
	'organized_output_folder': ConfigValue('Paths', ConfigValueType.Path, os.path.join(_data_dir, 'organized_apps'), 'organized-output-folder'),
	'icon_folder': ConfigValue('Paths', ConfigValueType.Path, os.path.join(_data_dir, 'icons'), 'icon-folder'),

	'catlist_path': ConfigValue('Arcade', ConfigValueType.Path, None, 'catlist-path'),
	'languages_path': ConfigValue('Arcade', ConfigValueType.Path, None, 'languages-path'),
	'skipped_source_files': ConfigValue('Arcade', ConfigValueType.StringList, [], 'skipped-source-files'),
	'memcard_path': ConfigValue('Arcade', ConfigValueType.Path, None, 'memcard-path'),
	'exclude_non_arcade': ConfigValue('Arcade', ConfigValueType.Bool, False, 'exclude-non-arcade'),
	'exclude_pinball': ConfigValue('Arcade', ConfigValueType.Bool, False, 'exclude-pinball'),

	'mac_db_path': ConfigValue('Mac', ConfigValueType.Path, None, 'mac-db-path'),
	'launchers_for_unknown_mac_apps': ConfigValue('Mac', ConfigValueType.Bool, False, 'launchers-for-unknown-mac-apps'),

	'dos_db_path': ConfigValue('DOS', ConfigValueType.Path, None, 'dos-db-path'),
	'launchers_for_unknown_dos_apps': ConfigValue('DOS', ConfigValueType.Bool, False, 'launchers-for-unknown-dos-apps'),
	#TODO: Should be in other_config as it is inherently specific to the emulator (DOSBox) and not the platform
	'dosbox_configs_path': ConfigValue('DOS', ConfigValueType.Path, os.path.join(_data_dir, 'dosbox_configs'), 'dosbox-configs-path')
}

class Config():
	class __Config():
		def __init__(self):
			self.values = {}
			for name, config in _config_ini_values.items():
				self.values[name] = config.default_value

			#TODO Load from command line
			parser = configparser.ConfigParser(interpolation=None)
			parser.optionxform = str
			self.parser = parser
			ensure_exist(_main_config_path)
			self.parser.read(_main_config_path)

		def rewrite_config(self):
			with open(_main_config_path, 'wt') as f:
				self.parser.write(f)

		def __getattr__(self, name):
			if name in self.values:
				config = _config_ini_values[name]

				if config.section not in self.parser:
					self.parser.add_section(config.section)
					self.rewrite_config()

				section = self.parser[config.section]
				if name not in section:
					section[name] = convert_value_for_ini(config.default_value)
					self.rewrite_config()
					value = config.default_value
				else:
					if config.type == ConfigValueType.Bool:
						value = section.getboolean(name, config.default_value)
					elif config.type == ConfigValueType.Path:
						value = os.path.expanduser(section[name])
					elif config.type == ConfigValueType.StringList:
						value = parse_string_list(section[name])
					elif config.type == ConfigValueType.PathList:
						value = parse_path_list(section[name])
				return value

			raise AttributeError(name)

	__instance = None

	@staticmethod
	def getConfig():
		if Config.__instance is None:
			Config.__instance = Config.__Config()
		return Config.__instance

main_config = Config.getConfig()

def load_ignored_directories():
	#TODO: Override by command line
	with open(_ignored_dirs_path, 'rt') as ignored_txt:
		ignored_directories = ignored_txt.read().splitlines()
	return ignored_directories
ignored_directories = load_ignored_directories()

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
		self.other_config = {}

	@property
	def is_available(self):
		return bool(self.paths)

class SystemConfigs():
	class __SystemConfigs():
		def __init__(self):
			self.parser = configparser.ConfigParser(interpolation=None, delimiters=('='), allow_no_value=True)
			self.parser.optionxform = str

			ensure_exist(_emulator_config_path)
			self.parser.read(_emulator_config_path)

			self.init_configs()

		def rewrite_config(self):
			with open(_emulator_config_path, 'wt') as f:
				self.parser.write(f)

		def init_configs(self):
			self.configs = {}
			for k, v in systems.items():
				self.init_config(k, v.other_config_names)
			for k, v in games_with_engines.items():
				self.init_config(k, v.other_config_names)
			for k, v in computer_systems.items():
				self.init_config(k, v.other_config_names)

		def init_config(self, name, other_configs):
			self.configs[name] = SystemConfig(name)
			if name not in self.parser:
				self.parser.add_section(name)
				self.rewrite_config()
			section = self.parser[name]

			if 'paths' not in section:
				section['paths'] = ''
				self.rewrite_config()
			if 'emulators' not in section:
				section['emulators'] = ''
				self.rewrite_config()
			self.configs[name].paths = parse_path_list(section['paths'])
			self.configs[name].chosen_emulators = parse_string_list(section['emulators'])

			for other_config_name, default_value in other_configs.items():
				if other_config_name not in section:
					section[other_config_name] = convert_value_for_ini(default_value)
					self.rewrite_config()
				#TODO: Should I support other data types and whatnot
				self.configs[name].other_config[other_config_name] = section.get(other_config_name, default_value)

	__instance = None

	@staticmethod
	def getConfigs():
		if SystemConfigs.__instance is None:
			SystemConfigs.__instance = SystemConfigs.__SystemConfigs()
		return SystemConfigs.__instance

system_configs = SystemConfigs.getConfigs()
