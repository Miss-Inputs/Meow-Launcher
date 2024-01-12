"""This will probably be thrown out the window as we rewrite everything to use pydantic_settings"""
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path

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
