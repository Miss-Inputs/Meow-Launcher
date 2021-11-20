import configparser
from collections.abc import Sequence
from pathlib import Path

from meowlauncher.config_types import ConfigValueType, TypeOfConfigValue


def parse_string_list(value: str) -> Sequence[str]:
	if not value:
		return ()
	return tuple(item for item in value.split(';') if item)

def parse_path_list(value: str) -> Sequence[Path]:
	if not value:
		return ()
	return tuple(Path(p).expanduser() for p in parse_string_list(value))

def parse_value(section: configparser.SectionProxy, name: str, value_type: ConfigValueType, default_value: TypeOfConfigValue) -> TypeOfConfigValue:
	try:
		if value_type == ConfigValueType.Bool:
			return section.getboolean(name, default_value)
		if value_type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
			return Path(section[name]).expanduser()
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
	def __init__(self, section: str, value_type: ConfigValueType, default_value: TypeOfConfigValue, name: str, description: str):
		self.section = section
		self.type = value_type
		self.default_value = default_value
		self.name = name #This is for humans to read!
		self.description = description
