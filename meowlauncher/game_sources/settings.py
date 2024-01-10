"""If a game source has settings that aren't anywhere else, they should go in here to be imported by meowlauncher.config"""


from collections.abc import Sequence
from pathlib import Path

from pydantic import Field
from meowlauncher.settings import Settings


class SteamConfig(Settings):
	@classmethod
	def section(cls) -> str:
		return 'Steam'

	@classmethod
	def prefix(cls) -> str | None:
		return 'steam'

	force_create_launchers: bool = False
	"Create launchers even for games which are'nt launchable"

	warn_about_missing_icons: bool = False
	'Spam console with debug messages about icons not existing or being missing'

	use_steam_as_platform: bool = True
	'Set platform in game info to Steam instead of underlying platform'


default_gog_folder = Path('~/GOG Games').expanduser()
default_wine_gog_folder = Path('~/.wine/drive_c/GOG Games').expanduser()


class GOGConfig(Settings):
	"""Configs for GOG source"""

	@classmethod
	def section(cls) -> str:
		return 'GOG'

	@classmethod
	def prefix(cls) -> str | None:
		return 'gog'

	folders: Sequence[Path] = (default_gog_folder,)
	'Folders where GOG games are installed'

	use_gog_as_platform: bool = Field(default=False, title='Use GOG as platform')
	'Set platform in game info to GOG instead of underlying platform'

	windows_gog_folders: Sequence[Path] = (default_wine_gog_folder,)
	"""Folders where Windows GOG games are installed"""

	use_system_dosbox: bool = True
	'Use the version of DOSBox on this system instead of running Windows DOSBox through Wine'


class ItchioConfig(Settings):
	@classmethod
	def section(cls) -> str:
		return 'itch.io'

	@classmethod
	def prefix(cls) -> str | None:
		return 'itch-io'

	itch_io_folders: Sequence[Path] = Field(default_factory=tuple, title='itch.io folders')
	"""Folders where itch.io games are installed"""

	use_itch_io_as_platform: bool = Field(default=False, title='Use itch.io as platform')
	"""Set platform in game info to itch.io instead of underlying platform"""
