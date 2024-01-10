"""If a game source has settings that aren't anywhere else, they should go in here to be imported by meowlauncher.config"""


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
