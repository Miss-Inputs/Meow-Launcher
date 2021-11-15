from meowlauncher.configured_emulator import ConfiguredEmulator
from meowlauncher.data.emulators import mame
from meowlauncher.games.mame_common.mame_executable import MAMEExecutable


class ConfiguredMAME(ConfiguredEmulator):
	def __init__(self, config):
		self.executable = MAMEExecutable(config.exe_path)
		super().__init__(mame, config)
