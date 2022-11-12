from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from meowlauncher.config_types import ConfigValueType, TypeOfConfigValue

if TYPE_CHECKING:
	import configparser
	from collections.abc import Sequence


def parse_string_list(value: str) -> 'Sequence[str]':
	if not value:
		return ()
	return tuple(item for item in value.split(';') if item)

def parse_path_list(value: str) -> 'Sequence[Path]':
	if not value:
		return ()
	return tuple(Path(p).expanduser() for p in parse_string_list(value))

def parse_bool(value: str) -> bool:
	"""Parses various forms of yes/true or no/false into bool, for command line/option file purposes
	I swear there was some inbuilt way to do this oh well"""
	lower = value.lower()
	if lower in {'yes', 'true', 'on', 't', 'y', 'yeah'}:
		return True
	if lower in {'no', 'false', 'off', 'f', 'n', 'nah', 'nope'}:
		return False

	raise TypeError(value)

def parse_value(section: 'configparser.SectionProxy', name: str, value_type: ConfigValueType, default_value: TypeOfConfigValue) -> TypeOfConfigValue:
	try:
		if value_type == ConfigValueType.Bool:
			return parse_bool(section[name])
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

@dataclass(frozen=True)
class ConfigValue():
	section: str
	type: ConfigValueType
	default_value: TypeOfConfigValue
	name: str #This is for humans to read! I guess I could have called it display_name
	description: str
	