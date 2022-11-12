from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Union

#For type checking… hmm…
TypeOfConfigValue = Optional[Union[bool, str, Path, int, str, Sequence[str], Sequence[Path]]]

class ConfigValueType(Enum):
	Bool = auto()
	FilePath = auto()
	FolderPath = auto()
	Integer = auto()
	String = auto()
	StringList = auto()
	FilePathList = auto()
	FolderPathList = auto()

class PlatformConfig():
	def __init__(self, name: str, paths: Collection[Path], chosen_emulators: Sequence[str], options: Mapping[str, TypeOfConfigValue]) -> None:
		self.name = name
		self.paths = paths
		self.chosen_emulators = chosen_emulators
		self.options = options

	@property
	def is_available(self) -> bool:
		return bool(self.paths) and bool(self.chosen_emulators)

class RunnerConfig():
	def __init__(self, exe_path: str, options: Mapping[str, TypeOfConfigValue]|None=None):
		self.exe_path = exe_path
		self.options = options if options else {}

class EmulatorConfig(RunnerConfig):
	"""Hmm pointless class so far… what am I doing"""
	pass
	
@dataclass(frozen=True)
class RunnerConfigValue():
	"""This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno"""
	type: ConfigValueType
	default_value: TypeOfConfigValue
	description: str
	