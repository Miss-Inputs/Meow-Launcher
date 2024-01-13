from collections.abc import Sequence

from pydantic import Field

from meowlauncher.settings.settings import Settings


class ArcadeMAMEConfig(Settings):
	"""Configuration for MAME GameSource"""

	@classmethod
	def prefix(cls) -> str | None:
		return 'arcade'

	@classmethod
	def section(cls) -> str:
		return 'Arcade'

	source_files: str | None = None
	"""Only use drivers from certain source files, specified without suffix/directory (e.g. cps1, segas16b)
		Useful for testing/debugging, mostly, to avoid creating launchers for thousands of arcade machines"""

	drivers: Sequence[str] = Field(default_factory=tuple)
	"""Only use certain drivers, specified by basename
	Useful for testing/debugging, mostly, to avoid creating launchers for thousands of arcade machines, or to pick on just one specific machine"""

	skipped_source_files: Sequence[str] = Field(default_factory=tuple)
	"""List of MAME source files to skip (not including extension)
	For example, they might be non-working and you don't want to enable skip_non_working or you want to avoid the check altogether for more performance, maybe they are bothersome or uninteresting to you"""

	non_working_whitelist: Sequence[str] = Field(default_factory=tuple)
	'If exclude_non_working is True, allow these machines anyway even if they are marked as not working'

	exclude_non_arcade: bool = False
	'Skip machines not categorized as arcade games or as any other particular category (various devices and gadgets, etc)'

	exclude_pinball: bool = False
	'Whether or not to skip pinball games (physical pinball, not video pinball)'

	exclude_system_drivers: bool = False
	'Skip machines used to launch other software (computers, consoles, etc)'

	exclude_non_working: bool = False
	'Skip any driver marked as not working'
