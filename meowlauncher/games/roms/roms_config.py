"""Putting this here so roms_info can use it too, without causing a circular import by importing roms… hrm does this make sense?
TODO: Maybe .roms_config could just be accessible from ROMGame"""
from collections.abc import Sequence

from pydantic import ByteSize, Field

from meowlauncher.settings.settings import Settings


class ROMsConfig(Settings):
	"""Config specific to ROMs entirely as a game source"""

	@classmethod
	def section(cls) -> str:
		return 'ROMs'

	skipped_subfolder_names: Sequence[str] = Field(default_factory=tuple)
	'Always skip these subfolders in every ROM dir'

	excluded_platforms: Sequence[str] = Field(default_factory=tuple)
	"""Really just here for debugging/testing, excludes platforms from the ROMs game source"""

	platforms: Sequence[str] = Field(default_factory=tuple)
	"""Really just here for debugging/testing, forces ROMs game source to only use certain platforms"""

	find_equivalent_arcade_games: bool = False
	'Get info from MAME machines of the same name'

	max_size_for_storing_in_memory: ByteSize = ByteSize(1024 * 1024)
	"Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup (unless it doesn't actually speed things up)"
