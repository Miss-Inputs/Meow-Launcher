from collections.abc import Sequence

from meowlauncher.config.config import Config, configoption

__doc__ = """Putting this here so roms_info can use it too, without causing a circular import by importing roms… hrm does this make sense?
TODO: Maybe .roms_config could just be accessible from ROMGame"""

class ROMsConfig(Config):
	"""Config specific to ROMs entirely as a game source"""
	@classmethod
	def section(cls) -> str:
		return 'ROMs'

	@configoption
	def skipped_subfolder_names(self) -> Sequence[str]:
		'Always skip these subfolders in every ROM dir'
		return ()

	@configoption
	def excluded_platforms(self) -> Sequence[str]:
		"""Really just here for debugging/testing, excludes platforms from the ROMs game source"""
		return []

	@configoption
	def platforms(self) -> Sequence[str]:
		"""Really just here for debugging/testing, forces ROMs game source to only use certain platforms"""
		return []
	
	@configoption
	def find_equivalent_arcade_games(self) -> bool:
		'Get info from MAME machines of the same name'
		return False

	@configoption
	def max_size_for_storing_in_memory(self) -> int:
		'Size in bytes, any ROM smaller than this will have the whole thing stored in memory for speedup (unless it doesn\'t actually speed things up)'
		return 1024 * 1024
