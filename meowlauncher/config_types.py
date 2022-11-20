from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#For type checking… hmm…
TypeOfConfigValue = bool | str | Path | int | str | Sequence[str] | Sequence[Path] | None

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
	def __init__(self, exe_path: Path, options: Mapping[str, TypeOfConfigValue]|None=None):
		self.exe_path = exe_path
		self.options = options if options else {}

class EmulatorConfig(RunnerConfig):
	"""Hmm pointless class so far… what am I doing"""
	
@dataclass(frozen=True)
class RunnerConfigValue():
	"""This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno"""
	type: type
	default_value: Any #TODO: Should be generic subclass of type
	description: str
	