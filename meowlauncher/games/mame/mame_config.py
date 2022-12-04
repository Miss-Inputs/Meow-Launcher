from collections.abc import Sequence

from meowlauncher.config.config import Config, configoption


class ArcadeMAMEConfig(Config):
	"""Configuration for MAME GameSource"""

	@classmethod
	def prefix(cls) -> str | None:
		return None
	
	@classmethod
	def section(cls) -> str:
		return 'Arcade'
	
	@configoption('Arcade')
	def source_files(self) -> str | None:
		"""Only use drivers from certain source files, specified without suffix/directory (e.g. cps1, segas16b)
		Useful for testing/debugging, mostly, to avoid creating launchers for thousands of arcade machines"""
		return None

	@configoption('Arcade')
	def mame_drivers(self) -> Sequence[str]:
		"""Only use certain drivers, specified by basename
		Useful for testing/debugging, mostly, to avoid creating launchers for thousands of arcade machines, or to pick on just one specific machine"""
		return []
		
	@configoption('Arcade')
	def skipped_source_files(self) -> Sequence[str]:
		"""List of MAME source files to skip (not including extension)
		For example, they might be non-working and you don't want to enable skip_non_working or you want to avoid the check altogether for more performance, maybe they are bothersome or uninteresting to you"""
		return ()

	@configoption('Arcade')
	def non_working_whitelist(self) -> Sequence[str]:
		'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'
		return ()

	@configoption('Arcade')
	def exclude_non_arcade(self) -> bool:
		'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'
		return False

	@configoption('Arcade')
	def exclude_pinball(self) -> bool:
		'Whether or not to skip pinball games (physical pinball, not video pinball)'
		return False

	@configoption('Arcade')
	def exclude_system_drivers(self) -> bool:
		'Skip machines used to launch other software (computers, consoles, etc)'
		return False

	@configoption('Arcade')
	def exclude_non_working(self) -> bool:
		'Skip any driver marked as not working'
		return False

	@configoption('Arcade')
	def use_xml_disk_cache(self) -> bool:
		"""Store machine XML files on disk
		Maybe there are some scenarios where you might get better performance with it off (slow home directory storage, or just particularly fast MAME -listxml)
		Maybe it turns out _I'm_ the weird one for this being beneficial in my use case, and it shouldn't default to true? I dunno lol
		Anyway TODO: This should be part of a Config associated with the MAME Emulator class, not the MAME GameSource class"""
		return True
