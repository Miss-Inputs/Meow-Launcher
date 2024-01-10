from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any

from collections.abc import Sequence

if TYPE_CHECKING:
	import configparser

def parse_string_list(value: str) -> 'Sequence[str]':
	"""Parses a string as a semicolon-separated list"""
	if not value:
		return ()
	return tuple(item for item in value.split(';') if item)

def parse_path_list(value: str) -> 'Sequence[Path]':
	"""Parses a string as a semicolon-separated list of Paths, expanding home directories"""
	if not value:
		return ()
	return tuple(Path(p).expanduser() for p in parse_string_list(value))

def parse_bool(value: str) -> bool:
	"""Parses various forms of yes/true or no/false into bool, for command line/option file purposes
	I swear there was some inbuilt way to do this oh well
	:raises ValueError: if value is not some kind of yes/no"""
	lower = value.lower()
	if lower in {'yes', 'true', 'on', 't', 'y', 'yeah', 'nah yeah'}:
		return True
	if lower in {'no', 'false', 'off', 'f', 'n', 'nah', 'nope', 'yeah nah'}:
		return False

	raise ValueError(value)

def parse_value(value: str, value_annotation: type) -> Any:
	"""Parses a user-supplied (via config etc) string into whatever type it is expected to be"""
	if value_annotation == bool:
		return parse_bool(value)
	if value_annotation in {Path, PurePath}:
		return Path(value).expanduser()
	if value_annotation == Sequence[str]:
		return parse_string_list(value)
	if value_annotation in {Sequence[Path], Sequence[PurePath]}:
		return parse_path_list(value)
	return value_annotation(value)

def parse_config_section_value(section: 'configparser.SectionProxy', name: str, value_type: type, default_value: Any) -> Any:
	"""TODO: This is currently used by platform_config and emulator_config and probably won't be when they are reworked"""
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
