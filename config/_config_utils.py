import os

from common_types import ConfigValueType

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
	if value_type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
		return os.path.expanduser(section[name])
	if value_type == ConfigValueType.StringList:
		return parse_string_list(section[name])
	if value_type in (ConfigValueType.FilePathList, ConfigValueType.FolderPathList):
		return parse_path_list(section[name])
	if value_type == ConfigValueType.Integer:
		return section.getint(name, default_value)
	return section[name]

class ConfigValue():
	def __init__(self, section, value_type, default_value, name, description):
		self.section = section
		self.type = value_type
		self.default_value = default_value
		self.name = name #This is for humans to read!
		self.description = description
