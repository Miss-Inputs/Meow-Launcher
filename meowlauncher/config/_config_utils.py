import os

from meowlauncher.common_types import ConfigValueType


def parse_string_list(value: str):
	if not value:
		return []
	return [item for item in value.split(';') if item]

def parse_path_list(value: str):
	if not value:
		return []
	return [os.path.expanduser(p) for p in parse_string_list(value)]

def parse_value(section, name: str, value_type: ConfigValueType, default_value):
	try:
		if value_type == ConfigValueType.Bool:
			return section.getboolean(name, default_value)
		if value_type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
			return os.path.expanduser(section[name])
		if value_type == ConfigValueType.StringList:
			return parse_string_list(section[name])
		if value_type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
			return parse_path_list(section[name])
		if value_type == ConfigValueType.Integer:
			return section.getint(name, default_value)
		return section[name]
	except KeyError:
		return default_value

class ConfigValue():
	def __init__(self, section: str, value_type: ConfigValueType, default_value, name: str, description: str):
		self.section = section
		self.type = value_type
		self.default_value = default_value
		self.name = name #This is for humans to read!
		self.description = description
