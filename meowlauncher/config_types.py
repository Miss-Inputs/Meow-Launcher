"""This will probably be thrown out the window as we rewrite everything to use pydantic_settings"""
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# For type checking… hmm…
TypeOfConfigValue = bool | str | Path | int | str | Sequence[str] | Sequence[Path] | None


class PlatformConfig:
	"""Configuration for a ROM platform. This class will probably be dismantled/thrown out the window/whatever other words you like to say"""

	def __init__(
		self,
		name: str,
		paths: Collection[Path],
		chosen_emulators: Sequence[str],
		options: Mapping[str, TypeOfConfigValue],
	) -> None:
		self.name = name
		self.paths = paths
		self.chosen_emulators = chosen_emulators
		self.options = options

	@property
	def is_available(self) -> bool:
		return bool(self.paths) and bool(self.chosen_emulators)


class RunnerConfig:
	"""Configuration for a Runner. Probs going to rework this one too"""

	def __init__(self, exe_path: Path, options: Mapping[str, TypeOfConfigValue] | None = None):
		self.exe_path = exe_path
		self.options = options if options else {}


class EmulatorConfig(RunnerConfig):
	"""Hmm pointless class so far… what am I doing"""


@dataclass(frozen=True)
class RunnerConfigValue:
	"""This is actually just config.ConfigValue without the section field. Maybe that should tell me something. I dunno"""

	type: type
	default_value: Any  # TODO: Should be generic subclass of type
	description: str
