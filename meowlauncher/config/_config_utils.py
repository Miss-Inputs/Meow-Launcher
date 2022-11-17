from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from collections.abc import Sequence

if TYPE_CHECKING:
	import configparser

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

def parse_value(value: str, value_type: type) -> Any:
	if value_type == bool:
		return parse_bool(value)
	if value_type == Path:
		return Path(value).expanduser()
	if value_type == Sequence[str]:
		return parse_string_list(value)
	if value_type == Sequence[Path]:
		return parse_path_list(value)
	return value_type(value)

def parse_config_section_value(section: 'configparser.SectionProxy', name: str, value_type: type, default_value: Any) -> Any:
	try:
		if value_type == bool:
			return parse_bool(section[name])
		if value_type == Path:
			return Path(section[name]).expanduser()
		if value_type == Sequence[str]:
			return parse_string_list(section[name])
		if value_type == Sequence[Path]:
			return parse_path_list(section[name])
		if value_type == int:
			return section.getint(name, default_value)
		return value_type(section[name])
	except KeyError:
		return default_value

@dataclass(frozen=True)
class ConfigValue():
	section: str
	type: type
	default_value: Any
	readable_name: str
	description: str
	